# batch10-deferred-20260829 worksheet — t_c513dc22845c (十戒)

Citation-window repair (stitched-Kwic rewindow): 1 op(s); blind-reviewed (r1, r2, r3).

deferred-queue citation-window repair: rows whose stored Kwic was not contiguous corpus text (stitched at batch-2 time, when the cited files were absent from the local corpus) are rewindowed to the verbatim contiguous corpus window around the nearest headword occurrence (punctuation-tolerant anchor), window length matching the row's own sibling convention; where the corpus writes the phrase with different punctuation than the SourceTerm, the row declares the editorial-punctuation variant triple; one entry bound to a stale unknown-state CorpusBaselineSha256 is rebound to the guide's frozen manifest sha (fleet majority). 41 further deferred rows were machine-verified verbatim-contiguous and left unchanged..

Gates: audit hardPass (beforeViolations 11 -> 0: corpus contiguity of every new window, headword-present law, variant triple, baseline rebind, per-row diff confinement, carryover lists clean on changed bytes).
Dictionary edits local-only (agent clone, contrib branch); no push.

## S1-a residue relocation (2026-09-01)

Removed from entry.v2.json (production-shape hygiene,
SPEC_S1_20260901.md §3); values preserved verbatim:

- `Senses[0].Occurrences[2].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[3].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[4].ActorAttribution.AuthoredVoiceRiskReviewed`: true

- s1-20260901: residue-key purge per SPEC_S1_20260901_v2.md (aa-residue-AuthoredVoiceRiskReviewed x3)
- q3-20260901: re-window/mis-binding repairs per SPEC_Q3_20260901.md + AMENDMENT 1 (B-extend x1)
- r1b-20260903: R1b retired-source removals per SPEC_R1b_20260903.md + AMENDMENTS 1-2 (occ-remove-retired x1)
