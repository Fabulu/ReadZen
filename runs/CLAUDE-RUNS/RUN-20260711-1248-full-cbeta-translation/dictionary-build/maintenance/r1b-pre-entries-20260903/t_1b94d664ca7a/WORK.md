# batch10-deferred-20260829 worksheet — t_1b94d664ca7a (施主)

Citation-window repair (stitched-Kwic rewindow): 2 op(s); blind-reviewed (r1, r2, r3).

deferred-queue citation-window repair: rows whose stored Kwic was not contiguous corpus text (stitched at batch-2 time, when the cited files were absent from the local corpus) are rewindowed to the verbatim contiguous corpus window around the nearest headword occurrence (punctuation-tolerant anchor), window length matching the row's own sibling convention; where the corpus writes the phrase with different punctuation than the SourceTerm, the row declares the editorial-punctuation variant triple; one entry bound to a stale unknown-state CorpusBaselineSha256 is rebound to the guide's frozen manifest sha (fleet majority). 41 further deferred rows were machine-verified verbatim-contiguous and left unchanged..

Gates: audit hardPass (beforeViolations 11 -> 0: corpus contiguity of every new window, headword-present law, variant triple, baseline rebind, per-row diff confinement, carryover lists clean on changed bytes).
Dictionary edits local-only (agent clone, contrib branch); no push.

- t3a-register-20260831: process-register rewrites per SPEC_T3_REGISTER_20260831.md (A7-reviewed-narrative x4)

- t2b-20260831: T2a-excluded tail rewrites per SPEC_T2B_20260831.md (rules B1-B6; B1 x14)

## S1-a residue relocation (2026-09-01)

Removed from entry.v2.json (production-shape hygiene,
SPEC_S1_20260901.md §3); values preserved verbatim:

- `Senses[0].Occurrences[0].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[1].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[2].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[3].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[4].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[5].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[6].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[7].ActorAttribution.AuthoredVoiceRiskReviewed`: true

- s1-20260901: residue-key purge per SPEC_S1_20260901_v2.md (aa-residue-AuthoredVoiceRiskReviewed x8)
- q3-20260901: re-window/mis-binding repairs per SPEC_Q3_20260901.md + AMENDMENT 1 (B-extend x1)
