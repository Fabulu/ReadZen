# FINDINGS — blind review, lane F1 round r1, reviewer 2 (2026-09-05)

Inputs read (nothing else): `maintenance/f1-blind-r1-rows-20260905.json`,
`maintenance/f1-blind-r1-materials/pre|post/{t_ab715aa474d5,t_351fa42d396b}.json`.

## Method

1. **Step 0 integrity** — sha256 recomputed over the raw bytes of all 4 materials
   files; all four equal the `materials` pins in the rows header
   (`materialsPinsOk: true`):
   - `pre/t_ab715aa474d5.json` = `38b82ff0…bdd84a`
   - `post/t_ab715aa474d5.json` = `39e33fd4…06ebe`
   - `pre/t_351fa42d396b.json` = `81fdac52…9ab5a`
   - `post/t_351fa42d396b.json` = `9e261eb0…ada2d`
2. **Mechanical verification** — `verify.py` (this directory, run with
   `python -X utf8`) implements A1–A4, B1/B2 (+ B3' slot semantics, unused this
   round: no row has non-null `oi`), B4, C1–C2, E1–E3; `==` on JSON values is
   deep equality of parsed values; it also prints a full recursive PRE→POST
   diff of both entries and a first-divergence/codepoint trace for every
   flagged string.
3. **Eyeball pass** — the rows file and all 4 materials were read in full with
   the Read tool; every flag below was re-derived by hand against the bytes
   before being written.
4. Every row not flagged counts as accepted (`rowsChecked: 10`).

The lane's actual edit (from the PRE→POST deep diff, identical in shape for
both entries): sense-1 slot de-attributed (`MasterName` → `null`,
`ContextMasters` Dehui/utterer → Dongyang Dehui/compiler, new
`ActorAttribution` with label "the monastic code's institutional voice",
rewritten `AttributionNote`), `RelatedMasters` Dehui → Dongyang Dehui, and for
t_351fa42d396b an `Explanation` rewrite "redacted by Dehui," → "redacted by
Dongyang Dehui,". No other path differs PRE→POST (sense counts and occurrence
counts identical; second sense of t_351fa42d396b byte-identical).

## Flags (8 violations on 5 rows)

| RowId | Law | Materials bytes (frozen) | Row claims | Diverging bytes |
|---|---|---|---|---|
| R0000 | A2 | POST `t_ab715aa474d5` slot(1,2).MasterName = `null` | `newMasterName: "Dongyang Dehui"` | `null` vs `"Dongyang Dehui"` |
| R0002 | A2 | POST `t_351fa42d396b` slot(1,1).ContextMasters = `[{"MasterName": "Dongyang Dehui", "Roles": ["compiler"]}]` | `newContextMasters` = same master, `Roles: ["utterer"]` | `"compiler"` vs `"utterer"` |
| R0004 | A2 | POST `t_ab715aa474d5` slot(1,2).ActorAttribution.ActorLabel = `"the monastic code's institutional voice"` | `newActorAttribution.ActorLabel` = `"the code compiler's editorial voice"` | whole label differs (ActorLabel is the only differing ActorAttribution key) |
| R0004 | A4 | POST slot AttributionNote contains `"the monastic code's institutional voice"` | label `"the code compiler's editorial voice"` must appear in `newAttributionNote` and in the POST note | label appears in **neither** (the row's own `newAttributionNote` also carries the institutional-voice wording, contradicting its own ActorLabel) |
| R0006 | A1 | PRE `t_351fa42d396b` slot(1,1).Kwic = `二時上粥飯。三時上茶湯。大眾諷經` | `carriedKwic` = `二時上粥飯。三時猫茶湯。大眾諷經` | char index 8: materials `上` U+4E0A vs row `猫` U+732B |
| R0006 | A2 | POST slot Kwic = same `…三時上茶湯…` (unchanged, as "carried" requires) | same corrupted `carriedKwic` | char index 8: `上` U+4E0A vs `猫` U+732B |
| R0008 | B1 | POST `t_351fa42d396b` sense(1).Explanation contains `redacted by Dongyang Dehui,` and contains `redacted by Dongyang Dehui (非粥非飯),` **0** times | `after` = `redacted by Dongyang Dehui (非粥非飯),` must occur exactly once | insertion ` (非粥非飯)` present in row only; `非粥非飯` occurs nowhere in POST |
| R0008 | B2 | POST Explanation = PRE with `redacted by Dehui,` → `redacted by Dongyang Dehui,` (one replacement) | replacement with the `(非粥非飯)`-bearing `after` | first divergence at char 165: expected `…Dehui (非粥非…` vs actual `…Dehui, sch…` |

## Accepted rows (5)

- **R0001** (occ-attribution, t_ab715aa474d5 slot(1,2)) — every A-law passes;
  this row's claims match the frozen POST bytes exactly (MasterName null,
  compiler role, institutional-voice label present in both note fields,
  carried RelPath / FromLb 1144b03 / ToLb 1144b04 / Kwic unchanged,
  postOccurrenceRels order and count 3 correct, occurrences 1 and 3 deep-equal
  PRE→POST).
- **R0003** (occ-attribution, t_351fa42d396b slot(1,1)) — same shape, all
  A-laws pass; carried kwic is the correct `上`-form.
- **R0005** (relatedmasters-rename, t_ab715aa474d5) — C1: PRE `[Baizhang
  Huaihai, Dehui, Hongzhi Zhengjue]` → POST `[Baizhang Huaihai, Dongyang
  Dehui, Hongzhi Zhengjue]`, `postRelatedMasters` equals POST; C2: `new` =
  `Dongyang Dehui` = the roster name quoted in `laneLaw.t48n2025Class`.
- **R0007** (relatedmasters-rename, t_351fa42d396b) — C1/C2 pass on the
  4-element list (`Dehui` once, order preserved, POST matched).
- **R0009** (explanation-rewrite, t_351fa42d396b) — B1: `before` once in PRE,
  `after` once in POST; B2: single replacement reproduces the POST Explanation
  exactly (the only PRE→POST diff at that path is this replacement).

## Law E report (both entries, no flags)

- **E1**: neither retired RelPath (`T/T48/T48n2023.xml`, `X/X63/X63n1245.xml`)
  appears in any POST Occurrences; ClaimAnchors are `[]`/absent in all
  materials entries.
- **E2**: sense counts (1; 2) and every sense's occurrence count (3; 3 and 6)
  identical PRE→POST; the recursive diff confirms no list-length change
  anywhere.
- **E3**: no POST occurrence MasterName, no ContextMasters[].MasterName, and
  no RelatedMasters element equals bare `"Dehui"`; the roster form
  `Dongyang Dehui` is what appears.

## Law B4 report

Evaluated once per (entry, si) touched by a Law-B row — only
(t_351fa42d396b, si=1). Six maximal CJK runs in POST Explanation + Note
(二時上粥飯, 三時上茶湯, 除二時粥飯是雜用心處, 粥飯主人 ×2, 二時粥飯 — five
distinct); each is anchored by a POST Occurrences kwic (substring containment
either way). No B4 flags.

## Caveats

- `rowSha` is not part of any stated law and no canonicalization is specified;
  six common canonical JSON forms matched 0/10 rows, so it is treated as
  unverifiable from the inputs and was not used to flag.
- A3's "covered slots (match on oi)" set was collected per entry over
  occ-attribution rows; all such rows are si=1 so sense-scoping is moot.
- Field equality is deep equality of parsed JSON values (per the task's `==`);
  raw-byte identity is separately pinned by the Step 0 hashes.
- Multiple rows describe the same physical slot edit (R0000/R0001/R0004;
  R0002/R0003/R0006; R0008/R0009); the frozen POST bytes adjudicate which
  claims match, which is exactly what the A/B laws test.
