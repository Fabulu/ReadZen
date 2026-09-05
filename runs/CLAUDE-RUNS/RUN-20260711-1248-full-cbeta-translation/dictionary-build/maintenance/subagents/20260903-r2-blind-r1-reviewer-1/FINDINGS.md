# Blind review r2/r1 — reviewer 1 (2026-09-04)

## Inputs

- Rows: `maintenance/r2-blind-r1-rows-20260903.json` (16 rows, R0000..R0015, 3 entries)
- Materials: `maintenance/r2-blind-r1-materials/{pre,post}/{t_ea2a427c7aba,t_057cc9ea8755,t_968a2f97c9ff}.json`

Nothing outside the task-file inputs was read.

## Step 0 — integrity

All 6 sha256 pins recomputed from raw bytes match the rows header exactly
(`pre/post` x 3 entries). `materialsPinsOk: true`.

## Method

1. `verify.py` (run with `python -X utf8`) implements every law mechanically:
   A1/A2/A3 (occ-attribution), B1/B2 (+B3, see adjudication below), B4
   (CJK-run anchoring, regex `[㐀-鿿豈-﫿]+` = U+3400-U+9FFF + U+F900-U+FAFF),
   C1/C2, D1, E1/E2. Equality is deep equality of parsed JSON; string
   divergences are re-derived and printed with first-divergence codepoints.
2. The rows file and all 6 materials were also read in full with the Read
   tool; every row was eyeballed against the bytes. One initial eyeball
   candidate (R0000 `newAttributionNote` "says that" vs POST "states that")
   was re-derived and DISCARDED — the row's `new` note actually reads
   "states that" and equals POST; only its `old` note (correctly) has
   "says that".
3. A full recursive PRE->POST structural diff of all three entries was
   computed to catch unlisted changes: t_ea2a427c7aba 17 changed paths
   (oi=1/8/9 attribution rewrites + RelatedMasters[7] rename + Explanation
   fragment), t_057cc9ea8755 2 (sense Note + oi=3 AttributionNote),
   t_968a2f97c9ff 1 (SearchAliases append). Every difference is covered by a
   row claim; no unlisted change exists.

## Law-B3 adjudication (documented deviation)

B3's literal reading (`PRE slot.AttributionNote == before`, `POST == after`)
is vacuous for the two attributionnote-rewrite rows: `before`/`after` are
fragments (B1/B2 semantics), and the rows' field name `OccAttributionNote`
does not exist at sense level. Literal B3 evaluates False for BOTH R0007 and
R0015. I adjudicated B1 (containment exactly once) and B2 (single-replacement
equality) at the pinned slot `slot(entry,si,oi).AttributionNote` and treated
B3 as that slot-pin. This does not change which rows are defective: R0015's
after (百丈自編) is absent from POST under either reading; R0007's after
(至柔等編) is present in POST.

## Flags (12 flags, 8 rows flagged; 8 rows accepted)

| Row | Law | Diverging bytes (row vs frozen material) |
|-----|-----|------------------------------------------|
| R0000 | A2 | POST slot (t_ea2a427c7aba, si1, oi8) `MasterName = null`; row claims `newMasterName = "Dongyang Dehui"`. (All other A1/A2/A3 fields of this row match.) |
| R0009 | A2 | POST slot (si1, oi9) `ContextMasters Roles = ["compiler"]`; row claims `["utterer"]`. |
| R0010 | A2 | POST slot (si1, oi1) `ActorAttribution.ActorLabel = "the monastic code's institutional voice"`; row claims `"the code compiler's editorial voice"`. |
| R0011 | A1 | PRE slot (si1, oi8) Kwic has 內 U+5167 (`…如尋常坐禪向內坐…`); row `carriedKwic` has 猫 U+732B (`…如尋常坐禪向猫坐…`), first divergence char 11. |
| R0011 | A2 | Same 猫/內 divergence vs POST slot Kwic — carried means unchanged, and it is not. |
| R0012 | A1 | PRE slot (si1, oi1) `FromLb = "1143a07"` (U+0037); row `carriedFromLb = "1143a08"` (U+0038). |
| R0012 | A2 | Same 1143a08/1143a07 divergence vs POST slot FromLb. |
| R0013 | D1 | PRE SearchAliases `["one fails, two is wrong"]` + row `added = "一不成二不是"` (no 、) ≠ POST `["one fails, two is wrong", "一不成、二不是"]` (with 、 U+3001). The row's `postSearchAliases` field itself matches POST; the `added` claim contradicts it. (R0008 covers this same change correctly.) |
| R0014 | B1 | Row `after = "verse in his recorded sayings, compiled by his disciples, retains (非攝非散)"`; POST Note has the prefix but ZERO occurrences of the appended `(非攝非散)`. |
| R0014 | B2 | PRE Note with before->after ≠ POST Note: row side has `retains (非攝非散) the` ( `(` U+0028 ), POST has `retains the ordina…` (`t` U+0074) at char 537. |
| R0015 | B1 | Row `after` contains 百丈自編 (百 U+767E); POST slot (t_057cc9ea8755, si1, oi3) AttributionNote contains 至柔等編 (至 U+81F3). `after` occurs 0 times in POST. |
| R0015 | B2 | Replacement divergence at char 99: row `…disciples (百丈自編): in` vs POST `…disciples (至柔等編): in`. (R0007 makes the same edit with 至柔等編 and passes B1/B2.) |

## Clean checks (no flags)

- E1: neither retired RelPath (`T/T48/T48n2023.xml`, `X/X63/X63n1245.xml`)
  appears in any POST Occurrence or ClaimAnchor of any of the three entries.
- E2: sense counts (2/1/1) and per-sense occurrence counts (9,3 / 6 / 10)
  identical PRE->POST for all entries.
- A3: sense-1 occurrence rels order and count 9 match all occ rows;
  uncovered slots oi=2..7 of t_ea2a427c7aba si1 are deep-equal PRE->POST.
- B4: all 21 CJK runs (t_057cc9ea8755 si1) and all 7 CJK runs
  (t_ea2a427c7aba si1) in POST Explanation+Note are kwic-anchored; 0
  unanchored.
- C1/C2 (R0004): PRE RelatedMasters contains "Dehui" exactly once; POST is
  the same list with that element replaced by "Dongyang Dehui" (position 8);
  roster name in `laneLaw.t48n2025Class` is 'Dongyang Dehui' — match.
- D1 (R0008): PRE + ["一不成、二不是"] == POST; postSearchAliases == POST.
- Accepted rows: R0001, R0002, R0003, R0004, R0005, R0006, R0007, R0008.

## Unverifiable from inputs (noted, not flagged)

- `rowSha` per row: no canonical serialization specified in the inputs;
  treated as metadata.
- `laneLaw.defectCensus` names t_ab715aa474d5 and t_351fa42d396b, neither of
  which is in the materials set — nothing to check against.

## Deliverables

- `verify.py` — the verifier (self-contained, re-runnable).
- `verdicts.json` — schema-exact verdict: pinsOk true, 16 rows checked,
  12 flags.
- `FINDINGS.md` — this file.
