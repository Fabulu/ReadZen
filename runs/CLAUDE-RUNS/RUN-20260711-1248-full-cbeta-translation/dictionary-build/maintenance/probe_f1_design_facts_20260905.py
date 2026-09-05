#!/usr/bin/env python3
"""F1 design facts: the R2-installed convention bytes to mirror.

A. One installed R2-repaired ea2 row in full (window 1143a07):
   MasterName / ContextMasters / ActorAttribution / AttributionNote —
   the frozen institutional-voice convention this lane reuses.
B. The second installed ea2 row's note (1113a21) — note the
   slot-specific variation.
C. Roster: "Dongyang Dehui" membership now (and "Dehui" absence).
D. The in-house precedent t_3f7a6ab74b68 context block.
E. Current bytes of the two F1 target rows + RelatedMasters + the
   351fa sense-1 Explanation sentence carrying bare "Dehui".
F. Fleet sanity: after R2, exactly these 2 rows carry MasterName
   "Dehui" on T48n2025 fleet-wide (no others lurk).
"""
from __future__ import annotations

import json
from pathlib import Path

CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
TERMS = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs"
             r"\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation"
             r"\dictionary-build\terms")
REG = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\Assets"
           r"\Data\zen-masters.json")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


tb = load(CLONE / "termbase.v2.json")
by_id = {e["Id"]: e for e in tb["Entries"]}

print("== A/B: installed R2 ea2 repaired rows ==")
ea2 = by_id["t_ea2a427c7aba"]
for o in ea2["Senses"][0]["Occurrences"]:
    if o.get("FromLb") in ("1143a07", "1113a21"):
        print(json.dumps(o, ensure_ascii=False, indent=2))

print("== D: precedent t_3f7a6ab74b68 (context block only) ==")
prec = by_id.get("t_3f7a6ab74b68")
if prec:
    for o in (prec.get("Senses") or [{}])[0].get("Occurrences") or []:
        if o.get("ContextMasters") or o.get("ActorAttribution"):
            print(json.dumps({"RelPath": o.get("RelPath"),
                              "FromLb": o.get("FromLb"),
                              "MasterName": o.get("MasterName"),
                              "ContextMasters": o.get("ContextMasters"),
                              "ActorAttribution": o.get("ActorAttribution")},
                             ensure_ascii=False, indent=2))
            break

print("== C: roster ==")
import re
reg_text = REG.read_text(encoding="utf-8") if REG.exists() else ""
print("Dongyang Dehui in roster:", "Dongyang Dehui" in reg_text)

print("== E: F1 target current bytes (terms side) ==")
for eid in ("t_ab715aa474d5", "t_351fa42d396b"):
    e = load(TERMS / eid / "entry.v2.json")
    s1 = e["Senses"][0]
    for oi, o in enumerate(s1["Occurrences"], 1):
        if o.get("MasterName") == "Dehui":
            print(f"{eid} s1 o{oi}:", json.dumps(
                {k: o.get(k) for k in ("RelPath", "FromLb", "ToLb",
                                       "Kwic", "MasterName",
                                       "ContextMasters",
                                       "AttributionNote")},
                ensure_ascii=False, indent=2))
    print(f"{eid} s1 RelatedMasters:", s1.get("RelatedMasters"))
    if eid == "t_351fa42d396b":
        m = re.search(r"[^.]*Dehui[^.]*\.", s1.get("Explanation") or "")
        print("351fa s1 Dehui sentence:", m.group(0) if m else None)

print("== F: fleet census of MasterName 'Dehui' on T48n2025 ==")
hits = []
for e in tb["Entries"]:
    for si, s in enumerate(e.get("Senses") or [], 1):
        for oi, o in enumerate(s.get("Occurrences") or [], 1):
            if o.get("MasterName") == "Dehui":
                hits.append((e["Id"], si, oi, o.get("RelPath"),
                             o.get("FromLb")))
print(json.dumps(hits, ensure_ascii=False, indent=2))
print("count:", len(hits))
