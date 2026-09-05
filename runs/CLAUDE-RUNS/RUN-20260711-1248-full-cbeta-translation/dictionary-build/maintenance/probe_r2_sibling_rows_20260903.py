#!/usr/bin/env python3
"""Where are the 2 sibling [Dehui] rows? (census mismatch triage)"""
import json
from pathlib import Path

CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
live = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
ids = {x["Id"] for x in live["Entries"]}
for eid in ("t_ab715aa474d5", "t_351fa42d396b"):
    print(eid, "in clone:", eid in ids)

print("\nMasterName==Dehui rows (any rel):")
for x in live["Entries"]:
    for si, s in enumerate(x.get("Senses") or [], 1):
        for oi, o in enumerate(s.get("Occurrences") or [], 1):
            if o.get("MasterName") == "Dehui":
                print("  ", x["Id"], x.get("SourceTerm"), f"s{si}o{oi}",
                      o.get("RelPath"), o.get("FromLb"))

print("\nT48n2025 rows mentioning Dehui anywhere in the occurrence:")
for x in live["Entries"]:
    for si, s in enumerate(x.get("Senses") or [], 1):
        for oi, o in enumerate(s.get("Occurrences") or [], 1):
            if (o.get("RelPath") == "T/T48/T48n2025.xml"
                    and "Dehui" in json.dumps(o, ensure_ascii=False)):
                print("  ", x["Id"], x.get("SourceTerm"), f"s{si}o{oi}",
                      "MasterName=", repr(o.get("MasterName")),
                      o.get("FromLb"))

print("\nBy SourceTerm:")
for name in ("一日不作一日不食", "粥飯"):
    for x in live["Entries"]:
        if x.get("SourceTerm") == name:
            print(name, "->", x["Id"])
            for si, s in enumerate(x.get("Senses") or [], 1):
                for oi, o in enumerate(s.get("Occurrences") or [], 1):
                    if o.get("RelPath") == "T/T48/T48n2025.xml":
                        print(f"   s{si}o{oi} {o.get('FromLb')} "
                              f"MasterName={o.get('MasterName')!r}")
