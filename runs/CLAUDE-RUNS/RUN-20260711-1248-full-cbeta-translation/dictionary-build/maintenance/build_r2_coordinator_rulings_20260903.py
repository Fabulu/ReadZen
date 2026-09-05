#!/usr/bin/env python3
"""Write the R2 r1 coordinator rulings (run AFTER
probe_r2_ruling_bytes_20260903.py, which produces the byte evidence).

Single flag to rule: R0007@reviewer2, law B3. Ruling: REFUTED with
bytes — the row is oracle-exact and satisfies the corrected law B3'
(find-once inside the occurrence slot's AttributionNote); the defect
was the law's wording, which demanded full-string equality from a row
class whose before/after are anchored fragments by construction (same
class of law-wording artifact as R1c's A3). Product bytes unaffected.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ev = json.loads(
    (HERE / "r2-ruling-bytes-20260903.json").read_text(encoding="utf-8"))
adj = json.loads(
    (HERE / "r2-blind-r1-adjudication-20260903.json").read_text("utf-8"))
flags = adj["honestFlags"]
if len(flags) != 1 or flags[0]["rowId"] != "R0007":
    raise SystemExit(f"expected exactly one honest flag R0007, got "
                     f"{[(f['rowId'], f['reviewer']) for f in flags]}")
flag = flags[0]
if not all((ev["oracleExact"], ev["beforeCountInPreSlot"] == 1,
            ev["afterCountInPostSlot"] == 1, ev["replayEqualsPost"],
            ev["slotOtherwiseUnchanged"])):
    raise SystemExit("ruling bytes did not verify — refuse to refute")

rulings = [{
    "rowId": flag["rowId"],
    "reviewer": flag["reviewer"],
    "ruling": "refuted",
    "refutedWithBytes": {
        "oracleExact": ev["oracleExact"],
        "entry": ev["entry"], "si": ev["si"], "oi": ev["oi"],
        "slotField": ev["slotField"],
        "lawDefect": (
            "Law B3 as stated demanded full-string equality between the "
            "slot's AttributionNote and the row's before/after; every "
            "prose-rewrite row in this lane carries FIND-ONCE anchored "
            "fragments by construction (B1/B2 are the governing laws). "
            "Corrected law B3': PRE slot AttributionNote contains "
            "`before` exactly once AND POST slot == PRE slot with "
            "`before`->`after` replaced once AND `after` occurs exactly "
            "once in the POST slot. All three verified; the slot is "
            "otherwise byte-unchanged."),
        "evidence": (
            "probe_r2_ruling_bytes_20260903.py -> r2-ruling-bytes-"
            "20260903.json: row payload == engine+materials oracle; "
            "before x1 in PRE slot; replay(before->after) == POST slot "
            "exactly; after x1 in POST slot; no other slot field "
            "changed. Reviewer 1 hit the same law fork and documented "
            "it in notes without flagging."),
    },
    "reviewerFlagReason": flag.get("reason"),
}]

out = {
    "schemaVersion": "r2-blind-r1-coordinator-rulings",
    "round": "r1",
    "ruledOn": [f"{r['rowId']}@{r['reviewer']}" for r in rulings],
    "rulings": rulings,
}
(HERE / "r2-blind-r1-coordinator-rulings-20260903.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(json.dumps({"ruledOn": out["ruledOn"],
                  "rulings": [r["ruling"] for r in rulings]}, indent=2))
