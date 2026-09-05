#!/usr/bin/env python3
"""Decisive: inline census vs r2.derive() on the same clone_state."""
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
print("inline census:", dict(census))
print("r2.T4825:", repr(r2.T4825))
try:
    wl = r2.derive(by_id)
    print("r2.derive OK:", wl)
except SystemExit as ex:
    print("r2.derive FAILED:", ex)
    # bisect: replicate derive line by line
    c2 = Counter()
    for eid, e in by_id.items():
        for s in e.get("Senses") or []:
            for o in s.get("Occurrences") or []:
                if (o.get("RelPath") == r2.T4825
                        and o.get("MasterName") == "Dehui"):
                    c2[eid] += 1
    print("bisect census:", dict(c2))
    print("T4825 is:", r2.T4825, "| DEFECT_CENSUS is:", r2.DEFECT_CENSUS)
    import inspect
    src = inspect.getsource(r2.derive)
    print("derive source head:")
    print("\n".join(src.splitlines()[:16]))
