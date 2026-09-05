#!/usr/bin/env python3
"""Render-only staged-surface eyeball for R2 (writes nothing).

Runs AFTER publisher stage, BEFORE install. Reads the staged
termbase.v2.json (fresh-build/r2-20260903/publication-stage/public/)
and the clone HEAD bytes, and renders the changed surface for human
review:
  - changed entry set vs HEAD == exactly the 3 products;
  - no staged product entry cites either retired rel in Occurrences /
    ClaimAnchors / SourceTexts; no NON-product entry changed;
  - occurrence counts preserved vs HEAD (坐禪 9+3; 攝心 6; 一不成，二不是 10);
  - renders: the 3 re-attributed ea2 rows (masterName / contextMasters /
    actorLabel / attributionNote head), the rewritten prose (ea2
    Explanation, 057 Note + s1o3 AttributionNote), and 968's staged
    SearchAliases — for eyeball comparison against the SPEC's frozen
    correction design.
"""
import json
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
STAGE = (BUILD / "fresh-build" / "r2-20260903" / "publication-stage"
         / "public" / "termbase.v2.json")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}

mani = json.loads(
    (BUILD / "maintenance" / "r2-20260903-generic-manifest.json")
    .read_text(encoding="utf-8"))
wl = {p["id"] for p in mani["products"]}

staged = json.loads(STAGE.read_text(encoding="utf-8"))
staged_by_id = {e["Id"]: e for e in staged["Entries"]}
head = subprocess.run(
    ["git", "-C", str(CLONE), "show", "HEAD:termbase.v2.json"],
    capture_output=True, text=True, encoding="utf-8").stdout
head_by_id = {e["Id"]: e for e in json.loads(head)["Entries"]}


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


changed = sorted(eid for eid in staged_by_id
                 if canon(staged_by_id[eid]) != canon(head_by_id.get(eid)))
print(f"staged entries: {len(staged_by_id)}; changed vs HEAD: "
      f"{len(changed)}; == 3 products: {set(changed) == wl}")
if set(changed) != wl:
    print(f"  CHANGED SET: {changed}")

leftover = []
for eid in wl:
    for s in (staged_by_id[eid].get("Senses") or []):
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") in RETIRED:
                leftover.append(f"{eid} occ")
        for a in s.get("ClaimAnchors") or []:
            if a.get("RelPath") in RETIRED:
                leftover.append(f"{eid} anchor")
        for rel in s.get("SourceTexts") or []:
            if rel in RETIRED:
                leftover.append(f"{eid} sourceTexts")
print(f"retired-rel citations left in staged products: {len(leftover)} "
      f"{leftover[:5]}")

for eid in sorted(wl):
    sc = [len(s.get("Occurrences") or [])
          for s in staged_by_id[eid].get("Senses") or []]
    hc = [len(s.get("Occurrences") or [])
          for s in head_by_id[eid].get("Senses") or []]
    print(f"{eid} {staged_by_id[eid]['SourceTerm']}: occurrence counts "
          f"HEAD {hc} -> staged {sc}")

# ---- ea2: the 3 repaired rows + RelatedMasters + Explanation ---------------
e = staged_by_id["t_ea2a427c7aba"]
print(f"\n=== t_ea2a427c7aba {e['SourceTerm']} staged s1: repaired rows ===")
for oi in (1, 8, 9):
    o = e["Senses"][0]["Occurrences"][oi - 1]
    aa = o.get("ActorAttribution") or {}
    print(f"  occ{oi}: {o.get('RelPath')} {o.get('FromLb')}->"
          f"{o.get('ToLb')}")
    print(f"    MasterName: {o.get('MasterName')!r}")
    print(f"    ContextMasters: "
          f"{json.dumps(o.get('ContextMasters'), ensure_ascii=False)}")
    print(f"    Actor: {aa.get('Status')} / {aa.get('Kind')} / "
          f"{aa.get('ActorRole')} / {aa.get('ActorLabel')!r}")
    note = str(o.get("AttributionNote") or "")
    print(f"    note head: {note[:170]}...")
print(f"  RelatedMasters: "
      f"{json.dumps(e['Senses'][0].get('RelatedMasters'), ensure_ascii=False)}")

# ---- prose renders -----------------------------------------------------------
CJK = re.compile(r"[㐀-鿿豈-﫿]+")
for eid, fields in (
    ("t_ea2a427c7aba", (("Explanation", None),)),
    ("t_057cc9ea8755", (("Note", None), ("AttributionNote", 3))),
):
    e = staged_by_id[eid]
    print(f"\n=== {eid} {e['SourceTerm']} staged prose ===")
    for field, oi in fields:
        if oi is None:
            text = str(e["Senses"][0].get(field) or "")
        else:
            text = str(e["Senses"][0]["Occurrences"][oi - 1]
                       .get(field) or "")
        print(f"  -- {field}" + (f" (occ {oi})" if oi else "") + " --")
        for sent in re.split(r"(?<=[.;]) ", text):
            if sent.strip():
                mark = " [CJK]" if CJK.search(sent) else ""
                print(f"     {sent}{mark}")

# ---- 968: staged SearchAliases ----------------------------------------------
e = staged_by_id["t_968a2f97c9ff"]
print(f"\n=== t_968a2f97c9ff {e['SourceTerm']} staged SearchAliases ===")
print(f"  {json.dumps(e['Senses'][0].get('SearchAliases'), ensure_ascii=False)}")
