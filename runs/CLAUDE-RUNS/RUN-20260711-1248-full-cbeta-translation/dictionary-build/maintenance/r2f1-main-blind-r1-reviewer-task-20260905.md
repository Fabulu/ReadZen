# Blind review task — combined R2+F1 MAIN publication, round r1

You are an independent reviewer. Work ALONE from the permitted inputs.
Do not read any other file. Do not run git commands against any clone.
Your job: verify every row of a publication-diff review file against
frozen materials, byte by byte.

## Your working directory

`runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation/dictionary-build/maintenance/subagents/20260905-r2f1-blind-r1-reviewer-N/`

Write ALL your outputs there: `verdicts.json`, `FINDINGS.md`,
`verify.py`, `verify-report.txt`.

## Permitted inputs (read these and nothing else)

- `maintenance/r2f1-main-blind-r1-rows-20260905.json` — 11 rows
  (`R0000`..`R0010`, deck order; each row carries its index in
  `rowIndex` if present — identify rows by position `R%04d`).
- `maintenance/r2f1-main-blind-r1-materials-20260905/`:
  - `main-head-<eid>.json` for 5 entry ids — the publication target's
    committed MAIN state at the moment of publication
    (`{"__absent__": true}` means the entry did not exist on main);
  - `staged-<eid>.json` for the same 5 ids — the staged publication
    bytes;
  - `surface-facts.json` — the publication surface numbers
    (entry counts, changed/added sets, Dehui census, non-product
    regression, alias deltas).

The rows file's `materialsPins` maps every material file to its
sha256. VERIFY EACH PIN over raw bytes before anything else. If any
pin fails, stop and report `materialsPinsOk: false`.

## FORBIDDEN (reading any of these voids the round)

`r2f1-main-blind-r1-plants-*.json`, any `*transform*`,
`*adjudicate*`, `*gates*`, `*manifest*`, `*receipt*`,
`*archive-bundle*`, `*blind-r1-rows*` of OTHER lanes (r2-, f1-),
any file under `subagents/`, any clone working tree, any JSONL
transcript.

## Context (what this round reviews)

A dictionary correction arc published 5 verified entries to a main
publication surface. The lanes' own reviews covered the product
bytes. THIS round reviews the publication step's own claims: the OLD
main-HEAD state of each product slot (including absence claims), the
NEW staged state, and the surface census numbers.

## Laws

For `kind: "occ-attribution"` rows (window locator + both states):
- **A1** `relPath`/`fromLb`/`toLb`/`si`/`oi` locate a real occurrence
  in `staged-<eid>.json` (Senses[si-1].Occurrences[oi-1]), and its
  `RelPath`/`FromLb` equal the row's.
- **A2** `carriedKwic` == that staged occurrence's `Kwic`, byte-exact.
- **B1** `oldWindowPresent` is true iff an occurrence with the same
  `RelPath`+`FromLb` exists in `main-head-<eid>.json` (for the
  `{"__absent__": true}` material: false).
- **B2** when present, `oldMasterName`/`oldContextMasters`/
  `oldAttributionNote` equal that main-HEAD occurrence's fields,
  byte-exact; when absent, all three are null.
- **C1** `newMasterName`/`newContextMasters`/`newAttributionNote`
  equal the staged occurrence's fields, byte-exact.
- **C2** `newActor` equals the staged occurrence's ActorAttribution
  fields (Status/Kind/ActorLabel/ActorRole), byte-exact.
- **C3** `newActor.ActorLabel` appears verbatim (case-insensitive
  substring) inside `newAttributionNote`.

For `kind: "note-provenance"`: old/new has-provenance flags and the
excerpt must match `main-head-`/`staged-t_057cc9ea8755.json` (the
X70n1399 occurrence's AttributionNote; `至柔等編` present exactly in
the staged note, absent in the old).

For `kind: "alias-add"`: `oldAliases`/`newAliases` equal the sense-0
SearchAliases of `main-head-`/`staged-t_968a2f97c9ff.json`; the
`addedAlias` is in new but not old.

For `kind: "surface-census"`:
- **D1** entryCount == lengths of the material sets' implications ==
  `surface-facts.json` (before = main entries; after = before + 1);
- **D2** `changedSetEqualsWorklist` is true iff exactly the 5 product
  ids differ between main-head and staged materials;
- **D3** `dehuiCensusBefore`/`dehuiCensusAfter` == the actual
  MasterName == "Dehui" rows recomputed over ALL material files —
  NOTE: the materials cover only the 5 products; for the census
  recompute use `surface-facts.json` as the frozen record and check
  internal consistency (before lists exactly 1 row inside a product;
  after empty);
- **D4** `nonProductRegression` == [] and `aliasLostCount` ==
  `len(surface-facts.aliasLost)`.

**E1** every row's `entry` is one of the 5 material ids.

## Deliverables

1. `verdicts.json` — EXACT schema:
   `{"reviewer": "reviewerN", "materialsPinsOk": bool,
     "rowsChecked": <int, must be 11>, "flags": [
       {"row": "R00ii", "laws": ["A2"], "claim": "<what the row
        claims>", "actual": "<what the bytes say>", "divergingBytes":
        "<exact byte-level diff>"}], "notes": "<free text>"}`
   A row is FLAGGED iff it violates any law. A clean row is not
   flagged.
2. `FINDINGS.md` — your method, the flag table, per-accepted-row
   one-line justifications.
3. `verify.py` + `verify-report.txt` — a mechanical checker you write
   implementing the laws; run it with `python -X utf8`.

Honesty rules: flag ONLY real law violations you can cite diverging
bytes for. Do NOT flag stylistic differences. If you are unsure,
check the bytes again. `rowSha` is not a law — ignore it.
