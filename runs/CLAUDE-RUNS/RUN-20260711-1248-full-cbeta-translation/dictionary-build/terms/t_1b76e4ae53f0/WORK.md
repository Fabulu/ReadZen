# 金彈子 — full corpus, modifier, object, and public-feedback audit

## Identity, inherited lead, and governing rules

- Source term: `金彈子`; deterministic ID: `t_1b76e4ae53f0`.
- Re-read `DICTIONARY_ENTRY_GUIDE.md` §5, including the public-reader gates 11–17, the indexed-discovery rule, item-8 different-things test, item-10 attribution ladder, and the new opening-interpretation rule.
- Inherited research lead: the completed `金` entry (`t_3c1e31a193cd`) had already found the Nanquan Puyuan gold-pellet/silver-pellet exchange, Zhengtang Bian's price verse, the exact gold/silver ball-family inventory, and the provisional conclusion that the exchange locally ranks Nanquan's requested Chan explanation over the lecturer's offered scripture explanation. This work was retained as a lead, then re-tested against the full 金彈子 concordance rather than copied as authority.
- Inherited-lead verdict: **keep with narrower headword scope.** The case-level ranking survives because both the exchange turn structure and Zhengtang Bian's explicit preciousness/price line support it. It does not turn 金彈子 into “enlightenment,” and the furnace, hunting, funeral, gold/clay, and thrown-projectile witnesses require the entry to describe the object and its wider deployments.

## Three-engine discovery and exact counts

- indexed-discovery-path: `indexed_kwic.py` used the desktop v4 `search.inverted.bin` postings (stamp `269db8235c174e058e36b01e0af365ac`, 3,601,348 terms, 4,990 documents, path checksum verified) followed by exact `search.text.bin` confirmation. For 金彈子 it found 251 all-corpus candidate documents, 150 allowlisted candidate documents at the shared-gram stage, and 70 sidecar hits in 52 allowlisted files. It was also run for 黃金彈子, 銀彈子, 泥彈子, 金毬, 金球, 紅爐, 彈子, the definition formulas, furnace/casting forms, exchange forms, and projectile verbs.
- website-index-path: the website's actual `ZenLinkPage/lib/bigram-search.js` v3 sharded engine was run through `web_index_kwic.mjs --exact`. Manifest: 5,014 documents with unigrams. Its exact text-shard confirmation found 金彈子 **83 / 61**, 銀彈子 **8 / 8**, 泥彈子 **58 / 36**, 金毬 **17 / 17**, 金球 **1 / 1**, 黃金彈子 **2 / 2**, 紅爐 **1,031 / 270**, and 彈子 **259 / 108**. These remain discovery figures because website shards are not the XML evidence authority.
- XML authority: apparatus-excluding `zc.count` gives 金彈子 **83 hits / 61 allowlisted texts**, 黃金彈子 **2 / 2**, 銀彈子 **8 / 8**, 泥彈子 **56 / 34**, 金毬 **17 / 17**, 金球 **1 / 1**, 紅爐 **1,030 / 270**, and 彈子 **256 / 106**. The repaired inventory has 14 saved KWICs: nine exact-headword anchors, two marked `family` witnesses for 黃金彈子, and three marked `contrast` witnesses for the headword-free price verse, the 黃金為彈子 material scene, and distinct 金毬.
- The engine disagreements are preserved rather than averaged: the desktop text sidecar misses some XML-confirmed 金彈子 witnesses, while website shards retain three extra mud-pellet hits and one extra red-furnace hit. Only `zc` counts and anchors control the entry.

## Gold ball, silver ball, and pellet correction

- The user's golden/silver-ball requirement was treated as a hard research gate, not a translation preference.
- Exact ball spellings: 金毬 **17 / 17** and 金球 **1 / 1**. Website exact confirmation gives zero for 銀毬, 銀球, 黃金毬, 黃金球, 白銀毬, and 白銀球; the prior apparatus-clean `zc` inventory likewise found zero. The corpus's paired gold/silver object is therefore not a 毬/球 pair.
- Exact pellet spellings: 金彈子 **83 / 61** and 銀彈子 **8 / 8**. Five texts transmit the same Nanquan exchange: four use barter (博) and one uses exchange (換). They are duplicate transmissions of one encounter, not five independent rankings.
- 金毬 is kept as a distinct lexical object. Its witnesses predominantly roll, reflect, or play with a ball; Dahong Shousui's rushing-water witness is stored as `family` and excluded from headword depth. 金彈子 is instead cast round, traded, thrown, fired at birds, and driven through targets. English aliases include “gold ball” for retrieval, but the preferred target “gold pellet” preserves the projectile constraint.

## Definition-formula and deployment inventory

- Definition formulas: `金彈子者`, `所謂金彈子`, `謂之金彈子`, `名為金彈子`, `喚作金彈子`, `何謂金彈子`, and `如何是金彈子` each returned zero exact website-shard confirmations. No direct “X means Y” formula was found.
- Material/forming frames: red-furnace gold pellet **28 / 27** by `zc`; cast into a gold pellet **10 / 10**; one firing cast into a gold pellet **6 / 6**; the longer yellow-gold pellet **2 / 2**; one exact overnight-forging form. Cishou Huaishen's roundness and no-tongs-or-hammer predicates are unique and retained.
- Projectile frames: newly out of the red furnace and smashing the iron face occurs in a broad repeated family; exact `zc` probes find 19 punctuated smash continuations plus two unpunctuated. Throwing, releasing from a high peak, knocking down a white phoenix, shooting an oriole, scattering birds, and breaking a primordial trace were separately inspected.
- Exchange frames: four barter versions and one exchange version of Nanquan's gold/silver case; one Foyan Qingyuan gold-for-workers'-clay exchange; one Zixian Jue appraisal of Luopu trading Linji's gold pellet for Jiashan's clay pellet; a separate gold-for-dung-ball poem was inspected but excluded because the retained gold/clay witnesses already establish the exchange class and have clearer attribution.
- Appraisal/genre frames retained: early lamp encounter, later signed verse on that encounter, early public answer, case verse, later evening address, ordinary hunting allusion, two funeral services, an independent thrown-projectile verse, and old-case lineage commentary.
- Omitted duplicates: repeated transmissions of Nanquan, repeated red-furnace formulae, and later copies of Cishou Huaishen's verse were not allowed to inflate depth. Each retained occurrence contributes a distinct fact, period, genre, speaker, or correction.

## Sense adjudication

- One sense. The same small round projectile is cast, traded, pointed out, thrown, used as bird-shot, and rhetorically forged at funerals. Those are actions and deployments of one thing, not different referents.
- Literal hunting and figurative Chan launchings remain one ordinary-scene-plus-deployment sense: the projectile's roundness, cost, flight, target, and impact are precisely the constraints that make the later uses intelligible.
- 金毬/金球 are different written lexical objects and remain outside the sense. Gold, yellow gold, silver pellet, clay pellet, and red furnace are components or related contrasts, not senses of this headword.
- No master-specific sense was created. Nanquan, Fengxue, Foyan, Shiqi, Sanyi, Shending, and others make different local uses of the same portable pellet image.

opening-interpretation-verdict: the sole sense begins with the corpus-earned answer that this is a small round projectile cast from expensive gold, ordinarily throwable at a bird or target, which Chan speakers redeploy as an offered/refused exchange, a furnace-launched impact, and a contested object of value. That interpretation precedes names and quotation detail, is reconstructed from casting, roundness, bird-shot, trade, and impact predicates, and imports no outside doctrine or alleged intention.

## Modifier and display verdicts

- modifier-relation-verdict: `material-attested`. The material relation is direct here, unlike 金鎖: Shuangshan Yuan says the prince does not stint yellow gold **for making pellets**; Cishou Huaishen says one firing **casts** the gold pellet and calls it perfectly round; Sanyi Mingyu says one night's fire **forged** a yellow-gold pellet; the broad red-furnace family repeatedly launches it from a furnace.
- material-claim-verdict: **licensed for the pictured projectile.** “Gold pellet” may be displayed because the corpus supplies made-from-gold and casting/forging predicates, not merely graph composition. This does not assert that every narrated Chan event involved physical gold ammunition; it identifies the concrete object whose properties the records deploy.
- display-modifier-verdict: `a gold pellet` is the preferred target because material and projectile are both established. `a gold ball` is retained as an alternate and “golden ball” as a search alias for the user's natural lookup wording. “Golden sphere” is rejected as the display because it loses shooting and impact; “enlightenment pellet” is rejected because no formula supports it.
- symbolism-verdict: no universal gold=enlightenment code. The Nanquan exchange licenses a local value ranking, the Foyan/Shiqi and Linji/Jiashan clay exchanges carry their own named appraisals, and the furnace/funeral uses exploit forging and impact. None turns the headword into a doctrinal synonym.

## Item-11 inference ledgers

### A. Ordinary object and action

- observation: Cishou Huaishen says one firing casts it, it is perfectly round without tongs or hammer, it is released from a high peak, and it knocks down a white phoenix; Shuangshan Yuan spends yellow gold on pellets and shoots an oriole.
- minimal-inference: 金彈子 is a small round gold projectile or shot, not merely a shining sphere.
- ordinary-bridge: a pellet is round, throwable, and aimed at a target; casting gold into it and expending it on bird-shot makes material and cost load-bearing.
- falsification-searches: 金毬, 金球, silver-ball spellings, silver pellet, clay pellet, casting, forging, roundness, throwing, shooting, striking, birds, furnace, and non-projectile ball scenes.
- counterexamples: 金毬 and 金球 can roll or reflect without being projectiles; they are different compounds and do not erase the pellet's attested shooting predicates.
- scope: corpus-wide ordinary image underlying the headword.
- verdict: direct.

### B. Nanquan gold/silver exchange

- observation: the lecturer offers scripture exposition if Nanquan explains Chan; Nanquan refuses to barter a gold pellet for a silver pellet; Zhengtang Bian later says people know preciousness but not price.
- minimal-inference: inside this encounter, the requested Chan explanation is placed on the gold side of a refused unequal exchange and the offered scripture lecture on the silver side.
- ordinary-bridge: gold ordinarily commands a premium over silver, and barter syntax aligns the two offered performances with the two pellets; the later price verse confirms that valuation is active.
- falsification-searches: every gold/silver pellet transmission, the three non-paired silver-pellet contexts, 金毬/銀毬 and 金球/銀球, gold/silver material and color series, and later comments on Nanquan's case.
- counterexamples: other silver-pellet contexts are independent forged-object images; gold and silver elsewhere can appear in parallel rather than ranked.
- scope: Nanquan's public exchange and Zhengtang Bian's signed later comment only.
- verdict: licensed.

### C. Furnace projectile

- observation: Fengxue Yanzhao answers with a gold pellet newly out of a red furnace smashing an ācārya's iron face; Cishou casts and launches it; the family contains 28 red-furnace frames and at least 21 smash continuations.
- minimal-inference: the records deploy the pellet as a newly forged, forceful verbal projectile capable of breaching a hardened respondent or monk.
- ordinary-bridge: a fired projectile travels and strikes; furnace and impact predicates make heat, formation, launch, and force explicit.
- falsification-searches: cast/forge/furnace predicates, every iron-face continuation, literal bird-shot, simple rolling-ball scenes, exchange-only frames, and funeral frames.
- counterexamples: not every occurrence strikes a face; exchange and funeral scenes use value or forging instead. Therefore “verbal projectile” is a deployment, not the lexical definition.
- scope: Fengxue formula and its multi-source descendants.
- verdict: licensed.

### D. Gold/clay exchange family

- observation: Foyan Qingyuan offers gold pellets for workers' clay pellets; Yingan Tanhua says recognizing either shows where the other lands; Shiqi Tongyun points right and left, then sends even the fully knowing person to carry bricks; Zixian Jue laughs at Luopu's Linji-gold/Jiashan-clay trade.
- minimal-inference: named masters reuse material contrast to rank or test specific exchanges, then reopen easy conclusions about simply possessing or recognizing the gold side.
- ordinary-bridge: gold and clay differ in ordinary value, while exchange and landing remain actions of the same pellet form.
- falsification-searches: all gold/clay and gold/dung contexts, “where it lands” forms, pointing gestures, lineage labels, and contexts that reverse or level the contrast.
- counterexamples: Shiqi refuses to let correct identification finish the encounter; Yingan makes recognition reciprocal. A fixed gold=correct/clay=wrong code is too broad.
- scope: Foyan/Yingan/Shiqi and Luopu/Linji/Jiashan case families.
- verdict: licensed locally; universal symbolism rejected.

### E. Funeral forging

- observation: Sanyi Mingyu says one night's fire forged the deceased into a yellow-gold pellet for display and bird-scattering; Shending Yikui calls the pellet refined a hundred times in the red furnace Ke'an Lizong's lifelong people-facing functioning.
- minimal-inference: funeral addresses reuse forging and projectile predicates to appraise named Chan teachers after death.
- ordinary-bridge: a furnace forms/refines a pellet; the funeral text itself names the deceased and explicitly equates the pellet with Ke'an's lifelong functioning in one witness.
- falsification-searches: funeral-service headings, governing names, fire/cremation context, ordinary casting verses, red-furnace public answers, and possible relic/body compounds.
- counterexamples: these are named funeral deployments, not proof that a corpse literally becomes ammunition or that every gold pellet names a master.
- scope: two attributed funeral services.
- verdict: direct as deployment; literal transformation rejected.

## Public-feedback ledger

- feedback-observations: exact predicates establish cast gold, round pellet form, bird-shot, barter against silver and clay pellets, furnace launch, iron-face impact, funeral forging, throwing, and target-breaking.
- feedback-inference-verdict: the smallest full conclusion is “a gold pellet”: an expensive round projectile that Chan speakers make exchangeable, forgeable, launchable, and publicly contestable. Nanquan's gold-over-silver valuation is real but case-scoped.
- feedback-falsification-searches: all three engines; exact headword concordance; direct definition formulas; gold/silver and gold/clay exchanges; 金毬/金球 and every silver-ball spelling; casting, forging, roundness, furnace, bird, throw, strike, landing, price, funeral, and nested forms.
- feedback-counterexamples: non-paired silver pellets defeat a universal silver code; rolling/reflecting 金毬 scenes are a different compound; Shiqi's brick-carrying correction and Yingan's reciprocal recognition block an easy gold=final-answer equation.
- feedback-scope: ordinary projectile image corpus-wide; furnace projectile in the repeated Fengxue family; comparative ranking local to named exchanges; funeral use local to named services.
- lookup-probes: gold pellet, golden pellet, gold ball, golden ball, gold shot.
- modifier-relation-verdict: `material-attested`, by yellow-gold-for-pellets plus cast/forge/red-furnace predicates.
- display-modifier-verdict: show “a gold pellet”; retain gold/golden ball as alternate or alias, never as a replacement that loses projectile behavior.
- material-claim-verdict: gold construction belongs to the pictured object and is directly supported; no claim is made that the recorded public exchanges used literal ammunition.
- symbolism-verdict: reject universal gold=enlightenment; retain explicit local price, exchange, forging, and force relations.
- verb-frame-verdict: one sense—cast, forge, trade, point to, throw, shoot, strike, and land all govern the same pellet object. 金毬 is excluded as a different compound rather than forced into a second sense.

## Attribution ladder

- Nanquan Puyuan resolves from his explicit lamp-record section; Zhengtang Bian from the inline signature 正堂辯; Fengxue Yanzhao and Shuangshan Yuan from explicit anthology headings; Cishou Huaishen from the inline 慈受深 attribution.
- Shiqi Tongyun, Sanyi Mingyu, Shending Yikui, and Zixian Jue resolve from their own record titles and governing sections. Deming resolves from the explicit volume-six byline `嗣法弟子德明答頌` in Daxiu Zhu's *Hundred Questions*; Daxiu is the collection master, not the verse author. Their notes name every raised earlier speaker used in the explanation.
- Dahong Shousui resolves from his explicit biography in the Continued Lamp Record. The distinct-headword contrast witness remains attributed even though it does not count toward depth.
- No occurrence is assigned to “a master,” “a monk,” or an unnamed text.

## Family-propagation ledger

- **金 — keep/cross-link:** its existing wealth sense already anchors Nanquan and Zhengtang; its metal sense supports material casting controls and already warns against universal enlightenment symbolism. Add/retain 金彈子 in RelatedTerms; no definition rewrite needed.
- **銀 — keep/cross-link:** the existing silver entry treats Nanquan's ranking as local and independent silver-pellet images separately. Retain that boundary.
- **銀彈子 — build/audit separately:** eight exact witnesses include the Nanquan duplicates and three independent forged-object contexts. Do not derive its whole definition from being the lower side of Nanquan's trade.
- **泥彈子 — build/audit separately:** fifty-six apparatus-clean matches include gold/clay exchanges, independent rebukes, hand-formed mud pellets, and flower-sermon criticism. Do not define it merely as the opposite of gold.
- **金毬 / 金球 — keep separate:** rolling, reflection, swift-water, and golden-sphere scenes are a ball family, not projectile depth for 金彈子.
- **紅爐 — keep/retest relation:** the 1,030-hit furnace entry/family must distinguish literal forge, testing/refining image, and the repeated newly-emerged-pellet formula without making furnace a universal awakening symbol.
- No dependent entry was edited in this task; the ledger records deliberate propagation work for the coordinator.

## Final omission and quote audit

- Every Chinese string used as evidence in the article is contained in a stored, exact, verified KWIC under the sole sense.
- Nine standalone cards contain the exact SourceTerm and count toward depth. The two exact `黃金彈子` cards are explicitly `EvidenceRole: family`. Zhengtang Bian's price verse, Shuangshan Yuan's `黃金為彈子` material scene, and Dahong Shousui's distinct `金毬` card are explicitly `EvidenceRole: contrast`. All five support cards are excluded from depth.
- Nine standalone anchors across seven source texts exceed the four-anchor frequency floor because they preserve distinct lexicographically useful facts or exact speakers; two family and three contrast controls remain excluded from depth.

## 2026-07-13 second exact-turn and evidence-role repair

- Split the compact Nanquan/Zhengtang row. Nanquan Puyuan now owns only the transmitted headword exchange; Zhengtang Bian owns only his signed price verse, which lacks `金彈子` and is marked `contrast` rather than counted as lexical depth.
- Split the Shiqi evening address into three exact-turn rows: Foyan Qingyuan's quoted gold-for-clay offer, Yingan Tanhua's quoted reciprocal landing comment, and Shiqi Tongyun's own headword question and brick-carrying correction.
- Reclassified `黃金為彈子` as thematic/material `contrast` support and distinct-headword `金毬` as lexical `contrast` support. The two actual `黃金彈子` witnesses remain valid `family` evidence.
- The entry does not use a frequency statement as a definition, does not open with a calque or quotation pile, and does not infer doctrine or speaker intention.
- A final full-case attribution audit corrected the signed `百問` verse from collection master Daxiu Zhu to its explicit author, his successor Deming.
- p1-20260901: publish-backlog repairs per SPEC_P1_20260901.md + SPEC_P1_20260901_v2.md §8 (note x14, utterer x8, structured-link x4, utterer-skip x3, utterer-deferred-nonroster x3, rewindow-replace x3, dangling x3, span-declare x1, sourcetexts-fill x1, t3b2-keep x1, t3b2-apply x1)
- a1-20260903: attribution repairs per SPEC_A1_20260902.md + AMENDMENTS 1-3 (muc-context-row x3)
