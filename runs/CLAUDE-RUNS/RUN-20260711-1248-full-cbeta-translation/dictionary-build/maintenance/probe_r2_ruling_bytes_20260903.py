#!/usr/bin/env python3
"""Byte evidence for the R2 r1 coordinator ruling (R0007, law B3).

The flagged honest row is the attributionnote-rewrite (t_057cc9ea8755
s1 o3). Law B3 as literally worded demanded full-string equality
between the slot's AttributionNote and the row's before/after; the row
— like every prose-rewrite row in this lane — carries FIND-ONCE
fragments. This probe proves the corrected law on the frozen materials:

  B3'  PRE slot AttributionNote contains `before` exactly once, AND
       POST slot AttributionNote == PRE slot with `before` replaced by
       `after` once, AND `after` occurs exactly once in the POST slot.

plus the row's oracle-exactness (its full payload equals the row
rebuilt from the engine + frozen materials, exactly as the rows builder
constructs honest rows).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
MAT = HERE / "r2-blind-r1-materials"

_spec = importlib.util.spec_from_file_location(
    "r2_eng", HERE / "r2_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

rows_doc = json.loads(
    (HERE / "r2-blind-r1-rows-20260903.json").read_text(encoding="utf-8"))
adj = json.loads(
    (HERE / "r2-blind-r1-adjudication-20260903.json").read_text("utf-8"))
flag = adj["honestFlags"][0] if len(adj["honestFlags"]) == 1 else None
if not flag or flag["rowId"] != "R0007":
    raise SystemExit(f"expected exactly one honest flag R0007, got "
                     f"{[f['rowId'] for f in adj['honestFlags']]}")
row = next(r for r in rows_doc["rows"] if r["rowId"] == "R0007")
assert row["class"] == "attributionnote-rewrite", row["class"]

by_id = eng.clone_state()
worklist = eng.derive(by_id)
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)
for eid in worklist:
    assert out[eid].encode("utf-8") == (MAT / "post" / f"{eid}.json"
                                        ).read_bytes()
    assert eng.canon(pre_state[eid]) == (MAT / "pre" / f"{eid}.json"
                                         ).read_text(encoding="utf-8")

rec = next(r for r in records if r["class"] == "attributionnote-rewrite")
pre_obj = json.loads((MAT / "pre" / "t_057cc9ea8755.json")
                     .read_text(encoding="utf-8"))
post_obj = json.loads((MAT / "post" / "t_057cc9ea8755.json")
                      .read_text(encoding="utf-8"))
pre_slot = pre_obj["Senses"][0]["Occurrences"][rec["oi"] - 1]
post_slot = post_obj["Senses"][0]["Occurrences"][rec["oi"] - 1]
before, after = rec["before"], rec["after"]


def body_json(r: dict) -> str:
    body = {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}
    return json.dumps(body, ensure_ascii=False, sort_keys=True)


oracle_row = body_json({
    "entry": rec["entry"], "class": rec["class"], "si": rec["si"],
    "field": rec["field"], "oi": rec.get("oi"),
    "before": before, "after": after,
})

evidence = {
    "schemaVersion": "r2-ruling-bytes",
    "round": "r1",
    "rowId": "R0007",
    "reviewerFlagReason": flag.get("reason"),
    "oracleExact": body_json(row) == oracle_row,
    "entry": rec["entry"], "si": rec["si"], "oi": rec["oi"],
    "field": rec["field"],
    "slotField": "AttributionNote",
    "correctedLaw": ("B3' = PRE slot AttributionNote contains `before` "
                     "exactly once AND POST slot == PRE slot with "
                     "`before`->`after` replaced once AND `after` occurs "
                     "exactly once in the POST slot"),
    "beforeCountInPreSlot": pre_slot["AttributionNote"].count(before),
    "afterCountInPostSlot": post_slot["AttributionNote"].count(after),
    "replayEqualsPost": (pre_slot["AttributionNote"]
                         .replace(before, after, 1)
                         == post_slot["AttributionNote"]),
    "before": before,
    "after": after,
    "preSlotAttributionNote": pre_slot["AttributionNote"],
    "postSlotAttributionNote": post_slot["AttributionNote"],
    "slotOtherwiseUnchanged": all(
        pre_slot[k] == post_slot[k] for k in pre_slot
        if k not in ("AttributionNote",)
    ) and set(pre_slot) == set(post_slot),
}
assert evidence["oracleExact"], "row is not oracle-exact"
assert evidence["beforeCountInPreSlot"] == 1
assert evidence["afterCountInPostSlot"] == 1
assert evidence["replayEqualsPost"]
assert evidence["slotOtherwiseUnchanged"]

out_path = HERE / "r2-ruling-bytes-20260903.json"
out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2)
                    + "\n", encoding="utf-8", newline="")
print(json.dumps({k: evidence[k] for k in (
    "rowId", "oracleExact", "beforeCountInPreSlot",
    "afterCountInPostSlot", "replayEqualsPost",
    "slotOtherwiseUnchanged")}, indent=2))
