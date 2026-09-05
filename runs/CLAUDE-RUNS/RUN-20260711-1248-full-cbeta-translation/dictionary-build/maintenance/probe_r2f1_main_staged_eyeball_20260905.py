#!/usr/bin/env python3
"""Render-only staged-surface laws for the combined R2+F1 MAIN publish.

Runs AFTER publisher stage, BEFORE install (writes nothing). Compares
the staged surface (fresh-build/r2f1-main-20260905/publication-stage/
public/) against the publish clone's main HEAD:

  LAW 1  per-id changed set == exactly the 5 products
         (4 changed + the t_351fa42d396b add);
  LAW 2  entry count 4,715 -> 4,716 (exactly +1);
  LAW 3  no-regression: every non-product entry byte-identical to
         main HEAD (the law the rejected wholesale checkout would
         have broken — it would have touched ~347+ entries);
  LAW 4  staged Dehui census == 0 (main had exactly 1, inside a
         product);
  RENDER the 5 repaired windows as they will appear ON MAIN, plus
         RelatedMasters and the rewritten Explanation sentence;
  REPORT aliases delta vs main HEAD and order inversions outside the
         products (both expected minimal/empty).
"""
import json
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
MAIN = Path(r"C:\programmieren\CbetaZenTranslations")
STAGE = (BUILD / "fresh-build" / "r2f1-main-20260905" / "publication-stage"
         / "public" / "termbase.v2.json")

mani = json.loads(
    (BUILD / "maintenance" / "r2f1-main-20260905-generic-manifest.json")
    .read_text(encoding="utf-8"))
wl = {p["id"] for p in mani["products"]}

staged = json.loads(STAGE.read_text(encoding="utf-8"))
staged_by_id = {e["Id"]: e for e in staged["Entries"]}
head = subprocess.run(
    ["git", "-C", str(MAIN), "show", "HEAD:termbase.v2.json"],
    capture_output=True, text=True, encoding="utf-8").stdout
head_by_id = {e["Id"]: e for e in json.loads(head)["Entries"]}
head_order = [e["Id"] for e in json.loads(head)["Entries"]]


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


changed = sorted(eid for eid in staged_by_id
                 if eid not in head_by_id
                 or canon(staged_by_id[eid]) != canon(head_by_id[eid]))
added = sorted(eid for eid in changed if eid not in head_by_id)
lost = sorted(eid for eid in head_by_id if eid not in staged_by_id)
print(f"LAW1 changed set == 5 products: "
      f"{set(changed) == wl} (changed {len(changed)}, added {added}, "
      f"lost {lost})")
print(f"LAW2 entry count {len(head_by_id)} -> {len(staged_by_id)} "
      f"(+1 exactly: {len(staged_by_id) == len(head_by_id) + 1})")

regressed = [eid for eid in head_by_id
             if eid not in wl
             and canon(head_by_id[eid]) != canon(staged_by_id.get(eid, {}))]
print(f"LAW3 non-product regression: {len(regressed)} "
      f"{regressed[:5]} (must be 0)")

dehui = [f"{eid} {o.get('RelPath')} {o.get('FromLb')}"
         for eid, e in sorted(staged_by_id.items())
         for s in e.get("Senses") or []
         for o in s.get("Occurrences") or []
         if o.get("MasterName") == "Dehui"]
print(f"LAW4 staged Dehui MasterName rows: {len(dehui)} {dehui[:5]} "
      f"(must be 0)")

# aliases delta + order inversions (report-only)
s_idx = json.loads((STAGE.parent / "termbase.index.json")
                   .read_text(encoding="utf-8"))
h_idx = json.loads(subprocess.run(
    ["git", "-C", str(MAIN), "show", "HEAD:termbase.index.json"],
    capture_output=True, text=True, encoding="utf-8").stdout)
sa, ha = dict(s_idx.get("Aliases") or {}), dict(h_idx.get("Aliases") or {})
print(f"aliases delta vs main HEAD: added {sorted(set(sa) - set(ha))}, "
      f"lost {sorted(set(ha) - set(sa))}, "
      f"changed {sorted(k for k in set(sa) & set(ha) if sa[k] != ha[k])}")
staged_order = [e["Id"] for e in staged["Entries"]]
pos = {eid: i for i, eid in enumerate(staged_order)}
inv = [a for a, b in zip(head_order, head_order[1:])
       if a in pos and b in pos and pos[a] > pos[b] and a not in wl
       and b not in wl]
print(f"order inversions outside products: {len(inv)} {inv[:5]}")

# ---- renders: the 5 repaired windows as they appear ON MAIN -----------------
RENDERS = (
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1113a21"),
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1143a07"),
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1143a12"),
    ("t_ab715aa474d5", "T/T48/T48n2025.xml", "1144b03"),
    ("t_351fa42d396b", "T/T48/T48n2025.xml", "1127c04"),
)
for eid, rel, lb in RENDERS:
    for s in staged_by_id[eid].get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") == rel and o.get("FromLb") == lb:
                aa = o.get("ActorAttribution") or {}
                print(f"\n=== {eid} {staged_by_id[eid]['SourceTerm']} "
                      f"{lb} (on main) ===")
                print(f"  kwic: {o.get('Kwic')}")
                print(f"  MasterName: {o.get('MasterName')!r}")
                print(f"  ContextMasters: "
                      f"{json.dumps(o.get('ContextMasters'), ensure_ascii=False)}")
                print(f"  Actor: {aa.get('Status')} / {aa.get('Kind')} / "
                      f"{aa.get('ActorLabel')!r}")
                print(f"  note: {o.get('AttributionNote')}")

# R2's remaining products: alias + wording spot-render
e968 = staged_by_id["t_968a2f97c9ff"]
print(f"\n=== t_968a2f97c9ff {e968['SourceTerm']} SearchAliases ===")
print(f"  {json.dumps(e968['Senses'][0].get('SearchAliases'), ensure_ascii=False)}")
e057 = staged_by_id["t_057cc9ea8755"]
note3 = e057["Senses"][0]["Occurrences"][2].get("AttributionNote") or ""
print(f"\n=== t_057cc9ea8755 攝心 occ-3 note (compiler provenance) ===")
print(f"  {note3[:220]}")

# 351fa Explanation sentence
CJK = re.compile(r"[㐀-鿿豈-﫿]+")
e = staged_by_id["t_351fa42d396b"]
print(f"\n=== t_351fa42d396b 粥飯 staged s1 Explanation ===")
for sent in re.split(r"(?<=[.;]) ",
                     str(e["Senses"][0].get("Explanation") or "")):
    if sent.strip():
        mark = " [CJK]" if CJK.search(sent) else ""
        print(f"     {sent}{mark}")
print(f"\nRelatedMasters 351fa: "
      f"{json.dumps(e['Senses'][0].get('RelatedMasters'), ensure_ascii=False)}")
print(f"RelatedMasters ab715: "
      f"{json.dumps(staged_by_id['t_ab715aa474d5']['Senses'][0].get('RelatedMasters'), ensure_ascii=False)}")
