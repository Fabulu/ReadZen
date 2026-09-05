#!/usr/bin/env python3
"""Render before/after proof for the finished repair lanes (read-only).

Blocks:
  1-2. R1c re-anchors: frozen pre/post materials (byte evidence).
  3.   Live zc counts NOW (the rewritten count sentences stay true).
  4.   R1b sample (t_d7725cb0c8c0 水頭, double removal): git 87a6975
       -> f3a2317.
  5.   Q3 sample: first receipt record's entry, git 967db5e^ -> 967db5e.
  6.   C1 withdrawal: manifest withdrawn list; id present in 20c9011^
       and absent in 20c9011.
"""
import json
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402

CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
MAT = BUILD / "maintenance" / "r1c-blind-r1-materials"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def git_entry(rev: str, eid: str):
    out = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"{rev}:termbase.v2.json"],
        capture_output=True).stdout
    for e in json.loads(out.decode("utf-8"))["Entries"]:
        if e.get("Id") == eid:
            return e
    return None


def occ_line(o, w=46):
    return (f"    {o.get('RelPath')} {o.get('FromLb')}->{o.get('ToLb')} "
            f"[{o.get('MasterName')}] "
            f"{str(o.get('Kwic') or '')[:w]!r}")


print("=" * 78)
print("BLOCK 1 — R1c: t_057cc9ea8755 攝心 (frozen pre -> post materials)")
print("=" * 78)
pre = load(MAT / "pre" / "t_057cc9ea8755.json")
post = load(MAT / "post" / "t_057cc9ea8755.json")
P, Q = pre["Senses"][0]["Occurrences"], post["Senses"][0]["Occurrences"]
for j, (a, b) in enumerate(zip(P, Q)):
    if a != b:
        print(f"  occurrence slot {j + 1} (the ONLY changed slot):")
        print("  BEFORE (retired anthology):")
        print(occ_line(a, 60))
        print(f"        AttributionNote: {a.get('AttributionNote')}")
        print("  AFTER (Shiwu Qinggong's own record):")
        print(occ_line(b, 60))
        print(f"        AttributionNote: {b.get('AttributionNote')}")
print("  Note sentence:")
print("  BEFORE: Shiwu Qinggong's community verse retains the ordinary "
      "finite action by listing chanting and ... (攝心除睡, two in two)")
print("  AFTER:  " + next(s for s in post["Senses"][0]["Note"].split(". ")
      if "own record" in s) + ".")
print("  Count sentence:")
print("  BEFORE: " + next(s for s in pre["Senses"][0]["Explanation"]
      .split(". ") if "attested" in s) + ".")
print("  AFTER:  " + next(s for s in post["Senses"][0]["Explanation"]
      .split(". ") if "attested" in s) + ".")

print()
print("=" * 78)
print("BLOCK 2 — R1c: t_ea2a427c7aba 坐禪 (frozen pre -> post materials)")
print("=" * 78)
pre = load(MAT / "pre" / "t_ea2a427c7aba.json")
post = load(MAT / "post" / "t_ea2a427c7aba.json")
P, Q = pre["Senses"][0]["Occurrences"], post["Senses"][0]["Occurrences"]
for j, (a, b) in enumerate(zip(P, Q)):
    if a != b:
        print(f"  occurrence slot {j + 1}:")
        print("  BEFORE (retired, attributed to the lost 長蘆 manual):")
        print(occ_line(a, 60))
        print("  AFTER (T48n2025 坐禪儀 section, Dehui the redactor):")
        print(occ_line(b, 60))
print("  RelatedMasters:")
print(f"  BEFORE: {pre['Senses'][0]['RelatedMasters']}")
print(f"  AFTER:  {post['Senses'][0]['RelatedMasters']}")
print("  Note counts:")
print("  BEFORE: " + next(s for s in pre["Senses"][0]["Note"].split(". ")
      if "exact occurrences" in s) + ". | " + next(
          s for s in pre["Senses"][0]["Note"].split(". ")
          if "sources" in s) + ".")
print("  AFTER:  " + next(s for s in post["Senses"][0]["Note"].split(". ")
      if "exact occurrences" in s) + ". | " + next(
          s for s in post["Senses"][0]["Note"].split(". ")
          if "sources" in s) + ".")
print("  Explanation manual sentence 2 (head):")
print("  BEFORE: " + pre["Senses"][0]["Explanation"].split(". ")[1][:150]
      + " ...")
print("  AFTER:  " + post["Senses"][0]["Explanation"].split(". ")[1][:150]
      + " ...")

print()
print("=" * 78)
print("BLOCK 3 — live corpus counts NOW (dictionary-build/zc.py)")
print("=" * 78)
for term in ("攝心", "坐禪", "攝心除睡"):
    c = zc.count(term)
    print(f"  zc.count({term!r}) = {c.get('hits')} hits / "
          f"{c.get('files')} files")

print()
print("=" * 78)
print("BLOCK 4 — R1b sample: t_d7725cb0c8c0 水頭 (git 87a6975 -> f3a2317)")
print("=" * 78)
a = git_entry("87a6975", "t_d7725cb0c8c0")
b = git_entry("f3a2317", "t_d7725cb0c8c0")
pa, pb = a["Senses"][0]["Occurrences"], b["Senses"][0]["Occurrences"]
print(f"  occurrences {len(pa)} -> {len(pb)}; removed slots:")
kept = 0
for o in pa:
    if o.get("RelPath") in ("T/T48/T48n2023.xml", "X/X63/X63n1245.xml"):
        print("  REMOVED " + occ_line(o, 50))
    else:
        kept += 1
print(f"  survivors kept: {kept} == len(after) {len(pb)}: "
      f"{kept == len(pb)}")

print()
print("=" * 78)
print("BLOCK 5 — Q3 samples (git 967db5e^ -> 967db5e)")
print("=" * 78)
q3r = load(BUILD / "maintenance" / "q3-edit-receipt-20260901.json")
print(f"  Q3 receipt: {q3r['productsCount']} products; classes="
      f"{q3r['editClassCounts']}")
# Self-proving sample: scan product entries, diff occurrences across the
# Q3 commit. A-rebind signature = FromLb changed, Kwic byte-equal (same
# evidence, corrected line binding). Show first entry exhibiting it.
shown = 0
for eid in q3r["products"]:
    if shown:
        break
    qa, qb = git_entry("967db5e^", eid), git_entry("967db5e", eid)
    if not (qa and qb):
        continue
    for si, (sa, sb) in enumerate(zip(qa["Senses"], qb["Senses"])):
        oa = sa.get("Occurrences") or []
        ob = sb.get("Occurrences") or []
        if len(oa) != len(ob):
            continue
        for j, (x, y) in enumerate(zip(oa, ob)):
            if (x != y and x.get("Kwic") == y.get("Kwic")
                    and x.get("FromLb") != y.get("FromLb")):
                print(f"  {eid} sense {si + 1} slot {j + 1} "
                      "(Kwic byte-identical, lb re-bound):")
                print("  BEFORE: " + occ_line(x, 50))
                print("  AFTER:  " + occ_line(y, 50))
                shown += 1
                break
        if shown:
            break

print()
print("=" * 78)
print("BLOCK 6 — C1 withdrawal (manifest; git 20c9011^ -> 20c9011)")
print("=" * 78)
c1 = load(BUILD / "maintenance" / "c1-20260902-generic-manifest.json")
print(f"  manifest keys: {sorted(c1)}")
wd = c1.get("withdrawn") or []
if isinstance(wd, dict):
    wd = wd.get("ids") or []
print(f"  withdrawn: {wd}")
print(f"  products: {[p.get('id') for p in c1.get('products', [])]} "
      f"(modes: {[p.get('mode') for p in c1.get('products', [])]})")
for w in (wd if isinstance(wd, list) else [])[:3]:
    wid = w.get("id") if isinstance(w, dict) else w
    print(f"  {wid}: in 20c9011^ = {git_entry('20c9011^', wid) is not None}"
          f"; in 20c9011 = {git_entry('20c9011', wid) is not None}")
