#!/usr/bin/env python3
"""R2 pre-apply: snapshot the pre-state (bytes + shas + PRE audits) of
the three products at clone HEAD 145b090, before r2_transform --apply.

Outputs (maintenance/):
  r2-pre-entries-20260903/<eid>/entry.v2.json   pre bytes (blind round)
  r2-pre-terms-shas-20260903.json               sha256 of every terms file
  r2-pre-attribution-pre-20260903.json          audit_attribution PRE (3)
  r2-pre-depth-pre-20260903.json                audit_depth_sense PRE (3)
"""
from __future__ import annotations

import hashlib
import io
import json
import runpy
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
TERMS = BUILD / "terms"
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
CLONE_HEAD_PIN = "145b090"
COHORT = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
PRE_DIR = HERE / "r2-pre-entries-20260903"
import subprocess  # noqa: E402

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD {head[:7]} != pin {CLONE_HEAD_PIN}")
dirty = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                       capture_output=True, text=True).stdout.splitlines()
if dirty:
    raise SystemExit(f"clone dirty: {dirty[:5]}")

canon = json.dumps
PRE_DIR.mkdir(exist_ok=True)
for eid in COHORT:
    dst = PRE_DIR / eid
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copy2(TERMS / eid / "entry.v2.json", dst / "entry.v2.json")

shas = {}
for p in sorted(TERMS.glob("*/entry.v2.json")):
    shas[p.parent.name] = hashlib.sha256(
        p.read_bytes()).hexdigest()
(HERE / "r2-pre-terms-shas-20260903.json").write_text(
    json.dumps(shas, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(f"pre snapshot: {len(shas)} terms files; "
      f"products {[e for e in COHORT]} copied")

paths = [str(TERMS / e / "entry.v2.json") for e in COHORT]

sys.argv = ["audit_attribution.py", "--json", "--output",
            str(HERE / "r2-pre-attribution-pre-20260903.json"), *paths]
buf = io.StringIO()
try:
    with redirect_stdout(buf):
        runpy.run_path(str(BUILD / "audit_attribution.py"),
                       run_name="__main__")
except SystemExit:
    pass
attr = json.loads(
    (HERE / "r2-pre-attribution-pre-20260903.json").read_text("utf-8"))
rows = attr.get("failures", [])
print(f"PRE attribution rows on products: {len(rows)}")
for r in rows[:10]:
    print("  PRE ROW:", r.get("kind"), str(r.get("detail"))[:120])

sys.argv = ["audit_depth_sense.py", "--report",
            str(HERE / "r2-pre-depth-pre-20260903.json"),
            "--paths", *paths]
buf = io.StringIO()
try:
    with redirect_stdout(buf):
        runpy.run_path(str(BUILD / "audit_depth_sense.py"),
                       run_name="__main__")
except SystemExit:
    pass
depth = json.loads(
    (HERE / "r2-pre-depth-pre-20260903.json").read_text("utf-8"))
res = depth.get("results") or {}
items = list(res.values()) if isinstance(res, dict) else list(res)
hard = [x for x in items if x.get("hardPass")]
print(f"PRE depth results: {len(items)}; hardPass true: {len(hard)}")
