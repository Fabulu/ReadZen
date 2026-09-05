#!/usr/bin/env python3
"""Probe: A1 pre-apply snapshot (MUST run BEFORE engine --apply).

Captures the POST-side comparison baselines the gates need but can no
longer compute after terms bytes change:

  1. sha256 of EVERY terms/*/entry.v2.json in the tree
     -> a1-pre-terms-shas-20260903.json (off-worklist protection law)
  2. fresh full-fleet attribution audit on current bytes
     -> a1-fleet-attribution-pre-20260903.json (fleet regression law PRE)

Plus the apply preconditions asserted up front (so --apply cannot land on
drifted bytes): clone HEAD pin + clean status, and terms bytes ==
canon(clone bytes) for all 35 worklist entries.

Sanity law: the fresh PRE's failure rows restricted to the 35 worklist
entries must equal the worklist details rows exactly (bytes unchanged
since probe_a1_worklist_20260902.py ran) — kinds and details included.
"""
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent

_spec = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

details = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8"))
worklist = details["worklist"]
assert len(worklist) == 35

# ---- apply preconditions -----------------------------------------------------
by_id = eng.clone_state()  # pins HEAD 20c9011 + clean, else SystemExit
drift = []
for eid in worklist:
    cur = (BUILD / "terms" / eid / "entry.v2.json").read_text(encoding="utf-8")
    if cur != eng.canon(by_id[eid]):
        drift.append(eid)
if drift:
    raise SystemExit(f"terms bytes != canon(clone) for {drift[:5]} "
                     f"({len(drift)}) — refuse to snapshot/apply")
print(f"precondition: clone pinned + clean; terms == canon(clone) for all "
      f"{len(worklist)}")

# ---- 1. full terms-tree sha snapshot ------------------------------------------
shas = {}
for p in sorted((BUILD / "terms").glob("*/entry.v2.json")):
    shas[p.parent.name] = hashlib.sha256(
        p.read_bytes()).hexdigest()
(HERE / "a1-pre-terms-shas-20260903.json").write_text(
    json.dumps({"schemaVersion": "a1-pre-terms-shas",
                "entries": len(shas),
                "shas": shas},
               ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8", newline="")
print(f"terms-tree snapshot: {len(shas)} entry.v2.json files hashed")

# ---- 2. fresh full-fleet attribution audit (default scope: STATUS=done) -------
out_path = HERE / "a1-fleet-attribution-pre-20260903.json"
proc = subprocess.run(
    [sys.executable, "-X", "utf8", str(BUILD / "audit_attribution.py"),
     "--json", f"--output={out_path}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
if proc.returncode not in (0, 1):
    raise SystemExit(f"fleet audit crashed rc={proc.returncode}: "
                     f"{proc.stderr[-1500:]}")
report = json.loads(out_path.read_text(encoding="utf-8"))

ID_RE = re.compile(r"t_[0-9a-f]{12}")
fleet_pairs = set()
worklist_rows = set()
for f in report.get("failures", []):
    m = ID_RE.search(str(f.get("entry", "")))
    if not m:
        continue
    eid = m.group(0)
    kind = f["kind"]
    fleet_pairs.add((eid, kind))
    if eid in set(worklist):
        worklist_rows.add((eid, kind, str(f.get("detail", ""))))

# sanity law: PRE rows on the 35 == the details rows (kind+detail exact)
detail_rows = {(eid, kind, det)
               for eid, rows in details["stillFailing"].items()
               for kind, det in rows}
if worklist_rows != detail_rows:
    only_pre = sorted(worklist_rows - detail_rows)[:6]
    only_details = sorted(detail_rows - worklist_rows)[:6]
    raise SystemExit(f"fresh PRE rows on the 35 != worklist details "
                     f"(pre-only {only_pre}; details-only {only_details}; "
                     f"|pre|={len(worklist_rows)} "
                     f"|details|={len(detail_rows)})")

kind_counts = {}
for eid, kind, _ in detail_rows:
    kind_counts[kind] = kind_counts.get(kind, 0) + 1
print(json.dumps({
    "fleetFailingPairs": len(fleet_pairs),
    "fleetFailureRows": len(report.get("failures", [])),
    "worklistRows": len(worklist_rows),
    "kindsOnWorklist": kind_counts,
    "sanityLaw": "PASS (fresh PRE rows == worklist details rows)",
}, ensure_ascii=False, indent=2))
