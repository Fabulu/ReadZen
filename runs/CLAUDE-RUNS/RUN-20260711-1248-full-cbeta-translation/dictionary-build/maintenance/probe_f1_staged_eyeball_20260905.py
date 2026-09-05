#!/usr/bin/env python3
"""Render-only staged-surface eyeball for F1 (writes nothing).

Runs AFTER publisher stage, BEFORE install. Reads the staged
termbase.v2.json (fresh-build/f1-20260905/publication-stage/public/)
and the clone HEAD bytes, and renders the changed surface for human
review:
  - changed entry set vs HEAD == exactly the 2 products;
  - no staged product entry cites either retired rel in Occurrences /
    ClaimAnchors / SourceTexts; no NON-product entry changed;
  - occurrence counts preserved vs HEAD (一日不作一日不食 3; 粥飯 3+6);
  - renders: the 2 re-attributed rows (masterName / contextMasters /
    actorLabel / attributionNote head), both entries' RelatedMasters,
    and 351fa's rewritten Explanation sentence — for eyeball comparison
    against the SPEC's frozen correction design;
  - staged census: zero MasterName 'Dehui' rows anywhere in the staged
    surface (SPEC §7 preview).
"""
import json
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
STAGE = (BUILD / "fresh-build" / "f1-20260905" / "publication-stage"
         / "public" / "termbase.v2.json")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}

mani = json.loads(
    (BUILD / "maintenance" / "f1-20260905-generic-manifest.json")
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
      f"{len(changed)}; == 2 products: {set(changed) == wl}")
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

# ---- the 2 repaired rows + RelatedMasters ------------------------------------
for eid, si, oi in (("t_ab715aa474d5", 1, 2), ("t_351fa42d396b", 1, 1)):
    e = staged_by_id[eid]
    o = e["Senses"][si - 1]["Occurrences"][oi - 1]
    aa = o.get("ActorAttribution") or {}
    print(f"\n=== {eid} {e['SourceTerm']} staged s{si} o{oi}: repaired row ===")
    print(f"  {o.get('RelPath')} {o.get('FromLb')}->{o.get('ToLb')}")
    print(f"  kwic: {o.get('Kwic')}")
    print(f"  MasterName: {o.get('MasterName')!r}")
    print(f"  ContextMasters: "
          f"{json.dumps(o.get('ContextMasters'), ensure_ascii=False)}")
    print(f"  Actor: {aa.get('Status')} / {aa.get('Kind')} / "
          f"{aa.get('ActorRole')} / {aa.get('ActorLabel')!r}")
    print(f"  GrammarEvidence: {aa.get('GrammarEvidence')}")
    print(f"  note: {o.get('AttributionNote')}")
    print(f"  RelatedMasters: "
          f"{json.dumps(e['Senses'][0].get('RelatedMasters'), ensure_ascii=False)}")

# ---- 351fa: rewritten Explanation sentence -----------------------------------
CJK = re.compile(r"[㐀-鿿豈-﫿]+")
e = staged_by_id["t_351fa42d396b"]
print(f"\n=== {eid} {e['SourceTerm']} staged s1 Explanation ===")
text = str(e["Senses"][0].get("Explanation") or "")
for sent in re.split(r"(?<=[.;]) ", text):
    if sent.strip():
        mark = " [CJK]" if CJK.search(sent) else ""
        print(f"     {sent}{mark}")

# ---- staged census (SPEC §7 preview) ------------------------------------------
dehui = []
for eid, e2 in sorted(staged_by_id.items()):
    for s in e2.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("MasterName") == "Dehui":
                dehui.append(f"{eid} {o.get('FromLb')}")
print(f"\nstaged census MasterName 'Dehui' rows: {len(dehui)} {dehui[:5]}")
