#!/usr/bin/env python3
"""Render-only eyeball probe for R1b (writes nothing).

Renders the changed surface for human review (the user's look-at-it
rule): for representative entries — a same-sense double removal (水頭),
the note-count rewrite (t_50d75aeeeef1), the residual-row entry (坐堂),
a newly below-floor entry, and a plain single removal — the PRE
occurrence list (marked REMOVED/SURVIVOR), the POST occurrence list,
and the sense's prose-anchoring verdict. Prints the Note sentence
before/after for the rewrite entry. Verifies the 2 BLOCKED entries are
byte-untouched in terms/ (still carrying their retired occurrences).
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))

_spec = importlib.util.spec_from_file_location(
    "r1b_eng", HERE / "r1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

TERMS = BUILD / "terms"
clone_by_id = eng.clone_state()
receipt = json.loads(
    (HERE / "r1b-edit-receipt-20260903.json").read_text(encoding="utf-8"))
recs = receipt["editRecords"]

SAMPLES = [
    ("t_d7725cb0c8c0", "same-sense double removal (水頭)"),
    ("t_50d75aeeeef1", "note-count rewrite entry"),
    ("t_b97e19fa54b2", "residual performer rows (坐堂)"),
    ("t_f5e1fe96407c", "newly below-floor entry"),
    ("t_044652c7b411", "plain single removal"),
]

for eid, why in SAMPLES:
    pre = clone_by_id[eid]
    post = json.loads((TERMS / eid / "entry.v2.json").read_text(
        encoding="utf-8-sig"))
    term = pre.get("SourceTerm")
    removed = {(r["si"], r["oi"]) for r in recs
               if r["entry"] == eid and r["class"] == "occ-remove-retired"}
    print(f"\n=== {eid} {term} — {why} "
          f"(removed {len(removed)}; pre senses "
          f"{len(pre['Senses'])}, post {len(post['Senses'])}) ===")
    for si in sorted({si for si, _ in removed}):
        ps, qs = pre["Senses"][si - 1], post["Senses"][si - 1]
        print(f"  sense {si}: {len(ps.get('Occurrences') or [])} -> "
              f"{len(qs.get('Occurrences') or [])} occurrences")
        for oi, o in enumerate(ps.get("Occurrences") or [], 1):
            mark = "REMOVED  " if (si, oi) in removed else "survivor "
            print(f"    {mark} {o.get('RelPath')} "
                  f"{str(o.get('Kwic') or '')[:44]!r}")
        # post prose anchoring over surviving kwics + anchors
        survivors = [str(o.get("Kwic") or "")
                     for o in qs.get("Occurrences") or []]
        survivors += [str(a.get("Kwic") or "")
                      for a in qs.get("ClaimAnchors") or []]
        prose = "\n".join(str(qs.get(k) or "")
                          for k in ("Explanation", "Note"))
        danglers = [q for q in sorted(set(re.findall(eng.CJK_RE.pattern,
                                                     prose)))
                    if not any(q in k or k in q for k in survivors if k)]
        print(f"    POST prose anchored: {not danglers}"
              + (f" (danglers: {danglers[:3]})" if danglers else ""))
        if eid == "t_50d75aeeeef1":
            pre_note = str(ps.get("Note") or "")
            post_note = str(qs.get("Note") or "")
            print(f"    NOTE pre : {pre_note[:160]}")
            print(f"    NOTE post: {post_note[:160]}")

# blocked entries untouched in terms/
print("\n=== blocked entries (must be byte-identical to clone) ===")
for eid in ("t_057cc9ea8755", "t_ea2a427c7aba"):
    cur = (TERMS / eid / "entry.v2.json").read_text(encoding="utf-8")
    same = cur == eng.canon(clone_by_id[eid])
    retired_left = sum(
        1 for s in clone_by_id[eid].get("Senses") or []
        for o in s.get("Occurrences") or []
        if o.get("RelPath") in eng.RETIRED)
    print(f"  {eid} {clone_by_id[eid].get('SourceTerm')}: "
          f"byte-identical to clone: {same}; retired occurrences "
          f"still present: {retired_left}")
