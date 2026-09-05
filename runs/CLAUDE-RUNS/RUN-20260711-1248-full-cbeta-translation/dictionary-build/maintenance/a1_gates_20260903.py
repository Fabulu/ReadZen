#!/usr/bin/env python3
"""A1 lane gates (SPEC_A1_20260902.md §4 + AMENDMENTS 1–3).

Gates:
  1. audit_attribution over all 35 repaired terms entries == ZERO
     failure rows of any kind (the lane's own success law).
  2. depth PRE/POST per entry (PRE = clone bytes materialized with
     WORK.md/evidence.draft.json siblings, POST = terms bytes):
     hardPass true→false blocks; flag movement recorded.
  3. zc on the new claim anchor (ok, count==1, stored lbs == fresh) +
     the AMENDMENT 3 anchor-removal coverage law (removed kwic ⊆ a
     surviving occurrence's kwic; no ClaimAnchors left on the sense).
  4. determinism: engine re-run from fresh clone bytes produces
     byte-identical output (twice).
  5. confinement: canon(engine(clone)) == terms bytes for all 35, and
     the receipt's entryShas match the written bytes.
  6. independent path-scope byte-diff (C1's diff_paths, not the
     engine's flat()): changed paths ⊆ the AMENDMENT 1–2 scope; every
     entry has a non-empty diff.
  7. off-worklist protection: full terms-tree re-hash vs
     a1-pre-terms-shas-20260903.json — exactly the 35 changed.
  8. fleet regression: fresh full-fleet audit POST — zero rows on the
     35, failing (id, kind) pairs POST ⊆ PRE, resolved recorded.

Outputs maintenance/a1-gates-20260903.json. Exit 0 iff CLEAN.
"""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import io
import json
import re
import runpy
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402

TERMS = BUILD / "terms"
EXPECTED_COUNTS = {
    "muc-utterer": 83, "muc-verse-author": 8, "vague-reword": 17,
    "dangling-anchor": 1, "performer-context-row": 2,
    "performer-grammar-proof": 1, "anon-monk-restructure": 1,
    "grammar-evidence-repeat": 1, "reviewed-fields": 1, "anchor-remove": 1,
}

_spec = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

details = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8"))
worklist = details["worklist"]
assert len(worklist) == 35
wl_set = set(worklist)

receipt = json.loads(
    (HERE / "a1-edit-receipt-20260903.json").read_text(encoding="utf-8"))
problems: list[str] = []
if not receipt.get("applied"):
    problems.append("receipt not applied")
if receipt.get("products") != worklist:
    problems.append("receipt products != worklist")
if receipt.get("editClassCounts") != EXPECTED_COUNTS:
    problems.append(f"receipt classCounts {receipt.get('editClassCounts')} "
                    f"!= expected")
if len(receipt.get("editRecords", [])) != 116:
    problems.append(f"receipt editRecords {len(receipt.get('editRecords', []))}"
                    " != 116")

clone_by_id = eng.clone_state()  # pins HEAD + clean

report: dict = {"schemaVersion": "a1-gates", "lane": "A1",
                "cloneHead": eng.CLONE_HEAD_PIN, "products": len(worklist)}


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


# ---- gate 1: zero attribution failures on the 35 -----------------------------
post_paths = [str(TERMS / e / "entry.v2.json") for e in worklist]
attr35 = run_audit(HERE / "a1-gate-attribution-post-20260903.json", post_paths)
rows35 = attr35.get("failures", [])
if rows35:
    problems.append(f"gate1: {len(rows35)} failure rows remain on the 35: "
                    f"{rows35[:4]}")
report["attribution35"] = {"failureRows": len(rows35),
                           "kinds": sorted({r["kind"] for r in rows35})}
print(f"gate1 attribution on 35: {len(rows35)} failure rows")

# ---- gate 2: depth PRE/POST ---------------------------------------------------
PRE_DIR = HERE / "a1-gate-pre-entries-20260903"
if PRE_DIR.exists():
    shutil.rmtree(PRE_DIR)
for eid in worklist:
    d = PRE_DIR / eid
    d.mkdir(parents=True)
    (d / "entry.v2.json").write_text(eng.canon(clone_by_id[eid]),
                                     encoding="utf-8", newline="")
    for sib in ("WORK.md", "evidence.draft.json"):
        src = TERMS / eid / sib
        if src.is_file():
            (d / sib).write_text(src.read_text(encoding="utf-8"),
                                 encoding="utf-8", newline="")
pre_paths = [str(PRE_DIR / e / "entry.v2.json") for e in worklist]

pre_depth = run_depth(HERE / "a1-gate-depth-pre-20260903.json", pre_paths)
post_depth = run_depth(HERE / "a1-gate-depth-post-20260903.json", post_paths)


def mset(flags):
    return collections.Counter(
        json.dumps(x, ensure_ascii=False, sort_keys=True) for x in flags)


regressed, improved, flag_diffs = [], [], []
for eid in worklist:
    a, b = pre_depth[eid], post_depth[eid]
    if a["hardPass"] != b["hardPass"]:
        (improved if b["hardPass"] else regressed).append(
            {"id": eid, "hardFlagsBefore": a["hardFlags"],
             "hardFlagsAfter": b["hardFlags"]})
    elif (mset(a["hardFlags"]) != mset(b["hardFlags"])
          or mset(a["reviewFlags"]) != mset(b["reviewFlags"])):
        flag_diffs.append({"id": eid,
                           "hardFlags": [a["hardFlags"], b["hardFlags"]],
                           "reviewFlags": [a["reviewFlags"], b["reviewFlags"]]})
if regressed:
    problems.append(f"gate2: depth hardPass true->false on "
                    f"{[x['id'] for x in regressed]}")
report["depth"] = {"entries": len(worklist), "improved": improved,
                   "regressed": regressed, "flagDiffs": flag_diffs}
print(f"gate2 depth: improved {len(improved)}, regressed {len(regressed)}, "
      f"flagDiffs {len(flag_diffs)}")

# ---- gate 3: zc on the new anchor + anchor-removal coverage ------------------
zc_targets = []  # (label, anchor dict)
new_entry = json.loads((TERMS / "t_057cc9ea8755" / "entry.v2.json")
                       .read_text(encoding="utf-8-sig"))
zc_targets.append(("new-anchor t_057cc9ea8755",
                   new_entry["Senses"][0]["ClaimAnchors"][-1]))
# AMENDMENT 3 coverage law: the removed t_2e77bc793d0c a[0] kwic must be
# contained in a surviving occurrence's kwic (o1, same record/master)
removed_kwic = ("。雪竇因風吹火。傍指出一箇半箇。一箇兩箇千萬箇脫却籠頭卸角"
                "馱左轉右轉隨後來紫胡要打劉")
t2e77 = json.loads((TERMS / "t_2e77bc793d0c" / "entry.v2.json")
                   .read_text(encoding="utf-8-sig"))
holders = [o for o in t2e77["Senses"][0]["Occurrences"]
           if removed_kwic.lstrip("。、，") in str(o.get("Kwic") or "")]
if not (t2e77["Senses"][0].get("ClaimAnchors") is None and holders):
    problems.append("gate3: anchor-removal coverage fails (ClaimAnchors "
                    f"left: {t2e77['Senses'][0].get('ClaimAnchors')!r}; "
                    f"holders: {[h.get('MasterName') for h in holders]})")
zc_bad = 0
for label, anchor in zc_targets:
    v = zc.verify(anchor["RelPath"], anchor.get("Kwic") or "")
    if not (v.get("ok") and v.get("count") == 1):
        problems.append(f"gate3 zc {label}: {v}")
        zc_bad += 1
    elif (anchor.get("FromLb"), anchor.get("ToLb")) != (v["fromLb"], v["toLb"]):
        problems.append(f"gate3 lbs {label}: "
                        f"({anchor.get('FromLb')},{anchor.get('ToLb')}) != "
                        f"({v['fromLb']},{v['toLb']})")
        zc_bad += 1
report["zc"] = {"anchorsChecked": len(zc_targets), "bad": zc_bad}
print(f"gate3 zc: {len(zc_targets)} anchors, {zc_bad} bad")

# ---- gates 4+5: determinism + confinement ------------------------------------
by_id = dict(clone_by_id)
eng.clone_snapshot.clear()
import copy  # noqa: E402
eng.clone_snapshot.update(
    {eid: copy.deepcopy(clone_by_id[eid]) for eid in worklist})
out1, _ = eng.transform(by_id)
by_id2 = eng.clone_state()
eng.clone_snapshot.clear()
eng.clone_snapshot.update(
    {eid: copy.deepcopy(by_id2[eid]) for eid in worklist})
out2, _ = eng.transform(by_id2)
if out1 != out2:
    problems.append("gate4: engine nondeterministic")
conf_mismatch = []
for eid in worklist:
    written = (TERMS / eid / "entry.v2.json").read_text(encoding="utf-8")
    if out1[eid] != written:
        conf_mismatch.append(eid)
    if receipt["entryShas"][eid] != hashlib.sha256(
            written.encode("utf-8")).hexdigest():
        problems.append(f"gate5: receipt sha mismatch for {eid}")
if conf_mismatch:
    problems.append(f"gate5: canon(engine(clone)) != terms bytes for "
                    f"{conf_mismatch[:5]} ({len(conf_mismatch)})")
report["determinism"] = {"checked": 35, "nondeterministic": out1 != out2}
report["confinement"] = {"checked": 35, "mismatch": conf_mismatch}
print(f"gate4+5 determinism+confinement: mismatches {len(conf_mismatch)}")

# ---- gate 6: independent path-scope byte-diff ---------------------------------
def _join(parts: list[str]) -> str:
    out = ""
    for p in parts:
        out += p if p.startswith("[") else ("." + p if out else p)
    return out


def diff_paths(a, b, parts=None) -> set[str]:
    parts = parts or []
    out: set[str] = set()
    if type(a) is not type(b):
        return {_join(parts) or "<root>"}
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.add(_join(parts + [k]))
            else:
                out |= diff_paths(a[k], b[k], parts + [k])
    elif isinstance(a, list):
        if len(a) != len(b):
            out.add(_join(parts) + "<len>")
        for i in range(min(len(a), len(b))):
            out |= diff_paths(a[i], b[i], parts + [f"[{i}]"])
    elif a != b:
        out.add(_join(parts) or "<root>")
    return out


ALLOWED = (
    re.compile(r"^Senses\[\d+\]\.(?:Explanation|Note|ClaimAnchors)"
               r"(?:[.\[]|$)"),
    re.compile(r"^Senses\[\d+\]\.Occurrences\[\d+\]\."
               r"(?:ContextMasters|ContextActors|ActorAttribution|"
               r"AttributionNote|GrammarEvidence|MasterName)"
               r"(?:[.\[]|$)"),
)
escaped_all, empty_all = [], []
changed_path_counts = {}
# fresh clone bytes: gates 4+5 mutated the dicts shared with clone_by_id
clone_fresh = eng.clone_state()
for eid in worklist:
    post_obj = json.loads((TERMS / eid / "entry.v2.json")
                          .read_text(encoding="utf-8-sig"))
    actual = diff_paths(clone_fresh[eid], post_obj)
    changed_path_counts[eid] = len(actual)
    if not actual:
        empty_all.append(eid)
    for p in actual:
        # a <len> marker on a scoped LIST path (e.g. ContextMasters<len>)
        # is the append itself — in scope iff the stripped path matches
        q = p[:-len("<len>")] if p.endswith("<len>") else p
        if not any(rx.search(q) for rx in ALLOWED):
            escaped_all.append(f"{eid}: {p}")
if escaped_all:
    problems.append(f"gate6: diff escaped allowed paths: "
                    f"{escaped_all[:6]} ({len(escaped_all)})")
if empty_all:
    problems.append(f"gate6: entries with empty diff: {empty_all}")
report["byteDiff"] = {"escaped": escaped_all, "empty": empty_all,
                      "changedPathsPerEntry": changed_path_counts}
print(f"gate6 byte-diff: escaped {len(escaped_all)}, empty {len(empty_all)}")

# ---- gate 7: off-worklist protection ------------------------------------------
pre_shas = json.loads(
    (HERE / "a1-pre-terms-shas-20260903.json").read_text(encoding="utf-8"))
now_shas = {}
for p in sorted(TERMS.glob("*/entry.v2.json")):
    now_shas[p.parent.name] = hashlib.sha256(p.read_bytes()).hexdigest()
if set(now_shas) != set(pre_shas["shas"]):
    problems.append("gate7: terms-tree entry set changed "
                    f"(+{sorted(set(now_shas) - set(pre_shas['shas']))[:3]} "
                    f"-{sorted(set(pre_shas['shas']) - set(now_shas))[:3]})")
changed = {e for e in now_shas
           if now_shas[e] != pre_shas["shas"].get(e)}
if changed != wl_set:
    problems.append(f"gate7: changed entries != worklist: extra "
                    f"{sorted(changed - wl_set)[:5]}, missing "
                    f"{sorted(wl_set - changed)[:5]}")
report["offWorklist"] = {"entriesBefore": pre_shas["entries"],
                         "entriesNow": len(now_shas),
                         "changed": sorted(changed),
                         "changedIsExactlyWorklist": changed == wl_set}
print(f"gate7 off-worklist: {len(now_shas)} entries, changed "
      f"{len(changed)} == worklist: {changed == wl_set}")

# ---- gate 8: fleet regression --------------------------------------------------
fleet_out = HERE / "a1-fleet-attribution-post-20260903.json"
proc = subprocess.run(
    [sys.executable, "-X", "utf8", str(BUILD / "audit_attribution.py"),
     "--json", f"--output={fleet_out}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
if proc.returncode not in (0, 1):
    problems.append(f"gate8: fleet audit crashed rc={proc.returncode}: "
                    f"{proc.stderr[-800:]}")
else:
    post = json.loads(fleet_out.read_text(encoding="utf-8"))
    pre = json.loads(
        (HERE / "a1-fleet-attribution-pre-20260903.json")
        .read_text(encoding="utf-8"))

    def rows(artifact):
        return [(re.search(r"t_[0-9a-f]{12}", str(f.get("entry", ""))).group(0),
                 f["kind"], str(f.get("detail", "")))
                for f in artifact.get("failures", [])
                if re.search(r"t_[0-9a-f]{12}", str(f.get("entry", "")))]

    pre_rows, post_rows = rows(pre), rows(post)
    rows_on_wl = [r for r in post_rows if r[0] in wl_set]
    if rows_on_wl:
        problems.append(f"gate8: {len(rows_on_wl)} failure rows on worklist "
                        f"entries POST: {rows_on_wl[:4]}")
    pre_pairs = {(e, k) for e, k, _ in pre_rows}
    post_pairs = {(e, k) for e, k, _ in post_rows}
    new_pairs = post_pairs - pre_pairs
    if new_pairs:
        problems.append(f"gate8: newly-failing fleet pairs: "
                        f"{sorted(new_pairs)[:6]} ({len(new_pairs)})")
    resolved_pairs = pre_pairs - post_pairs
    report["fleet"] = {
        "preFailingPairs": len(pre_pairs),
        "postFailingPairs": len(post_pairs),
        "newlyFailingPairs": sorted(new_pairs),
        "resolvedPairs": sorted(resolved_pairs),
        "postRowsOnWorklist": len(rows_on_wl),
    }
    print(f"gate8 fleet: pre {len(pre_pairs)} -> post {len(post_pairs)} "
          f"pairs; newly {len(new_pairs)}; resolved {len(resolved_pairs)}; "
          f"rows on worklist POST {len(rows_on_wl)}")

report["verdict"] = "CLEAN" if not problems else "INVESTIGATE"
report["problems"] = problems
(HERE / "a1-gates-20260903.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(json.dumps({"verdict": report["verdict"], "problems": problems},
                 ensure_ascii=False, indent=2))
sys.exit(0 if not problems else 1)
