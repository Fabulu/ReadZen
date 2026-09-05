#!/usr/bin/env python3
"""Render-only staged-surface eyeball for R1b (writes nothing).

Runs AFTER publisher stage, BEFORE install. Reads the staged
termbase.v2.json (fresh-build/r1b-20260903/publication-stage/public/)
and the
clone HEAD bytes, and renders the changed surface for human review:
  - changed entry set vs HEAD == exactly the 43 products;
  - NO staged product entry cites either retired rel (occurrences or
    ClaimAnchors); no NON-product entry changed (so the 2 prose-gate
    BLOCKED entries stay byte-identical, retired occurrences intact);
  - the one rewritten Note sentence (t_50d75aeeeef1) in the staged
    bytes, with its live survivor arithmetic;
  - per-sample renders: the same-sense double removal (水頭) and the
    residual-row entry (坐堂) occurrence lists as staged.
"""
import hashlib
import json
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
STAGE = (BUILD / "fresh-build" / "r1b-20260903" / "publication-stage"
         / "public" / "termbase.v2.json")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
BLOCKED = ("t_057cc9ea8755", "t_ea2a427c7aba")
NOTE_ENTRY = "t_50d75aeeeef1"

mani = json.loads(
    (BUILD / "maintenance" / "r1b-20260903-generic-manifest.json")
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
      f"{len(changed)}; == 43 products: {set(changed) == wl}")

leftover = []
for eid in wl:
    for s in (staged_by_id[eid].get("Senses") or []):
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") in RETIRED:
                leftover.append(f"{eid} occ")
        for a in s.get("ClaimAnchors") or []:
            if a.get("RelPath") in RETIRED:
                leftover.append(f"{eid} anchor")
print(f"retired-rel citations left in staged products: {len(leftover)} "
      f"{leftover[:5]}")

untouched_ok = all(canon(staged_by_id[e]) == canon(head_by_id[e])
                   for e in BLOCKED)
blocked_left = {e: sum(1 for s in staged_by_id[e].get("Senses") or []
                       for o in s.get("Occurrences") or []
                       if o.get("RelPath") in RETIRED) for e in BLOCKED}
print(f"blocked pair byte-identical in stage: {untouched_ok}; "
      f"retired occurrences still present: {blocked_left}")

note = str(staged_by_id[NOTE_ENTRY]["Senses"][0].get("Note") or "")
import re
m = re.search(r"\d+ exact occurrences? from \d+ distinct works", note)
occs = staged_by_id[NOTE_ENTRY]["Senses"][0].get("Occurrences") or []
print(f"staged note sentence: {m.group(0) if m else None!r}; live "
      f"occurrences {len(occs)}, distinct rels "
      f"{len({o.get('RelPath') for o in occs})}")

for eid, why in (("t_d7725cb0c8c0", "double removal"),):
    print(f"\n{eid} {staged_by_id[eid]['SourceTerm']} ({why}) staged s1:")
    for o in staged_by_id[eid]["Senses"][0].get("Occurrences") or []:
        print(f"    {o.get('RelPath')} {str(o.get('Kwic') or '')[:44]!r}")
