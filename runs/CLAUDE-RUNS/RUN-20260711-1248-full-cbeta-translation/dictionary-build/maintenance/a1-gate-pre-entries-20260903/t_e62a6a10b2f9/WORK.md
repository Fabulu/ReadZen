# 金毬 — independent-headword research and QA ledger

## Decision and inherited provenance

- Governing rules: `DICTIONARY_ENTRY_GUIDE.md` §5 items 0–18 and `REMEDIATION_MASTER.md` active public-feedback calibration lane.
- Inherited lead: `REQUESTED_TERMS.md`, the completed standalone `金` study, and the paired pellet studies warned not to conflate `金毬` with `金彈子`, and identified rushing-water play, rolling, sun/moon, and lamp-ball contexts as the families to test.
- inherited-feedback-lead-decision: **KEEP AS AN INDEPENDENT HEADWORD.** The graph form has 17 exact occurrences and a coherent verb system—play, roll, float, and hang—that differs from the cast, throw, strike, and barter system of `金彈子`. Split the celestial/reflected orb from the acted-on rolling ball because the corpus names a different referent there.

## Required website, desktop, and XML inventory

- Website v3 sharded engine, `web_index_kwic.mjs --exact`: `金毬` **17 hits / 17 allowlisted files**, zero failed exact-shard checks. `急水打金毬` 9/9; `八花磚上輥金毬` 1/1; `火裏輥金毬` 2/2 after exact confirmation.
- Desktop v4 inverted/KWIC index, `indexed_kwic.py`: `金毬` **17 exact sidecar hits / 17 allowlisted files** from 20 all-corpus posting candidates. Integrity stamp `269db8235c174e058e36b01e0af365ac`, 3,601,348 terms, 4,990 documents, verified path checksum.
- Authoritative apparatus-excluding XML: `zc.count("金毬")` = **17 hits / 17 allowlisted files**.
- Exact XML predicate counts: `打金毬` 9/9; `輥金毬` 5/5; `泛金毬` 1/1; `挂金毬` 1/1; `金毬翻水面` 1/1; `金毬輥出` 1/1.
- Every saved occurrence passed `zc.verify`; discovery counts were not treated as final evidence.

## Complete 17/17 occurrence inventory

1. Rushing-water family, nine files: `T51n2077`, `X64n1260`, `X79n1559`, `X80n1565`, `X81n1568`, `X81n1571`, `X85n1590`, and `X85n1593` transmit Dahong Shousui's same address; `J34nB301` is Nanyue Jiqi Hongchu's later interview reuse. The eight Dahong witnesses are transmission duplicates, not eight independent deployments.
2. Old-monkey/eight-flower-brick family, two files: `C078n1720` and Cishou Huaishen's own `X73n1451`; the latter is damaged at the brick graph but confirms author and context. The cleaner explicitly signed compendium witness is stored.
3. Fire-turtle family, two independent speakers: Duanqiao Miaolun in `X70n1394` and Zhuoyuan Miaodao in `X83n1574` both pair a turtle rolling the ball in fire with a blue rabbit hanging a mirror in water. Duanqiao's own record is stored; Zhuoyuan is inventoried as independent corroboration.
4. Single-witness deployments: Lanshi Ling's ball rolling out purple haze (`J28nB218`); Jiguang Huo's pool of stars and moon floating a golden orb (`J36nB367`); Zhean Jingfan's wind rolling a ball across water (`J36nB369`); and Buyan Le's red sun hanging a golden orb (`J38nB419`). All four are stored because each supplies a unique predicate, referent, or genre.
- Omission decision: eight stored anchors preserve every distinct referent and deployment. The remaining nine witnesses add transmission or exact-form breadth without a new lexicographic fact and are excluded as duplicate padding.

## Definition formulas and countersearch

- Zero XML hits for `金毬者`, `所謂金毬`, `謂之金毬`, `名為金毬`, `喚作金毬`, `何謂金毬`, `如何是金毬`, and `金毬是`.
- `黃金毬` and `金毬兒` are zero, so the headword is not an elided longer yellow-gold form or diminutive in this corpus.
- `金球` is 1/1 and explicitly describes a red sun rolling a golden sphere. It is a related modern-form graph, not silently merged into the 17 witnesses.
- `金彈子` is 83/61 and has materially different casting, round-projectile, launching, striking, and exchange predicates. It is not a spelling variant.
- `銀毬` is zero; no gold/silver ball hierarchy can be manufactured from a nonexistent paired form.

## Three-layer image and modifier audit

### Sense 1 — acted-on ball image

1. graph composition: gold + ball; the modifier relation remains unresolved in this family.
2. ordinary scene: a rounded ball can be played, rolled, or move across a surface; rushing water, brick, fire, purple haze, and water provide the stated settings.
3. Chan deployment: masters claim the rushing-water feat, compare it inside an interview, and place the moving ball in old-case, monkey, turtle, and portrait verses. Dahong's same address overtly places remaining obstruction beyond the feat.

### Sense 2 — celestial or reflected orb

1. graph composition: the same golden-ball wording.
2. ordinary scene: the round red sun is orb-like; stars and moon reflected in a pool produce bright rounded light on water.
3. Chan deployment: Buyan Le answers a New Year hall question with the red sun hanging as the orb; Jiguang Huo uses the pool image in a travel verse.

- modifier-relation-verdict: sense 1 **whole quoted image / material, color, value, and conventional-name relations unresolved**; sense 2 **appearance/color**. No moving-ball witness melts, casts, assays, compares color, or otherwise resolves what `金` contributes.
- display-modifier-verdict: **PASS after revision.** Sense 1 preserves the source modifier in “gold-ball image” without turning it into a material or appearance claim; sense 2 explicitly names an orb of sun or reflected light.
- material-claim-verdict: **not established and not asserted.** The strongest physical predicates in sense 1 concern motion and placement, not composition; its color is also unresolved.
- symbolism-verdict: **reject.** Neither sense equates gold or the ball with enlightenment. Dahong's address directly undercuts treating his feat as terminal, and no paired silver ball exists.

## Sense split and verb-frame adjudication

- sense-target-distinguishability: **KEEP TWO.** “The gold-ball image in play and rolling scenes” names an acted-on ball while leaving its modifier unresolved; “golden orb of the sun or reflected light” names a celestial/reflected referent whose appearance is explicit. A reader can distinguish them from the targets alone.
- `打/輥` ordinarily act on or move a ball; `挂` with the explicitly named red sun and `泛` with stars, moon, and pool assign the shape to celestial/reflected light. Those incompatible referents trigger and satisfy items 8 and 14.
- Rolling versus playing is not split within sense 1: these are different actions on the same image. Sun versus pool reflection stays one sense because both passages use the ball wording for a visible celestial-light orb rather than an acted-on ball.
- final-family-definition-retest: all eight stored anchors fit one and only one sense. No occurrence is used to support incompatible definitions.

## Item-11 inference ledger A — moving ball

- observation: Dahong Shousui claims `急水打金毬` and then names cords, a gold lock, and one further obstruction; Nanyue Jiqi Hongchu repeats the feat as an interview comparison. Cishou Huaishen, Lanshi Ling, Duanqiao Miaolun, and Zhean Jingfan use `輥`, `輥出`, or water-surface motion.
- minimal-inference: one sense is a gold-ball image treated as moving, played, or rolled in claims, interviews, and verses; Dahong's own speech refuses to let the feat stand as a terminal achievement.
- ordinary-bridge: balls can be played and rolled; the conjunction “even so” followed by remaining bonds and obstruction explicitly narrows the preceding feat.
- falsification-searches: all motion verbs, material predicates, gold-ball variants, sun/moon/light controls, `金彈子`, `金球`, `銀毬`, direct awakening equations, and every Dahong parallel.
- counterexamples: explicit sun and pool-reflection witnesses name a different referent and are split; no casting/material witness appears; `金彈子` supplies different projectile grammar.
- scope: corpus-wide for the moving image; local to each named feat, interview, or verse for appraisal.
- verdict: **licensed**.

## Item-11 inference ledger B — celestial/reflected orb

- observation: Buyan Le explicitly gives `一輪紅日挂金毬`; Jiguang Huo places `星月`, a pool, and `泛金毬` in one scene.
- minimal-inference: a second sense is the golden orb of the sun or celestial light reflected on water.
- ordinary-bridge: a round sun is orb-like, and stars/moon seen in a pool are reflections; “golden” describes the visible sphere without proving metal composition.
- falsification-searches: red-sun, moon, stars, pool, water, reflection, hanging, floating, material, casting, and conventional-name controls; the sole `金球` witness was checked independently.
- counterexamples: the played/rolled ball family does not name sun or reflected light and remains sense 1; Zhean's water-surface ball lacks an explicit light source and is conservatively retained there.
- scope: multi-source appearance use, limited to explicit celestial/reflection controls.
- verdict: **licensed**.

## Opening interpretation and public-feedback ledgers

- opening-interpretation-verdict: **PASS after revision — sense 1.** The opening preserves an acted-on gold-ball image, explicitly leaves material, color, value, and conventional wording unresolved, and gives Dahong's same-speech limitation before quotations.
- opening-interpretation-verdict: **PASS — sense 2.** The opening identifies sun/reflected light and its use in a hall answer and travel verse before naming speakers.
- feedback-inference-verdict: **keep the headword and two referential senses; reject material and enlightenment overreach.**
- feedback-observations: 17/17 exact witnesses; distinct motion predicates; explicit red sun; stars/moon in a pool; Dahong's further-obstruction reversal; no silver-ball mate.
- feedback-falsification-searches: definition formulas, every occurrence, verb clusters, material and appearance controls, `黃金毬`, `金毬兒`, `金球`, `金彈子`, `銀毬`, awakening equations, and duplicate-transmission audit.
- feedback-counterexamples: celestial/reflected occurrences defeat a single acted-on-ball sense; projectile grammar defeats conflation with `金彈子`; Dahong's own continuation defeats a uniformly triumphant or enlightenment reading.
- feedback-scope: moving-ball image across named Chan deployments; celestial/reflected orb only where the referent is explicit; no universal symbolic code.

## Family propagation and retrieval

- `金`: **KEEP** its revised ordinary gold/commodity/comparison sense plus Five-Phase Metal. `金毬` remains a local family and does not create bare-gold enlightenment or a separate appearance sense.
- `金彈子`: **KEEP DISTINCT.** Projectile/casting/barter grammar differs from play/roll/float/hang grammar. Cross-link only.
- `金球`: **KEEP AS RELATED, NOT MERGED.** Its one red-sun occurrence supports the celestial-image comparison but remains a separately spelled headword.
- `銀` and `銀彈子`: **KEEP.** No `銀毬` exists, so this entry changes neither their senses nor the local Nanquan pellet ranking.
- lookup-probes sense 1: `gold ball`, `golden ball`, `rolling gold ball`, `play ball in rushing water`, `fire turtle golden ball`.
- lookup-probes sense 2: `golden orb`, `gold sun ball`, `golden sun sphere`, `moon reflection golden ball`, `golden ball on water`.
- lookup-probes: the two sense-specific lists above are the approved combined retrieval set; they remain separated in `SearchAliases` so a celestial query does not rewrite the primary moving-ball gloss.
- Search aliases are retrieval metadata; “enlightenment” is excluded because it is not a lexical equivalent.

## Depth and attribution

- Frequency floor for 17 hits is at most three exact anchors. This entry stores **8 exact occurrences across 8 files and 8 responsible masters**, not to pad the count but to preserve every distinct motion, referent, limitation, and genre found.
- Sense 1 has six occurrences across hall address, interview, old-case verse, and portrait verse. Sense 2 has two independent master/source occurrences, sufficient for multi-source validation.
- Attribution ladder: explicit biography resolves Dahong Shousui; own-record titles resolve Nanyue Jiqi Hongchu, Lanshi Ling, Duanqiao Miaolun, Jiguang Huo, Zhean Jingfan, and Buyan Le; the inline verse label `慈受深` resolves Cishou Huaishen in the compendium.
- Every occurrence has a source-and-speaker note. Every Chinese phrase used in prose is contained in a stored occurrence.

## Final QA record

- JSON parse: **PASS** — two distinguishable senses and eight exact-headword occurrences.
- `zc.verify`: **PASS 8/8** with exact primary-edition `FromLb`/`ToLb` matches for every stored KWIC.
- `audit_attribution.py`: **PASS** — eight of eight occurrences named, eight source-and-speaker notes, all 11 Chinese strings in prose anchored, zero hard failures. Six source-attested names remain under the shared deferred non-roster counter while roster expansion is external.
- `audit_depth_sense.py --ids t_e62a6a10b2f9`: **PASS** — one audited, zero hard failures, zero review flags, multi-sense entry, no batch cluster.
- `audit_public_feedback.py` final targeted run over standalone silver, silver pellet, and this entry: **PASS 3/3**, zero flags.
- JSON whitespace/diff check: **PASS**.
- No `STATUS`, merge, manifest registration, or edits outside this term directory are authorized or performed.
- p1-20260901: publish-backlog repairs per SPEC_P1_20260901.md + SPEC_P1_20260901_v2.md §8 (note x8, utterer x4, utterer-deferred-nonroster x3, utterer-rename x1, t3b2-apply x1)
