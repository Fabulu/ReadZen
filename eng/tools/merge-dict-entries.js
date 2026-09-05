// eng/tools/merge-dict-entries.js
// Assembles gate-passed Zen dictionary entries into the community termbase.v2.json
// (rich) plus a downgraded legacy termbase.json, in the CbetaZenTranslations repo.
//
// Include criterion: a term dir counts as merge-ready when terms/<id>/STATUS == "done"
// (set only after it clears gate 3). Override with --status=<word> for dry runs.
// Existing v2 entries are preserved (by Id); existing legacy termbase.json entries not yet
// covered are migrated in as provisional single-sense entries so community data is never lost.
//
// Usage:
//   node eng/tools/merge-dict-entries.js                 # merge STATUS==done -> real repo
//   node eng/tools/merge-dict-entries.js --status=verified --out=<dir> --dry   # dry run
//
// NOTE: run with a normal Node (not the workflow sandbox); Date/crypto are available here.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const REPO = 'C:\\programmieren\\MergeWorkCbeta\\CBETA-Translator';
const RUN = path.join(REPO, 'runs', 'CLAUDE-RUNS', 'RUN-20260711-1248-full-cbeta-translation', 'dictionary-build');

const args = process.argv.slice(2);
const getArg = (name, def) => {
  const a = args.find(x => x.startsWith(`--${name}=`));
  return a ? a.split('=').slice(1).join('=') : def;
};
const TERMS_DIR = getArg('terms-dir', path.join(RUN, 'terms'));
const INCLUDE_STATUS = getArg('status', 'done');
const OUT_DIR = getArg('out', 'C:\\temp\\NewTranslationrepos\\CbetaZenTranslations');
const DRY = args.includes('--dry');
const REQUIRE_BASELINE = args.includes('--fresh');
const FRESH_BASELINE = readJsonSafe(path.join(RUN, 'fresh-build', 'corpus-baseline.json'));

const V2 = path.join(OUT_DIR, 'termbase.v2.json');
const LEGACY = path.join(OUT_DIR, 'termbase.json');
const INDEX = path.join(OUT_DIR, 'termbase.index.json');
const SHARD_DIR = path.join(OUT_DIR, 'termbase');
const NOW = new Date().toISOString();
const FORBIDDEN_ENGLISH = /\b(?:Buddhism|meditation|Bodhiteaching)\b/i;
// Explicit deterministic-ID migrations. When a source headword is corrected after an
// older artifact was published, preserve-by-ID must not retain the obsolete duplicate.
const ID_REPLACEMENTS = new Map([
  ['t_d69c18a98053', 't_bc9b4740f883'], // 吃茶去-derived ID -> canonical 喫茶去 ID
  ['t_d3c00df255f8', 't_d0b8619bf019'], // full-width-comma 雲從龍，風從虎 -> canonical ideographic-comma headword
  ['t_d0b24f7f47f8', 't_15201b52222e'], // unsupported 虎靠山處 headword -> attested 虎逢山勢 headword
  ['t_1a6cdc16c248', 't_968a2f97c9ff'], // duplicate-SourceTerm 一不成，二不是 legacy id -> canonical ComputeId id (occurrences merged into the survivor)
]);

function readJsonSafe(p) { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; } }
const readJson = readJsonSafe;
const computeId = term => 't_' + crypto.createHash('sha256').update(String(term).trim(), 'utf8').digest('hex').slice(0, 12);
const field = (o, ...keys) => { for (const k of keys) if (o && o[k] != null) return o[k]; return undefined; };

// --- collect merge-ready entries from term dirs ---
const collected = [];
for (const id of fs.existsSync(TERMS_DIR) ? fs.readdirSync(TERMS_DIR) : []) {
  const dir = path.join(TERMS_DIR, id);
  if (!fs.statSync(dir).isDirectory()) continue;
  const statusP = path.join(dir, 'STATUS');
  const status = fs.existsSync(statusP) ? fs.readFileSync(statusP, 'utf8').trim() : '';
  if (status !== INCLUDE_STATUS) continue;
  const obj = readJson(path.join(dir, 'entry.v2.json'));
  if (!obj) { console.warn(`skip ${id}: unreadable entry.v2.json`); continue; }
  // Accept a single DictionaryEntry OR a DictionaryFile envelope.
  const envEntries = field(obj, 'Entries', 'entries');
  const e = Array.isArray(envEntries) ? envEntries[0] : obj;
  const term = field(e, 'SourceTerm', 'sourceTerm');
  if (!e || !term) { console.warn(`skip ${id}: no SourceTerm`); continue; }
  if (REQUIRE_BASELINE && (!FRESH_BASELINE || field(e, 'CorpusBaselineSha256', 'corpusBaselineSha256') !== FRESH_BASELINE.manifestSha256)) {
    throw new Error(`fresh entry ${id} does not match frozen corpus baseline`);
  }
  if (!field(e, 'Id', 'id')) e.Id = computeId(term);
  // WrittenUtc is optional source metadata. Preserve null/missing values exactly:
  // inventing NOW here makes the rich artifact differ from its source and causes
  // most shards to churn on every merge.
  collected.push(e);
}

// --- merge with existing v2 (preserve only for the incremental legacy flow) ---
// A --fresh build is status-authoritative: preserving an older output would
// resurrect entries whose approval was later revoked or whose STATUS was
// deliberately demoted after semantic review.
const byId = new Map();
for (const e of collected) byId.set(field(e, 'Id', 'id'), e);
const existingV2 = readJson(V2);
const existingV2Entries = existingV2 && field(existingV2, 'Entries', 'entries');
if (!REQUIRE_BASELINE && Array.isArray(existingV2Entries)) for (const e of existingV2Entries) {
  const id = field(e, 'Id', 'id');
  const replacement = ID_REPLACEMENTS.get(id);
  if (replacement && byId.has(replacement)) continue;
  if (id && !byId.has(id)) byId.set(id, e);
}

// --- migrate existing legacy termbase.json entries not yet covered (don't lose community data) ---
const existingLegacy = readJson(LEGACY);
if (!REQUIRE_BASELINE && Array.isArray(existingLegacy)) {
  const haveTerms = new Set([...byId.values()].map(e => String(field(e, 'SourceTerm', 'sourceTerm') || '').trim()));
  for (const le of existingLegacy) {
    const term = String(field(le, 'SourceTerm', 'sourceTerm') || '').trim();
    if (!term || haveTerms.has(term)) continue;
    const id = computeId(term);
    const replacement = ID_REPLACEMENTS.get(id);
    if (replacement && byId.has(replacement)) continue;
    if (byId.has(id)) continue;
    byId.set(id, {
      Id: id, SourceTerm: term, CreatedBy: field(le, 'CreatedBy', 'createdBy') || null, WrittenUtc: field(le, 'WrittenUtc', 'writtenUtc') || NOW,
      Senses: [{ SenseKey: null, MasterName: null, PreferredTarget: field(le, 'PreferredTarget', 'preferredTarget') || '', AlternateTargets: field(le, 'AlternateTargets', 'alternateTargets') || [], Status: field(le, 'Status', 'status') || 'preferred', Explanation: null, Validation: 'provisional', Note: field(le, 'Note', 'note') || '', Occurrences: [], SourceTexts: [], RelatedMasters: [], RelatedTerms: [] }],
    });
    haveTerms.add(term);
  }
}

// Defensive: normalize any camelCase field names to the PascalCase schema before writing
// (a research agent occasionally slips into camelCase; the C# reader is case-sensitive).
const KEYMAP = { id:'Id', sourceTerm:'SourceTerm', createdBy:'CreatedBy', writtenUtc:'WrittenUtc', senses:'Senses',
  corpusBaselineSha256:'CorpusBaselineSha256',
  senseKey:'SenseKey', masterName:'MasterName', preferredTarget:'PreferredTarget', alternateTargets:'AlternateTargets', searchAliases:'SearchAliases',
  status:'Status', explanation:'Explanation', validation:'Validation', note:'Note', occurrences:'Occurrences', claimAnchors:'ClaimAnchors', claimText:'ClaimText',
  relPath:'RelPath', fromLb:'FromLb', toLb:'ToLb', kwic:'Kwic', curated:'Curated', attributionNote:'AttributionNote',
  actorAttribution:'ActorAttribution', contextMasters:'ContextMasters', kind:'Kind', actorLabel:'ActorLabel',
  actorRole:'ActorRole', rungsChecked:'RungsChecked', reviewedBy:'ReviewedBy', reviewedUtc:'ReviewedUtc',
  grammarEvidence:'GrammarEvidence', roles:'Roles', evidenceRole:'EvidenceRole',
  sourceTexts:'SourceTexts', relatedMasters:'RelatedMasters', relatedTerms:'RelatedTerms' };
const normKeys = o => Array.isArray(o) ? o.map(normKeys)
  : (o && typeof o === 'object' ? Object.fromEntries(Object.entries(o).map(([k, v]) => [KEYMAP[k] || k, normKeys(v)])) : o);

// Defensive: coerce field VALUES to the states the readers actually understand.
// - Validation outside {provisional, multi-source, disputed} renders no badge in the SPA and no
//   state in the desktop editor: "single-source" is the observed slip, and it means provisional.
// - Curated=false occurrences are dropped by DictionaryEditorWindowViewModel on the user's first
//   save of that sense, so a non-curated occurrence is data we would silently lose.
const VALIDATION = new Set(['provisional', 'multi-source', 'disputed']);
const STATUS = new Set(['preferred', 'allowed', 'deprecated', 'forbidden']);
const normValues = e => {
  for (const s of e.Senses || []) {
    s.SearchAliases = Array.isArray(s.SearchAliases)
      ? [...new Set(s.SearchAliases.map(x => String(x).trim()).filter(Boolean))]
      : [];
    const v = String(s.Validation || '').trim().toLowerCase();
    s.Validation = VALIDATION.has(v) ? v : 'provisional';
    const st = String(s.Status || '').trim().toLowerCase();
    s.Status = STATUS.has(st) ? st : 'preferred';
    for (const o of s.Occurrences || []) o.Curated = true;
    for (const o of s.ClaimAnchors || []) o.Curated = true;
  }
  return e;
};

// Sort by SourceTerm with an explicit Id tie-break. A stable sort alone left
// duplicate-SourceTerm families in Map order, which is products-first — so
// which twin came first depended on WHICH entries happened to be products in
// that install (R1a reordered six duplicate families this way). The Id
// tie-break makes the published order deterministic per pair regardless of
// cohort membership.
const byTermThenId = (a, b) => {
  const c = String(field(a, 'SourceTerm', 'sourceTerm')).localeCompare(String(field(b, 'SourceTerm', 'sourceTerm')));
  return c !== 0 ? c : String(field(a, 'Id', 'id') || '').localeCompare(String(field(b, 'Id', 'id') || ''));
};
const all = [...byId.values()].map(normKeys).map(normValues).sort(byTermThenId);
const forbiddenEntries = all.filter(e => FORBIDDEN_ENGLISH.test(JSON.stringify(e)));
if (forbiddenEntries.length) {
  const terms = forbiddenEntries.map(e => field(e, 'SourceTerm', 'sourceTerm')).join(', ');
  throw new Error(`Forbidden reader-facing English (Buddhism/meditation) in dictionary entries: ${terms}`);
}
const v2File = { SchemaVersion: 2, Entries: all };

// --- downgrade to legacy array (corpus-wide sense per entry) ---
const legacy = all.map(e => {
  const senses = field(e, 'Senses', 'senses') || [];
  const s = senses.find(x => field(x, 'SenseKey', 'senseKey') == null) || senses[0] || {};
  const note = String(field(s, 'Note', 'note') || '').trim();
  return {
    SourceTerm: field(e, 'SourceTerm', 'sourceTerm'), PreferredTarget: field(s, 'PreferredTarget', 'preferredTarget') || '',
    AlternateTargets: field(s, 'AlternateTargets', 'alternateTargets') || [], SearchAliases: field(s, 'SearchAliases', 'searchAliases') || [], Status: field(s, 'Status', 'status') || 'preferred',
    Note: note || (field(s, 'Explanation', 'explanation') || ''), CreatedBy: field(e, 'CreatedBy', 'createdBy') || null, WrittenUtc: field(e, 'WrittenUtc', 'writtenUtc') ?? null,
  };
}).sort((a, b) => a.SourceTerm.localeCompare(b.SourceTerm));

// --- web delivery artifacts: a tiny eager index + lazy per-term shards ---
// The reader underlines terms, which needs ONLY the headwords (a few KB); the prose
// (Explanation/Note/AttributionNote = ~90% of the bytes) is needed for one entry at a
// time, on click. So we ship:
//   termbase.index.json   [[term, firstGloss], …]  — eager, small, drives the highlighting
//   termbase/<NNN>.json   { Entries: [ …full… ] }  — lazy, fetched on click, cached
// The shard is keyed by the first character's code point so an entry's shard NEVER moves
// as the dictionary grows: adding a term rewrites one small file, not all of them.
const SHARD_COUNT = 256;
const shardOf = term => (String(term).codePointAt(0) || 0) % SHARD_COUNT;
const pad3 = n => String(n).padStart(3, '0');

const index = all.map(e => {
  const senses = field(e, 'Senses', 'senses') || [];
  const s = senses.find(x => field(x, 'SenseKey', 'senseKey') == null) || senses[0] || {};
  return [field(e, 'SourceTerm', 'sourceTerm'), field(s, 'PreferredTarget', 'preferredTarget') || ''];
});
// Search aliases must remain resolvable even when a duplicate headword entry is
// retired in favour of a canonical entry.  Keep the existing Terms contract and
// add an alias -> canonical headword map; ambiguous aliases are omitted rather
// than silently choosing one entry.
const canonicalTerms = new Set(index.map(([term]) => term));
const aliasOwners = new Map();
for (const e of all) {
  const sourceTerm = field(e, 'SourceTerm', 'sourceTerm');
  for (const sense of field(e, 'Senses', 'senses') || []) {
    for (const raw of field(sense, 'SearchAliases', 'searchAliases') || []) {
      const alias = String(raw).trim();
      if (!alias || alias === sourceTerm || canonicalTerms.has(alias)) continue;
      if (!aliasOwners.has(alias)) aliasOwners.set(alias, sourceTerm);
      else if (aliasOwners.get(alias) !== sourceTerm) aliasOwners.set(alias, null);
    }
  }
}
const aliases = Object.fromEntries([...aliasOwners]
  .filter(([, owner]) => owner)
  .sort(([a], [b]) => a.localeCompare(b, 'zh-Hant')));
const indexFile = { SchemaVersion: 2, Terms: index, Aliases: aliases };

const shards = new Map();
for (const e of all) {
  const id = shardOf(field(e, 'SourceTerm', 'sourceTerm'));
  if (!shards.has(id)) shards.set(id, []);
  shards.get(id).push(e);
}

console.log(`[merge] ${collected.length} term-dir entries with STATUS=${INCLUDE_STATUS}; total after preserve/migrate: ${all.length}`);
if (DRY) {
  console.log(`[merge] DRY RUN — would write ${V2} (${all.length}) + ${LEGACY} (${legacy.length}) + index (${index.length}) + ${shards.size} shards. No files written.`);
} else {
  fs.writeFileSync(V2, JSON.stringify(v2File, null, 2), 'utf8');
  fs.writeFileSync(LEGACY, JSON.stringify(legacy, null, 2), 'utf8');

  fs.writeFileSync(INDEX, JSON.stringify(indexFile), 'utf8');
  fs.mkdirSync(SHARD_DIR, { recursive: true });
  // Rewrite only shards whose content actually changed, so an unchanged shard keeps its
  // mtime and stays out of the commit; drop shards that no longer have any terms.
  const live = new Set();
  let written = 0;
  for (const [id, entries] of shards) {
    const p = path.join(SHARD_DIR, `${pad3(id)}.json`);
    live.add(`${pad3(id)}.json`);
    const body = JSON.stringify({ SchemaVersion: 2, Entries: entries });
    if (!fs.existsSync(p) || fs.readFileSync(p, 'utf8') !== body) { fs.writeFileSync(p, body, 'utf8'); written++; }
  }
  for (const f of fs.readdirSync(SHARD_DIR)) {
    if (f.endsWith('.json') && !live.has(f)) fs.unlinkSync(path.join(SHARD_DIR, f));
  }

  const kb = p => (fs.statSync(p).size / 1024).toFixed(1);
  console.log(`[merge] wrote ${V2} + ${LEGACY}`);
  console.log(`[merge] wrote ${INDEX} (${kb(INDEX)} KB, ${index.length} terms) + ${shards.size} shards in ${SHARD_DIR} (${written} changed)`);
}
