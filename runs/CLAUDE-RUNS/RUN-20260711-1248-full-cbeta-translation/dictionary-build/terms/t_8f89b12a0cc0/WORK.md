# WORK — Gruel (粥)

## Scope and counts

- Zen allowlist only, using `zc.py` with UTF-8 output.
- Gruel (粥): 2,824 hits / 341 files.
- Eat gruel (喫粥): 748 / 182; gruel and rice (粥飯): 668 / 223; gruel-and-rice monk (粥飯僧): 59 / 42; “have you eaten your gruel?” (喫粥了也未): 101 / 67.

## Depth inventory

- Definition formulas searched: `如何是粥` 0; `所謂粥` 0; `謂之粥` 0; `名為粥` 0; `喚作粥` 0. `粥者` has 18 hits / 12 files, but inspection found grammatical strings such as “the person serving gruel” and the named phrase “Jiang's thin gruel,” not a definition of the headword.
- Institutional deployment included: the Chan monastic code's bowl-opening and gruel-eating rule; the kitchen distinction between cooking gruel and steaming rice; Zhaozhou's “two daily gruel-and-rice meals.”
- Public answers included: Changping answers “eating gruel and rice” to the question about talk surpassing buddhas and patriarchs; Guizong answers with “when gruel is thin, sit down later” to the question about the student's own self.
- Named cases included: Zhaozhou's “have you eaten your gruel?” / “go wash your bowl”; Ganzhi providing gruel and Nanquan breaking the pot.
- Ordinary/basic-lot deployment included: Baichi's “eating gruel and eating rice is your own basic lot”; Fayan's complete daily sequence.
- Period/genre spread: an early abridged transmission record, lamp records, Yunmen's own record, a monastic code, a later collected outline, and a late master's record. Duplicate recensions of the Zhaozhou case were excluded despite its 101 hits in 67 files.

## Family cross-check and sense decision

- Cross-checked `喫粥`, `粥飯`, `粥飯僧`, `喫粥了也未`, `鉢盂`, `洗鉢盂去`, and existing `本分事`.
- The existing `本分事` entry's “eating gruel and eating rice is your own basic lot” quotation verifies exactly and agrees with this entry.
- Gruel in the breakfast rule, kitchen, everyday sequence, Zhaozhou case, public answers, and Ganzhi's offering is the same concrete food. These are distinct deployments/readings, not different things, so item 8 requires one sense.
- `粥飯僧` refers to a person and is therefore a separate compound entry; its human referent must not be smuggled into the standalone `粥` sense.
- `鉢盂` is the eating bowl in Zhaozhou's instruction. `衣鉢` is robe-and-bowl as succession token; the entry does not conflate them.
- Final decision: keep PreferredTarget “gruel,” with “rice gruel” and “porridge” as alternatives. The #0g deviation is the corpus's use of an ordinary monastic meal inside public answers and cases, not a claim that the food symbolizes something.

## Exact verification

All nine curated KWICs passed `zc.verify`; all cited files are allowlisted. Verified anchors: X63n1245 0531c05–06; T47n1988 0554b16–18; J28nB202 0078c06; X80n1565 0342a04–06, 0332b13–14, 0183c04–05; T51n2077 0523b19–21; X64n1260 0044a22–23; B14n0082 0211a03–05.

## Omission audit

- Included every distinct deployment class used in the prose and anchored each substantive claim.
- Excluded duplicate recensions and later repetitions of Zhaozhou's bowl case; they establish breadth but add no new lexical deployment.
- Excluded `粥氣` / `粥飯氣` from the standalone sense because those compounds require their own adjudication and cannot be used to redefine the concrete headword without a family entry.
- No unresolved second sense was found.

## semantic-r001 public-feedback remediation (2026-07-14)

- feedback-inference-verdict: KEEP one concrete food sense. Breakfast rule, cooking, serving, eating, thinness, gruel-and-rice schedule, public answers, Zhaozhou case, Ganzhi offering, and basic-lot statement all denote the same cooked-grain meal.
- feedback-observations: The monastic code governs opening the bowl and eating gruel; a kitchen exchange contrasts cooking it with steaming rice; Changping and Guizong use it in direct public answers; Zhaozhou asks whether the newcomer ate it before ordering bowl washing; Ganzhi provides it before Nanquan breaks the pot; Baichi and Zhaozhou place it in the ordinary daily allotment.
- feedback-falsification-searches: Rechecked the bare word, eat gruel, gruel and rice, gruel-and-rice monk, completed-meal question, eating bowl, wash the bowl, robe-and-bowl, cooking versus steaming, thin gruel, two daily meals, basic lot, and gruel-smell compounds. Definition formulas returned no lexical self-definition.
- feedback-counterexamples: The gruel-and-rice monk compound refers to a person and cannot create a human sense for the bare food word. The eating bowl is distinct from the robe-and-bowl succession token. Public-case reuse does not turn the food into an abstract symbol.
- feedback-scope: One corpus-wide concrete meal sense spanning institutional rules, kitchens, ordinary schedules, answers, and cases.
- lookup-probes: Reader probes covered “rice porridge,” “congee,” “monastery breakfast,” “morning gruel,” and “breakfast porridge.” These are now approved SearchAliases.
- opening-interpretation-verdict: KEEP the concrete food first and surface the Chan bend in the same opening: an ordinary morning meal is repeatedly placed in public answers, case exchanges, and bowl-washing instruction.
- definition-formula-audit: All standard definition formulas returned zero; the referent is established by cook, serve, eat, thin, bowl, meal-schedule, tea, broth, and rice contrasts. These observable predicates keep the definition descriptive.
- nested-family-audit: Eat gruel, gruel and rice, gruel-and-rice monk, completed-meal question, eating bowl, wash-the-bowl, robe-and-bowl, basic lot, and gruel-smell were rechecked. Person, bowl-token, and compound referents remain separate.
- modifier-and-provenance-audit: No feedback modifier is at issue. All nine exact anchors were re-read and retain exact source-and-speaker attribution.
- semantic-propagation: Preserve the concrete food referent across eat-gruel and gruel-and-rice entries; keep the monk epithet, completed-meal formula, eating bowl, and robe-and-bowl distinct. Search should bridge gruel, porridge, congee, breakfast, and morning-meal language.
- final-cohort-gate: `run_cohort_gate.py` hardPass=true; exact KWIC 9/9, attribution hard failures 0, public-feedback flags 0, depth/sense hard failures 0, review flags 0, and forbidden-English matches 0. Report: `maintenance/semantic-cohorts/semantic-r001-owner1-gruel-gate.json`.
- p1-20260901: publish-backlog repairs per SPEC_P1_20260901.md + SPEC_P1_20260901_v2.md §8 (note x8, utterer x4, utterer-deferred-nonroster x4, t3b2-noop x2, drop-row x1, note-skip x1, utterer-skip x1, structured-link x1, t3b2-keep x1)
- a1-20260903: attribution repairs per SPEC_A1_20260902.md + AMENDMENTS 1-3 (muc-context-row x4)
