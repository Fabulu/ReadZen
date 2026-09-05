# 金 — research and QA ledger

## Deterministic identity and scope

- Source term: `金`
- Deterministic ID: `t_3c1e31a193cd` (first twelve hex digits of SHA-256 for the UTF-8 headword).
- This is a standalone keystone entry. No wave merge was run.
- Rules applied: `DICTIONARY_ENTRY_GUIDE.md` §5 in full, including the flyswatter test, scaled depth, item-8 referential splitting, family-evidence accounting, speaker attribution, quote anchoring, inference boundaries, and search aliases; `FIRST_PUBLIC_FEEDBACK_FIX.md` in full.

## Concordance and indexed discovery

- Final apparatus-excluding `zc.count("金")`: **37,149 hits / 452 allowlisted files**.
- Required fast discovery: `indexed_kwic.py 金 銀` used the single-character `search.text` fallback. Index-v4 integrity stamp `269db8235c174e058e36b01e0af365ac`, 3,601,348 indexed terms, 4,990 documents, path checksum verified. The discovery sidecar reported **37,439 / 452** for 金 and **2,972 / 373** for 銀. These are discovery counts, not saved evidence counts, because the sidecar can retain apparatus text.
- Required multi-character discovery: every researched family probe used `indexed_kwic.py` inverted postings followed by exact `search.text` confirmation. The saved probes included `金屎法`, `金者喻於法性`, `金屑雖貴落眼成翳`, `金佛不度爐`, `真金火裏`, `金銀等性`, `黃金為世界`, `白銀為壁落`, `金木水火土`, `肺名金`, `一金作種種器`, `竊金者誅`, `攫金者不見人`, `其色如金`, `黃如金`, `金從礦裏出`, and `如銷金者`.
- The index exposed why the XML gate remains mandatory: `認鑛為金` had an allowlisted XML witness under `zc` but zero sidecar confirmations for that exact graph form. It was not used. Every saved KWIC below passed `zc.verify` against primary XML.
- The website's actual JavaScript v3 sharded engine was also run through `web_index_kwic.mjs --exact` for the same broad set. Its manifest has unigrams and 5,014 documents; it reproduced the sidecar discovery count for 金 (**37,439 / 452**) in 15.9 ms and for 銀 (**2,972 / 373**) in 8.1 ms. The exact-shard results were used only to locate candidates because the website shards can retain apparatus; `zc.verify` remains the saving gate.

### Golden-ball / silver-ball correction inventory

The missed ball family was reopened with both discovery engines and the XML concordance. Exact apparatus-clean counts are:

- `金毬`: **17 / 17**; `金球`: **1 / 1**.
- `銀毬`, `銀球`, `黃金毬`, `黃金球`, `白銀毬`, `白銀球`: **0** exact main-text occurrences.
- `金彈子`: **83 / 61**; `銀彈子`: **8 / 8**.
- The paired gold/silver formula is therefore not 金毬/銀毬 but **金彈子/銀彈子**, literally a gold pellet or ball and a silver pellet or ball.

Every paired gold-pellet/silver-pellet passage was inventoried. Five allowlisted texts transmit the same Nanquan Puyuan encounter: `T/T51/T51n2076.xml`, `X/X80/X80n1565.xml`, `X/X80/X80n1568.xml`, and `X/X81/X81n1571.xml` use `不可將金彈子博銀彈子`; `C/C078/C078n1720.xml` uses the variant `不可將金彈子換銀彈子` and appends Zhengtang Bian's verse. The four lamp versions are duplicate transmissions, not four independent uses. The compendium's later comment is unique and load-bearing: `世人知貴不知價`, “people know what is precious but do not know the price.”

The remaining three 銀彈子 occurrences are not gold/silver pairs: `J/J26/J26nB187.xml` has an iron palm knead a silver pellet; `J/J27/J27nB197.xml` and `X/X72/X72n1435.xml` transmit the same silver-pellet line. They cannot be used to force a stable silver meaning.

The seventeen 金毬 witnesses were also disjointly inventoried: nine texts repeat Dahong Shousui's `急水打金毬`; two transmit the old-monkey/eight-flower-brick image; two put a turtle in fire rolling a golden ball; and four independent contexts picture a ball in purple haze, a moon or stars reflected on water, a wind-rolled ball on water, or a red sun hung as a golden ball. The sole 金球 witness likewise makes the red sun a rolling golden sphere. These are complete family images. They show feats, reflections, or rounded brilliance; they do not establish a standalone lexical equation.

Later gold-pellet comparisons were checked as controls. The family exchanges gold pellets for clay pellets, contrasts one with a dung ball, casts one in a furnace, and launches one as a projectile. This variation requires adjudicating the compounds in their own entries; it supplies no standalone sense or search route for the bare headword.

## Full-concordance sense and contamination audit

The raw character count was not treated as 37,149 standalone lexical uses. The concordance was screened by high-frequency continuation and context families, then by targeted predicates and explicit formulas. Major nested families include `金剛` (vajra/diamond), `黃金` (yellow gold), `金陵` (Jinling), `金粟`, `金山`, `金毛`, `金色`, `金鱗`, `金烏`, `真金`, `金輪`, `金針`, and `金身`. These do not establish a standalone sense merely by containing the graph. Proper names, place names, titles, personal epithets, scripture titles, and longer lexical compounds were excluded from standalone depth.

The item-8 retest after independent falsification produced two things:

1. **gold** — the metal, including its ordinary use as wealth or payment and its use as a standard of value or yellow brilliance. Refining, stealing, demanding, pricing, and comparing something to gold are different deployments of the same referent, not different things.
2. **Metal, the Five-Phase agent** — explicitly western/white and listed with Wood, Water, Fire, and Earth.

sense-target-distinguishability: `gold` names the ordinary material and its ordinary extensions; `Metal, the Five-Phase agent` names a member of the correlative Five-Phase series. Capitalization alone is not the distinction: the second sense is anchored by explicit phase membership and west/white correlations.

No separate sense was created for refined gold, pure gold, tested gold, a noun/verb alternation, or different positive and negative appraisals: those are readings or deployments of the same metal. No proper-name sense was created because sampled name contexts named other lexical objects rather than a corpus-wide standalone referent needed by this entry.

opening-interpretation-verdict: the ordinary sense begins by naming gold and explicitly folding wealth, value, and yellow-brilliance comparisons into ordinary extensions of that material. It names only corpus-attested local analogies and immediately rejects a universal enlightenment code. The second opening names Five-Phase Metal and its west/white correlations before describing its teaching-seat deployment. Both openings answer referent plus Zen deployment before quotation detail and remain within item-11 inference boundaries.

independent-falsification-resolution: **revise accepted** — the former metal, wealth, and appearance senses were different predicates/readings of gold rather than different things. They are merged. Five-Phase Metal remains separate because the corpus explicitly makes it a member of a different correlative system. No ball, sphere, or pellet phrase supplies an alias, target, or characterization for bare 金.

## The enlightenment hypothesis and controls

- Direct formula probes found no corpus-wide lexical equation of bare 金 with enlightenment or awakening.
- Positive evidence was retained rather than suppressed. The Shenhui witness explicitly reports `金者喻於法性`; Yongjue explicitly compares ore-removal with clarifying mind; Juelang's formula tests true gold in fire. These license local analogical explanation.
- The evidence does **not** license the lexical target “enlightenment.” The same corpus preserves Zhantang Wenzhun's `金屎法` reversal, Wuzu Fayan's precious gold dust that clouds the eye, Zhaozhou Congshen's gold buddha that does not survive the furnace, and gold/silver world imagery. These controls show unstable appraisal and multiple observable properties.
- Silver was researched as a control, not forced into the gold entry. `黃金為世界，白銀為壁落` makes both precious materials architectural; `金銀等性` coordinates the materials in analogy; `銀盌盛雪` belongs to its own longer family. Nothing supports a global gold=enlightenment / silver=other binary.
- The gold-pellet/silver-pellet case supports a narrower inference inside the **pellet family**. The lecturer proposes scripture exposition in exchange for Nanquan explaining Chan; Nanquan refuses to barter a gold pellet for a silver pellet, and Zhengtang Bian explicitly confirms a preciousness/price issue. That case belongs to the 金彈子/銀彈子 entries. It neither defines nor search-routes bare 金.
- Conclusion: **inference from corpus evidence is allowed; importing a universal symbolic code is not**. The entry states exactly where named speakers bend gold and stops at their stated comparisons.

## Public-feedback inference ledger

feedback-inference-verdict: The corpus licenses an inference from gold's expressly stated refining, testing, value, and color properties to local uses by named speakers. It does not license defining bare 金 as enlightenment.

feedback-observations: Gold is refined out of ore, made into vessels, tested in fire, stolen or demanded as wealth, and used as a yellow appearance standard. Separately, the graph names the western-white Metal phase. Ball and pellet compounds were checked as family controls only; they do not establish a referent or lookup route for bare 金. Named Chan passages also reverse gold's value or make precious gold obstructive.

feedback-falsification-searches: Tested direct enlightenment-equation patterns, the explicit `金者喻於法性` self-gloss, refining and fire formulas, the gold-and-shit formula, gold-dust warning, gold-buddha furnace control, yellow-gold/white-silver pairings, every 毬/球/彈子 gold-and-silver spelling requested above, gold/clay and gold/dung exchanges, and Five-Phase lists. Multi-character probes used both the inverted index and the website engine before XML verification.

feedback-counterexamples: `金屎法／不會如金／會得如屎`, `金屑雖貴落眼成翳`, and `金佛不度爐` defeat an invariant positive or enlightenment value; `黃金為世界，白銀為壁落` shows gold and silver used together architecturally. No ball-family witness is used to characterize the bare headword.

feedback-scope: The conclusions apply to the ordinary-gold referent and the distinct Five-Phase agent. Anchored family comparisons are retained only to delimit compound families. They do not reinterpret or route bare 金 through proper names, place names, titles, vajra compounds, balls, spheres, pellets, or other longer compounds.

lookup-probes: `gold`, `gold metal`, `pure gold`, `gold money`, `gold payment`, `gold color`, `golden color`, `yellow like gold`, `Five Phase Metal`, `Five Elements metal`, and `wuxing metal` are covered by PreferredTarget, AlternateTargets, or SearchAliases. `golden ball`, `gold ball`, `gold pellet`, `silver ball`, and `silver pellet` are deliberately rejected as lookup routes for bare 金; they belong to compound-family entries.

modifier-relation-verdict: `resolved` — the ordinary sense covers the material and its attested wealth/value/color comparisons without multiplying referents. Five-Phase Metal is independently established. Longer compounds retain their own lexical adjudication and do not characterize bare 金.

display-modifier-verdict: `resolved` — display `gold` for the ordinary material and its ordinary extensions, and `Metal, the Five-Phase agent` for the distinct correlative phase. No compound-family image appears as a bare-word display target.

material-claim-verdict: The entry says a compared flower is not thereby established as made of metal; that negative boundary is anchored by the explicit simile `菜花滿地黃如金`. Positive material claims are anchored by ore-refining and vessel-making witnesses.

## Depth ledger

- Saved occurrences: **21** across **19 distinct source files** after the exact-turn repair.
- Exact/compositional standalone witnesses that buy depth under the automated family-role gate: **10**.
- Family or contrast witnesses that do not buy standalone depth: **10**, including all retained 毬/球/彈子 evidence and Zhengtang Bian's single no-headword value verse.
- Per sense after the merge: ordinary gold 8 exact + 11 family/contrast; Five-Phase Metal 2 exact. The automated gate excludes both `family` and `contrast` roles from the depth count and reports the required ten exact witnesses. Every 金毬/金球/金彈子/銀彈子 witness is in the excluded family group.
- The entry therefore clears the high-frequency floor without using nested compounds to inflate depth. Unique high-value controls were retained beyond the floor because they change the definition audit.

## Attribution ladder

- Own-record titles resolve Shenhui, Yongjue Yuanxian, Juelang Daosheng, Tian'an Sheng, Xutang Zhiyu, Ruibai Mingxue, Wuyi Yuanlai, and Baishan Kai.
- Explicit inline attribution resolves Huiyuan of Lushan in `宗鏡錄`, Zhantang Wenzhun in Dahui Zonggao's reported exchange, Zhaozhou Congshen in `列祖提綱錄`, and Nanquan Puyuan with Huangbo Xiyun in the old-case collection.
- The explicit Rahulata section of `五燈會元` resolves Rahulata's own gold-in-the-well question; the explicit Tiantai Deshao section of `五燈嚴統` resolves Deshao's gold-with-gold statement.
- The explicit lamp biography resolves the swift-water golden ball to Dahong Shousui; Feiyin Tongrong resolves from his own record title. The linked-pearl XML's inline signature `正堂辯` resolves the later value verse to Zhengtang Bian rather than to Nanquan or the anonymous compiler.
- Every occurrence has a non-null `MasterName`; every attribution note names both the text and responsible speaker or examiner. Source-attested names absent from the current roster are identified as such rather than orphaned.

## 2026-07-13 exact-turn supersession

- Removed the row in which an unnamed monk said `金從礦裏出` but the occurrence was assigned to examiner Meixi Fudu.
- Removed anthology narration in which soldiers demanded gold from Miaogao; the biography subject was not the narrator of the headword line.
- Replaced them with two actor-pure, named statements: Rahulata on gold in and out of a well, and Tiantai Deshao on the nature of the realm of phenomena fitting “like gold with gold.”
- Split the combined Nanquan/Zhengtang locus. Nanquan's exact gold-pellet turn remains separately anchored; Zhengtang Bian's verse is now an actor-pure no-headword `contrast` row at the verified bounds `C078n1720:0674a24-b02`.
- Gold/enlightenment retest: the corpus strongly supports local purity, intrinsic-nature, equality, and true-side comparisons. Because the passages themselves say “is compared to,” “likewise,” and “like,” the evidence supports a scoped inference but not a second lexical sense making every bare occurrence mean enlightenment.
- Final targeted gates: `zc.verify` **21/21**; attribution **21/21 named and noted, zero hard failures**; depth **10 primary exact witnesses against floor 10**; public-feedback **PASS**.

## Quote and retrieval audit

- Every Chinese passage quoted or paraphrased in the explanations has a stored occurrence under the same sense. The Nanquan exchange, Zhengtang Bian's later price verse, Dahong Shousui's golden-ball feat, and Feiyin Tongrong's golden sun-sphere remain separately anchored and explicitly labelled family evidence rather than bare-word characterization.

## 2026-07-13 final complete-case correction

- Corrected `金屑雖貴落眼成翳` from Fayan Wenyi to **Wuzu Fayan** after widening the `法演禪師語錄` context to the Baiyun Haihui record.
- Removed the second identical Zhengtang Bian row at `C078n1720:0674a24-b02`; one actor-pure no-headword contrast witness remains.
- Restored Nanquan's exact `黃金` / `白銀` row to `EvidenceRole=family` under the nested-compound gate.
- Final role inventory: **20 total = 10 primary, 8 family, 2 contrast**; sense 1 has 18 rows (8 primary, 8 family, 2 contrast), and the Five-Phase Metal sense has 2 primary rows.
- Every saved occurrence passed `PYTHONIOENCODING=utf-8` `zc.verify`; stored line bounds are verifier outputs.
- Search aliases cover metal/refining, wealth/payment, color/appearance, and Five-Phase terminology. No ball, sphere, pellet, or silver-family phrase remains in `SearchAliases` for bare 金.
- Definition re-test after enrichment: the two retained senses name different things. Ordinary metal/commodity/value/comparison readings are merged; Five-Phase Metal remains separate; neither sense equates bare gold with enlightenment.
- p1-20260901: publish-backlog repairs per SPEC_P1_20260901.md + SPEC_P1_20260901_v2.md §8 (note x20, utterer x15, named-quoter x4, utterer-deferred-nonroster x3, utterer-skip x2, structured-link x2, rewindow-replace x1, t3b2-keep x1)
- a1-20260903: attribution repairs per SPEC_A1_20260902.md + AMENDMENTS 1-3 (muc-context-row x3)
