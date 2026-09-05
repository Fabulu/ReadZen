#!/usr/bin/env python3
"""Coordinator probe: byte-adjudicate the R0117 honest-flag (performer row
claiming Huitang Zuxin, flagged as 'unevidenced in kwic/note').

Prints the full pre occurrence (every field), every place the claimed
master's name/hanzi appears in the ENTRY's pre bytes (any field, any
sense), and the audit-provenance detail that scoped the edit.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads(
    (HERE / "a1-blind-r1-rows-20260903.json").read_text(encoding="utf-8")
)["rows"]
row = next(r for r in rows if r["rowId"] == "R0117")
print("== R0117 row ==")
print(json.dumps(row, ensure_ascii=False, indent=2))

eid, si, oi = row["entry"], row["si"], row["oi"]
pre = json.loads((HERE / "a1-blind-r1-materials" / "pre" / f"{eid}.json")
                 .read_text(encoding="utf-8"))
occ = pre["Senses"][si - 1]["Occurrences"][oi - 1]
print(f"\n== pre occurrence {eid} s{si} o{oi} ==")
print(json.dumps(occ, ensure_ascii=False, indent=2))

name = row["row"]["MasterName"]
hanzi = {"Huitang Zuxin": ["晦堂", "祖心", "晦堂祖心"]}.get(name, [])
pre_text = json.dumps(pre, ensure_ascii=False)
print(f"\n== name '{name}' anywhere in entry pre bytes: "
      f"{name in pre_text} ==")
for h in hanzi:
    print(f"   hanzi {h!r} in entry pre bytes: {h in pre_text}")
idx = pre_text.find(name)
if idx >= 0:
    print(f"   context: …{pre_text[max(0, idx - 120):idx + 160]}…")

# where in the entry does the claimed master's name occur (field paths)?
def walk(v, prefix=""):
    if isinstance(v, dict):
        for k, x in v.items():
            yield from walk(x, f"{prefix}.{k}" if prefix else k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk(x, f"{prefix}[{i}]")
    else:
        yield prefix, v

for p, v in walk(pre):
    s = str(v)
    if name in s or any(h in s for h in hanzi):
        print(f"   hit at {p}: {s[:200]}")

# audit provenance: what failure did this occurrence carry?
det = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8"))
print(f"\n== audit details for {eid} ==")
for kind, d in det["stillFailing"][eid]:
    print(f"   {kind}: {d}")
