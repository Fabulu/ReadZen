# How to Make a Zen Dictionary Entry — the canonical guide

**Audience:** any agent asked to create/expand Zen dictionary entries. Read this whole file first.
It contains the full procedure PLUS the peripheral knowledge (the thesis, ewk, the pilot, the
pitfalls). Linked docs live in this run: `runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation/`.

---

## 0. The one-paragraph version
We are building a **Zen-to-Zen dictionary**: every meaning-bearing word in a Chan text is defined
from how **Zen Masters actually use it across the Zen corpus**, never from a general Chinese or
Buddhist dictionary. An entry is a **lexicographic article** with one or more **senses**, each
grounded in **verbatim occurrences** pulled from the Zen-scoped concordance, linked to the texts
and masters, with a prose explanation and an honest **validation** state. A reading is only trusted
when it holds across **multiple independent Zen sources**; single-source readings are `provisional`;
attribution fights are `disputed`. Renderings are **deflationary and literal** — no imported
mystical or general-Buddhist abstraction.

---

## 1. The thesis (why the gate exists)
- **Zen = the records of Zen Masters** — sayings (語錄/廣錄), lamp/transmission records (燈錄),
  koan/case collections + verse commentary (頌古). NOT sutras, doctrine, Pure Land, Vinaya, meditation
  manuals.
- **Cases are public historical records, not paradoxes.** `公案` is a "public case" / "case": a recorded
  encounter involving named people, questions, answers, tests, verdicts, and later masters' comments. Never
  recategorize a case as a riddle, paradox, parable, allegory, code, mystical story, or mind-stopping device.
- **The Four Statements are boundary conditions:** a separate transmission outside teachings; not based on
  the written word; directly pointing at the human mind; seeing nature and becoming buddha. The records are
  historical evidence of that tradition, not scriptures that turn Zen into doctrine or an instruction system.
- **~1000 years, one tradition.** Chan texts say the same thing across a millennium. **Consistency
  exposes frauds** — a reading that only fits generic Buddhism, or only appears once, is suspect.
- **This is a HARD GATE.** No word is translated except through a Zen-grounded entry. The dictionary
  is the foundation for translating the whole Zen corpus.

## 2. The Zen corpus — ALWAYS Zen-scope your searches
- The prescriptive Zen allowlist is **`Assets/Data/zen-corpus.json`**. It is
  **frozen at 489 CBETA files representing 482 independent works**, with baseline SHA-256
  **`8ea7e8ab756138567783a1d3f9e01648885c1732a782ba601ba478742adddaff`**. The authoritative
  lock and manifest are `fresh-build/state.json` and `fresh-build/corpus-baseline.json` — where this
  prose and the lock files disagree, **the lock files win**. A different
  file count, work count, or hash is a structural blocker, not a baseline to accept silently. Two
  retired baselines remain lawful on legacy entries (`legacyCorpusBaselines` in the lock):
  `aa125d97f0eb402daef67596f649888e27f51e20e5bddf96189344b406ef3bf1` (490 files / 483 works) and
  `42d32a5294365a4aa4d5aa2b5f11729e147cb44324f4535065047e946e7b3a2a` (494 files / 487 works). An
  entry still carrying a legacy sha is temporarily accepted ONLY while its retained evidence cites
  none of the retired sources (`D46n8930`; `G084n2084`, `G084n2086`, `T48n2023`, `X63n1245`).
  The set was filtered
  from `C:\woodblocks\ZEN_TEXT_WORKLIST.md` (records of masters, minus Pure Land / Vinaya / Tiantai /
  Huayan / sutras / stele inscriptions / eminent-monk bios / chronicles / lexicons / anthologies).
- **NEVER run a raw concordance over the whole CBETA canon** (`CbetaZenTexts/xml-p5` is ALL 4,990
  files — the misleadingly-named full canon, Buddhist material included). Contaminated counts and
  non-Zen occurrences are a real failure mode we already hit on the buffalo pilot (an occurrence came
  from a Qing encyclopedia `B16n0088` — dropped).
- In the app this is enforced by `IZenTextsService.IsZen(relPath)` (reads the allowlist). The evidence
  service filters by it automatically. If you grep raw XML, filter hits to the frozen 494-file allowlist
  and count independent support by the 487 `work_id` values, never by file paths.
- Corpus on disk: `C:\temp\NewTranslationrepos\CbetaZenTexts\xml-p5` (TEI XML; Chinese in `<body>`).

### 2a. Source authority — independence is not equality

The allowlist says that a source may be consulted; it does **not** make every surviving container
equally authoritative. Evidence selection and validation use this hierarchy:

Source tier never overrides corpus admission. A directly authored Japanese, sectarian, meditation,
Pure Land, Vinaya, or doctrinal work remains outside the Chinese Zen-record evidence boundary even
if its internal authorship is certain. Discovery of such a work in the allowlist is a corpus
contamination finding to quarantine and repair, not a Tier 1 promotion.

1. **Tier 1 — Zen-master-authored texts.** Letters, verses, prefaces, commentaries, or other writing
   for which a Zen master is the proved author. A book bearing a master's name, a compiler's
   attribution, or a later quotation does not by itself establish authorship.
2. **Tier 2 — recorded sayings and discourse records.** 語錄, 廣錄, 普說, 法語, and comparable
   records preserving a named master's speech, including authored case/commentary collections whose
   exact turn and source history are recoverable.
3. **Tier 3 — lamps and lineage compilations.** 傳燈, 五燈, 會元, 聯燈, 祖堂集, derivative lineage
   histories, and later lamp anthologies. These are the least verified witnesses. Use them for
   discovery, corroboration, recension history, or where no higher witness survives; never let them
   silently control a meaning over a Tier 1 or Tier 2 witness.

`multi-source` requires testimonial independence, not merely two filenames or two `work_id` values:

- at least two independent deployment families, **and**
- at least one retained Tier 1 or Tier 2 witness.

Two lamps cannot certify `multi-source` by themselves. Multiple editions, abridgements, lamp
recensions, or passive quotations of the same inherited case count as one deployment family. A later
master creates a new deployment only by actively using, answering, criticizing, or interpreting the
word in new surrounding speech. A lamp-only sense remains `provisional` and must say that no stronger
witness has yet been found.

Evidence dossiers search and present higher tiers first. Lamps are preserved as supplementary
witnesses rather than silently deleted, but a retained lamp must state whether it is a recension,
passive quotation, active redeployment, or independent use.

When an installed entry already contains lamp evidence, retain the **single best useful lamp witness
per sense** when adequate Tier 1/2 evidence survives. If adequate stronger evidence does not survive,
retain the smallest useful set of genuinely independent lamp families needed to document the term,
and disclose that last-resort dependence. Prefer the earliest complete witness, the clearest
attribution, or a recension with material historical value. Parallel lamps from the same deployment
are padding and must be dropped. Lamp-dependent support remains `provisional`; extra lamp filenames
must never manufacture `multi-source` confidence.

If exhaustive bounded exact/compact discovery leaves only one genuine lamp family, retain a useful
entry as `provisional` rather than padding or deleting it merely for rarity. The lane receipt and
independent review must explicitly confirm single-family exhaustion. A deduplication from several
parallel recensions to that one family is a publishable repair.

The same single-family rule applies when the sole surviving family is Tier 1 or Tier 2. Stronger
evidence must never be penalized for lacking a weaker lamp fallback, and a redundant lamp must not be
reintroduced merely to make a numeric gate pass.

## 3. The data model (schema v2) — `Models/DictionaryEntry.cs`
- `DictionaryFile { SchemaVersion, Entries[] }` → persisted as **`termbase.v2.json`** via
  `IDictionaryStore` (dual-file: also writes a downgraded legacy `termbase.json`). Repo:
  `C:\temp\NewTranslationrepos\CbetaZenTranslations\` (github.com/Fabulu/CbetaZenTranslations).
- `DictionaryEntry { Id, SourceTerm, Senses[], CreatedBy?, WrittenUtc? }` — **one article per term.**
  `Id = DictionaryStore.ComputeId(SourceTerm)` (deterministic; the community merge key).
- `DictionarySense { SenseKey, MasterName?, PreferredTarget, AlternateTargets[], SearchAliases[], Status,
  Explanation, Validation, Note, Occurrences[], SourceTexts[], RelatedMasters[], RelatedTerms[] }`.
  `SearchAliases` are non-display reader lookup phrases governed by item 15; they are not automatically
  accepted translations and must not be shown as an interpretation menu.
  **SenseKey = null → corpus-wide Zen sense; SenseKey set (usually a master's CanonicalName) →
  master-specific sense.** `Validation ∈ {provisional, multi-source, disputed}`.
  **Historical origin is NOT a master-specific meaning.** A master may introduce, popularize, or supply the
  earliest surviving witness for a usage that later appears across the corpus; that sense still gets
  `SenseKey = null`. Set a master key only when that master's *meaning* is genuinely distinct.
  NOTE on polysemy: a term with two genuinely distinct CORPUS-WIDE meanings (not tied to a master) may carry
  TWO senses both with `SenseKey = null` — put the PRIMARY/Zen-technical sense at `Senses[0]` (the code + legacy
  downgrade treat `Senses[0]` as primary). This is an accepted pattern (e.g. 末後句, 隨波逐浪); gates should NOT
  flag two null SenseKeys as a defect.
  **This is only the mechanics. For the TEST of WHEN to split a sense at all, see the depth gate, item 8
  (split for a different THING, never for a different READING) — under-splitting is the live defect.**
  `Status ∈ {preferred, allowed, deprecated, forbidden}`.
- `DictOccurrence { RelPath, FromLb?, ToLb?, CharOffset?, Kwic, MasterName?, ApproxDate?, Curated,
  AttributionNote? }`. **Occurrences hang off the SENSE, not the entry.** `Kwic` = verbatim Chinese.
  `Curated = true` → a lexicographer-chosen *defining* occurrence (the few we persist).

## 4. THE CONSTRUCTION PIPELINE (the only production path for every new entry)

**Audit reset, 2026-07-22.** The full-tree audit found at least one confirmed defect in 3,244 of
3,969 articles. Many were relationship, attribution-surface, or register defects rather than wrong
definitions, but an 81.7% incidence proves that treating those requirements as later cleanup passes
does not work. The rules in §5, `ATTRIBUTION_FIX.md`, and `ACTOR_AUDIT.md` are therefore **acceptance
specifications inside this pipeline**, not additional passes to schedule after construction.

The unit of work is one **SHA-bound evidence-and-decision worksheet**. Corpus retrieval happens once;
the author reads each retained complete case once and records every judgment needed by the article.
The public JSON is generated from that worksheet. A validator may reject a decision, but no later
stage repeats research merely because an earlier stage failed to record it.

### Stage 1 — admit the lexical unit and freeze its identity

1. Confirm that the candidate is a stable, meaning-bearing unit with an observable Chan job: an
   answer, test-question, verdict, capping phrase, raised case, institutional role, technical
   distinction, or corpus-specific bend. Shared religious vocabulary is not an exclusion category.
2. Reject only for a specific recorded reason: particle, clipped n-gram, catalogue matter, pure
   person/title routed elsewhere, duplicate, or contained-only wording with no Chan deployment.
3. Compute the deterministic ID; check exact headword duplicates, graphic/punctuation variants,
   containment, and near-duplicates before research. One headword produces one article.
4. Bind the frozen corpus hash. Search independence is counted by canonical `work_id`, never files,
   split volumes, or duplicate editions.

**Output:** one admitted ID and an explicit admission/near-duplicate ruling. No prose and no entry
JSON are written at this stage.

### Stage 2 — retrieve once; build complete-case evidence dossiers

Batch discovery through `web_index_kwic.mjs` and cross-check with `indexed_kwic.py`; use
`zc.bridged_count` for high-recall discovery and `zc.count` for exact apparatus-clean attestation.
Indexes locate candidates; they never prove an occurrence. For each candidate witness retained for
judgment, the dossier stores the exact headword-bearing KWIC, source offsets and `FromLb`/`ToLb`,
canonical `work_id`, registered English source title, section/header context, complete encounter or
case, recurrence/deployment-family identity, and a `zc.verify` result. It also records false
substrings, catalogues, quoted-only appearances, and recensions so they cannot return as evidence.

Retrieval and source parsing are transport. Authors and reviewers reuse the same immutable dossier;
independence requires independent judgment, not a second corpus scan.

### Stage 3 — read once; fill the semantic-and-actor worksheet

The author reads every retained **complete case**, not merely the KWIC. For each occurrence, record:

- the exact actor of the headword-bearing turn or action; if not a linked master, the precise
  `ActorAttribution` outcome and six-rung evidence;
- every contextual person and a closed-vocabulary role, keeping roster-linked `ContextMasters`
  separate from identified-unlinked `ContextActors`;
- the lexical job, literal graph floor, grammatical proof, sense assignment, deployment family,
  independent-work status, and whether it is an original use, quotation, recension, later raising,
  or commentary;
- every self-definition, contrast, counterexample, distinct deployment, inherited research lead,
  flyswatter deviation, and family relation found, with `keep`, `reject`, or `unresolved` and a reason;
- the sense-split test: split different things, never different readings or noun/verb packaging;
- one clean English target and search aliases, earned from the Chan evidence rather than an outside
  religious equivalence.

This is the only authorial research record. `MasterName` is the exact headword utterer only. A title,
section owner, respondent, subject, or later quoter cannot fill it. The author must be able to point
from every proposed public claim to one or more dossier rows before construction begins.

### Stage 4 — derive structure mechanically; write reader prose last

A governed emitter transforms the worksheet into the unchanged `entry.v2.json` schema. It derives
IDs, source texts, work spread, validation state, occurrence source labels, claim anchors, and all
roster-safe master links from the recorded decisions. It must refuse incomplete rows rather than
invent a template value. `RelatedMasters` is derived only from roster-canonical figures materially
used by the sense; identified-unlinked people stay visible in structured actor data and never become
broken links. `RelatedTerms` comes from explicit accepted family decisions, followed by reciprocal
and dangling-target checks—not from generic similarity or a prose template.

Fresh acquisition must use `fresh-build/EVIDENCE_DRAFT_TEMPLATE.json` and compile with
`compile_evidence_draft.py --new-entry`. `fresh-build/state.json` binds construction-pipeline version
2, `construction_authoring_preflight.py` invokes that mode automatically, and
`checkpoint_fresh_lane.py` refuses a report produced without it. Omitting the flag is therefore not
a legacy shortcut for a new article. Existing-entry repair remains on the §4b preservation path.

Only after the evidence, actors, senses, and relationships are frozen does the author write the
`Explanation`. Its opening tells an English reader what the term means and what job it performs here.
Every further claim names the relevant speaker/source and has an anchor. No imported equivalence,
untranslated technical loan, pipeline statistic, occurrence ID, audit vocabulary, repeated opening,
name dump, generic deployment inventory, or prose transferable unchanged to another headword may
reach the reader. Build metadata stays out of reader prose.

### Stage 5 — cheap preflight before another reader sees it

Run deterministic checks over the exact emitted bytes: parse/schema and deterministic ID; unique
headword; corpus hash; exact headword boundary and `zc.verify`; registered title; `work_id` source
independence; exact-actor XOR and closed roles; roster/link safety; sense distinguishability; depth
and claim-anchor completeness; relationship reciprocity/dangling targets; English-first/forbidden
register; duplicated/template prose; and emitter idempotence. A failure returns to the worksheet or
emitter. Do not spend independent-review time on mechanically broken output.

### Stage 6 — blind, source-first independent review

A different reader receives the ID and immutable dossier, writes the actor/sense/meaning ruling from
the complete sources **before seeing the proposed answer**, and only then compares the worksheet and
entry. Every new entry receives this semantic review; machine-derived fields receive deterministic
verification rather than a second hand transcription. A disagreement blocks that coordinate for
adjudication. Review must also prove that the prose claims are anchored, unique evidence was not
discarded, and no relationship was inferred beyond the cases.

Every new author/emitter/rule combination starts with a representative ten-entry canary. No batch
scales until the canary has zero substantive misses and the settled-throughput speed gate passes.
A systemic defect quarantines at most the canary. Purely mechanical checks may be sampled only after
their deterministic whole-cohort gate is green; semantic and exact-actor review is never sampled away.

### Stage 7 — seal and install atomically

Seal exact entry, worksheet, dossier, review, and gate hashes in a collision-free manifest. Install
only reviewed bytes, then run one changed-cohort gate and one whole-tree publication gate at the
documented checkpoint. Regenerate aggregates/index/shards once; prove count and byte parity; roll
back the atomic cohort on failure. Dashboard numbers come from the sealed manifest, never estimates.

### What this pipeline replaces

For **new construction**, this seven-stage path replaces separate post-authoring attribution,
actor, dangling-quote, relationship, prose-hygiene, depth-enrichment, and template-cleanup passes.
Those documents and §5 remain the test oracle used at Stages 3–6; they are not additional workflow
queues. Existing-entry repair still follows §4b because it must preserve already verified work.
`IRIYA_CONSTRUCTION_SPEED_MODE.md` changes batching and transport only and may not create a parallel
semantic or verification path.

## 4b. REFRESHING EXISTING ENTRIES — INFORMED, NOT BLIND

Existing entries contain expensive research even when their anchors, counts, English, or schema reflect an older
specification. Do not throw that evidence away merely to obtain uniform prose.

1. **Mechanical audit first:** run every existing KWIC through `zc.verify`, synchronize `FromLb`/`ToLb`, refresh
   every stated `zc.count`, and flag a curated KWIC that does not contain the headword. This work is deterministic
   and should be separated from semantic re-research.
2. **Use the old entry as an evidence inventory, not as authority:** carry forward verified self-definitions,
   contrasts, variants, rare deployment shapes, and hard-won attribution notes. Re-check each against the Chinese.
   Old glosses, sense keys, counts, and interpretations receive no presumption of correctness.
3. **Re-derive structure under the final rules:** primary Zen-technical sense first; master key only for a genuinely
   master-specific meaning; all prose under #0/#0b–#0f.
4. **Never rebuild an existing entry blind unless calibration explicitly requires blindness.** Blind drafting can
   reproduce the corpus search while still under-harvesting a self-definition already found in the earlier work.
5. **Targeted refresh before wholesale rebuild:** anchor/count repair and a final-spec English/sense/depth sweep
   usually preserve more knowledge at lower risk than deleting all entries. A full rebuild, if chosen for
   uniformity, must still be informed by the old evidence and followed by deterministic QA.

### Repair installation law — reviewed deltas, never silent rewrites

Every repair release must be installed as an immutable, auditable delta. This is the standard procedure, not an
exception for the current connectivity repair:

#### Bounded repair convergence law (speed and non-regression)

**Hard wall-clock gate.** Every ordinary repair **or fresh-construction** cohort starts exactly once with
`dictionary_timegate.py start --receipt <cohort-timegate.json> --cohort <label> --mode <repair|new> --ids <ids...>`.
The receipt cannot be overwritten or restarted. The cumulative deadlines are: viability 90 seconds,
construction 330 seconds, independent review 510 seconds, union correction/convergence 630 seconds,
and publication/push 720 seconds. Check the matching phase before handing off. The construction and
correction convergence commands must pass `--timegate <receipt> --timegate-phase <phase>`; an expired
receipt makes the gate fail with exit 124. Unfinished entries are deferred at the deadline. They do not
receive a same-cohort timer reset, a v2 loop, compensating overtime, or an expanded research mandate.
**Do not seal a passing receipt at viability, research, construction, or review handoff.** Sealing is
terminal for that cohort and is permitted only after publication succeeds or when the cohort is explicitly
stopped/deferred at a deadline. A sealed receipt cannot authorize a later phase and must never be replaced
with a fresh same-cohort timer.

**The timegate receipt is artifact zero.** Start it before loading or building the prior union, selecting
IDs, counting hits, running schema/template preflight, reading sources, preparing research, or creating or
editing a cohort constructor. No setup command may be performed “off clock.” Maintain a complete timestamped
command audit from receipt creation onward. The construction-start watchdog must receive the union,
selection, count, preflight, research, constructor, and command-audit artifacts and prove that every artifact
modification time and every audited command epoch is at or after `startedEpoch`. Any pre-receipt artifact or
command is a hard failure: stop continued browsing and reschedule rather than wrapping prepared work in a
fresh timer.

**Ordinary cohort size is three entries.** The measured end-to-end repair path for three entries—including
16-context independent review, one finite correction transaction, aggregate regeneration, integrity audit,
Windows-Git commit/push, and terminal sealing—completed in 584 seconds. Five-entry construction repeatedly
consumed the 330-second construction window before review could begin. Larger sets therefore belong in
separately authorized complex work; do not enlarge an ordinary cohort merely because selection is fast.
However, completed research and hash-bound partial artifacts are not discarded. A deadline receipt must
record their hashes, exact remaining finite failures, and last green checks. A later cohort may assign one
such partial as an ordinary slot when viability estimates no more than 90 seconds of finite completion
work. That is a new scheduled cohort, not an extension of the expired one. A partial gets at most one such
continuation; if it misses again, move it to the complex queue instead of repeatedly resuming it.

Ordinary lamp repair is minimum-defensible, not enrichment: first seek two genuinely independent Tier 1/2
families per sense. When those do not exist, retain the smallest defensible set of genuinely independent,
nonredundant lamp families as explicitly provisional last-resort evidence.
Add a third higher-tier family only when already present in the same retained case packet and needed for
a distinct sense, contrast, or actor ruling. Seven-family harvesting is prohibited in this lane. Complex
multi-sense, anonymous-quotation, or source-conflict entries that cannot be settled inside the same clock
move to the complex queue without blocking the ordinary cohort.

The same deadlines govern discovery and new articles. Candidate generation must batch-count and admit or
defer the whole candidate set inside the 90-second viability window. **Viability admission is deliberately
mechanical:** run one multi-term `zc_batch.py count` traversal, prove the exact ledger/collision set, compute
the dynamic floor, and prove that enough distinct Tier-1/2 works exist to make the floor plausible. Check the
viability deadline immediately after those operations. Do not spend the 90-second window reading complete
contexts, resolving exact actors, inventing witness families, or drafting prose; those semantic operations
belong to construction and independent review. The CLI count command must use `zc.batch_count` for the whole
term set, never one full `zc.count` corpus traversal per term. **Collision discovery is fail-closed:** the
selector must load the bounded prior selection manifests plus publication-only receipts through the shared
union helper, record every contributing path and hash, and require the expected nonzero prior-manifest count.
An empty or incomplete discovery set, a filename-pattern mismatch, or any selected ID already present in that
union is a hard failure; code must never construct `hardPass: true` independently of those checks. Independent
collision review must finish before construction begins. A fresh entry must reach canonical
construction and a green `pre_review_decile.py --timegate <receipt>` before the construction deadline.

**Staged cohort checkpoint watchdog.** Use `maintenance/cohort_checkpoint_watchdog.py`; do not demand a
fully adjudicated constructor at 120 seconds. The fail-closed checkpoints are:

1. Receipt zero precedes every cohort artifact and command; mechanical union/selection/count viability
   completes by 90 seconds.
2. By 120 seconds the watchdog must actually invoke one bounded context-extraction/research command. Its
   receipt binds the exact selected IDs, literal command, complete command audit, extraction-output SHA,
   research-skeleton SHA, and a nonempty source-candidate list for every ID. Every candidate carries exact
   `relPath`, `fromLb`, `toLb`, canonical `workId`, authority tier, matched term, bounded complete context,
   matched span, and verified context/span hashes; the research skeleton binds the exact candidate hashes.
   Every audited command epoch must follow receipt zero and its argv must equal the invoked argv. An empty or
   relPath-only marker and an unexecuted research script are not progress.
3. The adjudicated generic-engine config must be complete by 240 seconds. The watchdog invokes the authorized
   generic engine through the stable dictionary environment wrapper by 250 seconds. It validates the complete
   generic-v2 config, deterministic/scoped ID and term equality, dossier and worksheet payloads, allowed-root
   containment, authorized engine/wrapper SHAs, and the constructor command audit before process creation.
4. Compile entry by entry. The first canonical product and its hash-bound receipt must exist by 270 seconds.
   The checkpoint parses its identity and term and requires the real compiler report to hard-bind its bytes.
5. All products, real preclosure, manifest, and closure must complete by 330 seconds.
   Their exact ID scope and product hashes must agree, and closure must bind the current manifest and
   preclosure hashes.

Each missing, empty, late, hash-drifted, or wrong-ID checkpoint exits 124 and writes
`continuedBrowsingProhibited: true`. Preserve bounded partial artifacts and stop; later phases cannot borrow
time or substitute a hand-written success marker. Checkpoint receipts are immutable; an existing receipt path
is a hard failure rather than permission to overwrite history.

Independent source-first review ends at 510 seconds; unread candidates are deferred. Corrections end at
630 seconds; unresolved disagreements move to the complex queue. The merged checkpoint and Windows Git push
must finish by 720 seconds. New-entry depth targets are also minimum-defensible: first seek two independent
strong families per sense; where the corpus lacks them, use the smallest defensible independent lamp fallback
and mark the sense provisional. Add only evidence needed for a distinct sense, contrast, or actor decision. Open-ended
enrichment, seven-witness harvesting, and repeated certainty passes are prohibited in ordinary fresh work.

For an exact cohort of existing-entry repairs, run
`run_bounded_repair_gate.py --output <unique-report> <fresh entry IDs>` **before independent review**.
The gate runs the changed-entry compiler round trip, exact spans, attribution, source authority, titles,
depth, prose/template, count, deployment, and semantic-regression checks together; it also compares every
`RelatedTerms` sense shape with the exact currently installed entry and checks the protected roster files
against `HEAD`. Do not substitute a hand-assembled subset of these checks.

Independent reviewers return one unioned finite defect list. A single integration owner applies that whole
list as one corrective transaction, recompiles the affected entries, and runs the same bounded repair gate
once more. The correction is not complete until this deterministic convergence gate is green. This verification
is part of the correction transaction, not a new semantic-review loop. The release gate then asserts the
already-green hashes; it must not be the first place that a title string, actor label, graph baseline, exact span,
or other deterministic defect is discovered.

Do not run the wave-global frozen-historical or obsolete wave-lineage baselines as author preflight for an exact
repair cohort. They can fail because of unrelated already-published changes and create no information about the
candidate products. Run those global controls at their own release checkpoint. Never ignore a changed-entry
failure merely because a global authority is stale.

1. **Freeze before copying:** a final closure and independent-review artifact must name every repaired entry and
   bind the entry and evidence-worksheet bytes by SHA-256. The install manifest must also bind the current installed
   baseline so a stale repair cannot overwrite newer work.
2. **Reconcile post-closure improvements explicitly:** if another reviewed lane legitimately strengthens an entry
   after its closure (for example, adding the reciprocal half of a cross-lane relationship), do not discard the
   improvement, silently edit the old closure, or waive hash checking. Produce a small superseding-delta receipt
   that binds the old closure, the later review/closure, the exact old and new hashes, and the reason. All other rows
   must still match their original closure.
3. **Dry-run the exact installation:** before mutation, require closure/review integrity, current-baseline parity,
   schema and semantic gates, duplicate checks, relationship symmetry, and aggregate/index/shard expectations to
   pass against the exact bytes that will be installed.
4. **Copy atomically with rollback:** back up every destination, install the staged entry bytes, and roll back the
   whole release on any copy, gate, merge, parity, or receipt failure. Never leave a partially installed lane.
5. **Post-copy prove both layers:** first prove byte-for-byte parity between installed entries and the reviewed staged
   entries. Then rerun worksheet-dependent semantic/connectivity gates against the hash-identical staged entries and
   their worksheets; installed `terms/` directories are not required to contain draft worksheets.
6. **Regenerate, never hand-edit, publication artifacts:** run the canonical merge after each successful release and
   require aggregate count, index count, and shard count to agree. Record before/after counts, timings, hashes,
   rollback outcome, and hard-pass status in the install receipt.
7. **One headword, one deterministic article:** before installation and again after merging, require both unique IDs
   and unique `SourceTerm` values. Recompute every expected ID as `t_` plus the first twelve hexadecimal digits of
   SHA-256 over the exact UTF-8 `SourceTerm`; an entry under any other ID is a normalization/collision defect, never
   a second article. If duplicate headwords contain different evidence or prose, merge every valid sense, occurrence,
   anchor, relationship, and source into the deterministic article and independently review the merged result before
   deleting the noncanonical directory. Equal drafts may be removed only after proving equality apart from the ID.
8. **Adversarial old-reading preservation gate:** an audit finding is a candidate, never permission to rewrite.
   Before editing, the repairer must reconstruct the complete source turn and actively state the strongest case that
   the installed value is correct. The repair ledger must bind the old entry hash and record: the challenged field,
   old value, proposed value, exact Chinese evidence, turn grammar, source/section identity, parallel witnesses and
   counterevidence, and one ruling: `KEEP_OLD`, `REPAIR`, or `PRESERVE_CONFLICT`. No `REPAIR` is valid merely because
   another entry, a title heuristic, a roster alias, or an auditor says so. When recensions genuinely disagree, store
   the disagreement; never force one voice into unanimity.
9. **Source-first independent repair review:** the independent reviewer receives the entry ID and evidence packet but
   writes an actor/sense/meaning ruling from the complete source before seeing the repairer's proposed after-value.
   Only then may the reviewer compare old and proposed values. A disagreement blocks that coordinate for adjudication;
   it does not get averaged away. Review must also prove that all unlisted fields and all unique old evidence remain
   byte-identical. Deletion or merging requires an explicit evidence-conservation table.
10. **Canary, regression, and rollback:** install no large repair lane until a representative canary contains zero
    substantive review failures. Rerun known public-feedback exemplars and every changed coordinate after repair, then
    rerun whole-tree schema, exact-evidence, deterministic-ID, unique-headword, relationship, forbidden-register, and
    aggregate/index/shard gates. Preserve immutable before bytes and roll back the complete atomic lane on any failure.
7. **No repair-by-deletion and no collateral mutation:** preserve verified evidence, anchor dangling quotations,
   touch only manifest-listed dictionary entries and generated dictionary artifacts, and never modify the lineage
   roster as part of dictionary repair.

Any missing review, unexplained hash drift, failed post-copy gate, or parity mismatch is a structural blocker. The
answer is an explicit reviewed delta or rollback—not an ad hoc rewrite and not relaxing the gate.

## 5. ANTI-PATTERNS (things we have already been burned by)

- **⛔ #0, THE GOVERNING RULE — DESCRIBE, DO NOT INTERPRET. The Zen texts are the measurement, not the
  annotator's interpretation.** An `Explanation` reports (a) the literal sense of the graphs, (b) the term's
  attested deployment in the corpus, quoting what masters actually said, and (c) genuinely structural facts
  (which cases, which masters, don't-cross-attribute). It MUST NOT assert the master's intent, the doctrinal
  "point," or the spiritual force of the term. Ban this vocabulary unless a corpus text literally says it:
  "meant to / in order to / the point is / this smashes / deflationary / throws him back on himself / expresses /
  symbolizes / represents." The burden of proof is on any claim of meaning beyond the literal, and the corpus
  almost never pays it. **(EXCEPTION — the attestable cultural deviation: see #0g, the flyswatter test.** The ban
  on "symbolizes/represents" targets IMPORTED mystical/doctrinal symbolism. It does NOT forbid stating an
  observable cultural/institutional fact about how the corpus deploys a word — e.g. that the whisk is the
  master's teaching-seat implement. That deviation is grounded in usage, not projected, and it is exactly what a
  Zen dictionary exists to surface.) **Offering a *menu* of readings is still interpreting** — three unproven readings are
  three violations, not neutrality. Where the tradition's force is contested, the honest entry states only that
  the texts record the word without gloss and takes no position; it does not enumerate the AI's guesses.
  - Worked example — `乾屎橛` ("a dry shit-stick"): the early draft asserted it was "meant to disgust… no positive
    doctrinal content," then a "corrected" version smuggled interpretation back as a three-reading menu
    (disgust / immanence / disposable). BOTH were wrong. Test the user gave: *"Do you mean disgust when you say
    toilet paper?"* You don't — you mean toilet paper. A shit-stick is the latrine wiping-tool; name the object,
    cite where it is spoken (Linji on 無位真人; Yunmen on 如何是佛; Deshan on the buddhas), and STOP. The final
    entry ends: "The texts assign the word no gloss beyond its literal sense, and neither does this entry."
  - This subsumes the older "fakeout" and "deflationary/literal" notes below: render what the words say; add nothing.
  - **BUT NOT thin.** "Do not interpret" is NOT "say less" — an empty entry is a failure too. Get the MAXIMUM out
    of the text: the definition must *emerge from accumulated attested usage*, not from a gloss of significance.
    Mine and quote (all grep-verified, from allowlist texts): (i) **in-corpus self-definitions** — where a text
    literally defines the term (眾中謂之著語; 於諸境上，心不染，曰無念; 本分事者，即當人本命元辰之落處也) — these are the
    richest describe-only content, foreground them; (ii) the full **deployment range** — is it spoken as an answer,
    an epithet, a verdict, a test-question, a genre label? (observable, not interpretive); (iii) **contrasts the
    texts themselves draw** (殺人刀 vs 活人劍 by one author; 分外 as the antonym of 本分事); (iv) **attested
    collocations & variants** with grep counts. Target: dense with corpus fact, zero imported reading. The former
    binary test—“is this in the text or my conclusion?”—was too crude and produced calque-only entries. Use item
    11 instead: keep direct statements and the smallest reproducible inference from anchored corpus evidence;
    cut conclusions that require outside doctrine, symbolism, intent, psychology, or background.

- **⛔ #0b — ZEN ONLY. Purge FIVE families of imported framing.** This is a ZEN dictionary. **Zen = the Chinese
  Chan textual record** (the allowlist corpus). It is NOT Japanese Zen-Buddhism, and **Zen has no "practice"** —
  the texts record sayings and encounters, not techniques. **CHINESE CHAN ONLY: no Dōgen (道元), no Japanese
  masters/sources, no Japanese-Zen concepts. LITMUS — if you need Japanese to describe a concept, it is
  certified NOT Zen: drop it (and reconsider whether the term belongs).** The Chan masters routinely MOCKED
  general-Buddhist piety, so never let it into a gloss. Base ALL understanding on the Zen corpus, nothing else.
  Banned framings —
  cut every one unless a Zen text literally says it (and even then, quote it as *the text's* claim, not the entry's):
  1. **Buddhist-doctrine framing** — importing general Mahāyāna/Abhidharma concepts as the meaning (śūnyatā/
     "emptiness" as doctrine, "defilements/attachments/karma/saṃsāra/nirvāṇa", "Buddha-nature as a metaphysical
     essence", six pāramitās, etc.). The Chan text's *use* of a word ≠ the Buddhist doctrine behind it.
  2. **Meditation / mindfulness framing** — "meditation, meditative, mindfulness, concentration, calm-abiding,
     tranquillity, awareness (as a practice)". The masters disdained quietistic sitting (默照/枯木死水); do NOT
     gloss any term as a meditation technique or endorse meditation. **`禪` is NEVER "meditation"** and
     untranslated Indic forms are not English definitions. Render `禪` as Chan/Zen or use the contextual English
     established by its attested predicates. Thus `禪床` = "Chan seat" (furniture), `坐禪` = "sitting Chan",
     `禪定` receives an evidence-grounded English rendering such as "Chan composure," and `參禪` = "investigate
     Chan" — never "meditation," "dhyana," or an unexplained Indic loanword.
  3. **Present-moment framing** — "the present moment, be here now, present-moment awareness, present scene,
     living in the now". Present-momentism is a modern-mindfulness overlay the Chan texts do not preach. `當下`
     = "on the spot / right there / immediately"; `目前` = "before your eyes / in front of you" — literal, not
     "the present".
  4. **Dualism framing** — "dualistic thinking, duality, non-dual, nonduality, transcend duality". (This is the
     original `凡情聖見`→"dualistic thinking" fakeout.) `分別` = "to distinguish / discrimination" (literal); do
     NOT inflate it into "dualistic parsing".
  5. **Practice / method framing** (and Japanese-Zen overlay) — "practice, method, technique, training,
     cultivation, discipline, exercise, huatou, huatou practice, koan practice, zazen, kōan-introspection, kenshō,
     satori". **Zen has no practice**; the texts record sayings and encounters. When a master says an action
     (`看箇無字` "look at the word 無"; `參` "investigate"; `起疑情` "raise the doubt"), render that literal
     instruction — do NOT re-categorize it as "a practice/method/technique," and do NOT import Japanese-Zen
     vocabulary. `看箇無字` is "look at the word 'no'": `無` is translated as **no**, not left as Japanese
     “Mu,” turned into a mantra, or recategorized as a meditation exercise.
     **`話頭` is not “huatou.”** Do not use that untranslated loanword as a target or explanatory category;
     translate the attested occurrence as the word, saying, remark, question, conversational thread, or other
     English warranted by its case. **`坐禪` is not Japanese zazen and not a meditation technique.** Treat it as
     a separate Chan term and derive its sense from Chinese Chan occurrences. Search explicitly for the corpus's
     mind-king/seat language (`心王`, `座`, and related collocations), but report “the seat of the mind-king” only
     where the Chinese evidence supports it.
     **Current calibration result:** exact searches for `心王座`, `心王之座`, `坐即心王`, and `心王安坐` return
     zero, so do **not** state that `坐禪` means “seat of the mind-king.” `禪床` is strongly attested as literal
     **“Chan seat”** furniture. For `坐禪`, foreground the Platform Record's direct graph-by-graph definitions and
     the corpus's recorded critiques (including Nan'yue's tile exchange and Linji's hall statement), without
     converting either the definitions or critiques into a method.
  If a term genuinely lives in Buddhist/meditation/present/dual/practice language in the wider tradition, the
  honest Zen entry either (a) shows how the CHAN corpus actually deploys it — often CRITICALLY, quote the
  critique — or (b) gives only the literal graphs. Never adopt the imported frame as the definition.

  - **⚠ CARVE-OUT — PRECEPTS (戒/律) ARE IN SCOPE. Do NOT filter them out under the "no practice" ban.** A precept is
    NOT a "practice"/technique — it is a hard RULE, and the masters discuss it constantly: `戒` alone is **9,514 hits
    in 412 allowlist files**, one of the largest terms in the corpus (it was wrongly omitted from the whole wave plan).
    By our own litmus — *if the Zen Masters talk about it, we are interested* — the precept vocabulary must be authored:
    戒, 律, 受戒, 持戒, 破戒, 戒律, 毘尼, 清規, 五戒, 菩薩戒, 戒定慧, 律師, 戒法, 戒體, 開遮, 無相戒, 心戒, 波羅提木叉.
    Define each by the ZEN deployment (#0g): show where the masters MOCK mere rule-keeping (`律師`, the Vinaya master,
    is frequently a foil) and where they RE-GROUND it (`無相戒` "formless precepts", `心戒` "mind-precept"). Report what
    the corpus says — do not decide in advance that Zen either upholds or discards precepts.
    - **The precept-VIOLATION cases show what the gate costs** — the corpus groups them (南泉斬貓 Nanquan cuts the cat,
      歸宗斬蛇 Guizong cuts the snake, 丹霞燒佛 Danxia burns the buddha). They are only legible against a real precept:
      a master who keeps it KILLS, and stands to lose everything. The corpus marks the weight itself — asked what the
      cat case means, the answer is `須是南泉始得` ("it takes a Nanquan to pull it off"); Guizong kills the snake and is
      SCOLDED, yet leaving a poisonous snake alive would kill the monks. Author these cases against that frame — but
      only assert the precept reading if a PASSAGE attests it (see the research task in `REQUESTED_TERMS.md`).

  - **⚠ GATE 2 — PUBLIC INTERVIEW / QUESTION-AND-ANSWER is non-negotiable Zen.** Zen Masters answer questions from
    anyone, anywhere, at all times, and expect the same of their community. **Question-and-answer is the sword and
    claw of the Zen sect** — it is not an optional genre, it is the mode of the tradition. The Q&A machinery must be
    fully covered: `問答` (question-and-answer, 1,242 hits), `爪牙` ("claws and fangs" — the school's weapons, 638),
    `機緣`, `徵` (to probe), `室中` (the entering interview), `問話`, `普說`, `秉拂` (take up the whisk = preside and
    answer — ties directly to the 拂子 authority deviation), `垂問`, `舉問`, `劍刃`, `對機`, `代語`. Most of these were
    missing from the wave plan. A "Zen" reading that makes the tradition silent, private, or interview-free is wrong.

- **⛔ #0c — DESCRIBE IN ENGLISH; TRANSLATE EVERYTHING. This is a dictionary.** The `PreferredTarget`,
  `Explanation`, and `Note` must READ IN ENGLISH and translate the Chinese, not leave the reader staring at
  untranslated graphs. `看箇無字` = **"look at the word 'no'"** (無 = "no"), not "look at 無" and not
  "看箇無字" bare. Translate every term and phrase you discuss (佛 = "buddha"; 無 = "no"; 主人公 = "the
  master of the house"). Chinese appears ONLY as quoted evidence — and every quoted Chinese phrase gets an
  English rendering right beside it, e.g. `狗子還有佛性也無` ("does a dog have buddha-nature or not?"). Chinese
  in parentheses as a reference is fine — "look at the word 'no' (看箇無字)" — but it ALWAYS carries its English;
  never leave Chinese untranslated. The `Kwic` field stays verbatim Chinese (it is the search anchor / evidence)
  — but nowhere else should Chinese stand without its English.
  Do not automatically leave `法` as the religious loan “Dharma.” Translate the compound's corpus function:
  `法嗣` in lamp headings is **“lineage heir,”** because it records a teacher-successor relation. For terms such as
  `法眼` and `法身`, derive the English target from their Chinese Chan occurrences and explicit comparisons; do not
  import a Buddhist-glossary definition merely because “Dharma eye/body” is familiar English.
  The same applies to phonetic borrowings: do not leave `三昧` as unexplained “samādhi.” In this termbase render it
  **“complete command”** and let each named compound's direct Chan definition and predicates establish its local use.
  This English-first gate applies to Indic technical loans generally: **prajna/prajñā, dhyana/dhyāna, and
  samadhi/samādhi may not stand as PreferredTargets, AlternateTargets, or explanatory substitutes.** Translate the
  attested use into English (for example, “complete discernment,” “composure,” or “complete command” where the
  entry's own evidence warrants those words). A transliteration is permitted only when the corpus or a linguistic
  note is explicitly discussing that form, never as the definition itself. Proper names and source titles remain
  proper names rather than targets for mechanical translation.
  **Why this is a fidelity rule, not merely a style preference:** imported equivalence is not evidence. A familiar
  Indic or modern umbrella term arrives carrying meanings assembled from other Buddha-using traditions. Substituting
  it for a Chinese Zen term silently conflates those traditions and lets an assumed outside counterpart define the
  entry. Zen repeatedly gives inherited words distinctive jobs in public questions, answers, contrasts, rebukes,
  titles, and cases. Therefore no entry may derive its English meaning from a presumed cross-tradition equivalent;
  the rendering must be earned anew from the Zen corpus's own predicates, grammatical roles, contrasts, explicit
  glosses, and observable deployment. Similar-looking vocabulary elsewhere is a research lead at most, never the
  definition authority.

- **⛔ #0d — THE ZEN RECORD, NOT THE WESTERN MYTH.** Treat the allowlist as the documentary record of one
  Chinese Chan tradition across roughly a thousand years. The unit of study is what named masters and students
  said and did, how other masters tested it, and how later masters quoted and commented on the same cases.
  - `公案` = **public case / case**, not "koan" as a Japanese religious technique. A case is a public record of
    real people in an encounter. Preserve names, speaker turns, actions, chronology, and later commentary.
  - Cases are NOT paradoxical anecdotes, riddles, parables, allegories, secret codes, nonsense stories, or
    devices for stopping thought. Apparent strangeness is a translation/context problem to investigate, never
    permission to mystify.
  - Zen is NOT tranquility, peace, quietism, meditation, mindfulness, present-momentism, New Age spirituality,
    reincarnation/afterlife doctrine, self-improvement, or a technique. If a text literally mentions quiet,
    rebirth, sitting, doubt, or an action, translate that occurrence exactly; never promote it into "what Zen is."
  - Do not preserve the romanizations “huatou,” “mu,” “koan,” “zazen,” or “zuochan” as if they named special Zen
    objects or techniques. Translate `話頭`, `無`, `公案`, and `坐禪` into evidence-backed English from their
    Chinese Chan usage; use transliteration only as a searchable cross-reference, never as the definition.
  - The Four Statements are the orientation: outside teachings; not based on written words; direct pointing at
    mind; see nature and become buddha. Do not turn the Statements themselves into a doctrine. Use them to catch
    imported framings that make textual authority, obedience, ritual, or altered states the definition of Zen.

- **⛔ #0e — TRANSLATE ZEN AS A CORPUS-SPECIFIC LANGUAGE.** "Zen texts are written in Zen" means that ordinary
  Literary Chinese graphs, Buddhist loanwords, stock allusions, and master-specific idioms acquire their usable
  English meaning from this corpus. A general Chinese dictionary supplies candidate graph senses, not the final
  Zen definition; a Buddhist dictionary, Japanese glossary, or familiar English religious term is even less
  authoritative.
  1. **Corpus context outranks fluency theater.** Resolve a term through its sentence, speaker, case, text genre,
     parallel occurrences, later comments on the same case, and multi-master consistency. Translation is an
     evidence-backed hypothesis accountable to the Chinese.
  2. **Do not collapse traditions through shared English.** Words such as "enlightenment," "mind," "nature,"
     "practice," and "meditation" can make unrelated systems sound alike. Re-derive the Zen referent instead of
     assuming that a familiar English religious word carries it.
  3. **Literal is the floor, not the whole job.** Start with graph values, then explain attested Zen usage in
     plain English. Identify names, places, quotations, puns, legal/bureaucratic language, and recurring cases.
     Put the needed context in `Explanation`, `Note`, or `AttributionNote`; an opaque literal calque is not a
     finished translation.
  4. **No unfootnoted semantic leap.** If the best English target is non-literal, state the literal wording and
     show the corpus evidence for the choice. If the evidence does not decide, keep the literal target and mark
     uncertainty rather than importing doctrine.
  5. **Translations and AI are leads, never sources.** Compare existing translations and use AI for segmentation,
     candidate glosses, names, and allusion leads, but verify every decision against the CBETA Chinese, the Zen
     concordance, and exact cases. Short spans + character breakdown + cross-corpus checking beat fluent invention.

- **⛔ #0f — DEPTH GATE: HARVEST EVERYTHING HIGH-VALUE BEFORE DRAFTING.** Mechanical perfection is necessary
  but not sufficient. An entry with perfect anchors that omits a found self-definition is still a failed entry.
  Before finishing each sense, search and record in `WORK.md`:
  1. **Every definition formula:** `X者`, `所謂X`, `謂之X`, `名為X`, `喚作X`, `何謂X`, `如何是X`, plus obvious
     punctuation/word-order variants. Include every distinct self-definition in the explanation, attributed to
     its author; if excluded, record the reason.
  2. **Every distinct deployment shape:** answer, question, appraisal, rebuke, verdict, instruction, case label,
     quotation, verse, prose comment, and historical retrospective.
  3. **Text-drawn relations:** contrasts, antonyms, enumerations, head/tail or other morphological variants,
     fixed collocations, and later comments on an earlier case.
  4. **Period, genre, and master spread:** early encounter/lamp material, a master's own record, case commentary,
     and later instructional records where attested. Do not mistake one prolific late text for corpus breadth.
  5. **A final omission audit:** compare the research notes to the draft sentence by sentence. Every unique
     high-value finding must be included, explicitly rejected with a reason, or marked unresolved. The usual
     “4–6 occurrences” target is not a cap when additional evidence is lexicographically unique.
  6. **⛔ FREQUENCY- AND DEPLOYMENT-SCALED DEPTH IS LAW — never draft to a fixed witness quota.** A flat pattern
     such as exactly three occurrences per entry is evidence of under-harvesting, not consistency. Scale the
     evidence set to the size and diversity of the concordance. A high-frequency or category-defining term must
     normally preserve representative anchors for every lexicographically distinct high-value deployment found:
     direct definition, named formula, institutional use, public interview, contrast or criticism, case-level use,
     re-grounding or inversion, important compound/family relation, and meaningful period/master/genre spread.
     **Count independent works, never XML files.** `Assets/Data/zen-corpus.json` assigns every file a
     `work_id`; split volumes and duplicate canon editions share one ID. `multi-source` requires exact
     lexical evidence from at least two distinct `work_id` values. Two files from one work remain one
     source, and parallel editions cannot promote a provisional sense.
     **The corpus baseline is a hard entry invariant.** Production drafting is forbidden until
     `fresh-build/corpus-baseline.json` exists and `fresh-build/state.json` says `corpusFrozen: true`.
     Every entry must store the baseline's exact manifest hash as `CorpusBaselineSha256`. Any manifest
     change invalidates counts, file/work spread, and validation status; `audit_corpus_baseline.py` must
     fail the entry until it is researched again against the new frozen baseline. Evidence outside the
     frozen file list is forbidden.
     For keystone terms with thousands of hits, three witnesses cannot establish this range. Do not pad with
     duplicates, and do not impose a numerical minimum as a substitute for judgment; add an occurrence when it
     anchors a distinct fact the prose depends on. `WORK.md` must inventory the searched deployment classes and
     state why each unique class was included, excluded, or remains unresolved. Root QA must reject suspiciously
     uniform occurrence counts across a batch and compare occurrence depth against corpus frequency and prose claims.
     *Worked example (the batch that produced this rule — user, 2026-07-12).* `戒` shipped with 3 occurrences against
     9,514 hits in 412 allowlist texts. Its deployment classes each want their own anchor: the ordination formula,
     a monastic-code (`清規`) line, an actual precept-BREAKING case, the re-grounding (`無相戒` / `心戒`), and the
     attested pair the entry's own prose already cites — `戒之一字，諸佛所師` ("the one word 'precept' is what the
     buddhas take as teacher") beside `戒之一字，諸祖所忌` ("…what the patriarchs avoid"). A witness the prose leans
    on but does not anchor is the commonest form of this failure.
     **Mechanical rejection floors (user, 2026-07-13):** root QA runs `audit_depth_sense.py` before registration.
     These are floors, never targets or caps: 3–19 hits require up to 3 anchors; 20–99 require 4; 100–499 require
     6; 500–1,999 require 7; 2,000–9,999 require 8; and 10,000+ require at least 10. A term with fewer corpus hits
     cannot be required to have more anchors than hits. Passing the floor does **not** prove adequate depth: every
     unique definition, deployment, contrast, family relation, and period/genre use still requires representation.
     Entries with 100+ hits must span at least four source texts when four exist. A batch clustering at its floors
     is a **mandatory review signal, not proof of failure**: inspect the deployment inventories and record whether
     the shared count reflects quota drafting or several honestly complete evidence sets. Never add quotations merely
     to alter a histogram. Every sense must have its own occurrence. A cluster may be rejected only when that review
     identifies an omitted distinct deployment, unsupported prose claim, or other entry-level defect; the numerical
     pattern alone cannot invalidate an entry. Agents may not evade the review by auditing only a convenient subset.
     Single-sense entries with 500+ hits and single-sense targets containing a semicolon are automatically queued
     for item-8 adjudication; the flag means “inspect for different things,” not “split automatically.”
     The same hash-aware gate also re-runs every occurrence through `zc.verify`, requires exact `FromLb`/`ToLb`,
     rejects banned framing, and rejects untranslated Chinese outside parentheses in prose fields. A separate
     read-only audit that merely reports these defects is not registration authority.
     **False-substring depth override:** raw character-hit counts can overstate the lexical concordance (for
     example 然頂 inside 雖然頂上, or 然香 inside 自然香). Never pad an entry with those rows merely to satisfy
     the raw-count floor. After a complete concordance adjudication, root may record a
     `depthCountOverride` in `fresh-build/semantic-regressions.json` with usable hit/file counts, an explicit
     basis, reviewer, and exact review report. **A stored-entry sample is never a complete concordance.** The
     override must also point to a SHA-bound candidate ledger containing every raw hit under the frozen corpus,
     with each row classified as usable, false substring, catalogue, contents, or duplicate; its baseline hash,
     row count, usable count, and file count must reconcile mechanically. `audit_depth_sense.py` otherwise rejects
     the override and uses the raw count. It then computes the floor from reviewed
     lexical uses while retaining the raw corpus count in its report. An author cannot use an undocumented
     exception, and independent full-case review still decides whether the surviving witness supports the sense.
     **Longer-compound rows do not satisfy exact-term depth.** A stored KWIC that contains the headword only as
     part of a longer lexical compound (for example 識心 inside 業識心) may be retained as explicitly labelled
     family evidence when it materially tests the definition, but it does not count toward the headword's
     occurrence floor, work spread, or multi-source verdict. The author must replace it with an independently
     attested lexical use before the author-side canary passes. A validator's raw substring match is never
     authority to treat the longer compound as an exact occurrence; this must be checked in the two-entry canary,
     not discovered for the first time during cohort review.
     **Term-specific hard gate — `業`, `無繩自縛`, and `撥無因果` (user, 2026-07-13):** before any is drafted,
     read `KARMA_RESEARCH_BRIEF.md` in full. These entries may not pass `audit_depth_sense.py` or registration unless
     `WORK.md` contains the exact completion ledger specified in that brief and the auditor. For `業`, the ledger
     must record the complete self-definition search (especially `業識`), word-versus-concept control, positive
     assertion evidence, the apophatic `佛是無業人，無因果` evidence with the `少室六門` attribution caveat,
     the corpus's `遮詮` self-gloss, `撥無因果`, the multi-source fox-case ironization, the `無繩自縛` control,
     the three-register test, the stance-versus-sense adjudication, and the final family/definition retest. For
     `無繩自縛`, it must record the 2/257 proximity
     result, the finding that this does not establish a karma phrase, the J34nB300 counterexample, and the final
     family/definition retest; the J34nB300 passage must be an exact occurrence anchor. These are evidence gates,
     not conclusions: a ledger item may report a negative result, but it may not be omitted.
     For `撥無因果`, the ledger must cover definition formulas, multi-source condemnation, the warning about
     mistaking rhetorical flourishes and situation-adapted talk, the apophatic register and `遮詮` self-gloss, the
     fox family, and the final family/definition retest.
  7. **⛔ ENRICHMENT REOPENS THE DEFINITION — cross-check the whole term family before preserving it.** Never add
     occurrences merely because they appear compatible with the existing gloss. Re-test the preferred target,
     sense split, validation state, explanation, and #0g deviation against the newly harvested evidence and against
     every overlapping or related entry: standalone graph, compounds, variants, antonyms/contrasts, named cases,
     linked terms, and any genuinely master-specific deployment. Check that the definitions can all be true at once
     without silently assigning one passage to incompatible senses. If the wider evidence weakens, contradicts, or
     narrows the old definition, revise the definition and sense structure first; preserving an old gloss is never
     more important than the corpus. Record the family comparison and resulting keep/revise decision in `WORK.md`.
  8. **⛔ SPLIT SENSES FOR DIFFERENT THINGS, NEVER FOR DIFFERENT READINGS (user, 2026-07-13).** The guide states the
     *mechanics* of `SenseKey` (§schema) but the **test for when a second sense is warranted** is this, and only this:
     - **SPLIT when the corpus uses the word for a DIFFERENT THING** — a different referent, named work/person,
       institutional object, or lexical object. **A word-class change is not sufficient.** A noun and verb that denote
       the same event or product are grammar, not polysemy: `普說` “a general address / give a general address,”
       `著語` “attach / attached comment,” `評唱`, `頌古`, and `下語` stay one sense unless the corpus
       supplies a genuinely different referent beyond the event's grammatical realization.
       This is polysemy, and it is a *fact about the texts*, not a judgement call. The attested families:
       (a) *literal vs. Zen-loaded* — `入室` "enter a room" vs. "enter the chamber for an interview"; `老僧` "an old
       monk" vs. "this old monk" (self-reference); `方丈` the quarters vs. the abbot; `衣鉢` the robe and bowl vs. the
       succession token; `話頭` a remark vs. the word raised for investigation.
       (b) *word vs. title/person* — `傳燈` transmit the lamp vs. the *Transmission of the Lamp*; `法眼` the eye of the
       teaching vs. Fayan Wenyi; `無相` without marks vs. Master Wuxiang.
       (c) *corpus-wide vs. genuinely master-specific* — `三句` the three phrases / **Yunmen's** three / **Linji's** three.
     - **DO NOT SPLIT for different READINGS of the SAME usage.** That is the interpretation menu banned by #0, and
       it is the single most likely way this rule gets abused. `乾屎橛` has ONE meaning and several things a modern
       reader might project onto it; collapsing it from two senses to one was correct and stays correct.
     - **The failure mode to watch for is UNDER-splitting, not over-splitting.** #0 rightly punishes menus, so an agent
       that has been corrected once will merge two genuinely distinct attested uses into one blurry sense to stay safe.
       That is a defect: it hides a fact about the corpus. If you can point at passage A where the word means one
       thing and passage B where it means another, and no single gloss covers both without vagueness — **split, and
       anchor an occurrence under each sense.** Put the primary/Zen-technical sense at `Senses[0]`.
     - Two senses whose `PreferredTarget`s paraphrase each other are a merge candidate, not a split (current smell:
       `賓主`, which carries "guest and host" and "guest and host (interchanging)" as two corpus-wide senses).
     - **A different ROLE of the same thing is not a different thing.** Gold stolen, demanded, priced, or spent is
       still gold unless the corpus establishes a distinct monetary object or lexicalized unit; “gold” versus
       “gold as wealth” is not a split merely because the governing verbs are commercial. Likewise, an object used
       as a comparison standard does not automatically create an adjectival/appearance sense of the bare graph:
       `菜花…黃如金` says flowers are yellow *like gold*; it does not by itself make bare `金` mean “gold-colored.”
       Test referent identity, not topic, favorable/hostile appraisal, grammatical role, or rhetorical function.
     - **GLOSS HYGIENE IS A HARD GATE (user, 2026-07-13).** Every pair of senses must be distinguishable from the two
       `PreferredTarget`s alone, without requiring the reader to inspect `Explanation`. Capitalization alone does not
       distinguish phrase from title: label the referents explicitly (for example, “lineage-transmission phrase” vs
       “book title”). A sentence containing the headword is not a gloss (`平常心是道` cannot be the target for `平常心`).
       A semicolon-fused `PreferredTarget` is also a hard failure: choose one clean preferred gloss and move a true
       synonym to `AlternateTargets`, or split only if the two sides are genuinely different things. The auditor
       mechanically rejects exact/case-only duplicates and common noun/verb packaging such as “a general address”
       versus “to give a general address.”
       A target that fuses a literal object with an institutional deployment must be split only when those are truly
       different things; otherwise rewrite one clean gloss. Multi-sense `WORK.md` files must contain
       `sense-target-distinguishability:` followed by a pair-by-pair keep/merge decision.
     Enrichment (item 7) must re-run this test: new evidence is exactly what exposes a second sense that the thin
     original draft could not see.
  9. **⛔ PRESERVE DISCOVERY PROVENANCE — inherited research must be tested, never silently discarded (user,
     2026-07-13).** A candidate mined from an existing entry, discovery report, requested-term note, debate brief,
     or user-supplied explanation carries that prior work into its own build. Before fresh drafting, `WORK.md` must
     identify the source entry/report, copy the useful inherited translation or interpretation as a **research
     lead**, and state what evidence originally motivated it. Then test that lead against the candidate's own full
     concordance, exact cases, graph values, and overlapping term family. Record an explicit **keep**, **revise**, or
     **reject** decision with reasons. Existing interpretations are not authority and never override the Chinese,
     but agents may not make valuable prior analysis disappear simply by starting a new article. For sayings and
     material-culture explanations, keep three layers distinct: the literal image, the inherited historical or
     practical explanation, and what the Chan passage itself demonstrably does with the image. Mark inference as
     inference when the corpus does not independently establish the background fact.

  10. **⛔ NAME THE SPEAKER — the container names him, so read the container (user, 2026-07-13).** An
     explanation that says *"a master said…"* is a defect whenever the master is knowable, and he almost
     always is. The KWIC line may not name him, but **the KWIC line sits inside a book, and the book names
     him**: a 語錄/廣錄 IS a named master's own record, and in an anthology or lamp record the nearest
     preceding entry header (`…禪師` / `…和尚`) names him. Measured: of 3,666 occurrences, **2,045 sit in a
     single master's own record** and only 25% carried a `MasterName`; genuinely container-less occurrences
     numbered **19**. So "the corpus doesn't name the speaker" is nearly always false — it means nobody
     looked past the quoted line.
     - Set `MasterName` on the occurrence, spelled **exactly** as the roster's `names[0]`, so the website's
       `#/master/{name}` link resolves.
     - `MasterName` must be a person's canonical name, never a speech frame, heading, or action clipped from
       the context. Labels such as `師乃`, `示眾`, `謂弟子`, `師以杖指法座`, and `作投機偈` are grammatical
       evidence to interpret, not people. The draft compiler hard-rejects unmistakable examples even while
       legitimate newly discovered Chinese master names await roster reconciliation.
     - Name him in the prose: not "a master answers", but "**Dongshan Shouchu** answers".
     - Name the source without breaking the English-first rule: every public
       `AttributionNote` must include the occurrence's exact `RelPath` (the stable,
       linkable source identity) and an intelligible English source label. Keep the
       Chinese canonical title in source metadata and the source card; do not require
       an unparenthesized Chinese title-run in English prose. The attribution audit
       accepts exact `RelPath` as the preferred source proof and parenthesized Chinese
       titles only as a migration fallback.
       **Exactly one source prefix:** never stack a new path prefix in front of a
       legacy title prefix (`Source record (path). Source record (title).`). Canonicalize
       the note to one `Source record (<exact RelPath>).` prefix. Likewise, no sentence
       may be repeated to satisfy depth or count ledgers, and phrases such as “the
       identified master” or “the cited participant” are unresolved placeholders, not
       reader prose. The hard gates reject all three families.
       **Reader-visible attribution prose is a hard publication surface, not migration
       scaffolding.** It must begin exactly `Source record (<exact RelPath>).`, contain
       exactly one source label, and continue as a grammatical English sentence naming
       the exact actor or actor class. Do not publish `Compiler narration: Source
       record ...`, `The source does not name an unnamed ...`, dangling `). :`, or
       mechanical labels such as `Exact actor:` without natural prose. Translation or
       normalization scripts must be idempotent: running one twice must produce
       byte-identical notes. Repeated nested expansions such as `the question says (the
       question says (...` are corruption and hard-fail the cohort. After any automatic
       rewrite, run it a second time in check mode and require zero changes before the
       human reader reviews the note.
       The exact path is not the English source label. Between that path prefix
       and the actor sentence, visibly name the work in English—for example,
       `Recorded Sayings of Zhaozhou` or `Compendium of the Five Lamps`. A note
       that jumps directly from `Source record (path).` to the master/actor, or
       says only `the source title`, hard-fails. The reader must know which
       human-readable work the source link opens.
       **The English label is registry data, not fresh translation.** Resolve the
       occurrence's exact `RelPath` against
       `/mnt/c/programmieren/CbetaZenTranslations/titles.jsonl` and include that
       row's `en` (or its registered `enShort`) verbatim in the note. Do not put
       an actor/action sentence after a marker called `English Label`, and do not
       improvise a new title. Every construction decile must pass
       `maintenance/audit_authoritative_source_titles.py` over all changed
       entries before independent review or installation.
       Distinct files and even distinct works do not prove distinct deployment:
       anthologies and recensions often repeat one utterance. Run
       `maintenance/audit_deployment_duplication.py` at every construction
       decile. Each flag is a mandatory human deployment-class ruling. A useful
       textual witness may remain, but repeated versions of one utterance count
       once for depth and must never be harvested to meet an occurrence floor.
       `Kwic` is the concise quotation shown to that reader, not the entire
       retrieval window. Preserve enough of the complete turn or case to make
       the actor and lexical job unambiguous, but re-cut any KWIC over 800
       characters; the linked source and review packet carry the wider context.
       An oversized copied passage is not a substitute for deciding the exact
       headword-bearing turn, and the public-prose gate rejects it.
       For a headword of two or more graphs, the persisted KWIC must contain
       exactly one exact headword span. If it contains none, it is not an
       occurrence; if it contains several across different turns, actor binding
       is ambiguous. Re-cut and re-verify the one intended turn. Single-graph
       entries are exempt from this count rule because natural clauses often
       repeat the graph, but still require full-turn reading.
       A genuine rhetorical repetition inside one actor's one turn must not be
       shortened or moved to a claim anchor merely to satisfy the count. Keep it
       as an occurrence and add `HeadwordSpanReview` with the actual `Count`,
       `Disposition: single-actor-single-turn-repetition`, and concrete
       `GrammarEvidence` proving that every span belongs to the same actor and
       turn. This is the only multi-span exception; it never licenses a KWIC
       spanning a question and answer or several cases.
     - ⚠ In the TEI header, `編` / `集` means COMPILER, not speaker (`宋 蘊聞編` on 大慧普覺禪師語錄 is the
       compiler; the master is Dahui, from the title). `說 / 撰 / 述 / 語 / 著` is the master himself.
     - ⚠ **The TEI `<author>` field is EMPTY for the entire X (卍續藏 / Manji) canon.** A pipeline that
       trusts it silently orphans passages: it is how we came to quote **Mazu Daoyi's own record** and
       **Baizhang Huaihai's own record** and write "a master said". **The TITLE is the reliable field.**
     - **TITLE-FIRST IS A CANDIDATE SHORTCUT, NOT A SPEAKER ORACLE (user, 2026-07-13).** Read the title
       first and classify whether the container is genuinely one master's own record. Then read the **entire
       encounter/case unit**, reconstruct every turn, and confirm that the exact headword utterance belongs to
       that owner. The title owner may instead be the addressee, respondent, person discussed, or host of another
       master. A compilation, preface/contributor section, visitor, embedded old case, quotation/citation,
       conflicting header, speaker shift, or uncertain case boundary disables automatic resolution and falls
       through to review/the ladder. Record title, section, whole-case evidence, exact-turn decision, confidence,
       and exceptions. Even if the title guess is right 95% of the time, a 5% bulk error rate is unacceptable.
       **No title/header packet may write or approve `MasterName` automatically.** A fixed 24-case validation
       found a false accept where `雪竇石奇禪師語錄` quotes `應庵祖云`: title parsing proposed Xuedou while
       the inline attribution names Yingan Tanhua. Packet output is only a retrieval/review accelerator until
       a prespecified stratified validation reaches zero false accepts, and even then an exact-turn human
       confirmation remains required. Inline `X云 / X曰 / X道` markers, partial title-alias matches, and a
       structural unit that does not contain its own stored KWIC are mandatory review vetoes.
     - **AN UNNAMED MASTER IS NOT A MASTER (user, 2026-07-13).** Anonymity is not a neutral state in this
       tradition — Zen is obsessive about attribution, and a saying with no one behind it is not Zen
       evidence. But you may only declare a speaker unnamed **after exhausting the search.** After the guarded
       title-first/whole-case check, use THE FALLBACK LADDER in order; stop at the first rung that names the
       exact speaker:
       1. the quoted line itself;
       2. **widen the context** — ±500, then ±2,000, then ±10,000 characters. The name is usually here:
          an exchange opens with the master named and continues with 師 ("the master") for pages after;
          **locate the exact KWIC, not `FromLb` alone**. CBETA line numbers repeat across fascicles, so a
          bare-lb lookup can silently open the wrong identically numbered passage;
       3. the section / 卷 header above the passage (`…禪師` / `…和尚` entry headers in anthologies);
       4. **the book's title** (a 語錄 / 廣錄 / 雜錄 IS a named master's record);
       5. the TEI header — remembering it is empty across the X canon;
       6. **the same passage in another text.** Cases travel: a lamp record or case collection quoting the
          same exchange will usually name him. Search the corpus for the KWIC string and read the parallel.
       Only when all six fail is the actor unnamed — and then say it **explicitly** ("the record does not
       name the questioning monk"), never a bare "a master said". Prefer replacing such an occurrence with
       an attributable one showing the same usage.
     - **EXACT-ACTOR XOR GATE.** `MasterName` names only the actor of the stored headword turn or action;
       it must never be filled with the respondent, record owner, addressee, later raiser, or other nearby
       master. Every occurrence must take exactly one branch:
       **Biography/office veto:** a master described as founding a monastery, receiving an appointment,
       occupying an office, living in a room, being buried at a location, attending a ceremony, or appearing
       as the subject of monastic-rule prose does **not** utter the headword merely because the sentence is
       about him. Likewise, the owner of a record does not utter words inside a quoted old case, scripture,
       preface, official's question, or compiler paragraph. These are narrated, identified-non-master, or
       embedded-voice cases unless the full encounter demonstrates the master's exact headword-bearing turn.
       1. **named actor:** nonempty roster-exact `MasterName`, with no `ActorAttribution`; or
       2. **reviewed exception:** `MasterName: null` plus `ActorAttribution.Status` equal to
          `"identified-non-master"` (the source personally names a layman, official, monk, compiler, or
          other non-master utterer; preserve that exact name in `ActorLabel`), `"reviewed-unnamed"` (a
          real **non-master** actor such as a monk/questioner survives all six rungs unnamed),
          `"narrated"` (the compiler or biographer uses the headword in narration), or `"impersonal"` (the
          headword is narrator-governed duration, scene state, or group nonresponse rather than one person's
          turn). A reviewed-unnamed record must store `Kind`, `ActorLabel`, `ActorRole`, all six exact
          `RungsChecked`, `ReviewedBy`, and `ReviewedUtc`. An impersonal record must store those identity and
          review fields plus concrete `GrammarEvidence`; it does not pretend the six person-finding rungs can
          name a non-personal grammatical subject. A bare null is unresolved and fails.
       `identified-non-master` must not carry the six-rung claim that its actor is unnamed; it requires
       concrete `GrammarEvidence` showing the naming formula. `narrated` also requires concrete
       `GrammarEvidence`. `ContextMasters` may separately list roster-exact named people. Both
       **A REVIEW LABEL IS NOT AN ACTOR.** Phrases such as `the fully reviewed source voice`,
       `reviewed source voice`, `the cited voice`, and `the cited figure` are generated placeholders,
       not exact attribution. They are forbidden in `ActorLabel`, `Kind`, `GrammarEvidence`,
       `AttributionNote`, and article prose. Read the full case and store the actual named master,
       identified non-master, unnamed monk/questioner, compiler narration, verse voice, or impersonal
       construction. Exhausting six rungs does not turn an unspecified "source voice" into a person.
       **`Section master` is always a forbidden placeholder, never an attribution.** A section label can
       be a person's name, but it can also be a genre, heading, ordinal, document number, lineage heading,
       or navigation marker (`示眾`, `頌古`, `舉古`, `拈古`, `序`, `機緣`, `No.1310-C`, and similar forms).
       Copying any such label into `ActorLabel` is a hard failure. Read the complete headword-bearing turn;
       name its actual utterer, record the precisely typed editorial heading, or use a fully evidenced
       narrated/impersonal/reviewed-unnamed branch. Author-green and publication gates must reject the
       literal string `Section master` before independent review.
       `ActorAttribution.ActorRole` and every `ContextMasters.Roles` value are closed to exactly:
       `utterer`, `respondent`, `questioner`, `interlocutor`, `addressee`, `section-subject`,
       `record-owner`, `person-described`, `person-discussed`, `commentator`, `later-raiser`,
       `later-quoter`, `teacher`, `student`, `compiler`, `verse-author`, `case-figure`. Context never
       counts as the exact actor and never satisfies the named-actor gate. Put all finer descriptions in
       `GrammarEvidence`, never in either structured role field.
       **Editorial-heading attribution is typed, not templated.** When an impersonal/narrated row assigns
       the exact headword to a heading, `ActorAttribution.HeadingType` is required and is closed to exactly
       `biography`, `poem`, `portrait`, `raised-case`, or `section`. `verse-author` is permitted as a
       contextual role only for `poem` and `portrait`; a `biography` heading uses `section-subject` and
       must never call its subject a verse author. Reader prose must name the same heading type and must
       not contain generated duplication such as `poem heading heading` or `biographical section heading
       heading`. The attribution validator enforces this before compile.
       **Full-case reviewer traps (fresh-build findings, 2026-07-14):** a KWIC containing the headword in
       two different turns is not one attributable occurrence—re-cut it to one turn or store the turns
       separately. A preface author's summary of a master belongs to the preface author, not the record's
       master. A term inside a nested or imagined quotation belongs to the quoted actor (including a named
       non-master such as Indra), not automatically to the master currently telling the story. Conversely,
       prose following `上堂` remains the master's speech merely because one clause resembles a section
       label. Read outward far enough to establish the governing speech boundary before classifying it as
       editorial. These checks are mandatory in both owner review and independent KEEP review.
       The public card must label this field **Exact actor**, render reviewed unnamed/impersonal states
       explicitly, render bare null as **Attribution incomplete**, and put linked contextual people on a
       separate **Named context** line.
       Every roster-exact master name written in `Explanation` or `Note` must render as an inline link to
       `#/master/{name}` as well. Metadata-only attribution is insufficient: reader prose names the speaker,
       the name links to the roster page, and the adjacent quoted Chinese links to its numbered evidence card.
       **Every master is nameable.** `ActorAttribution.Kind` must never be `master`, `Zen master`,
       `teacher`, or an equivalent escape label. If the exact actor is a master, work the container and
       ladder until his roster-exact name is established or reject the occurrence; the anonymous branch is
       only for actors whom the source itself presents as non-master participants.
       This applies to euphemisms as well: `record voice`, `room-instruction author`, `hall author`, or
       `case-specific unnamed voice` cannot hide an unresolved master. A `reviewed-unnamed` row whose
       `ActorRole` is `utterer` must carry concrete grammatical evidence that the source presents a
       non-master actor (for example 僧, 客, 居士, 官, 婆, 童, 侍者, or another explicit participant role).
       Otherwise resolve the master through the ladder or replace the occurrence. The validator checks
       both `Kind` and `ActorLabel`, not one field alone.
     - Never invent a name. A speaker you cannot attest stays unattested.
     - **⛔ ANCHOR DANGLING QUOTES; DO NOT CLEAN THEM AWAY (user, 2026-07-13).** During the
       attribution remediation, every Chinese string used as evidence in `Explanation` or `Note` must
       gain a stored `Occurrence` when it contains the headword, or a stored `ClaimAnchor` when it does
       not. Both require `zc.verify`, a correct source/lb/KWIC, the exact actor's
       roster-exact `MasterName`, and a source-and-speaker `AttributionNote`. Do not meet the dangling-
       quote gate by deleting useful evidence. Deletion is permitted only for a demonstrable typo or a
       string that is not a corpus claim at all; record that exception in `WORK.md`. Re-test the
       definition and sense split against every newly anchored witness before accepting the entry.
     - **⛔ CLAIM ANCHORS ARE NOT OCCURRENCES AND DO NOT BUY DEPTH (2026-07-14).** Every `Occurrence`
       must contain the exact `SourceTerm`, except the governed graphic-variant case below. Evidence for
       a quoted family, contrast, parallel, alternate passage, or longer compound that is not an occurrence
       of the headword as the same lexical item belongs
       in the sense's `ClaimAnchors`, never `Occurrences`. A `ClaimAnchor` must store `ClaimText` (an exact
       substring of its KWIC), `RelPath`, exact lb range, exact contiguous `Kwic`, `MasterName` or complete
       `ActorAttribution`, `ContextMasters`, and a source-and-actor `AttributionNote`; `zc.verify` must pass.
       It does **not** count toward the frequency-scaled headword or source-spread floor. Every sense must
       retain an exact-headword occurrence.
       This prevents a `老婆禪` article from reaching its quota with `老婆心`, or a `犯戒` article with
       `破戒`. `audit_depth_sense.py` enforces the distinction mechanically.

  11. **⛔ INFER FROM THE CORPUS; DO NOT IMPORT (first public-reader calibration, user, 2026-07-13).**
      “Describe, do not interpret” never meant “refuse to infer.” A dictionary that merely lists quotations
      while withholding the smallest conclusion those quotations establish is defective. Corpus-licensed
      inference is REQUIRED; outside interpretation remains forbidden. Every clarifying or nonliteral claim
      must have an auditable `WORK.md` inference ledger:
      - `observation:` exact occurrence IDs for the predicates, equations, contrasts, self-glosses, or repeated
        collocations;
      - `minimal-inference:` the least conclusion needed to make those observations intelligible;
      - `ordinary-bridge:` only the unavoidable ordinary-language or physical relation connecting premise and
        conclusion;
      - `falsification-searches:` explicit literal, ordinary, family, and contradictory searches;
      - `counterexamples:` what was found, including evidence that narrows or splits the claim;
      - `scope:` corpus-wide, house/family, case, master, or single witness;
      - `verdict:` `direct | licensed | uncertain | reject`.
      A claim passes only if a skeptical reader can reconstruct it from the anchored Chinese plus ordinary
      semantics, without importing a doctrine, symbolic code, alleged intention, psychology, or outside Zen
      history. `鳥道無蹤迹` (“the bird course has no tracks”) and independent empty-sky/no-trace predicates
      license **“a bird's trackless flight-course.”** They do not license “a spiritual path that cannot be
      traveled,” because the corpus repeatedly says `行鳥道` (“travel the bird course”). Calling views and an
      approving mind a `金鎖` and speaking of opening or smashing it licenses **figurative obstruction**; it does
      not license “gold symbolizes attainment/value.” Negative material evidence also does not prove a positive
      symbolism. Reviewer tests: delete all outside background; narrow the claim if a critic can accept every
      premise and still reasonably deny it; reject prose that could be pasted onto many unrelated headwords.

  12. **⛔ A CALQUE IS A FLOOR, NOT A DEFINITION — NAME THE ORDINARY SCENE AND THE ZEN BEND.** For every
      concrete image, idiom, saying, institutional object, or opaque compound, the entry and `WORK.md` must keep
      three layers distinct: (1) graph composition; (2) the ordinary referent/scene and its load-bearing physical
      or institutional constraint; (3) the attested Chan deployment/deviation. The preferred target plus its
      first explanatory sentence must let an English reader picture the right kind of thing. Merely spacing the
      graphs—`鳥道` = “bird path”—fails when it suggests the wrong scene. The corpus-supported scene is a bird's
      course through open air that leaves no fixed ground track; the Chan record then places that image in the
      Three Roads and public interviews. Do not turn the ordinary scene into hidden doctrine. Mine the predicates
      that make the image usable (`無蹤`, `沒蹤由`, `不曾棲`, opening, binding, burning, carrying, fitting, etc.) and
      anchor them. A full deployment list does not compensate for an undefined image.

  13. **⛔ MODIFIER IS NOT MATERIAL — AND UNPROVED SYMBOLISM IS NOT THE CURE.** For headwords containing
      apparent material/color modifiers such as `金 / 銀 / 玉 / 鐵 / 銅 / 木 / 石 / 泥`, classify the relation in
      `WORK.md` as `material-attested | appearance/color | conventional-name | figurative-image | unresolved`,
      with exact evidence. “Made of/from X” requires a direct material predicate or decisive physical contrast
      (burning a wooden buddha, melting a gold buddha, dissolving a mud buddha, casting an iron landmark); graph
      composition alone is insufficient. Conversely, do not invent what the modifier symbolizes. **The displayed
      target must not preserve a material-looking calque that an ordinary English reader will naturally understand
      as construction material and then bury the denial in a note.** If the modifier remains unresolved, name the
      established referent or whole image without asserting material (`gold-lock barrier`, not “a lock made of
      gold”), and state the unresolved source modifier in the explanation. Retain an English material adjective only
      when direct material evidence supports it or when the wording cannot falsely imply composition. If concrete
      and figurative referents both occur, apply item 8 and split. `金鎖` is the calibration failure: “a lock made of
      gold,” “valuable fastening,” and “prized formulations” were unsupported. Its barrier and chain/fetter
      predicates establish the complete figurative images, while architectural occurrences must be tested against
      the corpus's ornate palace register rather than treated as solid-gold hardware.
      **Term-specific hard gate — `金鎖`:** “not separately glossed in the current anchors” is not a research
      conclusion. `金` is abundant in the allowlisted corpus. Before revising `金鎖`, run a corpus-wide modifier
      study: definition formulas and explicit equations for `金`; material controls (`金佛`, furnace/melting/casting
      predicates, objects demonstrably made from gold); color/appearance uses; conventional names and epithets;
      figurative comparisons; `金鎖 / 黃金鎖` lock-barrier frames; chain/fetter frames; and the closest parallel
      compounds. Record counts, representative exact anchors, counterexamples, and a keep/revise/unresolved verdict
      for every candidate inference about `金`. The final article must use the strongest minimal inference that
      survives this comparison. It may remain unresolved only after this full search, never because the first five
      occurrences did not volunteer a gloss.

  14. **⛔ INCOMPATIBLE VERB FRAMES REOPEN THE SENSE SPLIT.** Cluster the headword's governing verbs and
      predicates before preserving one sense. Actions that require different objects—unlock/open/smash a lock or
      barrier versus bind/pull apart/escape a chain or fetter—automatically queue item-8 adjudication. They do not
      auto-split, but a one-sense decision must show how one referent really supports every frame; otherwise split
      and anchor each thing. This gate also catches object-versus-stroke `棒`, organ-versus-speaking-capacity
      `舌頭`, and other grammar-visible under-splits without reviving reading menus.

  15. **⛔ SEARCHABILITY IS PART OF THE DICTIONARY.** A correct entry that a reader cannot retrieve under a
      common English equivalent is still broken. Each sense must record 3–5 natural lookup probes in `WORK.md`
      and store approved non-display `SearchAliases` separately from `AlternateTargets`: translation alternates
      are lexical claims; aliases are retrieval metadata. The website/desktop search must test every preferred
      target, alternate, and alias and return the intended entry. Rank exact Chinese/headword and exact preferred
      matches above alternates, aliases, controlled-synonym expansions, and mere prose mentions. Normalize case,
      punctuation, and safe spacing/hyphen variation. Use small, sense-approved synonym clusters—e.g.
      road/path/way/route, gate/barrier/pass, staff/stick, shout/yell—not uncontrolled thesaurus expansion; `道`
      meaning “the Way” proves why blind global replacement is forbidden. Calibration: `玄路` must be retrievable
      under dark/hidden/mysterious + road/path/way/route even though “the hidden road” remains preferred.
      **Aliases cannot make a component impersonate its compounds.** `gold ball`, `gold pellet`, and `golden sphere`
      belong to the independently adjudicated `金毬 / 金球 / 金彈子` objects, not to bare `金`; route those queries to
      the longest matching lexical entry. Search recall never overrides items 8 or 16.

  16. **⛔ NESTED COMPOUNDS CANNOT BUY THE HEADWORD'S MEANING OR DEPTH.** Inventory longer lexical objects
      containing the string before interpreting counts. `金鎖骨`, `金鎖子骨`, and `黃金鎖子` do not automatically
      evidence standalone `金鎖`; classify them as family, distinct compound, or contamination and exclude them
      from exact-sense depth unless the standalone word is independently active in the occurrence. This extends
      the longest-match rule from interface mechanics to research semantics. A compound may be retained as clearly
      labelled family/counterevidence, but it cannot create a bare-word sense, alias, ordinary image, modifier
      verdict, or characteristic Zen deployment. Describe each compound by its own predicates; do not project one
      common theory (for example “brightness”) across `銀盌`, `銀山鐵壁`, `銀籠`, and `白銀世界` without convergent proof.

  17. **⛔ PROPAGATE A COMPONENT CORRECTION THROUGH ITS WHOLE FAMILY.** When evidence changes a component's
      ordinary image, modifier relation, sense structure, or aliases, re-test every dependent compound and linked
      article before accepting the repair. `金鎖` therefore reopens `金鎖玄路`, `玄關`, `凡情聖見`, and `無事人`;
      `鳥道` reopens `三路` and `玄路`. Record keep/revise/reject for every dependent entry. Never fix the visible
      article while leaving its old false premise embedded elsewhere.

  18. **⛔ OPEN WITH THE CORPUS-EARNED INTERPRETATION — QUOTATIONS ARE EVIDENCE, NOT THE ENTRY.** Every sense's
      `Explanation` begins with one or two short plain-English sentences answering: **what is this thing here,
      and how does the Chan record characteristically use, load, contrast, or bend it?** State the referent and
      the narrowest warranted Zen deployment or tension before naming speakers or presenting quotations. This is
      interpretation by corpus inference, and it is required: converge the headword's predicates, exchanges,
      contrasts, repeated formulas, later comments, and counterexamples into a reader-ready statement. It is not
      outside interpretation: do not import doctrine, symbolism, intent, approval, a prescribed method, or a
      familiar religious meaning that the allowlisted record does not supply. The opening fails if it merely
      repeats the PreferredTarget/calque, reports frequency, begins “Literally…,” says only “the corpus records…,”
      or strings together “X says…” quotations without telling the reader what they establish. Quotations and
      named attributions follow immediately as proof. Each `WORK.md` records `opening-interpretation-verdict:`
      with the observations, inference, scope, and counterexample that license the opening; it must agree with
      the item-11 ledger and the #0g deviation. A second reviewer asks whether the opening is both informative
      without the quotations and falsifiable by them.

      **RETROSPECTIVE APPLICATION IS MANDATORY.** Items 11–18 apply to every existing entry, including
      entries that already passed attribution/depth review, and to every future entry. The first calibration
      found 391 explanations beginning with “Literally…” and 28 headwords containing the listed apparent-material
      graphs. Detectors create review queues; they never auto-rewrite. For each flagged entry one reviewer builds
      the evidence/inference chain, a second performs the falsification and sense audit, and root adjudicates.

  19. **⛔ FORBIDDEN ENGLISH LABELS — `Buddhism` AND `meditation` NEVER APPEAR IN THE DICTIONARY (user,
      2026-07-13).** These two exact English words are hard-invalid, case-insensitively, in every reader-facing
      field: preferred/alternate targets, search aliases, explanations, notes, occurrence attribution notes,
      related labels, and generated dictionary artifacts. `Buddhism` falsely collapses unrelated Buddha-using
      traditions into a modern umbrella identifier; define the Zen Buddha and every invoked figure by the Chan
      record's own deployment. `meditation` imports an English category that the headword does not say and is
      especially forbidden as a translation or explanation of `坐禪`. Translate the Chinese and describe the
      observable postures, predicates, exchanges, warnings, and institutional uses instead.

      **Proper names are atomic and are never partially translated.** In particular, `Bodhidharma` must remain
      `Bodhidharma`; the mechanically corrupted form `Bodhiteaching` is hard-invalid in every reader-facing field
      and generated artifact. The same gate applies to any proper name whose internal spelling resembles a
      translatable common noun: translate the surrounding sentence, not a substring of the person's name.

      **`Dhyana` is not an English translation and may not be a reader-facing target or explanatory substitute.**
      When `禪` or `定` requires an English activity or condition word, infer the English rendering from its
      attested Chan use—such as **composure** for the settled condition tested amid movement and noise—without
      importing an external system. A transliteration may appear only where the corpus or a linguistic note
      itself is explicitly discussing that form; it is never a shortcut around the English-first rule. For
      `坐禪`, translate and describe what the complete compound observably does in the Chan record rather than
      displaying “sitting dhyana.”

      For `坐禪`, `面壁`, `壁觀`, and related terms, run an explicit instruction-genre falsification search: look
      for numbered steps, prescribed duration, breath/body directions, manuals, and repeated imperative formulas.
      If none survive the allowlist, report that measured absence; do not infer an imported system. Also test the
      wall/movement family: `心如牆壁`, the corrections against forced dull unknowing, and answers to `不動尊` such
      as `行住坐臥`, `來千去萬`, `寸步千里`, and `上馬見路`. These may license movement-compatible immobility,
      but they do not prove an external historical thesis about Dogen or Bodhidharma. Preserve that thesis as an
      inherited research lead and accept only the relation the anchored Chan evidence supports.

  19a. **⛔ `不二` IS “NOT TWO,” NEVER THE IMPORTED ABSTRACTION “NON-DUALITY.”** Preserve the grammar the
      records actually contest. `不二` says “not two”; `不二法門` is “the gate of not-two.” Do not promote
      “non-duality,” “nondual awareness,” “oneness,” or any New Age/metaphysical abstraction into a preferred or
      alternate rendering, Explanation, or Note. A hidden `SearchAliases` value such as `nonduality` is allowed
      solely so a reader searching the familiar mistranslation reaches the corrective entry; it is retrieval
      metadata, never a lexical claim and must not be displayed as one. Research the standalone word separately
      from compounds under items 15–16. Mandatory calibration includes `要急相應惟言不二` together with Yuanwu's
      recorded reply `早是二了也`, and the public question `如何是不二之言` answered `更添些子得麼`. These are not
      permission to explain an esoteric doctrine: they show that masters retain and test the words “not two,”
      including by pointing out that naming or adding to them can itself make two.

  20. **⛔ EVIDENCE FIRST, THEN PROGRAMMATIC COMPILATION — NEVER DRAFT FROM PROSE FILLER (user,
      2026-07-14).** Beginning with fresh wave `f002`, author `fresh-build/entries/<id>/evidence.draft.json`
      from `fresh-build/EVIDENCE_DRAFT_TEMPLATE.json`; do not hand-author production `entry.v2.json`.
      **Authoritative-path gate (2026-07-16):** throughout the fresh rebuild, current entry bytes live only
      at `fresh-build/entries/<id>/entry.v2.json`. The historical `terms/<id>` tree is reference-only and may
      be absent or stale. Never use it for current-hash binding, collision detection, repair, independent
      review, promotion, or completion counts. A collision exists only if the SHA of the same fresh-build
      path changes after binding. Every repair/review ledger must name the fresh-build path explicitly.
      Fill the concrete evidence decisions first: stored evidence keys licensing the opening, Zen bend,
      counterexample/limit, different-thing sense test, alias rationale, modifier controls, family controls,
      distinct work IDs, and an exact full-case actor proof for every occurrence and claim anchor. Empty
      fields and reasoned `not-applicable` findings are different: a nonapplicable control still names what
      was tested and why it does not apply.

      Run `compile_evidence_draft.py`. It strips research-only fields and emits the **unchanged schema-v2
      production shape** (`Id`, `SourceTerm`, `Senses`, `Occurrences`, `ClaimAnchors`, and the existing
      reader-facing fields). The website, application, merger, and final dictionary receive the same format;
      this is an authoring transformation, not a schema migration. The compiler hard-rejects generic text
      such as “expanded/full context establishes,” “the quoted clause supplies the wording,” TODOs,
      or polished database-process boilerplate such as “the stored turns define the scope,” “the evidence
      rows preserve the headword,” and “the selected deployments remain bounded.” Those sentences describe
      the annotation process and tell a reader nothing about the term. Every `CorpusEarnedOpening` must instead
      give a short, term-specific inference from the stored Chan contexts: what the thing is or does here,
      how it functions in an encounter, and—where attested—where Zen bends it. Merely inserting the preferred
      English target into a reusable process paragraph is a hard failure across the whole cohort.
      The opening may appear **once only**: copying it verbatim into `EvidenceBody` is also a hard compile
      failure. Evidence paragraphs must add anchored facts, contrasts, limits, or deployments rather than
      repeating the interpretation or narrating that database rows exist.
      **Descriptor-substitution is still a template.** Sentences such as “the `<unique-label>` cases
      support the literal target X,” “six work-distinct witnesses preserve the `<unique-label>`
      construction,” “the `<unique-label>` evidence fixes the entry at its corpus wording,” or
      “nearby sayings are excluded unless they reproduce the `<unique-label>` unit” are hard failures
      even when every entry inserts a different label. The same applies to generic split, alias,
      modifier, family, and `ZenBend` controls. Each field must name an observable fact from this
      headword's actual cases—who asks, answers, quotes, raises, appraises, contrasts, or limits it.
      `audit_batch_semantic_templates.py` normalizes these structural frames and must pass author-side;
      a unique adjective or compound noun cannot disguise empty reader prose.
      **A lane ordinal is never semantic evidence.** `A101`, `B131`, `C121`, or any comparable batch
      coordinate may appear in a ledger or receipt, but never in `CorpusEarnedOpening`, `EvidenceBody`,
      `Note`, `ZenBend`, `CounterexampleOrLimit`, `DifferentThingTest`, `AliasRationale`,
      `ModifierControls`, or `FamilyControls`. Sentences such as “the rendering of C121 keeps its
      distinctive image,” “for C121 shorter matches lose semantic control,” and “C121 excludes nearby
      imagery” are prohibited templates even when the substituted descriptor is unique. The cohort gate
      normalizes every lane ordinal to `<lane>` and fails it immediately. After changing this detector,
      rerun it retrospectively on every authored-but-uninstalled cohort; an old green receipt does not
      grandfather prose that the strengthened gate can now identify.
      The discovered filler “X is the corpus expression for the action, image, or judgment described by
      the stored cases; the witnesses place it in direct answers, challenges, verses, appraisals, and
      narrative controls” is explicitly forbidden. Capitalizing a preferred target and inserting it into
      that sentence is not a definition, a Zen bend, or evidence analysis.
      Two further discovered families are hard failures: “X is the figure the records place inside Zen
      cases, quotations, and public questions; the selected witnesses define this figure by what masters
      ask, quote, praise, rebuke, or reenact,” and “X names a concrete implement, office, rite, or communal
      act in the public life of a Zen monastery; the selected witnesses show who performs it and where it
      enters the hall sequence.” A figure entry must say what that particular figure does in named Zen
      cases; an institutional entry must define that particular object, office, rite, or act. Neither may
      substitute a category description for the headword's meaning.
      The f004 A906–930 failure adds a fourth forbidden family: “X is the plain-English referent tested
      by the selected Chan records; the selected cases place X inside lineage records, public addresses,
      institutional narration, or inherited cases; the exact surrounding predicates delimit how the
      records use it.” This is annotation-process prose wearing a headword-specific noun phrase. It is a
      hard failure even when every occurrence and work ID verifies.
      **Cohort actor canary:** a checkpoint of five or more different entries may not pass when every
      occurrence has the identical anonymous `ActorAttribution` signature and the cohort contains no named
      utterer. Stop and read the full cases. The canary does not guess which actor is correct; it proves that
      a batch default has replaced occurrence-level adjudication. Independent review must not be the first
      place this collapse is detected.
      Varying the anonymous labels does not evade the canary: for ten or more entries and at least thirty
      occurrences, **zero named utterers is itself a hard batch stop**, whether the rows say `narrated`,
      `reviewed-unnamed`, or a mixture. This is a suspicion gate, not permission to manufacture names;
      genuinely anonymous evidence passes only when selected and adjudicated in a smaller coherent cohort
      whose full cases make that result credible. A large zero-name batch is never accepted by automation.
      **Public-feedback findings are hard in fresh construction:** `run_cohort_gate.py` must see zero flagged
      entries, not merely a successful auditor process. Missing item-11 ledgers, unresolved material/modifier
      claims, weak openings, or any other reader-facing finding block readiness until the author resolves and
      reruns them. A JSON report containing flags is not a green gate.
      **Independent-review artifacts are collision-proof:** every reviewer writes a reviewer-qualified,
      unique filename and must refuse to overwrite an existing review. Two reviewers may disagree; their
      separately hashed reports are evidence for adjudication. Reusing one generic pathname destroys that
      evidence and is a hard process failure. Promotion accepts only the explicitly selected report hash
      after contradictions are resolved; “last writer wins” is never an adjudication rule.
      **Exact KWIC means the complete stored span:** every occurrence and claim anchor must match fresh
      `zc.verify` on `RelPath`, exact KWIC text, `FromLb`, **and `ToLb`**. Checking only text and the start
      line is a hard gate defect: an expanded or shortened KWIC can retain its old start while its endpoint
      drifts. Custom focused gates must apply the same four-part test as `zc_batch.verify_entries`; labels
      such as “exact + FromLb” are insufficient and may not support readiness or promotion.
      **Decile case packets are the shared transport, not shared judgment:** before editing a decile, run
      `prepare_decile_case_packet.py START END --refresh-spans`. It writes one hash-bound packet containing
      fresh complete spans, 10k context, source title, work ID, line-anchored headings, and risk signals.
      Authors and independent reviewers reuse that source packet so XML/context extraction is paid once;
      each still makes and records an independent actor/semantic decision. A hash mismatch invalidates the
      packet. Run the expensive structural `attribution_packet.py` once at the final decile gate and reuse
      its existing exact-hash cache—never regenerate it during each entry edit and again during review.
      **New-acquisition case bundles are mandatory when a queue packet exists:** run
      `prepare_fullcase_review_bundle.py --packet <lane-packet> --output <hash-bound-bundle>` once per lane.
      The bundle preassembles a wide source window, exact line span, work ID, Chinese title, the current
      published English source-label candidate, section headings, speech-marker signals, and roster-name
      candidates for every discovery witness. This is navigation and candidate discovery only: it must set
      `automaticActorDecision` to null, and the author still reads the displayed full case and decides the
      utterer, context roles, sense, and prose. A missing label or ambiguous/multiple headword span remains
      a human repair, never a template fill. Authors and reviewers reuse the same hash-bound transport so
      corpus extraction is paid once while their judgments remain independent.
      **Candidate-first heading resolution:** bulk discovery may defer the expensive section-header lookup for
      candidate witnesses that are never retained.  After the author selects the depth families and before any
      actor decision, resolve the heading and full attribution ladder for every retained witness.  The final
      entry and review packet are unchanged: every stored occurrence still requires the exact heading/turn
      evidence.  This scheduling rule forbids inferring an actor from a title-only discovery packet; it merely
      avoids reading a multi-megabyte XML header for evidence that will immediately be discarded.
      Span refresh happens before compilation because it invalidates worksheet/output receipts. During
      drafting use fast compiler, exact-span, public-feedback, depth, and actor-distribution checks; reserve
      the complete cohort gate for the decile boundary. This changes transport and scheduling only, never
      the final entry schema, full-case reading requirement, or independent review standard.
      **Do not spend independent-review turns on mechanically broken drafts:** immediately before dispatch,
      run `pre_review_decile.py ... --output <unique-preflight.json>`. It reuses the production gates while
      omitting only the expensive final attribution packet. A non-green preflight stays with the author for
      repair; a green preflight still requires independent full-case reading. This is scheduling, not a waiver.
      Consecutively duplicated opening sentences are a hard public-feedback failure. Compilation or repair
      helpers must be idempotent: rerunning them may not prepend the same interpretation again.
      The same idempotence rule applies to attribution notes: `Name: Name:` is a hard attribution failure.
      `the reviewed compilation voice` is also a forbidden generated placeholder. A compilation may genuinely
      supply an anonymous compiler or verse voice, but that conclusion must be case-specific and observable;
      it may never be filled as the default when exact-turn resolution is unfinished.
      **Coalesce publication, never adjudication:** exact-hash KEEPs may be promoted as each independent report
      lands, but regenerate root/index/shards once after the concurrently reviewed round is settled (or at an
      explicitly requested checkpoint), not after every two- or three-entry partial result. Before reporting the
      accepted count, `publish_fresh_checkpoint.py` must still prove root, merged file, index, and shards agree.
      **Every KEEP retains its exact approved bytes:** promotion writes an immutable entry/worksheet snapshot
      keyed by the reviewed SHA. If a later broad helper mutates an unrelated KEEP, compare against the current
      root verdict and restore those bytes with `restore_root_approved.py`; never spend another semantic review
      merely to reconstruct a hash already independently approved. A legitimate REVISE supersedes the KEEP and
      is therefore ineligible for restoration.
      **Positive calibration:** read `PROSE_HYGIENE_PASS.md`. The accepted `鳥道` entry is the benchmark
      for ordinary pictured scene, corpus-earned Chan bend, counterexample discipline, honest unresolved
      buckets, searchability, and different-referent splitting. The accepted `和尚` entry is the benchmark
      for institutional role splitting and exact actor/source prose. All accepted entries receive the same
      retrospective prose-hygiene pass; a prior KEEP is not an exemption.
      Likewise forbidden are generic deployment inventories such as “the expression occurs in the cited
      questions, answers, actions, narration, or verse” and empty limiters such as “this sense remains limited
      to those deployments.” Name the actual attested question, action, contrast, institutional use, or limit.
      The compiler also rejects
      calque-first openings, missing aliases, null actor proof, incompatible context roles, missing work IDs,
      and forbidden English. Its receipt binds both worksheet and output hashes. `checkpoint_fresh_lane.py`
      refuses to ledger an entry whose worksheet, receipt, or compiled output diverges. Expensive cohort and
      independent-review gates remain adversarial backstops, not the first place template filler is found.

- **⛔ #0g — SURFACE THE DEVIATION (the flyswatter test). This is where a Zen dictionary earns its keep.** The
  value of an entry is not merely "how is this word used" — it is **WHERE ZEN CULTURE BENDS THE WORD** away from
  ordinary-Chinese and Buddhist usage. Everybody's dictionary already has `拂子` = "fly-whisk"; the Zen
  dictionary's job is to note that in the Chan records the whisk is the **master's implement of the teaching
  seat — the emblem of teaching authority** (Baizhang answers "what do you use to show people?" by raising the
  whisk, `百丈豎起拂子`). *That deviation is the entry.* For every term ask: **does the corpus deploy this word in
  a way ordinary Chinese or Buddhism would not?** If yes, the deviation is the CORE of the entry — state it, up
  front, grounded in how the corpus actually uses the word.
  - **This is not a licence to import mysticism.** The deviation must be **attestable** — visible in the deployment
    (the contexts it appears in, who wields it, what question it answers, what it is transmitted as), a
    cultural/institutional fact, not a meaning you project. TEST: *"the whisk is the teaching-seat implement"*
    PASSES (it appears in the high seat, in succession, as the answer to "what do you teach with"); *"the whisk
    symbolizes sweeping away delusion"* FAILS (a mystical meaning the texts never state). Per #0's exception, the
    first is required; the second is banned.
  - **Where deviations concentrate** (the high-value subset — most words carry NO deviation and need no entry):
    (a) concrete objects Zen ritualizes/re-purposes — `拂子` whisk, `拄杖` staff, `蒲團` cushion, `鉢盂` bowl;
    (b) ordinary words Zen loads — `賊` "thief", `老婆` "grandmotherly", `屎` "shit", `奴` "slave";
    (c) Buddhist terms Zen INVERTS or MOCKS — `佛` "buddha", `坐禪`, `修行`, `功德`, `念佛`;
    (d) bureaucratic/legal/military words Zen borrows — `公案` "public case", `勘` "interrogate", `印可` "certify",
    `令` "command", `賓主` "host and guest".
  - **Diminishing-returns signal:** if, after concordancing, a term is used only in its plain ordinary sense with
    no Zen deviation, it may not warrant an entry at all. Prioritize the deviations; do not manufacture one where
    the corpus shows none (say "no deviation from ordinary usage" honestly).
  - **Buddhist & pre-Zen FIGURES that the masters invoke ARE in scope — define them by the ZEN deployment.**
    When Zen Masters quote a pre-Zen or Buddhist figure/image, it *becomes a Zen figure*, and the entry describes
    how ZEN uses it, not the outside meaning. **The Zen Buddha ≠ the Buddhist Buddha:** the Buddhist 佛 is a
    cosmic miracle-worker who did a million things; the ZEN 佛 is mostly holding up the flower (拈花) and mounting
    and leaving the seat (陞座/下座). Define 佛 by *that* — the deviation is precisely the gap between the two.
    **LITMUS: if the Zen Masters talk about it, we are interested** — include it, grounded in the Zen occurrences,
    with the deviation (Zen use vs the Buddhist/ordinary use) surfaced. This does NOT contradict #0b: you still
    purge Buddhist DOCTRINE-as-meaning; you INCLUDE the figure/image and define it by the corpus's Zen use.
    (So 維摩詰, 眾盲摸象, 優曇華, 芥子納須彌 etc. are fine to author when Zen invokes them — describe the Zen
    deployment, not the sutra's doctrine. Exception still stands: lineage PATRIARCHS/MASTERS go on the master
    roster, not in the dictionary.)
- **Ellipsis / altered KWIC (NOT verbatim).** A `Kwic` MUST be an EXACT CONTIGUOUS substring of the
  cited file — no editorial "…", no inserted/dropped punctuation, no stitched-together spans. (Gate 3
  FAILed the buffalo pilot for exactly this: KWICs used "…" and a truncated `露地白牛` where the source
  continues `白牛常在面前`.) To show a long exchange, use a shorter EXACT span, or split it into MULTIPLE
  exact occurrences. The KWIC is a search re-anchor — it must match the file byte-for-byte (after XML-tag
  stripping).
- **Contamination via non-allowlist citation.** Every occurrence's RelPath must be in `zen-corpus.json`.
  (Gate 3 caught `B19n0103` 禪林象器箋 — a lexicon we excluded — cited in the buffalo entry.) Lexicons,
  encyclopedias, and other excluded texts are NOT evidence even if the phrase appears there.
- **X-canon dual lb editions.** X-canon files (`X*`) carry TWO `<lb>` systems: `ed="X"` (primary CBETA)
  and `ed="R"` (the Manji reprint). `FromLb`/`ToLb` MUST use the **`ed="X"`** number. Do NOT "correct" a
  correct `ed="X"` lb to the co-located `ed="R"` number — that is a real error gate 3 catches (b002 參禪).
  The KWIC (not the lb) is the durable anchor, so a wrong-edition lb degrades gracefully but should be right.
- **The over-interpretive gloss ("fakeout").** `凡情聖見` was rendered "dualistic thinking" — a
  generic-Buddhist abstraction imported over words that literally mean "ordinary feelings / holy
  views." The user flagged it as a fakeout. Render what the words say in Zen usage; don't smuggle in a
  concept the phrase doesn't state.
- **⛔ GOVERNED GRAPHIC VARIANT — the only headword-in-KWIC exception.** An occurrence may lack the
  canonical `SourceTerm` only when it contains an explicitly declared `VariantForm` for the same lexical
  item (for example canonical `飢來喫飯`, attested `饑來喫飯`). The exact `VariantForm` must occur in the
  KWIC, `EvidenceRole` must be `variant`, the entry/WORK ledger must document the graph substitution, and
  `zc.verify` must pass. Such a row anchors claims about that variant but does **not** count toward the
  exact-SourceTerm depth or source-spread floor. Family, contrast, substring, and merely related phrases
  are not variants and receive no exception. Never rewrite the source graph to manufacture a match.
- **Full-canon contamination.** Searching all of CBETA instead of the frozen 494-file Zen allowlist. Always
  Zen-scope, verify the baseline hash, and count source independence by `work_id` (487 works), not file count.
- **Occurrence dumping / storing everything.** Store curated few + counts; query the rest live.
- **Single-source over-claim.** Do not mark `multi-source` on one witness. Do not claim a reading is
  "distinctively master X's" without checking it isn't a shared trope (see buffalo caveats).
- **Trusting a translation as the source.** Ground in the **Chinese**, not an English rendering.

## 5b. Nested / overlapping terms (無 / 無門 / 無門關) — the strategy
Chinese terms nest by shared leading characters: 無 (no) ⊂ 無門 (Wumen) ⊂ 無門關 (the book). Left
unmanaged this breaks the hover/highlight. The rule set:
1. **Storage:** each is its own entry (distinct SourceTerm + deterministic Id). No merging, no special
   schema. Recording nested terms separately is fine and correct.
2. **Reader highlight + click + hover = LONGEST-MATCH WINS** (already implemented, both Zen and CC-CEDICT
   modes). At any position the LONGEST registered term is highlighted as ONE unit and opens on click.
   So inside 無門關 you get 無門關 (the book), not 無 (no) — the specific meaning, never overlapping marks.
3. **Reachability of shorter/nested terms** (the "how do I get 無 when I'm inside 無門關" problem):
   AUTO-COMPUTE nesting on the entry card from the term set — show "contains: 無門 · 無" and, on 無's card,
   "appears in: 無門 · 無門關". Derived for free from the loaded terms (no manual data), so every nested
   term is one click away even though the reader highlights only the longest.
4. **The trap — COINCIDENTAL PREFIX ≠ semantic relation.** 無門關 (book title) merely *starts with* 無
   (negation); they are unrelated. So the auto "contains/appears-in" list is NAVIGATIONAL, not a claim of
   meaning. Semantic links go in `RelatedTerms` and are the lexicographer's deliberate call (e.g. 無門關
   → 無門 the person = real; 無門關 → 無 = coincidental, DO NOT relate). When authoring a compound, add its
   genuine constituents to RelatedTerms; leave coincidental prefixes out.
5. **Browse / search:** group or indent entries by shared leading characters so the family is visible;
   substring search on 無 surfaces 無 / 無門 / 無門關 together.
6. **Authoring/verify check:** when a term is a prefix/substring of (or contains) an existing entry, the
   author/verifier must consciously decide the relationship (constituent vs coincidence) — flag it, don't
   auto-relate. (Candidate future automation in the editor/evidence service.)
7. **CC-CEDICT interplay:** hover/click is ONE mode at a time (Zen XOR CC-CEDICT), each doing its own
   longest-match — so there is no cross-dictionary overlap conflict.

## 6. r/zen orientation: sidebar, ewk, and dota2nub (use as METHOD; Chinese remains evidence)

These sources independently articulate the problem this project is solving. They are methodological orientation,
not dictionary evidence: do not cite Reddit in an entry, and verify every lexical claim against the allowlisted
Chinese corpus.

- **The r/zen sidebar:** defines Zen through the Four Statements — separate transmission outside teachings; not
  based on the written word; directly pointing at the human mind; seeing nature and becoming buddha. It points
  readers toward Zen-master records and treats Japanese “Zen-Buddhism” and meditation-centered accounts as a
  different subject. Sources: `https://www.reddit.com/r/zen/`, `/r/zen/wiki/fourstatements/`, and
  `/r/zen/wiki/getstarted/`.
- **ewk's position:** Zen is the roughly thousand-year historical record of a lineage of teachers; public cases
  are transcripts/records of named people's public interviews, not paradoxes, riddles, codes, or mind-stopping
  stories. Translation requires deep Zen context, comparison inside the record, and explanatory notes for
  cultural references; a bare literal calque can be English-looking nonsense. He repeatedly argues for defining
  Zen terms from Zen usage rather than Taoist, Buddhist, Japanese, or generic-Chinese contexts. Sources:
  `https://www.reddit.com/r/zen/comments/165ncqp/`, `/1mzvnt7/`, `/13tjczs/`, and `/1uqrrhh/`.
- **dota2nub's position:** English translation can falsely make unrelated traditions sound identical by mapping
  their distinct vocabulary to the same familiar religious words. Zen is unusually documented through masters
  interacting, testing one another, and requiring demonstration. Translation work should retain the Chinese,
  break down short spans, expose tool reasoning, compare versions, and treat AI output as corrigible rather than
  authoritative. Sources: `https://www.reddit.com/r/zen/comments/17v83rp/`, `/1048eie/`, `/166exf3/`, and
  `/17a22by/`.
- **Operational adoption:** cite multiple masters; weight a master's own record, independent lamp witnesses, and
  later case commentary separately; reconstruct named cases and speaker turns; prefer public “case” for `公案`;
  render `無` as “no” where the syntax says no; never default `禪`/`坐禪` to meditation; and reject mystical,
  paradoxical, doctrinal, or Japanese overlays unless the Chinese record itself supplies the wording.
- **Authority boundary:** Reddit can tell us where inherited translations may be suspect. It cannot decide a
  dictionary sense. The CBETA Chinese, exact KWICs, allowlist concordance, attribution, and cross-master evidence
  decide it.

## 7. The worked example — the BUFFALO pilot (read it)
- **`BUFFALO_PILOT.md`** (verdict + verbatim concordance) and **`BUFFALO_ENTRY.v2.json`** (the entry in
  schema shape). It is the model for a good entry:
  - Two senses: corpus-wide 水牯牛 ("the ox one herds") + Nanquan-specific ("the realized self moving
    among the different species 異類中行", with the all-fours gesture 兩手拓地).
  - **Multi-source** (五燈會元, 趙州語錄, 古尊宿語錄, 禪林象器箋…), verbatim Chinese, master + occurrence links.
  - **Honesty encoded:** the Nanquan sense is `disputed` because the strongest "master = my named buffalo"
    line is actually **Guishan's**, and 異類中行 is **also a Caodong term** (Yaoshan→Yunyan→Caoshan) — ewk
    over-claimed uniqueness. We caught it *because* we grounded in the Chinese. That catch is the feature.
  - We **dropped** the one occurrence from a non-Zen encyclopedia (`B16n0088`) — Zen-scope in action.

## 8. Tools & where things live
- **Evidence:** `Services/IDictionaryEvidenceService.GetEvidenceAsync` (Zen-scoped occurrences + master
  rollup; optional `restrictToRelPaths` to scope to one sense's texts).
- **Store:** `Services/IDictionaryStore` (Load/Save v2 + legacy). `DictionaryStore.ComputeId`.
- **Editor:** `Views/DictionaryEditorWindow` (rich multi-sense authoring + occurrence curator) — the
  human-in-the-loop surface. (Legacy flat editor `TermbaseEditorWindow` still exists.)
- **Zen scope:** `Assets/Data/zen-corpus.json` + `IZenTextsService.IsZen`. Worklist: `C:\woodblocks\ZEN_TEXT_WORKLIST.md`.
- **Masters:** `MasterCorpusIndex.Appearances` (RelPath↔master, primary/secondary); `Assets/Data/master-dates.json`.
- **Links:** `Services/ZenUriParser` (BuildUri passage, BuildMasterUri).

## 8b. VERIFICATION — the three gates (an entry is not `done` until it passes all three)
Nothing merges into `termbase.v2.json` until it clears three independent adversarial checks:
1. **Gate 1 — research self-check.** The authoring agent applies the multi-source gate as it drafts.
2. **Gate 2 — Claude adversarial pass.** An independent Claude verifier re-checks the Chinese, the
   sense split, and hunts over-reads (the buffalo Guishan/Caodong catch).
3. **Gate 3 — Codex adversarial pass.** A *different model* (Codex CLI, gpt-5.2-codex) independently
   re-derives from source. Run it:
   `pwsh eng/tools/codex-verify-dict-entry.ps1 -TermId <t_...>` → it follows `CODEX_VERIFY_SPEC.md`,
   greps each cited file to confirm every KWIC is verbatim, enforces the Zen allowlist, tests
   multi-source / over-read / imported-abstraction, and writes `terms/<id>/CODEX_VERDICT.md`
   (PASS | REVISE | FAIL). Codex has full FS access to the corpus/allowlist/entries.
Merge only entries that are PASS on gates 2 AND 3. REVISE → fix and re-run. FAIL/contamination → do not merge.

## 8c. REPAIR READINESS — defects must be impossible before rereview

Independent reading remains mandatory, but it must not be the first proof that
an author's edits reached the entry.  Before assigning a repaired cohort to a
fresh reviewer, run `audit_repair_readiness.py` against the rejecting review,
the repair-author ledger, and the final formal gate.  It is a hard gate:

1. Every `REVISE` entry must have a different current SHA-256 from the rejected
   bytes.  “Repaired” prose in a worksheet or script is irrelevant if the
   compiled entry stayed unchanged.
2. Every prior `KEEP` must remain byte-identical.  Authors do not opportunistically
   rewrite accepted neighbors.
3. The repair ledger and formal gate must both bind to the current entry bytes,
   and the complete cohort formal gate must be green.  Focused decile gates are
   checkpoints, not cohort clearance.
4. Every semantic defect found by an independent reviewer becomes a durable
   canary in `fresh-build/semantic-regressions.json` when it can be expressed
   mechanically.  Known false witnesses (for example 水月寺 for 水月 or 自然香
   for 然香) may never silently re-enter a later draft.
5. Evidence harvesting must classify the *whole lexical use*, not merely find
   the headword's character sequence.  A substring hit is a candidate to read,
   never evidence by itself.  Contents pages, catalogues, titles, and adjacent
   compounds receive the same veto before compilation.
6. The cheap depth-floor and English-first audits run per entry; cohort audits
   run at durable checkpoints. A batch clustered mechanically at the exact
   evidence floor requires a recorded qualitative review, but is not itself a
   failed authoring process. Add only genuinely different evidence, never
   padding, and quarantine only entries with an actual entry-level defect.
   For a mixed repair cohort, run the full gate over repaired entries plus
   immutable prior KEEPs, but pass every repaired ID as `--cluster-id`. The
   quota-cluster histogram then measures the author's actual batch rather than
   retroactively failing unchanged control entries. `audit_repair_readiness.py`
   requires that this cluster scope exactly equal the rejecting review's
   `REVISE` set; authors cannot hide a repaired row from the histogram.
7. A different worker still reads every occurrence in its full case and issues
   exact-hash `KEEP`/`REVISE` verdicts.  Passing repair readiness proves delivery
   and regression hygiene, not semantic correctness.
8. Attribution packets must be generator version 3 or later and expose
   `turnProofCandidates`: the exact headword-bearing clause plus the nearest
   visible speaker cue before and after it.  The author must decide from the
   complete case, but must record a decision consistent with that local proof.
   **OCCURRENCE-IDENTITY GATE:** a packet candidate is navigation only until its
   character span is proved to overlap the occurrence's complete stored `Kwic`.
   Never take `turnProofCandidates[0]` merely because it contains the headword:
   a full case can contain several questions, quotations, recensions, or speakers
   using the same term.  First locate the exact normalized stored KWIC in the
   full case.  If it occurs more than once, bind the intended copy with the
   source offset / `FromLb` plus enough distinguishing Chinese on both sides.
   Record that binding in the review ledger.  No bound overlap means the packet
   is defective and the occurrence must be re-extracted before actor review;
   it may not receive a default `KEEP`, `REVISE`, or attribution decision.
   In `僧問…X。師云…`, the monk utters X; the master's following response may
   supply context but cannot be assigned backward.  Generic actor prose and
   record ownership are never substitutes for this turn proof.
   Likewise, `古人云`, `古德云`, `先德云`, and `祖師云` introduce quoted
   precedent. The named ancestor/original speaker owns a headword inside that
   quotation; the present record owner is a later-raiser/quoter/commentator in
   context unless the complete case separately shows that he repeats the
   headword in his own turn. `audit_attribution.py` fails a fresh occurrence
   whose quoted-precedent marker lacks this role separation. This guard was
   promoted after both `善爲道路` and `通身是手眼` incorrectly assigned inherited
   words to the later commentator.
9. When a reviewer proves an exact-turn error, add an `occurrenceAssertions`
   canary keyed by `RelPath` + `FromLb` (and `KwicContains` where necessary) to
   `fresh-build/semantic-regressions.json`.  State the required `MasterName` or
   non-master actor status and any forbidden prior name.  Future author prose
   changes cannot then resurrect the disproved attribution while leaving the
   mechanical gates green.
10. Every link-bearing `MasterName` and every `ContextMasters[].MasterName`
    in a fresh entry must equal the roster's exact `names[0]` value. Chinese
    section headings, temple-title strings, aliases, and full record titles are
    source evidence, not public link keys. `run_cohort_gate.py` always invokes
    `audit_attribution.py --strict-roster`; “deferred non-roster” is diagnostic
    inventory and never a fresh-build pass. Canonicalize structured link fields
    only—never globally replace Chinese inside source titles or quotations.
    In mixed repair cohorts this strict check is scoped to exactly the `REVISE`
    IDs while accepted control hashes remain immutable; readiness enforces that
    equality. A genuinely source-proven figure absent from the current roster
    must remain non-linking (`MasterName: null`, no `ContextMasters` link) under
    the identified-unlinked-master rule below. Register the identity separately
    in `fresh-build/pending-roster.json` with Chinese aliases and exact source
    evidence, but pending registration never authorizes a broken public link.
    This is explicit integration debt, not roster completion: the final project
    audit requires the pending ledger to be empty after those candidates are
    incorporated into `master-dates.json` and the website roster.
11. **Resolve evidence identity before writing reader prose.** The authoring
    order is fixed: exact concordance row → complete-case reading → utterer and
    contextual-role decision → canonical roster resolution (or evidence-bound
    pending-roster registration) → work ID and case-family identity → claim
    anchors → prose. A heading, title, temple string, or record owner may never
    survive into a structured person field merely because later prose sounds
    plausible. If any occurrence lacks that structured packet, the entry is not
    ready to compile.
12. **Fail systemic defects early.** A 100-entry lane receives a durable
    checkpoint at 50, but five representative entries must first clear the same
    compiler, exact-KWIC, strict-roster, full-case actor, claim-anchor, depth,
    forbidden-English, and semantic-canary checks used at the checkpoint. If
    the same root-cause defect appears twice in that sample, stop bulk authoring,
    repair the worksheet/compiler/gate, and rerun the sample. Independent review
    still reads every final entry; the sample prevents an avoidable template or
    extraction defect from being multiplied one hundred times.
13. **Every rejection improves the production line.** The repair ledger must
    classify each `REVISE` by root cause (evidence selection, exact turn,
    identity canonicalization, work independence, sense boundary, inference,
    claim anchoring, or prose). A recurring mechanically expressible cause must
    become a compiler check, formal-gate assertion, or semantic canary before
    the next cohort opens. Repairing only the rejected JSON leaves the defect
    active and is not a complete repair.
14. **⛔ IRIYA/KOGA WHOLE-QUEUE QUARANTINE.** The 2,008 Japanese-dictionary
    headwords are suspicious selection leads, never lexical authorities. No
    entry from that source may be constructed until all 2,008 rows in
    `fresh-build/iriya-admission/` have been read in Chan corpus context and
    assigned exactly one first-pass disposition from `IRIYA_ADJUDICATION_GUIDE.md`:
    `KEEP (couplet)`, `KEEP (component)`, `PROVISIONAL`, or `REJECT`; every
    proposed buildable disposition additionally requires an exact, separate,
    matching independent disposition. Definitions, senses, examples, and glosses from Iriya/Koga remain
    behind the provenance firewall. `validate_iriya_admission.py --build-gate`
    is mandatory and locks the entire Iriya phase while even one row is
    unadjudicated. A checked `DEFER` or `REJECT` never becomes construction
    eligible, and frequency cannot override lexical-boundary or Zen-deployment
    failure.
15. **⛔ REPAIR-REASON CLOSURE PREcedes rereview.** A changed hash and a green
    mechanical cohort gate do not prove that the defect an independent reader
    rejected was repaired. Before dispatching any repaired `REVISE` entry,
    `audit_repair_reason_closure.py` must bind the rejecting review hash, repair
    ledger hash, and current authoritative entry hash. Every rejection reason
    must map to the exact changed coordinate or evidence row and carry an
    explicit closure with before/after value hashes, the evidence keys that
    license the new value, and complete-case proof for actor/turn defects. The
    gate fails closed on a missing mapping, unchanged or substantially unchanged
    rejected prose, copied sense explanations, forbidden reader terms, malformed
    attribution notes, or a marked question turn still assigned to the following
    master/narrator. Passing proves delivery only; a different reader still
    rereads every complete case and alone may issue KEEP. Calibration: the first
    Lane-B repair claimed 32 sealed repairs, yet independent rereview found 20
    still requiring revision, including eleven whose rejected prose survived
    substantially or verbatim. Never spend reviewer time rediscovering a defect
    that coordinate-level closure could have caught before dispatch.
    **A repair coordinate is an identity, not a line position or aggregate.** For
    queue/adjudication JSON, bind every changed field to the exact deterministic
    ID or authoritative term plus batch ordinal, and mechanically diff the
    resulting row objects against the rejecting bytes. A correct final KEEP/
    REJECT total does not prove that the intended rows changed: one repair
    accidentally rejected adjacent `十二時中` while leaving target `八萬四千`
    accepted, producing the expected 19/6 arithmetic with the wrong identities.
    The focused reviewer caught it. Textual patch context, array position, and
    summary counts are never repair authority without row-identity proof.
16. **⛔ ABSOLUTE LINEAGE-ROSTER WRITE PROHIBITION.** A dictionary worker may
    read the externally maintained lineage roster solely to resolve public link
    keys. It may **never** create, edit, normalize, regenerate, reorder, merge,
    cherry-pick, commit, or otherwise mutate `Assets/Data/lineage-masters.json`,
    `master-dates.json`, a website roster, lineage edges, teacher/student fields,
    or any other lineage-chart input. This prohibition applies to authors,
    reviewers, repair tools, installers, dashboard jobs, and coordinating agents;
    no dictionary task, missing link, absent identity, #0g figure, or pending
    attribution expands that authority. A corpus-attested identity absent from
    the roster goes only into the dictionary-owned
    `fresh-build/pending-roster.json` evidence ledger. It remains explicit link
    debt for the separate roster owner and must never be “fixed” by inserting a
    roster node. Before and after every dictionary wave, the coordinator must
    prove the roster path has no worktree or index diff and record its Git object
    ID/hash in the wave receipt. Any roster delta is a structural blocker: stop
    installation and report it; do not repair, revert, or reinterpret it inside
    the dictionary process.
17. **⛔ NO SEMANTIC TEMPLATE AUTHORING.** Batch tools may transport corpus
    windows, serialize already-made decisions, invoke the canonical compiler,
    and verify exact bytes. They may never *make* an actor, sense, definition,
    opening, Zen-bend, source-role, modifier/family-control, or claim-anchor
    decision by regex, row number, source-owner fallback, fixed position list,
    default one-sense assumption, or term-substituted prose template. In
    particular, a helper may not assign `impersonal` to selected ordinals,
    infer the utterer from the nearest `師曰`, force every candidate into one
    sense, or repeat generic “ordinary containment was excluded” controls
    without recording what was actually examined for that headword. Each
    production field must come from explicit per-entry data written after the
    complete case was read; programmatic transformation may then preserve that
    decision in the unchanged schema. Before any mass-authoring helper runs,
    inspect its source and compile one five-entry canary. If it contains a
    semantic default or automated attribution decision, quarantine the helper
    and every product it wrote. A compiler pass does not rehabilitate those
    products. This gate was added after an investigation-wave helper attempted
    regex/row-position attribution and universal one-sense output; it was
    stopped after one canary and no such artifact may enter `terms/`.
    Before any authoring write, run `assert_construction_lane_assignment.py`
    with the lane, lane position, ID, and term. The frozen lane manifest is the
    authority; never infer the next row from a global backlog ordinal, a prior
    report, or memory. A mismatch is a collision blocker and no draft may be
    written. This gate was added after a Lane-C worker nearly rebuilt Lane-A's
    `拈花示眾`; the assertion caught the correct Lane-C row as `同生同死`
    before any colliding file was created.
    **Do not repeat completed research merely because construction is a later
    phase.** SHA-bound `discoveryTransportEvidence` that was explicitly read in
    full case by both admission reviewers against the unchanged frozen corpus
    may be reused after a batched `zc.verify` pass. Construction must reread the
    transported full cases while writing its semantic fields, but need not find
    those same witnesses again. Run fresh concordance research only where the
    transported set does not meet the entry's individual depth/source floor,
    leaves a sense or utterer unresolved, or fails to test a material
    counterexample. Admission prose such as `independentReason` is routing
    evidence, never a template to copy into the public entry.
    Transport packets normally contain three admission witnesses; **three is
    not a construction quota and does not override the frequency floor.** Before
    calling any entry or checkpoint mechanically green, run
    `audit_depth_sense.py --paths` on the actual staged `entry.v2.json` files
    and retain its invocation-specific report. A focused exact, attribution, or
    template check is not a depth check and may not be summarized as “all
    mechanical gates green.” A depth hard failure requires fresh full-case
    research and a definition cross-check before construction moves on. This
    wording was added after a speed canary serialized three transported
    witnesses for 24 entries with 66–100 exact hits while its narrower checks
    incorrectly described them as sealed.
    **One full-case read may serve several gates; do not reopen the same XML by
    ceremony.** A SHA-bound packet that contains the complete case, exact KWIC,
    work identity, line anchors, title, and an explicit human/model adjudication
    may be the shared evidence record for construction, attribution review, and
    independent semantic review while those bytes remain unchanged. Every
    reviewer must still actually read the complete case and make the decision
    required by their gate; independence concerns the judgment, not redundant
    file retrieval. Reopen the source XML only when the packet is truncated,
    ambiguous, mismatched, exposes an actor or sense conflict, or changes hash.
    Run cheap syntax and changed-entry checks continuously, one changed-cohort
    depth/attribution/template gate at a checkpoint, and the expensive whole-tree
    gate once at final merge. Do not repeatedly launch overlapping full-tree or
    per-entry validators while a lane is still authoring. This changes no final
    output or quality gate; it removes duplicate I/O and duplicate reading.
    **Historical repair must begin from the current installed entry, never from
    an old worksheet snapshot.** Hydrate the repair worksheet from the current
    authoritative `terms/<id>/entry.v2.json` (or its byte-identical merged row),
    carry forward only worksheet-only proof fields, and then overlay only the
    explicitly authorized coordinates. Before compilation, mechanically prove
    that every non-authorized substantive field still equals the installed
    baseline. This prevents a one-coordinate repair from resurrecting stale
    actors, notes, or prose and turning into a large residual-failure loop. The
    rule was calibrated on seven attribution repairs: direct stale compilation
    produced 53 collateral findings; baseline hydration produced zero hard
    attribution failures for the same repaired coordinates.
    The standard command is
    `python3 hydrate_historical_repair.py <entry-id>`; retain its SHA-bound
    receipt under `maintenance/` in the repair closure. A historical repair
    compiled without that receipt is incomplete unless its worksheet was
    created after, and is mechanically proven byte-derived from, the current
    installed entry.
    The first five outputs of every new worker/compiler combination must pass the
    complete construction contract—not merely compile—before mass authoring:
    exact turn, actor ladder, depth and claim anchors, public-feedback receipt,
    work identity, corpus binding, forbidden English, and cross-entry template
    checks. A systemic omission may reach five canary drafts, never the rest of
    the cohort. Resolve packet-level actor ambiguity before public prose is
    authored. See `PROCESS_SPEED_ARCHITECTURE.md` for the end-to-end stage
    contract and scheduling rules.
    **The canary and every checkpoint must reject hollow serialization before
    independent review.** `Kwic` and `ClaimText` may not equal the bare
    headword; they must retain enough of the verified full case to show the
    asserted discourse job and marked turn. `Explanation` may not equal `Note`,
    and neither may merely restate an admission-ledger reason or a process claim
    such as “full-section review assigns.” Named turns may use the exact
    roster-linked `MasterName`; ambiguous, narrated, quoted-origin, heading, or
    non-master turns require structured `ActorAttribution` with headword-specific
    grammar evidence. The author must run the batch semantic-template audit on
    the five-entry canary and each changed checkpoint. This was made explicit
    after two investigation lanes compiled 45 plausible admissions with bare
    headword evidence or duplicated process prose, forcing an avoidable full
    repair pass.
18. **⛔ NO READZEN PRODUCTION PUBLICATION BEFORE FINAL AUTHORIZATION.** During
    construction, workers may generate local `termbase.v2.json`, search indexes,
    and shards so merge/reconciliation gates can test the exact website payload;
    they may also create local backup commits. They may **not** push the
    dictionary data repository, deploy the ReadZen SPA or its production data,
    trigger a production build hook, or otherwise make a partial dictionary
    publicly visible. Publication requires both (a) verified completion of the
    entire documented dictionary program and (b) the project owner's explicit
    authorization at that time. The separate progress dashboard is the only
    site that may be deployed while work remains. Reports must say “local
    publication artifacts generated” rather than “published” unless the live
    production deployment was actually authorized and verified.
19. **⏱ SPEED IS A HARD QUALITY GATE — BENCHMARK EVERY PROCESS CHANGE.** A
    workflow that eventually produces good entries but makes the documented
    queue practically unfinishable is defective. No new helper, validator,
    review pass, evidence format, checkpoint, or scheduling rule may enter the
    production path until a representative ten-entry canary records wall time
    by stage: evidence retrieval, complete-case semantic/actor reading, public
    prose, serialization, verification, focused attribution/work-source/
    template/batch-depth preflight, failures, repair,
    and settled re-run. Report **settled throughput**, including rework; raw
    first-draft speed is not the metric. The default production budget for a
    500-entry cohort with three collision-free author lanes is **four hours to
    settled checkpoint output**. A canary projecting above that budget is a
    speed-gate failure: remain in speed mode, identify the dominant stage, and
    redesign or batch it before mass production. Do not merely publish a
    longer ETA.

    The unchanged quality contract is the floor, not a reason to duplicate
    work. Transport/search/heading/count work is paid once and SHA-bound;
    semantic decisions remain explicit and complete-case grounded. Ten entries
    are the minimum normal reasoning/tool packet, fifty the normal complete
    cohort-gate boundary, and shared indexes/dictionaries replace per-entry
    subprocess loops. Machine-only authoring overhead should remain below five
    seconds per entry on the reference WSL workspace; any regression over 10%
    requires a written reason and a faster alternative test. Recursive repo or
    `/mnt/c` scans, serial `zc.count`/heading lookups, per-entry full-tree gates,
    repeated source discovery, reopening hash-identical evidence by ceremony,
    tiny worker assignments, and validators that repeat another gate's work are
    hard failures.

    Every accepted process change writes a durable speed receipt naming the
    before/after commands, sample IDs, machine/workspace, timings, failure and
    repair counts, output hashes or equivalence checks, and projected cohort
    completion time. It must also state which prior work it replaces so old and
    new paths cannot both run. If a speedup causes actor, sense, depth, quote,
    title, work-identity, or prose-template failures, quarantine its products,
    repair the shared cause, and rerun the canary; those failed drafts do not
    count toward throughput. See `IRIYA_CONSTRUCTION_SPEED_MODE.md` for the
    current measured implementation and `PROCESS_SPEED_ARCHITECTURE.md` for the
    end-to-end stage contract.

20. **⛔ FREQUENCY DISCOVERY IS A WIDE SEMANTIC FUNNEL, NOT A TOP-N WORD LIST.**
    Raw frequency ranks what to inspect; it never makes an ordinary fragment a
    dictionary headword. Before freezing a new 500-term frequency cohort,
    pre-vet at least the next 1,000 deduplicated ranked candidates in one bounded
    pass. Reject function words, incomplete question fragments, accidental
    bigrams, ordinary narrative glue, names already represented by a canonical
    person entry, and expressions merely contained in Zen books. Retain only a
    stable lexical unit whose complete cases show an observable Chan job such as
    an answer, test-question, verdict, capping phrase, raised case, institutional
    role, technical distinction, or corpus-specific bend. A common form such as
    `不得`, `不是`, `今日`, or `不知` does not survive merely because it occurs in
    hundreds of works; an interview frame survives only when the frame itself is
    independently deployable and the evidence states its job.

    Rank the semantic survivors by exact frequency and distinct-work spread,
    select the strongest 500, and preserve the remaining survivors as a reserve.
    If the first 1,000 yield fewer than 500, inspect the next 1,000 as one
    additional bounded funnel rather than repeatedly topping up small gaps.
    Checkpoint every 50 inspected rows and record explicit rejection reasons,
    screened-pool size, survivor count, selection cutoff, and reserve size.
    Occurrence floors apply **after** lexical-unit and Zen-deployment admission:
    ten or more exact hits across three works is the normal route; four to nine
    across two works requires especially clear deployment; two or three is
    provisional; one is normally a documented hapax unless it uniquely names a
    case, person, title, or indispensable technical expression. No numerical
    threshold auto-admits a candidate.

    Repeat this wide-funnel process in successive 500-entry cohorts until the
    measured semantic frontier reaches saturation or the dictionary approaches
    10,000 installed entries. Saturation is demonstrated by cohort-level
    acceptance rate plus the exact-hit and distinct-work frontier of accepted,
    rejected, provisional, and unresolved candidates; it is not declared from
    raw n-gram exhaustion. Before every freeze, eliminate exact duplicates and
    adjudicate near-duplicates: graph and punctuation variants, aliases,
    contained headword/component pairs, noun/verb restatements of one referent,
    and senses whose English targets cannot be distinguished. Merge or attach
    aliases/family relations when the corpus job is the same. Keep related
    headwords separately only when complete cases prove different lexical things
    or different Chan jobs, and record that reason. Every cohort receipt reports
    exact duplicates removed, near-duplicates merged, near-duplicates retained
    with reasons, and the unselected survivor reserve feeding the next cohort.
    Run `audit_frequency_candidate_duplicates.py --require-resolved` against the
    candidate manifest and its family-resolution ledger before freezing it. The
    audit normalises punctuation and whitespace only—never broad glyph
    substitution—and fails installed collisions, normalised duplicates, or any
    unadjudicated containment pair.
    **A punctuation/whitespace-normalised equality is an identity collision, not
    a near-duplicate requiring author judgment.** It is an automatic blocker at
    the earliest selection/readiness gate against both the installed index and
    every other row in the same cohort. It must never be transported as a
    pending family question or accepted/rejected as a variant edge; select the
    installed headword instead. The permanent regression pair is
    `牙上生牙、爪上生爪` versus installed `牙上生牙。爪上生爪`.
    **Repair cohorts have an additional live-identity gate before reservation or
    authoring.** Every repair candidate ID must already exist in the current
    published `termbase.v2.json`. If the ID is absent but exactly one published
    entry has the same `SourceTerm`, stop and produce an independently reviewed
    ID-migration receipt proving that only top-level `Id` and worksheet
    `Entry.Id` change; install the repair under the published ID. If neither the
    ID nor the exact headword exists, the row is acquisition work, not repair:
    preserve it in the acquisition queue and replace it with a genuine live
    repair. A repair batch may not increase entry count, silently retain both
    identities, or receive repair credit for a new headword. The atomic merge
    must prove that expected changed IDs equal actual changed IDs and that the
    entry count is unchanged.
    **Repair-lane ownership is exclusive and remains locked after owner
    closure.** Persist the assigned indices and IDs before editing. A worker may
    not advance into, inspect-and-rewrite, or “continue” another lane's range
    without a new root-issued reservation that proves zero overlap. Once a lane
    seals owner hashes, any later byte change invalidates reviews against those
    hashes. Quarantine the colliding bytes, restore the sealed owner state, and
    rerun independent review from the beginning; never intuitively merge two
    agents' competing repairs. Finishing a lane authorizes waiting and review,
    not claiming the next unassigned indices.
    Raise a saturation review flag only when **two consecutive** 1,000-row
    funnels each yield fewer than 15% high-confidence survivors after
    deduplication and either (a) the accepted-survivor median falls below ten
    exact hits across three independent works or (b) at least half of the
    survivors are provisional/below that normal floor. This flag requests a
    human stopping review; it does not silently discard the tail. The 10,000
    entry target is a planning ceiling, never a quota that licenses weak terms.

21. **⛔ HARVEST THE LEXICAL FAMILY BEFORE COMPILATION.** Exact-headword and
    actor work must not leave an entry isolated from the corpus vocabulary that
    makes it useful. After senses and evidence are stable, run one bounded
    family harvest against the inverted/KWIC indexes and the installed plus
    queued term authorities. Check: longer compounds containing the headword;
    independently stable contained components; punctuation or graph variants;
    paired formulas and recurring case-family neighbours; and corpus-attested
    contrasts or companion technical terms. Persist the queries, hit/work
    evidence, and ruling in `FamilyHarvest`; compile accepted independently
    useful terms into `Senses[].RelatedTerms`. A related term must itself be
    attested, searchable, and clarify a lexical or Chan-job relationship. Do not
    add every substring, incidental co-occurrence, generic topic word, person,
    or paraphrase merely to satisfy a quota.

    `RelatedTerms: []` is permitted only with a negative harvest receipt showing
    what was checked. The author preflight fails a missing harvest, an unresolved
    exact/near duplicate, a relation to an unknown/unqueued form, or a batch-wide
    empty-field template. The family harvest is paid once and SHA-bound so
    independent review checks the proposed relationships rather than rerunning
    discovery. Apply the same gate in the final revision pass over older entries;
    new construction must not knowingly enlarge that backlog.
    **Transition:** cohorts whose manifests and author packets were frozen before
    rule 21 was added are grandfathered under their existing schema and must not
    stop for serializer changes. They write one batch-level
    `FamilyHarvestDeferredToRevisionPass` receipt per fifty entries and receive
    the harvest in the final revision pass. Cohorts frozen after rule 21 must
    carry the field from their first canary.

22. **READER PROSE MUST NOT EXPOSE THE BUILD PIPELINE.** `Explanation` is an
    article for a reader, not a construction receipt. It must describe what the
    expression means and how named speakers use it in the cited cases. Do not
    write pipeline vocabulary there: `deployment`, `deployment-family`,
    `recurrence family`, `allowlist(ed)`, `independent works`, `frozen corpus`,
    `corpus baseline`, `concordance`, `stored witnesses`, evidence or packet
    `floor`, `packet`, `worksheet`, `cohort`, `SHA-256`, `exact turn`,
    `crossing-boundary`, or `false match`. Replace these with ordinary English
    such as *use*, *instance*, *related occurrences*, *works*, *the cited
    passages*, or state the actual textual observation. Raw inventory prose
    such as “329 times in 139 files/texts/works” does not by itself explain a
    word; use “widely attested” or a plain count only when frequency materially
    helps, and keep the explanatory focus on meaning and use.

    Raw occurrence handles are equally forbidden in reader prose. Never write
    “in o1 …; in o2 …”, `o1/o2/o3`, or the corresponding generated
    “Work has Master who is identified as …” recital. Name the speaker and work
    in ordinary sentences, grouping recensions or repeated uses where that is
    the actual point. An `Explanation` must also end as prose: a trailing bare
    sequence of master names is leaked scaffolding and must be removed. The
    author-side reader-register scan checks raw occurrence handles, generated
    actor-recital syntax, and terminal name dumps before fresh emission.

    This is a register rule, never authority to change a claim, quotation,
    master, line ID, gloss, or genuine count. `Witness` remains valid
    textual-critical language for an attested passage. `Manifest` is forbidden
    only when it names a build artefact; it remains ordinary English when used
    as a verb or adjective in the entry's subject matter. The reader-register
    gate is field-aware: violations in `Explanation` are release-blocking;
    internal `Note` violations are reported separately and become blocking if
    that field is rendered publicly. Authors run the gate before independent
    review, and repair workers use §8d coordinate-only hydration rather than a
    blind global replacement.

## 8d. STANDARD REPAIR PROTOCOL — preserve the good, change only the proved defect

This is the mandatory treatment for **every** repair of an installed, staged, or previously reviewed entry. It is
not a special recovery technique, and a worker may not substitute reconstruction, broad rewriting, or recompilation
of an old worksheet. The default repair unit is the smallest proved defective coordinate, not the whole article.

1. **Freeze identity and baseline.** Bind the repair to the deterministic entry ID, `SourceTerm`, current authoritative
   entry path, and SHA-256. For installed entries that path is `terms/<id>/entry.v2.json`; for an independently
   reviewed but not-yet-installed cohort it is the exact reviewed `fresh-build/entries/<id>/entry.v2.json`. Never bind
   by array position, visual row, nearby term, or batch arithmetic.
2. **Hydrate, do not reconstruct.** For an installed entry, run `python3 hydrate_historical_repair.py <entry-id>` from
   the current installed `terms/<id>/entry.v2.json`. For a reviewed staged entry, hydrate the worksheet from the
   current reviewed staged bytes and bind the rejecting review to that hash; never fall back to an earlier authoring
   worksheet or `terms/` row that predates the reviewed draft. Preserve substantive fields byte-for-byte and carry
   forward only worksheet-only proof material. An old worksheet is research history, not a repair baseline.
3. **Name the authorized surface.** Before editing, list the exact rejected coordinates/evidence rows and their
   reasons. Overlay only those coordinates. Every unrelated substantive field must remain equal to the frozen
   baseline; useful verified evidence must not be lost merely because one field failed. When the same passage is
   represented in more than one structured place (for example an `Occurrence` and a `ClaimAnchor`), list every mirror
   coordinate and update the actor, context roles, note, and proof consistently. A half-repaired duplicate is a failed
   repair.
4. **Prove delivery before rereview.** Emit a SHA-bound hydration/repair receipt under `maintenance/` containing the
   baseline hash, repaired hash, rejecting-review hash, authorized coordinates, before/after value hashes, evidence
   keys, and the invoked focused gates. Compile the current repaired worksheet and require exact parsed-object parity
   with the staged `entry.v2.json`; a hand-corrected entry whose worksheet would regenerate stale bytes is still a
   failed repair. `audit_repair_reason_closure.py` and `audit_repair_readiness.py` must pass. The readiness gate runs
   this worksheet/compiler parity check itself, so an author receipt cannot merely claim it.
5. **Review the changed meaning in full context.** A different worker reads every affected complete case and checks
   the exact utterer, quoted-original versus later-raiser/commentator layers, work independence, and whether the
   entry's definition and sense structure still hold after the new evidence. New evidence is precisely where a
   previously hidden sense or a false multi-source claim may emerge. Mechanical success never substitutes for this
   semantic reread. Unchanged prior `KEEP` entries stay hash-identical.
6. **Close only what changed.** The independent rereviewer receives the rejecting bytes, current repaired hashes,
   authorized-coordinate list, and full cases—but not a request to rediscover unrelated defects. For each repaired
   coordinate the closure records `KEEP` or `REVISE`, the exact actor/context/work ruling, `zc.verify`, and an explicit
   definition/sense verdict. Release is authorized only when every authorized coordinate closes and every unrelated
   reviewed entry remains byte-identical. Changed-entry focus saves time; it never licenses skipping the semantic
   reread of an affected case.
7. **Validate proportionately, then globally once.** Run cheap exact/attribution/depth/prose/template checks on the
   changed cohort continuously. Reuse still-valid hash-bound whole-tree receipts for unaffected bytes; do not replay
   expensive global scans after every coordinate. Run the necessary whole-tree gate once at the atomic release.
8. **Install atomically or not at all.** Stage repairs under `fresh-build/entries/`; install only the independently
   closed cohort, merge generated artifacts, verify aggregate parity, and write a durable closure ledger. Never use a
   repair script to edit `terms/` opportunistically.
9. **Turn the failure into prevention.** Classify the root cause. If it can recur, add the smallest compiler check,
   formal assertion, semantic regression canary, or process rule before the next cohort opens. A repaired JSON without
   a production-line guard is an incomplete repair.
10. **Repair the shared cause once; never hand-patch its repeated products.** When several rejected coordinates come
    from the same serializer, emitter, query builder, or template defect, correct that shared transformation first,
    run a two-entry positive/negative canary, and regenerate only the manifest-authorized affected worksheets and
    products. The repair receipt names the shared cause, the canary, and every regenerated ID. Unaffected fields and
    entries remain hash-identical. Repeating the same manual edit entry by entry is both a correctness defect and a
    speed defect because the next compilation can resurrect it.
11. **For lexical-family/connectivity repairs, evidence is a batch input and an empty result is a real ruling.** Run
    one apparatus-clean `zc` batch count over all source terms and every *named* candidate term in the repair cohort;
    reuse that immutable result for each row instead of launching one search process per entry. Every accepted edge
    records the candidate ID, exact query, hits/files/distinct works, relationship type, and the sense-level reason it
    clarifies the article. Every negative harvest records the same evidence for the named candidates actually tested.
    Pseudo-query prose, unnamed sentinel candidates, and forced links added merely to avoid `RelatedTerms: []` are hard
    failures. Where no useful relation survives, preserve `RelatedTerms: []` with the evidenced negative receipt.
    Graph variants and reciprocal relations are checked against the currently reviewed staged companions as well as
    installed authority, so same-release links do not disappear or become one-sided. Re-test the entry's definition
    and sense split against the newly collected evidence before closure; a mechanically correct edge must not leave a
    now-false definition standing.
    **Reciprocal closure is exact and release-wide.** For every accepted symmetric edge `A --type--> B`, require an
    accepted staged edge `B --type--> A` with the identical relation type, not merely `B` naming `A` in display prose
    or `RelatedTerms`. Expand the validation set through every touched companion until no new endpoint is discovered,
    then run reverse-parity on that fixed-point set. If a later lane changes either endpoint, every earlier closure
    whose hashes include that endpoint is stale and must be SHA-rebound and rerun before release. Passing per-lane
    counts cannot close a cross-lane graph.

The calibrated result behind this protocol is decisive: compiling stale repair worksheets produced 53 collateral
findings for seven attribution fixes; hydrating those same repairs from the installed baseline produced zero hard
attribution failures. Therefore any worker proposing reconstruction must first prove why hydration cannot represent
the authorized change; convenience or worksheet availability is not such proof.

**Calibration cases now carried by this law:** a later record owner must not replace the quoted original speaker;
`舉`/`祖師云` quotation boundaries must preserve the original utterer while naming the later raiser/commentator in
context; multiple books repeating one inherited case remain one deployment for validation; an internal section heading
can override an earlier packet heading; and removing one unanchored prose claim requires removing its structured
duplicates without disturbing the rest of the article. These are permanent regression families, not anecdotes.

## 9. Working durably at scale (don't lose work)
Follow **`LEDGER_SYSTEM.md`**: orchestrator persists on every worker return; small slices (≈1 term);
append-only `MANIFEST.jsonl` keyed by the deterministic `Id`; per-term dirs; status lifecycle
`todo→researching→drafted→validated→done`; resume by replaying the manifest. Write findings continually;
plan/usage limits WILL interrupt — the file ledger is what survives across sessions.

## 10. Reference docs (this run)
SPEC_v1 (Zen-dictionary vision + corpus scope) · SPEC_v2 (subsystem plan + current-state map) ·
SPEC_v3 (decisions: dual-file, multi-sense, buffalo pilot) · EWK_RECON_FINDINGS · BUFFALO_PILOT ·
BUFFALO_ENTRY.v2.json · LEDGER_SYSTEM · SPA_DICTIONARY_PLAN · TASK_LOG (chronology).
### Identified master without a canonical roster link

When full-case reading names the uttering master but no exact canonical roster label exists, keep `MasterName` null and use `ActorAttribution.Status = identified-unlinked-master`. This is not an anonymous-master escape hatch. It requires the explicit Chinese/English identity in `ActorLabel`, all six attribution rungs in order, exact-turn grammatical proof repeating that identity, and an `AttributionNote` that names the speaker. Never edit the lineage roster to make a dictionary occurrence pass.
Before assigning that status, resolve the source identity against **every existing roster alias**, not only
`names[0]`. If an exact alias matches, store its canonical `names[0]` in `MasterName`; the attribution gate
hard-fails a roster alias hidden as “unlinked.” This cheap preflight prevents a later reviewer from having
to rediscover canonical links case by case.

For a **contextual** person who is explicitly identified in the case but has no canonical roster label,
do not put a broken link in `ContextMasters`, do not erase the identity into prose, and do not edit the
lineage roster. Use `ContextActors` on the occurrence with `Status = identified-unlinked-master`,
`identified-non-master` for a personally named non-master, or `reviewed-unnamed` for an anonymous
contextual participant whose action or role is established by the complete turn. Supply the explicit
`ActorLabel`, closed non-utterer `Roles`, and case-specific `GrammarEvidence`; the same public label must
appear in `AttributionNote`. `ContextMasters`
remains link-only and contains exact roster `names[0]` values. A later roster reconciliation may promote
the structured unlinked identity without re-reading the case.

## Evidence-scaled receipt-first cohort schedule

The artifact-zero receipt binds the selected entries' ordered positive-integer dynamic floors and their
sum, `N`, as `admittedRequiredOccurrences`. The cohort watchdog derives the complete hard schedule;
callers may not override it:

- viability: 90 seconds;
- actual bounded extraction: 120 seconds;
- adjudicated config: `min(330, 180 + 6*N)` seconds;
- constructor invocation: config deadline + 10 seconds;
- first product: config deadline + 30 seconds;
- construction closure: config deadline + 90 seconds;
- independent review: construction deadline + 180 seconds;
- finite correction: review deadline + 120 seconds;
- publication: correction deadline + 90 seconds.

Every checkpoint receipt repeats the ordered floors, `N`, and complete derived schedule. Missing,
non-positive, reordered, or mismatched floors, totals, or deadlines fail closed. For `N=20`, the
downstream deadlines are 300/310/330/390/570/690/780 seconds.
