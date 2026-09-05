#!/usr/bin/env python3
"""R1b lane gates (SPEC_R1b_20260903.md §4 + AMENDMENTS 1-2).

Gates (all must be CLEAN; any failure blocks the lane):
  1. audit_attribution over the 43 repaired terms entries: ZERO rows on
     42 entries; on t_b97e19fa54b2 (坐堂) exactly the 2 documented
     pre-existing performer rows (kind narrated_action_performer_
     missing), DERIVED: PRE fleet rows on the entry minus rows on
     removed occurrences, renumbered through the removal (PRE s1 o2/o3
     -> POST s1 o1/o2 after o1's removal) — SPEC §1 residuals, out of
     scope.
  2. depth PRE/POST (PRE = clone bytes + siblings, POST = terms bytes):
     hardPass true->false = 0; flag movement must equal the lawful
     expected set EXACTLY —
       cleared invalid-kwic-anchor == the 46 removal sites
         (senseIndex/occurrenceIndex 0-based, NOT_IN_ALLOWLIST),
       cleared source-not-in-corpus-manifest == the audit's OWN PRE
         flags whose relPath is retired (firing law = deployment-class
         representatives, audit_depth_sense.py:648-667 — a retired
         occurrence that is a non-representative class member never
         fired PRE and clears nothing); non-retired PRE flags of that
         kind must SURVIVE,
       surfaced == below-frequency-floor on exactly the 20 frozen
         entries (the audit's entry-level tiered floor — SPEC AM2),
       review flags: no movement at all.
  3. removal coverage: per receipt record — post sense Occurrences ==
     pre minus exactly the removed rows (parsed-JSON equality against
     the RelPath filter law); senses never empty; the ONE rewritten
     Note (t_50d75aeeeef1 s1) satisfies the count sentence against
     live POST counts (find-once, N/M == live).
  4. determinism: engine re-run twice from fresh clone bytes is
     byte-identical.
  5. confinement: canon(engine(clone)) == terms bytes for all 43;
     receipt entryShas match the written bytes.
  6. independent path-scope byte-diff (diff_paths, not the engine's
     flat()): changed paths ⊆ Senses[i].Occurrences everywhere, plus
     exactly one Senses[0].Note on t_50d75aeeeef1; every entry has a
     non-empty diff.
  7. off-worklist protection: full terms-tree re-hash vs
     r1b-pre-terms-shas-20260903.json — exactly the 43 changed.
  8. fleet regression: fresh full-fleet audit POST — failing
     (entry,kind) pairs POST ⊆ PRE; the 2 坐堂 residual rows survive;
     resolved recorded; no rows on the other 42 worklist entries.

Outputs maintenance/r1b-gates-20260903.json. Exit 0 iff CLEAN.
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

TERMS = BUILD / "terms"
RESIDUAL_ENTRY = "t_b97e19fa54b2"          # 坐堂 — documented o2/o3 rows
RESIDUAL_KIND = "narrated_action_performer_missing"
NOTE_ENTRY = "t_50d75aeeeef1"
BELOW_FLOOR_FROZEN = [                     # SPEC AM2 (real-audit law)
    "t_022d58242948", "t_0c53a5a2243b", "t_3b9857d1cc19",
    "t_50d75aeeeef1", "t_5ab995298e4e", "t_9ba11d160033",
    "t_a5ffef8b3f2d", "t_b97e19fa54b2", "t_c945c2cc0e79",
    "t_cf2b777134bb", "t_d26799ff3ae1", "t_d7725cb0c8c0",
    "t_dc24f92ead78", "t_e9adcb470950", "t_ea85b794ca42",
    "t_ef5beb628603", "t_f0cb4dcfc70c", "t_f26addce7844",
    "t_f5e1fe96407c", "t_fe03a2a24e00",
]
EXPECTED_ENTRIES = 43
EXPECTED_COUNTS = {"occ-remove-retired": 46, "note-count-rewrite": 1}

_spec = importlib.util.spec_from_file_location(
    "r1b_eng", HERE / "r1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)
RETIRED = eng.RETIRED

receipt = json.loads(
    (HERE / "r1b-edit-receipt-20260903.json").read_text(encoding="utf-8"))
worklist = receipt["products"]
problems: list[str] = []
if not receipt.get("applied"):
    problems.append("receipt not applied")
if len(worklist) != EXPECTED_ENTRIES:
    problems.append(f"receipt products {len(worklist)} != {EXPECTED_ENTRIES}")
if receipt.get("editClassCounts") != EXPECTED_COUNTS:
    problems.append(f"receipt classCounts {receipt.get('editClassCounts')} "
                    f"!= expected {EXPECTED_COUNTS}")
if len(receipt.get("editRecords", [])) != 47:
    problems.append(f"receipt editRecords "
                    f"{len(receipt.get('editRecords', []))} != 47")

clone_by_id = eng.clone_state()  # pins 87a6975 + clean

# removal sites by entry (used by gates 1 and 3)
removal_by_entry: dict[str, dict[int, list[int]]] = {}
for rec in receipt["editRecords"]:
    if rec["class"] == "occ-remove-retired":
        removal_by_entry.setdefault(rec["entry"], {}).setdefault(
            rec["si"], []).append(rec["oi"])

report: dict = {"schemaVersion": "r1b-gates", "lane": "R1b",
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


# ---- gate 1: attribution POST (2 documented residuals only) ------------------
post_paths = [str(TERMS / e / "entry.v2.json") for e in worklist]
attr43 = run_audit(HERE / "r1b-gate-attribution-post-20260903.json",
                   post_paths)
rows43 = attr43.get("failures", [])
rows_by_entry = collections.defaultdict(list)
for r in rows43:
    m = re.search(r"t_[0-9a-f]{12}", str(r.get("entry", "")))
    rows_by_entry[m.group(0) if m else "?"].append(r)
bad_rows = {e: rr for e, rr in rows_by_entry.items() if e != RESIDUAL_ENTRY}

# expected POST residual rows: PRE fleet rows on the entry, minus rows
# on removed occurrences, renumbered through the removal (occurrences
# come first in the audit's merged row counter, so post_oi =
# pre_oi - #{removed ois < pre_oi} holds under both numbering laws)
removed_for_residual = {
    si: sorted(ois) for si, ois in removal_by_entry.get(
        RESIDUAL_ENTRY, {}).items()}
pre_fleet = json.loads(
    (HERE / "s1b-fleet-attribution-post-20260903.json")
    .read_text(encoding="utf-8"))
expected_residual = set()
for f in pre_fleet.get("failures", []):
    em = re.search(r"t_[0-9a-f]{12}", str(f.get("entry", "")))
    if (not em or em.group(0) != RESIDUAL_ENTRY
            or f.get("kind") != RESIDUAL_KIND):
        continue
    m = re.match(r"^.+? s(?P<si>\d+) o(?P<oi>\d+)(?:[ :]|$)",
                 str(f.get("detail", "")))
    if not m:
        continue
    si, oi = int(m["si"]), int(m["oi"])
    if oi in removed_for_residual.get(si, []):
        continue                    # row on a removed occurrence: clears
    shift = sum(1 for r in removed_for_residual.get(si, []) if r < oi)
    expected_residual.add((f"s{si} o{oi - shift}", RESIDUAL_KIND))
actual_residual = set()
for r in rows_by_entry.get(RESIDUAL_ENTRY, []):
    m = re.match(r"^.+? (s\d+ o\d+)(?:[ :]|$)", str(r.get("detail", "")))
    actual_residual.add((m.group(1), r["kind"]) if m
                        else (str(r.get("detail", ""))[:24], r["kind"]))
resid_ok = (not bad_rows and actual_residual == expected_residual)
if bad_rows:
    problems.append(f"gate1: rows on non-residual entries: "
                    f"{[(e, [r['kind'] for r in rr]) for e, rr in bad_rows.items()][:4]}")
if not resid_ok and not bad_rows:
    problems.append(f"gate1: residual rows on {RESIDUAL_ENTRY} != expected "
                    f"{sorted(expected_residual)}: got "
                    f"{sorted(actual_residual)}")
report["attribution43"] = {"failureRows": len(rows43),
                           "kinds": sorted({r["kind"] for r in rows43}),
                           "expectedResidual": sorted(expected_residual),
                           "actualResidual": sorted(actual_residual),
                           "residualRowsOk": resid_ok}
print(f"gate1 attribution on 43: {len(rows43)} rows "
      f"({sorted(rows_by_entry)}), expected {sorted(expected_residual)}, "
      f"residualOk={resid_ok}")

# ---- gate 2: depth movement == expected set exactly ---------------------------
PRE_DIR = HERE / "r1b-gate-pre-entries-20260903"
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

pre_depth = run_depth(HERE / "r1b-gate-depth-pre-20260903.json", pre_paths)
post_depth = run_depth(HERE / "r1b-gate-depth-post-20260903.json", post_paths)


def mkey(f):
    return json.dumps(f, ensure_ascii=False, sort_keys=True)


# expected sets derived from clone bytes + receipt
removal_sites = collections.Counter()          # (eid, si0, oi0) 0-based
for rec in receipt["editRecords"]:
    if rec["class"] == "occ-remove-retired":
        removal_sites[(rec["entry"], rec["si"] - 1, rec["oi"] - 1)] += 1
# expected cleared source flags: the audit's OWN PRE flags whose rel is
# retired. The flag fires only on deployment-class representatives
# (effective_occurrences, audit_depth_sense.py:648-667), so the clone's
# full citation-pair set would OVERCOUNT: a retired occurrence that is
# a non-representative class member never fired PRE. Non-retired PRE
# flags must SURVIVE (they sit on live evidence).
expected_cleared_src = set()
expected_kept_src = set()
for eid in worklist:
    for f in pre_depth[eid]["hardFlags"]:
        if f["kind"] == "source-not-in-corpus-manifest":
            if f.get("relPath") in RETIRED:
                expected_cleared_src.add((eid, f.get("relPath")))
            else:
                expected_kept_src.add((eid, f.get("relPath")))

regressed, improved = [], []
cleared_kwa = collections.Counter()            # removal sites seen cleared
cleared_src = collections.Counter()            # (eid, rel) seen cleared
surfaced_below = set()
unlawful = []
moved_review = []
for eid in worklist:
    a, b = pre_depth[eid], post_depth[eid]
    if a["hardPass"] != b["hardPass"]:
        (improved if b["hardPass"] else regressed).append(eid)
    pre_hard = collections.Counter(map(mkey, a["hardFlags"]))
    post_hard = collections.Counter(map(mkey, b["hardFlags"]))
    for x in (pre_hard - post_hard).elements():
        f = json.loads(x)
        if f["kind"] == "invalid-kwic-anchor":
            if f.get("verification", {}).get("error") != "NOT_IN_ALLOWLIST":
                unlawful.append(f"{eid}: cleared kwa not NOT_IN_ALLOWLIST")
            cleared_kwa[(eid, f.get("senseIndex"), f.get("occurrenceIndex"))] += 1
        elif f["kind"] == "source-not-in-corpus-manifest":
            cleared_src[(eid, f.get("relPath"))] += 1
        else:
            unlawful.append(f"{eid}: cleared {f['kind']} (unlawful)")
    for x in (post_hard - pre_hard).elements():
        f = json.loads(x)
        if f["kind"] == "below-frequency-floor":
            surfaced_below.add(eid)
        else:
            unlawful.append(f"{eid}: surfaced {f['kind']} (unlawful)")
    if collections.Counter(map(mkey, a["reviewFlags"])) != collections.Counter(
            map(mkey, b["reviewFlags"])):
        moved_review.append(eid)

if regressed:
    problems.append(f"gate2: depth hardPass true->false on {regressed}")
if cleared_kwa != removal_sites:
    problems.append(
        f"gate2: cleared invalid-kwic-anchor != removal sites: "
        f"missing {sorted(removal_sites - cleared_kwa)[:5]}, "
        f"extra {sorted(cleared_kwa - removal_sites)[:5]}")
if set(cleared_src) != expected_cleared_src or any(
        v != 1 for v in cleared_src.values()):
    problems.append(
        f"gate2: cleared source-not-in-corpus-manifest != audit PRE "
        f"retired-rel flags: missing "
        f"{sorted(expected_cleared_src - set(cleared_src))[:5]}, extra "
        f"{sorted(set(cleared_src) - expected_cleared_src)[:5]}")
kept_src_bad = []
for eid in worklist:
    post_kinds = collections.Counter(
        f["kind"] for f in post_depth[eid]["hardFlags"])
    for (e, rel) in expected_kept_src:
        if e != eid:
            continue
        alive = any(f["kind"] == "source-not-in-corpus-manifest"
                    and f.get("relPath") == rel
                    for f in post_depth[eid]["hardFlags"])
        if not alive:
            kept_src_bad.append(f"{eid}: {rel}")
if kept_src_bad:
    problems.append(f"gate2: non-retired source flags wrongly cleared: "
                    f"{kept_src_bad[:5]} ({len(kept_src_bad)})")
if surfaced_below != set(BELOW_FLOOR_FROZEN):
    problems.append(
        f"gate2: below-floor surfaced != frozen 20: missing "
        f"{sorted(set(BELOW_FLOOR_FROZEN) - surfaced_below)}, extra "
        f"{sorted(surfaced_below - set(BELOW_FLOOR_FROZEN))}")
if unlawful:
    problems.append(f"gate2: unlawful flag movement: {unlawful[:6]} "
                    f"({len(unlawful)})")
if moved_review:
    problems.append(f"gate2: review flags moved on {moved_review[:5]}")
report["depth"] = {
    "entries": len(worklist), "improved": improved, "regressed": regressed,
    "clearedKwaSites": sum(cleared_kwa.values()),
    "clearedSourcePairs": sum(cleared_src.values()),
    "expectedClearedSourcePairs": len(expected_cleared_src),
    "expectedKeptSourcePairs": len(expected_kept_src),
    "belowFloorSurfaced": sorted(surfaced_below),
    "unlawful": unlawful, "reviewMoved": moved_review,
}
print(f"gate2 depth: improved {len(improved)}, regressed {len(regressed)}, "
      f"kwa cleared {sum(cleared_kwa.values())}, src cleared "
      f"{sum(cleared_src.values())}, below-floor {len(surfaced_below)}, "
      f"unlawful {len(unlawful)}, reviewMoved {len(moved_review)}")

# ---- gate 3: removal coverage + note rewrite ----------------------------------
cov_bad = []
for eid, per_sense in sorted(removal_by_entry.items()):
    pre_e = clone_by_id[eid]
    post_e = json.loads((TERMS / eid / "entry.v2.json").read_text(
        encoding="utf-8-sig"))
    for si, ois in sorted(per_sense.items()):
        pre_s = pre_e["Senses"][si - 1]
        post_s = post_e["Senses"][si - 1]
        pre_occs = pre_s.get("Occurrences") or []
        expected_keep = [o for o in pre_occs
                         if o.get("RelPath") not in RETIRED]
        if len(expected_keep) != len(pre_occs) - len(ois):
            cov_bad.append(f"{eid} s{si}: removed count mismatch")
        if post_s.get("Occurrences") != expected_keep:
            cov_bad.append(f"{eid} s{si}: post Occurrences != pre minus "
                           "exactly the retired rows")
        if not post_s.get("Occurrences"):
            cov_bad.append(f"{eid} s{si}: sense emptied")
# the ONE note rewrite
note_e = json.loads((TERMS / NOTE_ENTRY / "entry.v2.json").read_text(
    encoding="utf-8-sig"))
note = str(note_e["Senses"][0].get("Note") or "")
ms = eng.SENT_RE.findall(note)
occs = note_e["Senses"][0].get("Occurrences") or []
if len(ms) != 1:
    cov_bad.append(f"{NOTE_ENTRY}: count-sentence matches {len(ms)} != 1")
else:
    m = eng.SENT_RE.search(note)
    n = int(re.search(r"(\d+)\s+exact", m.group(0)).group(1))
    mm = int(re.search(r"from\s+(\d+)\s+distinct", m.group(0)).group(1))
    if n != len(occs):
        cov_bad.append(f"{NOTE_ENTRY}: N {n} != live {len(occs)}")
    if mm != len({o.get("RelPath") for o in occs}):
        cov_bad.append(f"{NOTE_ENTRY}: M {mm} != live distinct rels")
if cov_bad:
    problems.append(f"gate3: coverage failures: {cov_bad[:5]} ({len(cov_bad)})")
report["removalCoverage"] = {"occRecords": sum(
    len(v) for per in removal_by_entry.values() for v in per.values()),
    "failures": cov_bad}
print(f"gate3 coverage: {len(cov_bad)} failures")

# ---- gates 4+5: determinism + confinement -------------------------------------
import copy  # noqa: E402

snap1 = {eid: copy.deepcopy(clone_by_id[eid]) for eid in worklist}
out1, _ = eng.transform(snap1)
by_id2 = eng.clone_state()
snap2 = {eid: copy.deepcopy(by_id2[eid]) for eid in worklist}
out2, _ = eng.transform(snap2)
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
report["determinism"] = {"nondeterministic": out1 != out2}
report["confinement"] = {"mismatch": conf_mismatch}
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


ALLOWED_OCC = re.compile(r"^Senses\[\d+\]\.Occurrences(?:[.\[]|$)")
escaped_all, empty_all = [], []
for eid in worklist:
    post_obj = json.loads((TERMS / eid / "entry.v2.json")
                          .read_text(encoding="utf-8-sig"))
    for p in diff_paths(clone_by_id[eid], post_obj):
        q = p[:-len("<len>")] if p.endswith("<len>") else p
        if ALLOWED_OCC.search(q):
            continue
        if eid == NOTE_ENTRY and q == "Senses[0].Note":
            continue
        escaped_all.append(f"{eid}: {p}")
    if not diff_paths(clone_by_id[eid], post_obj):
        empty_all.append(eid)
if escaped_all:
    problems.append(f"gate6: diff escaped allowed paths: "
                    f"{escaped_all[:6]} ({len(escaped_all)})")
if empty_all:
    problems.append(f"gate6: entries with empty diff: {empty_all}")
report["byteDiff"] = {"escaped": escaped_all, "empty": empty_all}
print(f"gate6 byte-diff: escaped {len(escaped_all)}, empty {len(empty_all)}")

# ---- gate 7: off-worklist protection ------------------------------------------
pre_shas = json.loads(
    (HERE / "r1b-pre-terms-shas-20260903.json").read_text(encoding="utf-8"))
now_shas = {}
for p in sorted(TERMS.glob("*/entry.v2.json")):
    now_shas[p.parent.name] = hashlib.sha256(p.read_bytes()).hexdigest()
if set(now_shas) != set(pre_shas["shas"]):
    problems.append("gate7: terms-tree entry set changed")
changed = {e for e in now_shas if now_shas[e] != pre_shas["shas"].get(e)}
wl_set = set(worklist)
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
fleet_out = HERE / "r1b-fleet-attribution-post-20260903.json"
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
        (HERE / "s1b-fleet-attribution-post-20260903.json")
        .read_text(encoding="utf-8"))

    def rows(artifact):
        return [(re.search(r"t_[0-9a-f]{12}", str(f.get("entry", ""))).group(0),
                 f["kind"], str(f.get("detail", "")))
                for f in artifact.get("failures", [])
                if re.search(r"t_[0-9a-f]{12}", str(f.get("entry", "")))]

    pre_rows, post_rows = rows(pre), rows(post)
    wl_rows = [r for r in post_rows if r[0] in wl_set]
    wl_rows_ok = (len(wl_rows) == 2
                  and all(r[0] == RESIDUAL_ENTRY
                          and r[1] == RESIDUAL_KIND for r in wl_rows))
    if not wl_rows_ok:
        problems.append(f"gate8: rows on worklist POST not exactly the 2 "
                        f"documented residuals: {wl_rows[:4]}")
    pre_pairs = {(e, k) for e, k, _ in pre_rows}
    post_pairs = {(e, k) for e, k, _ in post_rows}
    new_pairs = post_pairs - pre_pairs
    if new_pairs:
        problems.append(f"gate8: newly-failing fleet pairs: "
                        f"{sorted(new_pairs)[:6]} ({len(new_pairs)})")
    report["fleet"] = {
        "preFailingPairs": len(pre_pairs),
        "postFailingPairs": len(post_pairs),
        "newlyFailingPairs": sorted(new_pairs),
        "resolvedPairs": sorted(pre_pairs - post_pairs),
        "worklistRowsPost": wl_rows,
    }
    print(f"gate8 fleet: pre {len(pre_pairs)} -> post {len(post_pairs)} "
          f"pairs; newly {len(new_pairs)}; resolved "
          f"{len(pre_pairs - post_pairs)}; worklist rows POST {len(wl_rows)}")

report["verdict"] = "CLEAN" if not problems else "INVESTIGATE"
report["problems"] = problems
(HERE / "r1b-gates-20260903.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(json.dumps({"verdict": report["verdict"], "problems": problems},
                 ensure_ascii=False, indent=2))
sys.exit(0 if not problems else 1)
