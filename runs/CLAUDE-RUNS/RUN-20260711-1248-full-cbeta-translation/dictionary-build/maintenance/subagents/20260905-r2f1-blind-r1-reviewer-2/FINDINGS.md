# FINDINGS — blind review r2f1-main, round r1 (reviewer 2)

Working directory: `maintenance/subagents/20260905-r2f1-blind-r1-reviewer-2/`
Inputs read (and nothing else): the rows file and the 11 material files it pins.

## Method

1. **Pins first.** All 11 `materialsPins` sha256 were verified over raw bytes
   (independently via `Get-FileHash`, then re-verified inside `verify.py`
   before any row check). **All 11 match — `materialsPinsOk: true`.**
2. **Materials read in full**: 5 `main-head-<eid>.json`, 5 `staged-<eid>.json`
   (for `t_968a2f97c9ff` the sense-0 `SearchAliases` arrays were pulled
   directly), plus `surface-facts.json`. `main-head-t_351fa42d396b.json` is
   `{"__absent__": true}` as the census implies.
3. **Mechanical checker.** `verify.py` implements every law from the brief
   (A1–A2, B1–B2, C1–C3, note-provenance, alias-add, D1–D4, E1) with
   codepoint-exact (byte-exact) comparison of JSON-decoded string/list values,
   identifies rows by deck position `R0000..R0010`, recomputes the surface
   quantities from the 10 entry materials (changed set, Dehui census,
   added-set consistency), and writes `verdicts.json` + `verify-report.txt`.
   Run with `python -X utf8`; exit report saved as `verify-report.txt`.
4. Manual byte-reading of every flagged field confirmed each flag before it
   was recorded; no stylistic differences were flagged; `rowSha` ignored.

Recomputed from the materials (shared by both census rows): changed ids =
all 5 product ids (1 absent→added + 4 modified); Dehui census before =
`["t_ab715aa474d5 T/T48/T48n2025.xml 1144b03"]` (exactly 1 row, inside a
product), after = `[]`; `surface-facts.entryCount` 4715→4716 with `addedSet =
[t_351fa42d396b]` absent-on-main and present-staged; `len(aliasLost)` = 9.

## Flag table

| Row | Laws | Diverging bytes |
|---|---|---|
| R0001 | A2 | `carriedKwic` offset 2: row `兼` U+517C vs staged Kwic `齊` U+9F4A (`並宜兼赴` vs `並宜齊赴`) |
| R0004 | D1, D2 | `entryCount.after`: row `4715` vs surface-facts `4716` (and before+1); `changedSetEqualsWorklist`: row `false` vs recomputed `true` |
| R0007 | B1, B2 | `oldWindowPresent`: row `true` vs actual `false` — `main-head-t_ea2a427c7aba.json` has no occurrence `T/T48/T48n2025.xml @ 1143a07`; when absent B2 requires all-null, but row carries `oldMasterName: "Dehui"` and `oldAttributionNote: "…: the fabricated pre-publication main note"` |

Flag detail (same content as `verdicts.json`):

- **R0001 / A2** — the staged occurrence (t_ab715aa474d5, Senses[0].Occurrences[1],
  1144b03–1144b04) reads `並宜齊赴。當思古人一日不作一日不食之誡。`; the row's
  `carriedKwic` reads `並宜兼赴。…`. One character diverges. All other fields of
  this row (A1, B1, B2, C1–C3) pass byte-exact.
- **R0004 / D1** — row claims `after: 4715`; `surface-facts.json` says
  `after: 4716`, and the material implication (addedSet = the one id absent on
  main and present staged) forces after = before + 1 = 4716.
- **R0004 / D2** — row claims `changedSetEqualsWorklist: false`; recomputing
  main-head vs staged over the materials shows exactly the 5 worklist ids
  differ, so the true value is `true` (t_351fa42d396b added, the other 4
  modified).
- **R0007 / B1+B2** — main-head-t_ea2a427c7aba.json's only T48n2025 occurrence
  is at 1113a21; no occurrence exists at 1143a07 (R0002 covers the same window
  with the correct absent claim). The row's old note even self-describes as
  "the fabricated pre-publication main note" — it does not exist in the frozen
  main-HEAD bytes.

## Accepted rows (one line each)

- **R0000** — staged si1/oi8 (T48n2025 1113a21–1113a22) matches relPath/fromLb/toLb/Kwic; old state (null/[]/note) equals the main-HEAD occurrence byte-exact; new fields, actor, and C3 all byte-exact.
- **R0002** — staged si1/oi1 (1143a07–1143a12) matches all new-state bytes; main-HEAD has no occurrence at T48n2025@1143a07, so the absent claim with all-null old fields is correct.
- **R0003** — staged si1/oi9 (1143a12–1143a15) matches all new-state bytes; old window genuinely absent on main-HEAD (all-null old fields correct).
- **R0005** — same window as R0001 but `carriedKwic` `並宜齊赴。…` matches the staged bytes exactly; old Dehui/utterer state and new institutional-voice state match main-HEAD/staged byte-exact; C3 holds.
- **R0006** — main-head material is `{"__absent__": true}`, so oldWindowPresent=false with nulls is correct; staged si1/oi1 (1127c04–1127c10) matches Kwic/note/actor byte-exact; C3 holds.
- **R0008** — main-head-t_057cc9ea8755 has no X70n1399 occurrence (oldNoteHasProvenance=false correct); the staged occ-3 note contains `至柔等編` and the row's excerpt is a byte-exact prefix of it.
- **R0009** — old aliases `["one fails, two is wrong"]` and new aliases `[…, "一不成、二不是"]` equal the main-head/staged sense-0 SearchAliases; addedAlias is in new and not old.
- **R0010** — entryCount 4715→4716 equals surface-facts and before+1; changedSetEqualsWorklist=true equals the recomputation; Dehui census before (1 product row) / after (empty) equals both surface-facts and the material recompute; nonProductRegression=[] and aliasLostCount=9=len(aliasLost).

## Anomalies / notes

- The deck contains contradictory near-duplicate rows: R0001 vs R0005 (same
  window, Kwic differs by one character), R0002 vs R0007 (same window,
  opposite old-state claims), R0004 vs R0010 (opposite census numbers). In
  each pair exactly one row matches the frozen bytes.
- The two `surface-census` rows carry no `entry` field (schema of that kind);
  E1 was applied to every row that carries an entry — all 9 pass.
- No other law violations found; 8 of 11 rows are clean.
