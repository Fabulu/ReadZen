#!/usr/bin/env python3
"""Why does r2_transform.derive() see only 3 of the 5 Dehui rows?"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r2_transform_20260903 as r2  # noqa: E402

by_id = r2.clone_state()
census = Counter()
for eid, e in by_id.items():
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if (o.get("RelPath") == r2.T4825
                    and o.get("MasterName") == "Dehui"):
                census[eid] += 1
print("census via engine clone_state():", dict(census))
print("DEFECT_CENSUS:", r2.DEFECT_CENSUS)

for eid in ("t_ab715aa474d5", "t_351fa42d396b"):
    e = by_id.get(eid)
    print(f"\n{eid}: found={e is not None}")
    if e:
        print("  SourceTerm:", e.get("SourceTerm"))
        for si, s in enumerate(e.get("Senses") or [], 1):
            for oi, o in enumerate(s.get("Occurrences") or [], 1):
                mn = o.get("MasterName")
                print(f"  s{si}o{oi}: RelPath={o.get('RelPath')!r} "
                      f"MasterName={mn!r} "
                      f"match={(o.get('RelPath') == r2.T4825 and mn == 'Dehui')}")
                print("    MasterName type:", type(mn).__name__,
                      " len:", len(mn) if isinstance(mn, str) else "-",
                      " repr bytes:",
                      repr(mn.encode("utf-8")) if isinstance(mn, str) else "-")
