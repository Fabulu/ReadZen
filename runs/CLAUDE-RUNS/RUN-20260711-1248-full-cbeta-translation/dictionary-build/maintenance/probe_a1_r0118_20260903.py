#!/usr/bin/env python3
"""Coordinator probe: byte-adjudicate the R0118 honest-flag (performer-
grammar-proof sentence citing 'the verse after 頌曰' — flagged because the
stored kwic window itself contains no 頌曰).

Prints the row, the pre/post occurrence, zc evidence for the 頌曰 prefix
IMMEDIATELY before the kwic window (corpus bytes, count law), the
embedded-name check (趙州/投子 inside the kwic), and the audit detail
that scoped the edit.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402

rows = json.loads(
    (HERE / "a1-blind-r1-rows-20260903.json").read_text(encoding="utf-8")
)["rows"]
row = next(r for r in rows if r["rowId"] == "R0118")
print("== R0118 row ==")
print(json.dumps(row, ensure_ascii=False, indent=2))

eid, si, oi = row["entry"], row["si"], row["oi"]
pre = json.loads((HERE / "a1-blind-r1-materials" / "pre" / f"{eid}.json")
                 .read_text(encoding="utf-8"))
post = json.loads((HERE / "a1-blind-r1-materials" / "post" / f"{eid}.json")
                  .read_text(encoding="utf-8"))
occ = pre["Senses"][si - 1]["Occurrences"][oi - 1]
print(f"\n== pre occurrence {eid} s{si} o{oi} ==")
print(json.dumps(occ, ensure_ascii=False, indent=2))

rel = occ["RelPath"]
kwic = str(occ.get("Kwic") or "")
v_kwic = zc.verify(rel, kwic)
print(f"\nzc(kwic): {json.dumps(v_kwic, ensure_ascii=False)}")

for probe in ("頌曰" + kwic[:12], "頌曰。" + kwic.lstrip("。、，")[:12]):
    v = zc.verify(rel, probe)
    print(f"zc(prefix {probe[:22]!r}…): "
          f"{json.dumps(v, ensure_ascii=False)}")

print(f"\n趙州 in kwic: {'趙州' in kwic}; 投子 in kwic: {'投子' in kwic}")
print(f"stored FromLb={occ.get('FromLb')} ToLb={occ.get('ToLb')}")

post_occ = post["Senses"][si - 1]["Occurrences"][oi - 1]
print("\n== post ActorAttribution ==")
print(json.dumps(post_occ.get("ActorAttribution"), ensure_ascii=False,
                 indent=2))

det = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8"))
print(f"\n== audit details for {eid} ==")
for kind, d in det["stillFailing"][eid]:
    print(f"   {kind}: {d}")
