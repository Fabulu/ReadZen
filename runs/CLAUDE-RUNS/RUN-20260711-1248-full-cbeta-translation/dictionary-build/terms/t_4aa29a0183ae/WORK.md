# WORK — 斬猫

- Allowlist concordance: 156 hits / 53 files. Orthographic variant of 斬貓 (278 / 119), not a different meaning.
- Family cross-check: 斬猫, 南泉斬猫, 斬貓, 南泉斬貓, and 兩堂爭貓 all name the same recorded case at different spans; separate headwords preserve searchable orthography and morphology.
- Deployment harvest: case title/full narration; question about the case; later verdict; later verse; Dahui's explicit rejection of two common labels; explicit killing-precept question.
- Definition formulas: no `X者`-type lexical definition found. The case narration itself fixes the referent.
- #0f.8: one thing only—the named cat-cutting case/action. Questions, labels, verses, and comments are different deployments, not different referents.
- Precept research: an exact passage in X81n1568 asks, “Killing living beings is a major precept; why did Nanquan cut the cat and Guizong cut the snake?” The reply tells the questioner to repent. This establishes an attested passage-level relation, but does not state Nanquan's intention.
- Omission decision: variant-only duplicate witnesses were not padded into the entry; each retained occurrence anchors a different fact used by the prose.
- All five KWICs verified exact with zc.py; all paths are allowlisted and lb anchors synchronized.

## 2026-07-13 full remediation
- Rebuilt to 7 total / 6 exact witnesses across 6 exact sources; the complete event using expanded cat forms is family evidence, not duplicate depth.
- Preserved the hard killing-precept question, Miyun's repentance answer, and Dahui's rejection of two inherited rationales. Added Hu Anguo's public verse and Liaoan's hall deployment.
- Retested 斬猫 and 斬貓 as orthographic forms of one case, not separate events. All KWICs/bounds and both audits pass.

## 2026-07-14 semantic hard-pass ledger

- feedback-inference-verdict: PASS — `Nanquan's cat-cutting case` and the opening now identify the named event directly and prevent the bare imperative-like inference “cut the cat.”
- feedback-observations: The full Wansong transmission records the two halls, Nanquan's demand for an answer, the cutting, Zhaozhou's sandal, and Nanquan's rescue comment. Miyun Yuanwu faces the explicit killing-precept question; Jueyin answers a question about the case's import; Dahui Zonggao rejects two inherited rationales; Moan Xingdao, Hu Anguo, and Liaoan Yu reuse it in verse and hall address.
- feedback-falsification-searches: Rechecked 斬猫 156/53, 斬貓 278/119, 南泉斬猫 128/46, 南泉斬貓 217/108, 兩堂爭貓 30/29, 爭猫 31/29, 殺生是大戒 3/3, and 歸宗斬蛇 49/35.
- feedback-counterexamples: The two cat characters and expanded Nanquan/cat spans name one event, not different senses. Later explanations, questions, verses, and precept objections are incompatible responses to that event and cannot be promoted into a settled rationale for Nanquan.
- feedback-scope: One named public case and action, with searchable orthographic and expanded-form family members.
- lookup-probes: `Nanquan's cat-cutting case`, `Nanquan cat case`, `two halls fight over a cat`, `Zhaozhou sandal cat case`, `cat-killing precept question`, `Nanquan cuts the cat in two`.
- opening-interpretation-verdict: PASS — the entry tells the reader that this is Nanquan's named case and immediately narrates the event rather than leaving a literal verb-object fragment.
- definition-and-sense-verdict: KEEP one sense. Orthographic forms, title, verse, question, and precedent all refer to the same cat-cutting event.
- sense-target-distinguishability: PASS — one named-case sense; no grammar-only or paraphrase split exists.
- family-verdict: Both cat graphs, Nanquan expansions, two-halls dispute, Zhaozhou sandal, Guizong snake, killing precept, case titles, and inherited rationale families were cross-checked without collapsing separate entries.
- provenance-verdict: All seven stored KWICs remain exact, including six exact-headword witnesses plus the complete family narration, and every note names source and accountable speaker.
- propagation-verdict: Replaced the bare action target with a named-case target, added five retrieval probes, and preserved the precept carve-out and Dahui's explicit rejection as non-negotiable future evidence.
- final-gate: `semantic-r002-owner1-zhanmao-gate.json` hardPass=true; 7/7 stored KWICs verified and zero exact or attribution failures; entry SHA-256 `5c148b8560e62e4fca44a824028f99fbbd12c6fe9fff588f8e5ec147113bf164`.

## 2026-07-14 reviewer3 exact-turn repair

- Reapplied the actor ladder to the three question-form witnesses. The exact `斬猫` token is spoken by the unnamed monk questioning Miyun Yuanwu, the unnamed visitor questioning Jueyin, and the unnamed Chan visitor questioning Hu Anguo—not by the named respondents.
- Set each questioner to `reviewed-unnamed` only after recording all six checked rungs; retained Miyun Yuanwu, Jueyin, and Hu Anguo solely as context masters with respondent roles.
- Re-gate: `semantic-r002-owner1-zhanmao-gate.json` hardPass=true; 7/7 exact KWICs and zero attribution failures; repaired entry SHA-256 `42ab086f28ceeaa8382e258aa0066a5ff68803170014a825f72c41ccca504591`.
- p1-20260901: publish-backlog repairs per SPEC_P1_20260901.md + SPEC_P1_20260901_v2.md §8 (note x7, utterer x2, utterer-deferred-nonroster x2, rewindow-recut x1, t3b2-keep x1)
- a1-20260903: attribution repairs per SPEC_A1_20260902.md + AMENDMENTS 1-3 (muc-context-row x2)
