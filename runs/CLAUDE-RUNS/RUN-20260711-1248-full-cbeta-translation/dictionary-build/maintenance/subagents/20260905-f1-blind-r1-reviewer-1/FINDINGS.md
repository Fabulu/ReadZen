# Blind review findings — F1 lane r1, reviewer 1 (2026-09-05)

## Method

1. **Step 0 integrity**: computed sha256 of all 4 material files under
   `maintenance/f1-blind-r1-materials/` and compared against the
   `materials` pins in the rows header. All four matched
   (`materialsPinsOk: true`), so review proceeded.
2. **Full manual read**: read `f1-blind-r1-rows-20260905.json` (10 rows)
   and all four PRE/POST material files end-to-end with the Read tool,
   before writing any verdict code. This surfaced suspicious sibling
   pairs (rows making mutually exclusive claims about the same slot).
3. **Mechanical verification**: `verify.py` (run with `python -X utf8`)
   implements A1–A4, B1–B2 (B3' path included but not triggered — both
   prose rows have `oi: null`), B4 once per Law-B-touched `(entry, si)`,
   C1–C2, and E1–E3 across both entries. Deep equality on parsed JSON;
   B4 regex over POST `Explanation + "\n" + Note` (U+3400–U+9FFF,
   U+F900–U+FAFF maximal runs), anchored against POST
   `Occurrences`/`ClaimAnchors` kwics.
4. **Re-derivation**: every flag's contested bytes were re-derived with
   codepoint-level diffs (see `verify-report.txt`); manual reads
   independently confirmed each one.
5. Only the permitted inputs were read; nothing under `terms/`, the
   clone, other `maintenance/` files, or any dictionary tooling.

## Verdict summary

- Rows checked: 10 (R0000–R0009). Accepted: R0001, R0003, R0005, R0007,
  R0009. Flagged: R0000, R0002, R0004, R0006, R0008 (8 law violations).
- E1/E2/E3 pass for both entries (no retired RelPaths anywhere in POST;
  sense/occurrence counts stable PRE→POST; bare "Dehui" fully gone from
  POST MasterNames, ContextMasters, RelatedMasters).

## Flag table (diverging bytes)

| Row | Law | Materials say | Row claims |
|---|---|---|---|
| R0000 | A2 | POST `t_ab715aa474d5` si1/oi2 `MasterName: null` | `newMasterName: "Dongyang Dehui"` |
| R0002 | A2 | POST `t_351fa42d396b` si1/oi1 `ContextMasters[0].Roles: ["compiler"]` | `newContextMasters[0].Roles: ["utterer"]` (MasterName "Dongyang Dehui" itself matches) |
| R0004 | A2 | POST `t_ab715aa474d5` si1/oi2 `ActorAttribution.ActorLabel: "the monastic code's institutional voice"` | `newActorAttribution.ActorLabel: "the code compiler's editorial voice"` |
| R0004 | A4 | row's own `newAttributionNote` contains "the monastic code's institutional voice," only | requires ActorLabel "the code compiler's editorial voice" as casefolded substring of the note — absent |
| R0006 | A1 | PRE si1/oi1 `Kwic: 二時上粥飯。三時上茶湯。大眾諷經` | `carriedKwic: 二時上粥飯。三時猫茶湯。大眾諷經` — single-char substitution at index 8: materials `上` U+4E0A vs row `猫` U+732B |
| R0006 | A2 | POST si1/oi1 `Kwic` identical to PRE (`…三時上茶湯…`) | same wrong `carriedKwic` (carried must be unchanged PRE→POST) |
| R0008 | B1 | POST si1 `Explanation`: "…redacted by Dongyang Dehui, schedules…" — `after` occurs 0 times (PRE contains `before` exactly once, that half passes) | `after: "redacted by Dongyang Dehui (非粥非飯),"` |
| R0008 | B2 | PRE-with-replacement would read "Dehui (非粥非飯)," at char 165; POST reads "Dehui, sched" — byte-divergent | same `after` |

Codepoint evidence for R0006 (divergence at char 8):
materials `三(U+4E09) 時(U+6642) 上(U+4E0A) 茶(U+8336)` vs
row `三(U+4E09) 時(U+6642) 猫(U+732B) 茶(U+8336)`.

Codepoint evidence for R0008 (divergence at char 165):
expected `D e h u i ( 非(U+975E) 粥(U+7CA5) 非(U+975E) 飯(U+98EF) ) ,`
vs POST `D e h u i ,   s c h e d u`.

## Notes

- **Sibling contradictions**: R0000/R0001 target the same slot with
  identical `newAttributionNote`/`ActorAttribution` but different
  `newMasterName` ("Dongyang Dehui" vs null); the POST bytes are null,
  so R0001 is right and R0000 wrong. Likewise R0002/R0003/R0006 target
  the same slot; POST Roles are `["compiler"]`, matching R0003 (and
  R0006, which fails elsewhere on the kwic). R0008/R0009 both rewrite
  the same `before` fragment; POST matches R0009's plain rename.
- **B4**: evaluated once for `(t_351fa42d396b, si=1)` (the only
  Law-B-touched sense): 6 maximal CJK runs in POST `Explanation`+`Note`
  (二時上粥飯, 三時上茶湯, 除二時粥飯是雜用心處, 粥飯主人 ×2, 二時粥飯)
  — all anchored by occurrence kwics. No B4 flags. Had the POST
  contained R0008's 非粥非飯, that run would ALSO have been unanchored
  (no kwic contains it) — corroboration, not a separate flag.
- **Unverifiable from inputs**: `rowSha` on each row. No canonical row
  serialization is specified; four plausible canonicalizations
  (compact/sorted/indent-1/default, all with `rowSha` stripped) matched
  none of the sampled rows. No law references `rowSha`, so no flags were
  raised on it.
- `ClaimAnchors` is `[]` (t_ab715aa474d5) or absent (t_351fa42d396b);
  E1/B4 treated it as empty accordingly.

## Files

- `verify.py` — mechanical law checker (this review's only tool)
- `verify-report.txt` — full run log with codepoint diffs
- `verdicts.json` — deliverable (schema-exact)
