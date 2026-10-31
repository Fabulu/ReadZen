using ReadZen.App.Models;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace ReadZen.App.Services;

/// <summary>
/// Dual-file store for the rich Zen dictionary. termbase.v2.json is the source of truth for
/// new clients; termbase.json is a downgraded projection kept in sync for legacy clients.
/// </summary>
public sealed class DictionaryStore : IDictionaryStore
{
    public const int CurrentSchemaVersion = 2;

    private static readonly JsonSerializerOptions ReadOpts = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private static readonly JsonSerializerOptions WriteOpts = new()
    {
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };

    /// <summary>Deterministic id from the head term — every client derives the same id, so merges stay stable.</summary>
    public static string ComputeId(string sourceTerm)
    {
        var norm = (sourceTerm ?? "").Trim();
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(norm));
        return "t_" + Convert.ToHexString(bytes)[..12].ToLowerInvariant();
    }

    public async Task<DictionaryFile> LoadAsync(string root, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(root))
            throw new ArgumentException("Root is required.", nameof(root));

        var v2Path = IDictionaryStore.GetV2Path(root);
        if (File.Exists(v2Path))
        {
            var json = await File.ReadAllTextAsync(v2Path, Encoding.UTF8, ct);
            if (!string.IsNullOrWhiteSpace(json))
            {
                var file = JsonSerializer.Deserialize<DictionaryFile>(json, ReadOpts) ?? new DictionaryFile();
                return Normalize(file);
            }
        }

        // Public repositories keep rich entries in shards so no single Git blob
        // grows beyond the hosting limit. Local edited dictionaries still use v2.
        var shardRoot = Path.Combine(root, "termbase");
        if (Directory.Exists(shardRoot))
        {
            var shards = Directory.GetFiles(shardRoot, "*.json");
            if (shards.Length > 0)
            {
                var file = new DictionaryFile { SchemaVersion = CurrentSchemaVersion };
                foreach (var shard in shards.OrderBy(path => path, StringComparer.Ordinal))
                {
                    var json = await File.ReadAllTextAsync(shard, Encoding.UTF8, ct);
                    var part = JsonSerializer.Deserialize<DictionaryFile>(json, ReadOpts)
                        ?? throw new InvalidDataException($"Invalid dictionary shard: {shard}");
                    file.Entries.AddRange(part.Entries);
                }

                var indexPath = Path.Combine(root, "termbase.index.json");
                if (File.Exists(indexPath))
                {
                    using var index = JsonDocument.Parse(await File.ReadAllTextAsync(indexPath, Encoding.UTF8, ct));
                    var expected = index.RootElement.GetProperty("Terms").GetArrayLength();
                    if (file.Entries.Count != expected)
                        throw new InvalidDataException("Dictionary shard count differs from its index.");
                }
                return Normalize(file);
            }
        }

        // Older repositories without rich shards still use the legacy projection.
        var legacy = await LoadLegacyAsync(root, ct);
        return Normalize(MigrateFromLegacy(legacy));
    }

    public async Task SaveAsync(string root, DictionaryFile file, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(root))
            throw new ArgumentException("Root is required.", nameof(root));
        if (file == null)
            throw new ArgumentNullException(nameof(file));

        Directory.CreateDirectory(root);
        var normalized = Normalize(file);

        // Safety: never overwrite a non-empty file with empty data.
        var v2Path = IDictionaryStore.GetV2Path(root);
        if (normalized.Entries.Count == 0 && File.Exists(v2Path) && new FileInfo(v2Path).Length > 10)
            return;

        // 1. Write the rich v2 envelope.
        var v2Json = JsonSerializer.Serialize(normalized, WriteOpts);
        await WriteAtomicAsync(v2Path, v2Json, ct);

        // 2. Write the downgraded legacy array alongside it, for old clients.
        var legacy = DowngradeToLegacy(normalized);
        var legacyJson = JsonSerializer.Serialize(legacy, WriteOpts);
        await WriteAtomicAsync(IDictionaryStore.GetLegacyPath(root), legacyJson, ct);
    }

    // ---- migration / downgrade ----

    /// <summary>Build a v2 model from legacy entries: one entry per term, one corpus-wide sense each.</summary>
    public static DictionaryFile MigrateFromLegacy(IEnumerable<TermbaseEntry> legacy)
    {
        var file = new DictionaryFile { SchemaVersion = CurrentSchemaVersion };
        foreach (var e in legacy ?? Enumerable.Empty<TermbaseEntry>())
        {
            var term = e.SourceTerm?.Trim() ?? "";
            if (string.IsNullOrEmpty(term)) continue;

            file.Entries.Add(new DictionaryEntry
            {
                Id = ComputeId(term),
                SourceTerm = term,
                CreatedBy = e.CreatedBy,
                WrittenUtc = e.WrittenUtc,
                Senses = new List<DictionarySense>
                {
                    new()
                    {
                        SenseKey = null, // corpus-wide
                        PreferredTarget = e.PreferredTarget?.Trim() ?? "",
                        AlternateTargets = (e.AlternateTargets ?? new List<string>())
                            .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                            .Distinct(StringComparer.Ordinal).ToList(),
                        Status = string.IsNullOrWhiteSpace(e.Status) ? "preferred" : e.Status.Trim(),
                        Note = e.Note?.Trim() ?? "",
                        Validation = "provisional"
                    }
                }
            });
        }
        return file;
    }

    /// <summary>
    /// Project the rich model back to the legacy shape: one TermbaseEntry per term, taking the
    /// corpus-wide sense (or the first sense if none is corpus-wide). Master-specific senses are
    /// dropped from the legacy file — legacy clients only ever see the corpus-wide reading.
    /// </summary>
    public static List<TermbaseEntry> DowngradeToLegacy(DictionaryFile file)
    {
        var result = new List<TermbaseEntry>();
        foreach (var entry in file?.Entries ?? new List<DictionaryEntry>())
        {
            var term = entry.SourceTerm?.Trim() ?? "";
            if (string.IsNullOrEmpty(term) || entry.Senses == null || entry.Senses.Count == 0) continue;

            var sense = entry.Senses.FirstOrDefault(s => s.SenseKey == null) ?? entry.Senses[0];
            result.Add(new TermbaseEntry
            {
                SourceTerm = term,
                PreferredTarget = sense.PreferredTarget?.Trim() ?? "",
                AlternateTargets = (sense.AlternateTargets ?? new List<string>())
                    .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                    .Distinct(StringComparer.Ordinal).ToList(),
                Status = string.IsNullOrWhiteSpace(sense.Status) ? "preferred" : sense.Status.Trim(),
                // Legacy clients have only the Note field; fall back to the explanation so they still see prose.
                Note = !string.IsNullOrWhiteSpace(sense.Note) ? sense.Note.Trim() : (sense.Explanation?.Trim() ?? ""),
                CreatedBy = entry.CreatedBy,
                WrittenUtc = entry.WrittenUtc
            });
        }
        return result
            .Where(e => !string.IsNullOrWhiteSpace(e.SourceTerm))
            .OrderBy(e => e.SourceTerm, StringComparer.Ordinal)
            .ToList();
    }

    // ---- helpers ----

    private static async Task<List<TermbaseEntry>> LoadLegacyAsync(string root, CancellationToken ct)
    {
        var path = IDictionaryStore.GetLegacyPath(root);
        if (!File.Exists(path))
            return new List<TermbaseEntry>();

        var json = await File.ReadAllTextAsync(path, Encoding.UTF8, ct);
        if (string.IsNullOrWhiteSpace(json))
            return new List<TermbaseEntry>();

        return JsonSerializer.Deserialize<List<TermbaseEntry>>(json, ReadOpts) ?? new List<TermbaseEntry>();
    }

    private static DictionaryFile Normalize(DictionaryFile file)
    {
        file ??= new DictionaryFile();
        file.SchemaVersion = file.SchemaVersion <= 0 ? CurrentSchemaVersion : file.SchemaVersion;
        file.Entries ??= new List<DictionaryEntry>();

        foreach (var entry in file.Entries)
        {
            entry.SourceTerm = entry.SourceTerm?.Trim() ?? "";
            // Migrate-on-load: backfill deterministic id so all clients agree on the merge key.
            if (string.IsNullOrWhiteSpace(entry.Id) && !string.IsNullOrEmpty(entry.SourceTerm))
                entry.Id = ComputeId(entry.SourceTerm);

            entry.Senses ??= new List<DictionarySense>();
            foreach (var s in entry.Senses)
            {
                s.PreferredTarget = s.PreferredTarget?.Trim() ?? "";
                s.Status = string.IsNullOrWhiteSpace(s.Status) ? "preferred" : s.Status.Trim();
                s.Validation = string.IsNullOrWhiteSpace(s.Validation) ? "provisional" : s.Validation.Trim();
                s.Note = s.Note?.Trim() ?? "";
                s.AlternateTargets = (s.AlternateTargets ?? new List<string>())
                    .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                    .Distinct(StringComparer.Ordinal).ToList();
                s.SearchAliases = (s.SearchAliases ?? new List<string>())
                    .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                    .Distinct(StringComparer.OrdinalIgnoreCase).ToList();
                s.Occurrences ??= new List<DictOccurrence>();
                s.SourceTexts = (s.SourceTexts ?? new List<string>())
                    .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                    .Distinct(StringComparer.Ordinal).ToList();
                s.RelatedMasters = (s.RelatedMasters ?? new List<string>())
                    .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                    .Distinct(StringComparer.Ordinal).ToList();
                s.RelatedTerms = (s.RelatedTerms ?? new List<string>())
                    .Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => x.Trim())
                    .Distinct(StringComparer.Ordinal).ToList();
            }
        }

        file.Entries = file.Entries
            .Where(e => !string.IsNullOrWhiteSpace(e.SourceTerm))
            .OrderBy(e => e.SourceTerm, StringComparer.Ordinal)
            .ToList();
        return file;
    }

    private static async Task WriteAtomicAsync(string path, string content, CancellationToken ct)
    {
        var tmpPath = path + ".tmp";
        await File.WriteAllTextAsync(tmpPath, content, new UTF8Encoding(false), ct);
        File.Move(tmpPath, path, overwrite: true);
    }
}
