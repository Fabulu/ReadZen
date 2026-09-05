# WORK — 小參 (t_c945c2cc0e79)

## Concordance (Zen allowlist only)
- 小參 total ≈ 6,979 hits across 335 allowlist texts. Strongly multi-source.
- Top texts: X82n1571 五燈全書 (599), J37nB394 (206), X64n1260 列祖提綱錄 (203), J38nB406 (141), J34nB311 (98), J25nB174 (96), J33nB280 (86), J28nB202 (85), Dahui T47n1998A (…), Yuanwu T47n1997 (…), 敕修百丈清規 T48n2025 (31, definitional).

## Sense analysis
One corpus-wide sense (SenseKey=null): **the informal / lesser convocation**, contrasted with 上堂 (the great, formal convocation, "ascending the hall").
- Definitional anchor from the monastic code 敕修百丈清規 (T48n2025): 小參初無定所 (no fixed place); held in 寢堂/法堂 by size of assembly; announced by 小參牌; given at the 昏鐘 (evening bell) → hence 當晚小參 / 晚小參. The abbot 登座 「與五參上堂同」 — same procedure as 上堂, only informal in place/time.
- Genre-heading use in yulu: paralleled with 上堂 in fascicle listings (Yuanwu 卷第八　上堂八　小參一); heads live evening talks (Dahui 當晚小參…).

No master-specific bending; one sense.

## Speaker attribution — how confirmed
- **T48n2025** = 敕修百丈清規 (title No. 2025) — monastic rule, no single speaker → MasterName null. Two definitional occurrences (小參初無定所… ; 而謂之小參…).
- **T47n1998A** = 大慧普覺禪師語錄 (title No. 1998A). 當晚小參 heads Dahui Zonggao's own evening address (大慧宗杲 in master-dates.json).
- **T47n1997** = 圓悟佛果禪師語錄. Fascicle table-of-contents line enumerating 小參 beside 上堂; the record is Yuanwu Keqin's (圜悟克勤).

## KWIC verification
All 4 KWICs confirmed exact contiguous tag-stripped substrings (scripted PASS; layout newlines + tags removed). The Yuanwu TOC KWIC uses full-width ideographic spaces (U+3000) present verbatim in the file. FromLb = nearest preceding canon-edition `<lb>`.

## Multi-source verdict
**multi-source.** Definition (Baizhang code) + live genre use in Dahui and Yuanwu + 335 allowlist texts. The 上堂-vs-小參 contrast (formal vs informal/evening) is corpus-wide.

## GATE 2 (Claude adversarial verify+repair)
- KWIC exactness: all 4 KWICs EXACT contiguous tag-stripped substrings (Yuanwu TOC line keeps its U+3000 ideographic spaces verbatim). Zero ellipsis/alteration.
- Allowlist: T48n2025, T47n1998A, T47n1997, X82n1571, J37nB394 all IN zen-corpus.json (allowlist explicitly includes monastic rules — 敕修百丈清規 is legitimate). No contamination.
- FromLb: all confirmed nearest preceding <lb n> (T-canon ed="T").
- Attribution: occ[0]/occ[1] null (敕修百丈清規 monastic code, no speaker) OK; occ[2] Dahui (山僧…當晚小參, his yulu) OK; occ[3] REPAIRED MasterName 圜悟克勤 → null (fascicle TOC line 卷第八 上堂八 小參一 is structural apparatus, not an utterance; record still Yuanwu's via RelatedMasters).
- Multi-source: Baizhang code + Dahui yulu + Yuanwu yulu (+~335 texts). Confirmed.
- RelatedTerms (上堂/晚參/示眾/普說): deliberate semantic sibling-genre cross-refs. Kept.
- VERDICT: verified. 1 attribution repair (occ[3] → null).

## D003-A depth enrichment (2026-07-13)

- Frequency floor re-opened as a minimum: 4 → 9 anchors, now spanning 8 occurrence-bearing source texts.
- New deployment classes: the explicit small/great public question (小參/大參); New Year's Eve; release from the restraint; a memorial address before a spirit tablet; and a head-shaving/precept ordination convocation.
- Definition re-test: all new witnesses still name the same informal convocation event. The event can be a heading, be requested, or occur in phrases translated “hold/give a small convocation”; those are grammatical and editorial packagings, not different referents under item 8. No title/person referent was found.
- Family re-test: 上堂/大參 remains the formal contrast; 晚參 is a neighboring label. Occasion prefixes (歲夜/解制/對靈/授戒) classify deployments of 小參 rather than new senses.
- #0g: the word bends institutionally: the ostensibly “small” address is the teaching-seat event used at calendar turns, retreat release, ordination, and for the dead, and it is itself put into public question (“small = gruel; great = rice”).
- Omission audit: no distinct event, title, named work, or master-specific referent remains evidenced but unrepresented.

## 2026-07-13 risk remediation

### Discovery provenance and opening correction

The risk-third3 workbook selected this entry because eight of nine original rows had unresolved actors, seven notes lacked the exact source title, and 25 useful Chinese strings floated only in prose. The former opening “informal convocation” was too weak and partly misleading: the code prescribes a placard, notification, drum, assembled ranks, and the presiding abbot mounting the seat. The public target is now **small convocation**, with **special public address** and **evening address** as supported English alternatives. “Small” distinguishes this event within the address system; it does not make the event casual.

### Exact actor/source ledger

1. `T48n2025 1119c10–14`: impersonal institutional rule; no historical address-giver. Grammar prescribes venue, notification, placard, bell, drum, ranks, and abbot duties.
2. `T48n2025 1119c05–09`: impersonal institutional definition; conditional occasions culminate in the passive naming formula.
3. `T47n1998A 0812a28`: Dahui Zonggao gives that evening's address.
4. `T47n1997 0714a27`: impersonal table-of-contents count; Yuanwu Keqin is record subject, not speaker of the structural line.
5. `J37nB390 0539c07–08`: Beijing Chulin Shangrui narrates and asks the small/great-convocation questions; the unnamed deputy bursar gives the gruel/rice answers.
6. `X64n1260 0098c14`: Beichan Xian gives the New Year's Eve address.
7. `J25nB174 0707b14`: Juelang Daosheng gives the release-from-restraint address.
8. `J39nB465 0820c05–06`: Ziyong Ru gives the memorial address before Madam Zhao's spirit tablet.
9. `J34nB311 0621c14–15`: Juelang Daosheng gives the requested ordination address; Elder Juewu requests it and the disciple is beneficiary.
10. `T48n2025 1130c02–06`: impersonal running-title support; no speech predicate.
11. `X64n1260 0001a17–18`: Jiexian is the explicitly named author of the first preface and its four-category taxonomy.
12. `X64n1260 0002b21–22`: Xingyue is the explicitly named compiler-author of the editorial principles distinguishing evening and small convocations.
13. `T48n2023 1066b28–29`: Shiwu Qinggong gives the opening-of-restraint small convocation.
14. `X64n1260 0098c18–19`: Zhenjing Kewen gives the last-night-of-year small convocation.
15. `J37nB390 0539c07`: an unnamed novice reports the hung placard to Beijing Chulin Shangrui. All six rungs leave the novice unnamed; Chulin is scheduled address-giver and record owner.

Final XOR state: ten named actors, four reviewed impersonal structures, one six-rung reviewed-unnamed novice, and zero bare nulls. Five named actors remain explicit roster-reconciliation cases rather than being erased.

### Quote closure

The two expanded code witnesses now anchor the procedure and occasion strings rather than merely paraphrasing them:

- venue and procedure: `小參初無定所`, `寢堂`, `法堂`, `至日午後`, `侍者覆住持云令客頭行者報眾`, `掛小參牌`, `小參牌`, `當晚不鳴放參鐘`, `昏鐘鳴時行者覆住持`, `鳴鼓一通`, `眾集兩序歸位`, `住持登座提綱`, and `登座`;
- occasions and naming: `如住持入院`, `或官員檀越入山`, `或受人特請`, `或謂亡者開示`, `或四節臘則移於昏鐘鳴`, `而謂之小參`, `可以敘世禮`, `曰家教者是也`, `家教`, `然亦不鳴放參鐘`, and `謂猶有參也`.

Targeted witnesses anchor `已掛小參牌了也`, `結制小參`, `除夜`, `晚參`, and the four-category `上堂 / 小參 / 示眾 / 普說` taxonomy. The inherited source spelling `敕修百丈清規` returned zero; it was corrected to the attested `勅修百丈清規` (23 occurrences in the code) and anchored with a supporting running-title occurrence. Final attribution audit: **40/40 Chinese prose strings anchored**. No useful quotation was deleted.

### Event/heading grammar and family adjudication

Sense verdict: retain **one corpus-wide sense**. A scheduled event, a request to hold it, a discourse heading, a contents category, and the implied verb “give a small convocation” all point to the same public-address institution. They are grammar/editorial packaging, not different things. No named work, person, physical object, or master-specific referent was found.

The family relation is evidence-bounded:

- `上堂` is the neighboring regular teaching-hall address; the small convocation has no fixed room and the code schedules it specially, often at the evening bell.
- `示眾` and `普說` are independently listed address categories beside it by Jiexian; the entry does not pretend the taxonomy supplies fuller definitions than it does.
- `晚參` is separately listed by Xingyue beside four-season small convocation, so “evening address” cannot silently replace every `小參`.
- Occasion prefixes—New Year's Eve, opening/release of restraint, memorial, ordination—classify instances of the same event.

Allowlist count remains 7,023/337. Final depth is 15 stored occurrences: 12 exact event/category witnesses, two marked family taxonomies, and one marked source-title support witness. The frequency-scaled exact-evidence floor of ten is met.

### Public-feedback inference ledger

feedback-inference-verdict: `licensed-institutional-inference` — notification, placard, drum, assembled ranks, and seat ascent license “scheduled public address”; the sources do not license a doctrine about what every address accomplishes.

feedback-observations: `direct-multi-source` — the code defines venue, occasions, timing, and sequence; live records show evening, calendar, restraint, memorial, and ordination events; taxonomies keep neighboring formats distinct.

feedback-falsification-searches: `passed` — event, heading, request, title/person/object, master-specific, and longer-family uses were retested after enrichment; the wrong source-title graph was tested and corrected rather than normalized silently.

feedback-counterexamples: `retained` — Chulin's after-gruel event prevents reducing the term to clock time alone; the separate `晚參` category prevents treating every evening address as a small convocation; the impersonal code and contents rows prevent false title-owner speech.

feedback-scope: `public-address-event` — the entry describes this named institution and its attested occasions, not every assembly, every evening talk, or every use of `參`.

lookup-probes: `pass` — small convocation, special convocation, special public address, evening convocation, evening address, lesser convocation, and minor address all reach the entry.

opening-interpretation-verdict: `pass` — the opening names the institution and its observable Chan machinery before quotation, and is falsifiable against the no-fixed-place, placard, drum, ranks, and seat evidence.

### Verification

All 15 stored KWICs pass exact allowlisted `zc.verify` with matching line bounds. All attribution notes name the exact source and actor/impersonal branch. No merge, commit, or push was performed.

- t3b1-20260831: rule-22 pipeline-vocabulary rewrites per SPEC_T3B_20260831.md (T3b-1 deterministic families B1-B7; B1-2 x1, B2-meet-the-floor x1)
- r1b-20260903: R1b retired-source removals per SPEC_R1b_20260903.md + AMENDMENTS 1-2 (occ-remove-retired x1)
