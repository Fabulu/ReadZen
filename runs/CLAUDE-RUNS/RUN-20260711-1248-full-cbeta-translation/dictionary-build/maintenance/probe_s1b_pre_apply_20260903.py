#!/usr/bin/env python3
"""Pre-apply validation for S1-b/R (writes nothing to terms/).

Validates the census model against the REAL audit before the engine is
allowed to write:

  1. full-tree law: every terms/<eid>/entry.v2.json byte-equals
     canon(clone@5f0e127) — the census and engine see the same bytes the
     clone holds; snapshot all shas (gate 7 baseline:
     maintenance/s1b-pre-terms-shas-20260903.json).
  2. materialize the engine's POST state for the engine-derived cohort into a
     scratch directory (clone bytes transformed; each entry keeps its
     WORK.md / evidence.draft.json siblings so the depth audit sees the
     real worksheet context) and run the REAL audit_attribution over it:
     ZERO failure rows of any kind expected on the cohort.
  3. depth PRE/POST: PRE = clone bytes + siblings, POST = transformed
     bytes + siblings; hardPass true->false blocks.

Outputs maintenance/s1b-pre-attribution-20260903.json (+ depth pair);
prints verdict. Exit 0 iff all three hold.
"""
import hashlib
import importlib.util
import io
import json
import runpy
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))

_spec = importlib.util.spec_from_file_location(
    "s1b_eng", HERE / "s1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

clone_by_id = eng.clone_state()          # pins 5f0e127 + clean

# ---- 1. full-tree law + sha snapshot -----------------------------------------
shas = {}
drift = []
for p in sorted((BUILD / "terms").glob("*/entry.v2.json")):
    eid = p.parent.name
    raw = p.read_text(encoding="utf-8-sig")
    shas[eid] = hashlib.sha256(p.read_bytes()).hexdigest()
    if eid in clone_by_id and raw != eng.canon(clone_by_id[eid]):
        drift.append(eid)
print(f"terms entries: {len(shas)}; clone-drift: {len(drift)}")
if drift:
    raise SystemExit(f"ABORT: terms != canon(clone) for {drift[:5]}")
(HERE / "s1b-pre-terms-shas-20260903.json").write_text(
    json.dumps({"schemaVersion": "s1b-pre-terms-shas",
                "cloneHead": eng.CLONE_HEAD_PIN, "entries": len(shas),
                "shas": shas}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")

# ---- 2+3. POST materialization + audits --------------------------------------
import copy  # noqa: E402
worklist = eng.derive(clone_by_id)[0]
print(f"cohort: {len(worklist)} entries")
snapshot = {eid: copy.deepcopy(clone_by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)
print(f"engine: {len(records)} records, "
      f"classes={sorted({r['class'] for r in records})}")

PRE_DIR = HERE / "s1b-pre-entries-20260903"
POST_DIR = HERE / "s1b-post-entries-20260903"
for d in (PRE_DIR, POST_DIR):
    if d.exists():
        shutil.rmtree(d)
for eid in worklist:
    for d, text in ((PRE_DIR, eng.canon(clone_by_id[eid])),
                    (POST_DIR, out[eid])):
        e = d / eid
        e.mkdir(parents=True)
        (e / "entry.v2.json").write_text(text, encoding="utf-8", newline="")
        for sib in ("WORK.md", "evidence.draft.json"):
            src = BUILD / "terms" / eid / sib
            if src.is_file():
                (e / sib).write_text(src.read_text(encoding="utf-8"),
                                     encoding="utf-8", newline="")


def run_audit(out_path: Path, target_paths: list[str]) -> dict:
    sys.argv = ["audit_attribution.py", "--json", "--output", str(out_path),
                *target_paths]
    _buf = io.StringIO()
    try:
        with redirect_stdout(_buf):
            runpy.run_path(str(BUILD / "audit_attribution.py"),
                           run_name="__main__")
    except SystemExit:
        pass
    return json.loads(out_path.read_text(encoding="utf-8"))


def run_depth(out_path: Path, target_paths: list[str]) -> dict:
    sys.argv = ["audit_depth_sense.py", "--report", str(out_path),
                "--paths", *target_paths]
    _buf = io.StringIO()
    try:
        with redirect_stdout(_buf):
            runpy.run_path(str(BUILD / "audit_depth_sense.py"),
                           run_name="__main__")
    except SystemExit:
        pass
    return json.loads(out_path.read_text(encoding="utf-8"))["results"]


post_paths = [str(POST_DIR / e / "entry.v2.json") for e in worklist]
pre_paths = [str(PRE_DIR / e / "entry.v2.json") for e in worklist]

attr = run_audit(HERE / "s1b-pre-attribution-20260903.json", post_paths)
rows = attr.get("failures", [])
print(f"POST attribution rows on cohort: {len(rows)}")
for r in rows[:10]:
    print("  ROW:", json.dumps(r, ensure_ascii=False)[:220])

import collections  # noqa: E402
pre_depth = run_depth(HERE / "s1b-pre-depth-20260903.json", pre_paths)
post_depth = run_depth(HERE / "s1b-post-depth-20260903.json", post_paths)


def mset(flags):
    return collections.Counter(
        json.dumps(x, ensure_ascii=False, sort_keys=True) for x in flags)


regressed, improved, flag_diffs = [], [], []
for eid in worklist:
    a, b = pre_depth[eid], post_depth[eid]
    if a["hardPass"] != b["hardPass"]:
        (improved if b["hardPass"] else regressed).append(eid)
    elif (mset(a["hardFlags"]) != mset(b["hardFlags"])
          or mset(a["reviewFlags"]) != mset(b["reviewFlags"])):
        flag_diffs.append(eid)
print(f"depth: improved {len(improved)}, regressed {len(regressed)}, "
      f"flagDiffs {len(flag_diffs)}")
for eid in regressed:
    print("  REGRESSED:", eid, pre_depth[eid]["hardFlags"], "->",
          post_depth[eid]["hardFlags"])

ok = not rows and not regressed
print(json.dumps({"ok": ok, "postRows": len(rows),
                  "depthRegressed": regressed}, ensure_ascii=False))
raise SystemExit(0 if ok else 1)
