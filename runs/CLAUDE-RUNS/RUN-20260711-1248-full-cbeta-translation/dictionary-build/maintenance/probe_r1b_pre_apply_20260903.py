#!/usr/bin/env python3
"""Pre-apply validation for R1b (writes nothing to terms/).

Validates the census model against the REAL audits before the engine is
allowed to write (S1b probe pattern, R1b expectations):

  1. full-tree law: every terms/<eid>/entry.v2.json byte-equals
     canon(clone@87a6975); snapshot all shas (off-worklist gate
     baseline: maintenance/r1b-pre-terms-shas-20260903.json).
  2. materialize the engine's POST state for the engine-derived cohort
     (43 entries) into a scratch directory (clone bytes transformed;
     each entry keeps its WORK.md / evidence.draft.json siblings) and
     run the REAL audit_attribution over it. Expected: ZERO rows on 42
     entries; exactly the 2 documented pre-existing performer rows on
     t_b97e19fa54b2 (坐堂 s1 o2/o3 — SPEC §1 residuals, out of scope).
  3. depth PRE/POST (PRE = clone bytes + siblings, POST = transformed
     bytes + siblings): hardPass true->false = 0 (blocks). Movement IS
     expected here (unlike S1b): the census predicts below-floor
     surfacing and flag clears on removed occurrences. The probe prints
     the full movement; the gates script asserts movement == the frozen
     REAL-AUDIT set. Correction (AM2, recorded after the run): the
     census's flat-6/15-entry prediction was WRONG — the real audit
     (entry-level tiered representative floor) surfaces
     below-frequency-floor on 20 entries, so this probe's advisory
     census cross-check exits 1 on a lawful run; its attribution and
     depth-pair outputs are what the gates consume.

Outputs maintenance/r1b-pre-attribution-20260903.json (+ depth pair);
prints verdict.
"""
import collections
import copy
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
    "r1b_eng", HERE / "r1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

RESIDUAL_ENTRY = "t_b97e19fa54b2"      # 坐堂 — documented o2/o3 rows
census = json.loads((HERE / "r1b-census-20260903.json")
                    .read_text(encoding="utf-8"))
below_new = set(census["summary"]["belowFloorNew"])

clone_by_id = eng.clone_state()          # pins 87a6975 + clean

# ---- 1. full-tree law + sha snapshot ------------------------------------
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
(HERE / "r1b-pre-terms-shas-20260903.json").write_text(
    json.dumps({"schemaVersion": "r1b-pre-terms-shas",
                "cloneHead": eng.CLONE_HEAD_PIN, "entries": len(shas),
                "shas": shas}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")

# ---- 2+3. POST materialization + audits ---------------------------------
worklist = eng.derive(clone_by_id)[0]
print(f"cohort: {len(worklist)} entries")
snapshot = {eid: copy.deepcopy(clone_by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)
print(f"engine: {len(records)} records, "
      f"classes={sorted({r['class'] for r in records})}")

PRE_DIR = HERE / "r1b-pre-entries-20260903"
POST_DIR = HERE / "r1b-post-entries-20260903"
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

attr = run_audit(HERE / "r1b-pre-attribution-20260903.json", post_paths)
rows = attr.get("failures", [])
rows_by_entry = collections.defaultdict(list)
for r in rows:
    em = eng_re = None
    import re as _re
    em = _re.search(r"t_[0-9a-f]{12}", str(r.get("entry", "")))
    rows_by_entry[em.group(0) if em else "?"].append(r)
print(f"POST attribution rows on cohort: {len(rows)}")
for eid, rr in sorted(rows_by_entry.items()):
    for r in rr:
        print("  ROW:", json.dumps(r, ensure_ascii=False)[:220])
unexpected_attr = {e: rr for e, rr in rows_by_entry.items()
                  if e != RESIDUAL_ENTRY}
ok_attr = (not unexpected_attr
           and len(rows_by_entry.get(RESIDUAL_ENTRY, [])) == 2)

pre_depth = run_depth(HERE / "r1b-pre-depth-20260903.json", pre_paths)
post_depth = run_depth(HERE / "r1b-post-depth-20260903.json", post_paths)


def mset(flags):
    return collections.Counter(
        json.dumps(x, ensure_ascii=False, sort_keys=True) for x in flags)


regressed, improved, movement = [], [], {}
for eid in worklist:
    a, b = pre_depth[eid], post_depth[eid]
    if a["hardPass"] != b["hardPass"]:
        (improved if b["hardPass"] else regressed).append(eid)
    cleared = mset(a["hardFlags"]) - mset(b["hardFlags"])
    surfaced = mset(b["hardFlags"]) - mset(a["hardFlags"])
    cleared_r = mset(a["reviewFlags"]) - mset(b["reviewFlags"])
    surfaced_r = mset(b["reviewFlags"]) - mset(a["reviewFlags"])
    if cleared or surfaced or cleared_r or surfaced_r:
        movement[eid] = {
            "cleared": [json.loads(x) for x in cleared.elements()],
            "surfaced": [json.loads(x) for x in surfaced.elements()],
            "clearedReview": [json.loads(x) for x in cleared_r.elements()],
            "surfacedReview": [json.loads(x) for x in surfaced_r.elements()],
        }
print(f"depth: improved {len(improved)}, regressed {len(regressed)}, "
      f"entriesWithMovement {len(movement)}")
for eid in regressed:
    print("  REGRESSED:", eid, pre_depth[eid]["hardFlags"], "->",
          post_depth[eid]["hardFlags"])

# census cross-check: every belowFloorNew entry must surface a
# below-floor-ish flag; entries NOT in belowFloorNew must not
surfaced_below = {e for e, m in movement.items()
                  if any("floor" in json.dumps(f) for f in m["surfaced"])}
print(f"below-floor surfaced: {len(surfaced_below)}; "
      f"census belowFloorNew: {len(below_new)}; "
      f"missing={sorted(below_new - surfaced_below)} "
      f"extra={sorted(surfaced_below - below_new)}")
ok_depth = not regressed and surfaced_below == below_new

ok = ok_attr and ok_depth
print(json.dumps({"ok": ok, "postRows": len(rows),
                  "unexpectedAttrEntries": sorted(unexpected_attr),
                  "residualRows": len(rows_by_entry.get(RESIDUAL_ENTRY, [])),
                  "depthRegressed": regressed,
                  "belowFloorSurfaced": len(surfaced_below),
                  "censusBelowFloorNew": len(below_new)},
                 ensure_ascii=False))
raise SystemExit(0 if ok else 1)
