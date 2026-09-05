#!/usr/bin/env python3
"""Probe: restore the 35 A1 worklist terms files to the clone pre-state.

AMENDMENT 3 cycle — the first engine --apply wrote the r1 worksheet's
bytes; the corrected worksheet must re-apply from a clean pre-state
(the engine asserts terms == canon(clone pre-state) before writing).
Restores canon(clone bytes) for each worklist entry and verifies every
sha equals the a1-pre-terms-shas-20260903.json snapshot.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent

_spec = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

worklist = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8")
)["worklist"]
snap = json.loads(
    (HERE / "a1-pre-terms-shas-20260903.json").read_text(encoding="utf-8"))

by_id = eng.clone_state()
bad = []
for eid in worklist:
    p = BUILD / "terms" / eid / "entry.v2.json"
    p.write_text(eng.canon(by_id[eid]), encoding="utf-8", newline="")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if sha != snap["shas"][eid]:
        bad.append(eid)
if bad:
    raise SystemExit(f"restore sha mismatch: {bad}")
print(f"restored {len(worklist)} terms files to clone pre-state; "
      f"all shas == pre-snapshot")
