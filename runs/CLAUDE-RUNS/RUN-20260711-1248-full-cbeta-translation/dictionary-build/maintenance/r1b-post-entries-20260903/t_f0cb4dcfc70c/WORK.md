# batch10-deferred-20260829 worksheet — t_f0cb4dcfc70c (掛搭)

Citation-window repair (stitched-Kwic rewindow): 1 op(s); blind-reviewed (r1, r2, r3).

deferred-queue citation-window repair: rows whose stored Kwic was not contiguous corpus text (stitched at batch-2 time, when the cited files were absent from the local corpus) are rewindowed to the verbatim contiguous corpus window around the nearest headword occurrence (punctuation-tolerant anchor), window length matching the row's own sibling convention; where the corpus writes the phrase with different punctuation than the SourceTerm, the row declares the editorial-punctuation variant triple; one entry bound to a stale unknown-state CorpusBaselineSha256 is rebound to the guide's frozen manifest sha (fleet majority). 41 further deferred rows were machine-verified verbatim-contiguous and left unchanged..

Gates: audit hardPass (beforeViolations 11 -> 0: corpus contiguity of every new window, headword-present law, variant triple, baseline rebind, per-row diff confinement, carryover lists clean on changed bytes).
Dictionary edits local-only (agent clone, contrib branch); no push.

- t3b1-20260831: rule-22 pipeline-vocabulary rewrites per SPEC_T3B_20260831.md (T3b-1 deterministic families B1-B7; B1-11 x1)
