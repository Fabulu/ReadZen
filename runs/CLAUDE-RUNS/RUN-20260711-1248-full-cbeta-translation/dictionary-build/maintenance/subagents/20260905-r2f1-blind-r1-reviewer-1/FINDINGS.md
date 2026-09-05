# FINDINGS — blind review r1, reviewer1 (combined R2+F1 MAIN publication)

- Round: r2f1-main-blind-r1, cohort r2f1-main-20260905
- Reviewer: reviewer1 (independent, worked alone from permitted inputs only)
- Date: 2026-09-05
- Deliverables: `verdicts.json`, `verify.py`, `verify-report.txt`, this file

## Method

1. **Pins first.** sha256 over raw bytes of all 11 material files vs the rows
   file's `materialsPins` — all 11 match (`materialsPinsOk: true`). Review
   proceeded only after this gate.
2. **Permitted inputs only.** Opened by exact path: the rows JSON and, inside
   `r2f1-main-blind-r1-materials-20260905/`, the 5 `main-head-<eid>.json`, the
   5 `staged-<eid>.json`, and `surface-facts.json`. No other file was read; no
   git commands were run.
3. **Manual byte pass.** Read every row and every material occurrence it
   touches, comparing strings by eye first.
4. **Mechanical checker.** `verify.py` (run `python -X utf8`) re-implements
   every law byte-exactly: A1/A2/B1/B2/C1/C2/C3 (+E1) for occ-attribution,
   the note-provenance checks (flags, `至柔等編` present exactly once in the
   staged X70n1399 note, absent from the old material, excerpt = byte-prefix
   of the staged note), alias-add (sense-0 SearchAliases equality + membership),
   and D1–D4 for surface-census (D2's changed set recomputed as the ids whose
   main-head and staged JSON differ; D3's census recomputed as
   MasterName == "Dehui" occurrences over all main-head/staged materials and
   cross-checked against `surface-facts.json`). Output saved as
   `verify-report.txt`. `rowSha` was ignored per instructions.
5. **Targeted re-verification of flags.** For R0007, additionally confirmed
   over the raw main-head material: count of `1143a07` = 0, count of the
   claimed old note text = 0, MasterName == "Dehui" occurrences = 0, and the
   entry's only `T/T48/T48n2025.xml` window is `1113a21`.

## Flag table

| Row | Kind | Laws violated | Diverging bytes |
|-----|------|---------------|-----------------|
| R0001 | occ-attribution | A2 | `carriedKwic` char index 2 (1-based 3rd char): row `兼` U+517C (UTF-8 `E5 85 BC`) vs staged Kwic `齊` U+9F4A (UTF-8 `E9 BD 8A`) — `並宜兼赴。…` vs `並宜齊赴。…` (staged-t_ab715aa474d5.json, Senses[0].Occurrences[1].Kwic) |
| R0004 | surface-census | D1, D2 | D1: row `entryCount.after = 4715` vs `surface-facts.json` `"after": 4716` (last digit `5` vs `6`; before 4715 + the 1 absent-on-main product `t_351fa42d396b` forces after = before + 1). D2: row `changedSetEqualsWorklist = false` while all 5 product ids differ between their main-head and staged materials (recomputed true). |
| R0007 | occ-attribution | B1, B2 | B1: row `oldWindowPresent = true` but main-head-t_ea2a427c7aba.json contains no occurrence with RelPath `T/T48/T48n2025.xml` + FromLb `1143a07` (its only T48n2025 window is `1113a21`; `1143a07` byte count = 0). B2: claimed `oldMasterName "Dehui"` / `oldAttributionNote "…the fabricated pre-publication main note"` have zero matching bytes in the material (note-text count = 0; MasterName=="Dehui" count = 0); with the window absent all three old fields must be null. |

## Accepted rows (one-line justifications)

- **R0000** (t_ea2a427c7aba, T48n2025@1113a21, si1/oi8): staged occurrence #8 locates and byte-matches Kwic/note/actor/context; main-head has the same window with MasterName null, ContextMasters [], and the "Imperially Revised Baizhang Monastic Code, redacted by Dehui" note — all old/new fields equal. CLEAN.
- **R0002** (t_ea2a427c7aba, T48n2025@1143a07, si1/oi1): locator resolves to staged occurrence #1; main-head contains no 1143a07 window so oldWindowPresent=false with three nulls is correct; new-state fields byte-match staged. CLEAN.
- **R0003** (t_ea2a427c7aba, T48n2025@1143a12, si1/oi9): staged occurrence #9 matches locator, Kwic, note, actor (label verbatim inside note); no 1143a12 window on main so absence claims hold. CLEAN.
- **R0005** (t_ab715aa474d5, T48n2025@1144b03, si1/oi2): identical window to R0001 but with the correct staged Kwic `並宜齊赴…`; main-head occurrence #2 byte-matches oldMasterName "Dehui", oldContextMasters, and the "exact actor: Dehui … Exact speaker: Dehui" note. CLEAN.
- **R0006** (t_351fa42d396b, T48n2025@1127c04, si1/oi1): main-head material is `{"__absent__": true}` so oldWindowPresent=false/nulls are right; staged occurrence #1 byte-matches locator, Kwic, note, actor, context. CLEAN.
- **R0008** (t_057cc9ea8755, X70n1399): staged occ-3 AttributionNote contains `至柔等編` exactly once and the row's excerpt is a byte-prefix of it; main-head has no X70n1399 occurrence at all and no `至柔等編` anywhere, so oldNoteHasProvenance=false / newNoteHasProvenance=true hold. CLEAN.
- **R0009** (t_968a2f97c9ff): oldAliases == main-head sense-0 SearchAliases `["one fails, two is wrong"]`; newAliases == staged `[…, "一不成、二不是"]`; addedAlias in new only. CLEAN.
- **R0010** (surface-census): entryCount 4715→4716, changedSetEqualsWorklist true, Dehui census before/after, nonProductRegression [], aliasLostCount 9 == len(surface-facts.aliasLost) — all equal `surface-facts.json` and independently recomputable from the materials. CLEAN.

## Notes / anomalies

- Rows R0004 and R0010 are mutually contradictory surface-census claims over
  the same publication; the materials side with R0010 on every field.
- R0001 and R0005 describe the same window (t_ab715aa474d5, 1144b03) and
  differ only in one Kwic character; the staged bytes side with R0005.
- R0002 and R0007 describe the same window (t_ea2a427c7aba, 1143a07) and
  disagree on the old state; main-head bytes side with R0002 (window absent).
- The surface-census rows carry no `entry` field, so E1 is not applicable to
  them; every row that does carry `entry` names one of the 5 material ids.
- `rowSha` values were present but ignored, per the honesty rules.
