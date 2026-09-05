# FINDINGS — blind review r2 / round r1, reviewer 2 (20260903 tasking)

## Method

1. **Step 0 — integrity.** sha256 of all 6 frozen materials computed (PowerShell
   `Get-FileHash` AND inside `verify.py` over raw bytes) and compared to the
   `materials` pins in the rows header. **All 6 matched.** `materialsPinsOk: true`.
2. **Mechanical verification.** `verify.py` (run with `python -X utf8`) implements
   laws A1–A3, B1–B4, C1–C2, D1, E1–E2 exactly as specified: deep-equality slot
   lookups (`slot(entry,si,oi)` = `Senses[si-1].Occurrences[oi-1]`), one-replacement
   rebuilds for Law B, full-list reconstruction for C1/D1, retired-rel scan and
   count checks for E, and the `[㐀-鿿豈-﫿]+` run-anchoring regex for B4.
   Curated one-line reasons are applied via an explicit override table in the
   script that hard-fails if an override targets a flag the mechanical checks did
   not raise — detection itself is untouched mechanical.
3. **Eyeball pass.** The rows file and all 6 materials were read in full with the
   Read tool before scripting; every flag below was re-derived by printing the
   diverging values (codepoints for CJK diffs). The PRE→POST diff inventory
   (script output) confirms every changed JSON path in the three entries is
   explained by at least one consistent row: t_ea2a427c7aba 17 paths (occ oi=1/8/9
   attribution blocks, RelatedMasters[7] rename, Explanation rewrite),
   t_057cc9ea8755 2 paths (Note + oi=3 AttributionNote), t_968a2f97c9ff 1 path
   (SearchAliases append). No unexplained lane edits.

## Verdict

16 rows checked; **14 flags on 9 rows**; 7 rows accepted
(R0001, R0002, R0003, R0004, R0005, R0006, R0008). E1/E2 clean for all three
entries; B4 anchoring clean for both Law-B senses (7 CJK runs in
t_ea2a427c7aba si1 and 21 in t_057cc9ea8755 si1, all anchored to POST
Occurrences/ClaimAnchors kwics).

## Flags (with diverging bytes)

| Row | Law | Diverging bytes |
|-----|-----|-----------------|
| R0000 | A2 | POST slot(1,8) `MasterName` = `null`; row claims `newMasterName` = `"Dongyang Dehui"`. (Also contradicts laneLaw.t48n2025Class: Dehui is never a speaking master. Its otherwise-identical twin R0002 with `null` passes.) |
| R0009 | A2 | POST slot(1,9) `ContextMasters[0].Roles` = `["compiler"]`; row claims `["utterer"]`. Twin R0003 (`compiler`) passes. |
| R0010 | A2 | POST slot(1,1) `ActorAttribution.ActorLabel` = `"the monastic code's institutional voice"`; row claims `"the code compiler's editorial voice"`. All other ActorAttribution fields match. |
| R0011 | A1 | PRE slot(1,8) `Kwic` char index 11: `內` (U+5167) vs row `carriedKwic` `猫` (U+732B). PRE: `…如尋常坐禪向內坐…`; row: `…如尋常坐禪向猫坐…`. |
| R0011 | A2 | POST slot(1,8) `Kwic` still `內` (U+5167) — the "carried (unchanged)" claim is false for the same corrupted char. |
| R0012 | A1 | PRE slot(1,1) `FromLb` = `"1143a07"`; row `carriedFromLb` = `"1143a08"`. |
| R0012 | A2 | POST slot(1,1) `FromLb` = `"1143a07"`; `carriedFromLb "1143a08"` is not unchanged pre→post. |
| R0007 | B3 | B3's literal `==`: PRE slot(1,3) AttributionNote is 366 chars, `before` is a 48-char fragment; POST note 400 chars, `after` 82. See interpretation note below. |
| R0014 | B1 | POST Note contains `after` 0 times: `after` appends `(非攝非散)`, which appears nowhere in POST. PRE side contains `before` exactly once (passes). |
| R0014 | B2 | One-replacement rebuild vs POST Note first diverges at char 537: rebuilt `…retains (非攝非散) the ordinary…` vs POST `…retains the ordinary…`. |
| R0015 | B1 | POST slot(1,3) AttributionNote contains `after` 0 times: `after` writes compiler `百丈自編` (U+767E U+4E08 U+81EA U+7DE8) where POST reads `至柔等編` (U+81F3 U+67D4 U+7B49 U+7DE8). |
| R0015 | B2 | Rebuild first diverges at char 99: `…disciples (百丈自編): in the verse` vs POST `…disciples (至柔等編): in the verse`. |
| R0015 | B3 | Same literal-`==` fragment issue as R0007 (48/82-char fragments vs 366/400-char notes). |
| R0013 | D1 | `PRE SearchAliases + ["一不成二不是"]` ≠ POST `["one fails, two is wrong", "一不成、二不是"]`: row's `added` drops the ideographic comma `、` (U+3001) between `成` (U+6210) and `二` (U+4E8C). `postSearchAliases` itself matches POST; twin R0008 (with U+3001) passes D1 fully. |

## Interpretation notes for the coordinator

- **B3 fork (R0007, R0015).** The rows carry `field: "OccAttributionNote"`,
  which is not a sense-level key. For B1/B2 I resolved it to
  `slot(entry,si,oi).AttributionNote` (the only occurrence-level note); under
  that (substring) reading **R0007 is fully byte-consistent** with PRE and POST
  and would not be flagged, while R0015 still fails B1/B2 decisively. B3 as
  written, however, demands full-string equality of the slot note with
  `before`/`after`, which no fragment-style row can satisfy. I enforced B3
  literally (flagging R0007 too) and note the fork here so the byte-adjudicator
  can rule on the law's intent; either ruling leaves R0015 flagged.
- **Unverifiable from inputs.** `laneLaw.defectCensus` names `t_ab715aa474d5`
  and `t_351fa42d396b`, which are absent from the materials — no law attaches,
  nothing to check. `rowSha` per row is not verified because no law defines its
  serialization.
- **Duplicate-row structure.** The rows file describes the same edit twice in
  six cases (R0000/R0002, R0001/R0010/R0012, R0003/R0009, R0006/R0014,
  R0007/R0015, R0008/R0013). Each flagged twin contradicts the frozen PRE or
  POST bytes independently of its sibling; the passing twins are accepted on
  their own bytes. No law forbids the duplication itself.
