# lamp-revert-20260825 revert product t_1fe4eac13d6e

Term: 入門便喝
Mode: rowUnion
Restored rows (RelPath|FromLb): X/X69/X69n1357.xml|0473b24; X/X78/X78n1554.xml|0611a21; C/C077/C077n1710.xml|0690c21
Basis: user order 2026-08-25 — revert all lamp-repair deletions. Bytes recovered from termbase git history, sha-verified against the repair receipt baselines.

- reghomo-20260831: registry-title homoglyph repair (Essentials of the Mind b…->Essentials o… x2) per SPEC_REGHOMOGLYPH_20260831.md

## S1-a residue relocation (2026-09-01)

Removed from entry.v2.json (production-shape hygiene,
SPEC_S1_20260901.md §3); values preserved verbatim:

- `RelatedMasters`: []
- `Senses[0].Occurrences[1].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[7].ActorAttribution.AuthoredVoiceRiskReviewed`: true
- `Senses[0].Occurrences[9].ActorAttribution.AuthoredVoiceRiskReviewed`: true

- s1-20260901: residue-key purge per SPEC_S1_20260901_v2.md (aa-residue-AuthoredVoiceRiskReviewed x3, entry-residue-RelatedMasters x1)
- q3-20260901: re-window/mis-binding repairs per SPEC_Q3_20260901.md + AMENDMENT 1 (B-extend x1)
