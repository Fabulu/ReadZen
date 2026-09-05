#!/usr/bin/env python3
"""Probe: render the S1-b/R STAGED public surface for coordinator eyeball.

Reads the staged termbase (fresh-build/s1b-20260903/publication-stage/
public/) and prints, for sampled products, HEAD -> staged per-sense
ClaimAnchors shape with the removed anchors' ClaimText heads and the
survivor of the one partial-removal sense. Also prints the staged entry
count and the HEAD->staged changed-entry set (must be exactly the 53).
No writes.
"""
import json
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
STAGE = BUILD / "fresh-build" / "s1b-20260903" / "publication-stage"

mani = json.loads((BUILD / "maintenance" / "s1b-20260903-generic-manifest.json")
                  .read_text(encoding="utf-8"))
products = [p["id"] for p in mani["products"]]

staged = json.loads((STAGE / "public" / "termbase.v2.json")
                    .read_text(encoding="utf-8"))
staged_by_id = {e["Id"]: e for e in staged["Entries"]}
head_by_id = {e["Id"]: e for e in json.loads(subprocess.run(
    ["git", "-C", str(CLONE), "show", "HEAD:termbase.v2.json"],
    capture_output=True, text=True, encoding="utf-8").stdout)["Entries"]}


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


changed = sorted(eid for eid in staged_by_id
                 if canon(staged_by_id[eid]) != canon(head_by_id.get(eid)))
print(f"staged entries: {len(staged_by_id)} (HEAD {len(head_by_id)})")
print(f"changed vs HEAD: {len(changed)} == products: "
      f"{changed == sorted(products)}")

sample = ["t_cf6aac2f936b", "t_002c7f0ec57e", "t_00d347279628",
          "t_49100bcb7049", "t_baaf8fde82d2", "t_5892b09b6e92"]
for eid in sample:
    if eid not in products:
        print(f"!! {eid} not a product — sample bug")
        continue
    pre, post = head_by_id[eid], staged_by_id[eid]
    print(f"\n===== {eid}  term={pre['SourceTerm']!r} =====")
    for i, (ps, ss) in enumerate(zip(pre["Senses"], post["Senses"]), 1):
        pre_a = ps.get("ClaimAnchors")
        post_a = ss.get("ClaimAnchors")
        if pre_a is None and post_a is None:
            continue
        print(f"  s{i}: HEAD anchors={0 if pre_a is None else len(pre_a)} "
              f"-> staged anchors="
              f"{'ABSENT' if post_a is None else len(post_a)}")
        if pre_a:
            for j, a in enumerate(pre_a, 1):
                print(f"      removed a{j}: "
                      f"{str(a.get('ClaimText'))[:40]!r} kwic "
                      f"{str(a.get('Kwic'))[:24]!r}")
        if post_a:
            for j, a in enumerate(post_a, 1):
                print(f"      SURVIVOR a{j}: "
                      f"{str(a.get('ClaimText'))[:40]!r}")
    # the evidentiary bottom line: staged prose still anchored
    import re
    cjk = re.compile(r"[㐀-鿿豈-﫿]+")
    for i, ss in enumerate(post["Senses"], 1):
        prose = "\n".join(str(ss.get(k) or "") for k in ("Explanation",
                                                         "Note"))
        if not prose:
            continue
        kwics = [str(o.get("Kwic") or "") for o in ss.get("Occurrences")
                 or []]
        kwics += [str(a.get("Kwic") or "") for a in ss.get("ClaimAnchors")
                  or []]
        quotes = sorted(set(cjk.findall(prose)))[:3]
        for q in quotes:
            holder = next((k for k in kwics if q in k or k in q), None)
            print(f"  s{i} quote {q[:18]!r} -> "
                  f"{'anchored' if holder is not None else 'DANGLING'}")

sys.exit(0)
