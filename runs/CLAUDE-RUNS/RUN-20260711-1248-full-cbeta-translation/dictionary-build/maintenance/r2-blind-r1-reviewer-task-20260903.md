# Blind review task — dictionary edit lane R2, round r1 (2026-09-03)

You are an independent, adversarial reviewer. A dictionary edit lane has
produced a **change rows** file. Your job: verify every row's claims
against frozen PRE/POST materials and flag every violation.

You have NO knowledge of which rows, if any, were deliberately planted
defects. Judge the bytes and the laws only. Do not speculate about
intent; do not read anything outside the inputs listed below.

## Inputs (the ONLY files you may read)

- Rows: `maintenance/r2-blind-r1-rows-20260903.json` — header carries
  `laneLaw`, `materials` (sha256 pins), and `rows` (16 rows, `rowId`
  R0000..R0015).
- Materials (frozen verification set): `maintenance/r2-blind-r1-materials/`
  - `pre/<entryId>.json` — the entry BEFORE the lane
  - `post/<entryId>.json` — the entry AFTER the lane (exact published
    bytes)
- Your own working directory (see below) for your scripts and outputs.

**Forbidden**: every other file under `maintenance/` (including anything
named plants/registry/adjudication/SPEC), the `terms/` tree, the clone,
and any dictionary tooling. If a law below cannot be checked from the
inputs alone, say so in `notes` — do not go looking for more files.

## Step 0 — integrity

Compute sha256 of each of the 6 materials files and compare to
`materials` in the rows header. Any mismatch ⇒ `materialsPinsOk: false`
and STOP (deliver `verdicts.json` with the failure and no flags).

## Row classes and laws

Slot notation: `slot(entry, si, oi)` = `entry["Senses"][si-1]
["Occurrences"][oi-1]`. `sense(entry, si)` = `entry["Senses"][si-1]`.
`==` on JSON values means deep equality of parsed values.

### Law A — `occ-attribution` rows

Fields: `entry, si, oi, oldMasterName, oldContextMasters,
oldAttributionNote, newMasterName, newContextMasters,
newActorAttribution, newAttributionNote, carriedRelPath, carriedFromLb,
carriedToLb, carriedKwic, postOccurrenceRels, postOccurrenceCount`.

- **A1 pre-slot identity**: in PRE, `slot(entry,si,oi)` has
  `MasterName == oldMasterName`, `ContextMasters == oldContextMasters`,
  `AttributionNote == oldAttributionNote`, and its
  `RelPath/FromLb/ToLb/Kwic` equal the four `carried*` fields.
- **A2 post-slot identity**: in POST, `slot(entry,si,oi)` has
  `MasterName == newMasterName`, `ContextMasters == newContextMasters`,
  `AttributionNote == newAttributionNote`,
  `ActorAttribution == newActorAttribution`, and its
  `RelPath/FromLb/ToLb/Kwic` STILL equal the four `carried*` fields
  (carried means unchanged pre→post).
- **A3 sense coverage**: `sense(entry,si)` occurrence count is identical
  PRE→POST; every occurrence slot of that sense OTHER than slots covered
  by an `occ-attribution` row for this same entry (match on `oi`) is
  byte-identical PRE→POST (deep equal); `postOccurrenceRels` equals the
  POST sense's occurrence RelPaths in order; `postOccurrenceCount`
  equals the POST sense's occurrence count.

### Law B — prose-rewrite rows

Classes `explanation-rewrite`, `note-rewrite`, `attributionnote-rewrite`.
Fields: `entry, si, field, oi` (attributionnote only), `before`,
`after`.

- **B1**: PRE `sense(entry,si)[field]` contains `before` exactly once;
  POST `sense(entry,si)[field]` contains `after` exactly once.
- **B2**: PRE field with `before` replaced by `after` (one replacement)
  equals the POST field byte-for-byte.
- **B3** (attributionnote-rewrite only): PRE
  `slot(entry,si,oi).AttributionNote == before` and POST
  `slot(entry,si,oi).AttributionNote == after`.
- **B4 prose anchoring** — evaluate ONCE per (entry, si) touched by any
  Law-B row: every maximal CJK run (regex `[㐀-鿿豈-﫿]+`, i.e.
  U+3400–U+9FFF and U+F900–U+FAFF) in the POST sense's `Explanation` +
  `Note` joined by `\n` must be **anchored**: some POST
  `Occurrences`/`ClaimAnchors` kwic `k` (nonempty) exists with
  `run in k or k in run`. An unanchored run attached to a Law-B row's
  entry ⇒ flag that row under B4.

### Law C — `relatedmasters-rename` rows

Fields: `entry, si, renamed{old,new}, postRelatedMasters`.

- **C1**: PRE `sense(entry,si).RelatedMasters` contains `old` exactly
  once; POST `RelatedMasters` equals the PRE list with that one element
  replaced by `new` (order otherwise preserved); `postRelatedMasters`
  equals the POST field.
- **C2**: `renamed.new` equals the roster name published in the rows
  header `laneLaw.t48n2025Class` (the name in quotes: `Dongyang Dehui`).

### Law D — `searchaliases-add` rows

Fields: `entry, si, added, postSearchAliases`.

- **D1**: PRE `sense(entry,si).SearchAliases` + `[added]` (appended
  last) equals POST `SearchAliases`; `postSearchAliases` equals the POST
  field.

### Law E — lane law (check across all three entries)

- **E1**: no `RelPath` listed in `laneLaw.retiredRels` appears in any
  POST `Occurrences` or `ClaimAnchors` of any materials entry.
- **E2**: for each entry, the sense count and each sense's occurrence
  count are identical PRE→POST.
- E-law flags name the row that triggered your attention (if none, name
  the entry's first row and say so in `reason`).

## Method requirements

1. Write a `verify.py` (or similar) implementing the laws mechanically;
   run it with `python -X utf8`.
2. ALSO read the rows file and all 6 materials in full with your Read
   tool — eyeball every row against the bytes (mechanical checks miss
   what eyes catch; the coordinator byte-adjudicates on re-reads).
3. For every flag, re-derive the contested bytes before writing it
   (print the diverging values — codepoints for CJK diffs).

## Deliverables (in YOUR directory)

`maintenance/subagents/20260903-r2-blind-r1-reviewer-N/` (N given in
your tasking):

- `verdicts.json` — EXACTLY this schema:
  ```json
  {
    "reviewer": "reviewerN",
    "materialsPinsOk": true,
    "rowsChecked": 16,
    "flags": [{"rowId": "R0000", "law": "A2",
                "reason": "post slot FromLb 0672a08 != row 0672a07"}],
    "notes": "…anything the laws could not check, method notes…"
  }
  ```
  `rowsChecked` MUST equal the row count (16) — every row you do NOT
  flag counts as accepted. One flags entry per broken law per row (a
  row may break several laws).
- `FINDINGS.md` — your method, and a table of flags with the diverging
  bytes.
- Your `verify.py` etc.

Flag criteria reminder: a row is FLAGGED iff its claims contradict the
frozen materials or violate a law. Stylistic taste is not a law. If a
claim is unverifiable from the inputs, flag it and say what was missing.
