using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using ReadZen.App.Models;
using ReadZen.App.Services;
using Xunit;

namespace ReadZen.Tests.Services;

public class DictionaryStoreTests : IDisposable
{
    private readonly string _tempDir;
    private readonly DictionaryStore _svc = new();

    public DictionaryStoreTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), "readzen-dict-" + Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(_tempDir);
    }

    public void Dispose()
    {
        try { Directory.Delete(_tempDir, true); } catch { }
    }

    private static DictionaryFile SampleFile() => new()
    {
        SchemaVersion = 2,
        Entries = new List<DictionaryEntry>
        {
            new()
            {
                Id = DictionaryStore.ComputeId("水牯牛"),
                SourceTerm = "水牯牛",
                Senses = new List<DictionarySense>
                {
                    new()
                    {
                        SenseKey = null,
                        PreferredTarget = "water buffalo",
                        SearchAliases = new List<string> { "buffalo", "water ox" },
                        Status = "preferred",
                        Validation = "multi-source",
                        Explanation = "The ordinary draft buffalo; the ox one herds.",
                        Occurrences = new List<DictOccurrence>
                        {
                            new()
                            {
                                RelPath = "J/J24/J24nB137.xml", Kwic = "兩頭水牯牛", MasterName = null, Curated = true,
                                ActorAttribution = new DictActorAttribution
                                {
                                    Status = "reviewed-unnamed", Kind = "monk", ActorLabel = "unnamed monk",
                                    ActorRole = "questioner", RungsChecked = new List<string> { "line", "expanded-context", "section-header", "book-title", "tei-header", "parallel-passage" },
                                    ReviewedBy = "test", ReviewedUtc = DateTimeOffset.Parse("2026-07-13T20:15:00Z")
                                },
                                ContextMasters = new List<DictContextMaster>
                                {
                                    new() { MasterName = "Zhaozhou Congshen", Roles = new List<string> { "respondent" } }
                                },
                                EvidenceRole = "support"
                            }
                        }
                    },
                    new()
                    {
                        SenseKey = "Nanquan Puyuan",
                        MasterName = "Nanquan Puyuan",
                        PreferredTarget = "the realized self among the different species",
                        Status = "preferred",
                        Validation = "disputed",
                        RelatedTerms = new List<string> { "異類中行" }
                    }
                }
            }
        }
    };

    [Fact]
    public async Task Save_WritesBothV2AndLegacyFiles()
    {
        await _svc.SaveAsync(_tempDir, SampleFile());

        Assert.True(File.Exists(IDictionaryStore.GetV2Path(_tempDir)), "v2 file should exist");
        Assert.True(File.Exists(IDictionaryStore.GetLegacyPath(_tempDir)), "legacy file should exist");
    }

    [Fact]
    public async Task Save_LegacyFileIsBareArray_ReadableByOldShape_CorpusWideSenseOnly()
    {
        await _svc.SaveAsync(_tempDir, SampleFile());

        var legacyJson = await File.ReadAllTextAsync(IDictionaryStore.GetLegacyPath(_tempDir));
        // Old clients deserialize the legacy file as List<TermbaseEntry> — must stay a bare array.
        var legacy = JsonSerializer.Deserialize<List<TermbaseEntry>>(legacyJson,
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

        Assert.NotNull(legacy);
        var e = Assert.Single(legacy!);
        Assert.Equal("水牯牛", e.SourceTerm);
        // The corpus-wide sense wins the legacy row; the Nanquan-specific target must NOT leak.
        Assert.Equal("water buffalo", e.PreferredTarget);
    }

    [Fact]
    public async Task Save_ThenLoad_RoundTripsRichModel()
    {
        await _svc.SaveAsync(_tempDir, SampleFile());
        var loaded = await _svc.LoadAsync(_tempDir);

        var entry = Assert.Single(loaded.Entries);
        Assert.Equal("水牯牛", entry.SourceTerm);
        Assert.Equal(2, entry.Senses.Count);
        Assert.Equal(new[] { "buffalo", "water ox" }, entry.Senses[0].SearchAliases);
        var occurrence = Assert.Single(entry.Senses[0].Occurrences);
        Assert.Equal("reviewed-unnamed", occurrence.ActorAttribution?.Status);
        Assert.Equal("unnamed monk", occurrence.ActorAttribution?.ActorLabel);
        Assert.Equal("Zhaozhou Congshen", Assert.Single(occurrence.ContextMasters).MasterName);
        Assert.Equal("support", occurrence.EvidenceRole);
        var nanquan = entry.Senses.Single(s => s.SenseKey == "Nanquan Puyuan");
        Assert.Equal("disputed", nanquan.Validation);
        Assert.Contains("異類中行", nanquan.RelatedTerms);
    }

    [Fact]
    public async Task Load_MigratesFromLegacyWhenNoV2()
    {
        // Simulate a legacy-only repo: bare TermbaseEntry array, no v2 file.
        var legacy = new List<TermbaseEntry>
        {
            new() { SourceTerm = "佛性", PreferredTarget = "Buddha-nature", Status = "preferred", Note = "core term" }
        };
        var json = JsonSerializer.Serialize(legacy, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(IDictionaryStore.GetLegacyPath(_tempDir), json, new UTF8Encoding(false));

        var loaded = await _svc.LoadAsync(_tempDir);

        var entry = Assert.Single(loaded.Entries);
        Assert.Equal("佛性", entry.SourceTerm);
        var sense = Assert.Single(entry.Senses);
        Assert.Null(sense.SenseKey); // migrated as a corpus-wide sense
        Assert.Equal("Buddha-nature", sense.PreferredTarget);
        Assert.False(string.IsNullOrEmpty(entry.Id));
    }

    [Fact]
    public async Task Load_ReadsRichPublicShardsWhenV2IsAbsent()
    {
        var source = SampleFile();
        var shardRoot = Path.Combine(_tempDir, "termbase");
        Directory.CreateDirectory(shardRoot);
        await File.WriteAllTextAsync(Path.Combine(shardRoot, "009.json"),
            JsonSerializer.Serialize(source), new UTF8Encoding(false));
        await File.WriteAllTextAsync(Path.Combine(_tempDir, "termbase.index.json"),
            JsonSerializer.Serialize(new { Terms = new[] {
                new[] { source.Entries[0].SourceTerm, source.Entries[0].Senses[0].PreferredTarget }
            } }), new UTF8Encoding(false));

        var loaded = await _svc.LoadAsync(_tempDir);

        var entry = Assert.Single(loaded.Entries);
        Assert.Equal(2, entry.Senses.Count);
        Assert.Equal("reviewed-unnamed", Assert.Single(entry.Senses[0].Occurrences).ActorAttribution?.Status);
    }

    [Fact]
    public void ComputeId_IsDeterministicAndTrimInsensitive()
    {
        Assert.Equal(DictionaryStore.ComputeId("水牯牛"), DictionaryStore.ComputeId("  水牯牛 "));
        Assert.NotEqual(DictionaryStore.ComputeId("水牯牛"), DictionaryStore.ComputeId("異類中行"));
    }

    [Fact]
    public async Task Load_BackfillsIdForEntriesMissingOne()
    {
        // v2 file whose entry has no Id (e.g. hand-authored) — Normalize must backfill deterministically.
        var file = SampleFile();
        file.Entries[0].Id = "";
        var json = JsonSerializer.Serialize(file, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(IDictionaryStore.GetV2Path(_tempDir), json, new UTF8Encoding(false));

        var loaded = await _svc.LoadAsync(_tempDir);
        Assert.Equal(DictionaryStore.ComputeId("水牯牛"), loaded.Entries[0].Id);
    }
}
