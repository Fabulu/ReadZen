#!/usr/bin/env python3
"""SPEC_R2_20260903.md §3: post-apply gates. Run AFTER
r2_transform_20260903.py --apply and r2_pre_apply_20260903.py.

(clone = CLONE below; R2_CLONE_DIR may re-point it to a detached
worktree of the pin commit for the archive bundle's post-commit
re-run — the HEAD-pin and clean-status laws then hold there.)

  gate 1  identity: clone HEAD == 145b090 clean; terms bytes of the 3
          products == engine canon (recomputed); every OTHER terms file
          byte-identical to its pre-apply sha (off-worklist protection),
          incl. the 2 follow-up-lane sibling entries.
  gate 2  counts: sense + per-sense occurrence counts unchanged vs
          clone; retired rels absent from Occurrences/ClaimAnchors
          fleet-wide (direct scan of the written terms tree).
  gate 3  attribution convention (SPEC §3.3) on the 3 repaired rows +
          roster membership ("Dongyang Dehui" in roster_names();
          "Dehui" absent from every name-bearing field of ea2).
  gate 4  audit_attribution PRE/POST on the products: zero NEW failure
          rows (PRE = r2-pre-attribution-pre-20260903.json).
  gate 5  audit_depth_sense PRE/POST: no hardPass true -> false.
  gate 6  prose-anchoring + count-claims on the edited senses (anchor
          gate recomputed from the WRITTEN bytes; frozen count strings
          still present byte-exactly).
  gate 7  sibling protection: t_ab715aa474d5 + t_351fa42d396b terms
          bytes == clone canon (untouched by R2).
  gate 8  alias uniqueness: "一不成、二不是" owned by exactly one entry
          fleet-wide and absent from the installed index Aliases (so
          install adds exactly one row).
  gate 9  fleet regression: full-tree audit_attribution POST vs the
          R1c fleet artifact — zero NEW rows.

Writes maintenance/r2-gates-20260903.json (machine receipt; exit 0
only if every gate is CLEAN).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import runpy
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
TERMS = BUILD / "terms"
# R2_CLONE_DIR: see r2_transform_20260903.py (archive-bundle worktree
# re-run; unchanged default = the agent clone).
CLONE = Path(os.environ.get(
    "R2_CLONE_DIR", r"C:\temp\NewTranslationrepos\CbetaZenTranslations"))
CLONE_HEAD_PIN = "145b090"
COHORT = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
SIBLINGS = ("t_ab715aa474d5", "t_351fa42d396b")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
problems: list[str] = []
notes: list[str] = []

sys.path.insert(0, str(HERE))
import r2_transform_20260903 as r2  # noqa: E402


def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


# ---- gate 1: identity + off-worklist ----------------------------------------
head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
if head[:7] != CLONE_HEAD_PIN:
    problems.append(f"gate1: clone HEAD {head[:7]} != {CLONE_HEAD_PIN}")
dirty = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                       capture_output=True, text=True).stdout.splitlines()
if dirty:
    problems.append(f"gate1: clone dirty: {dirty[:3]}")

by_id = {e["Id"]: e for e in json.loads(
    (CLONE / "termbase.v2.json").read_text(encoding="utf-8"))["Entries"]}
import copy  # noqa: E402
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in COHORT}
out, records = r2.transform(snapshot)
for eid in COHORT:
    cur = (TERMS / eid / "entry.v2.json").read_text(encoding="utf-8-sig")
    if cur != out[eid]:
        problems.append(f"gate1: terms bytes != engine output for {eid}")

pre_shas = json.loads(
    (HERE / "r2-pre-terms-shas-20260903.json").read_text("utf-8"))
off_changes = []
for p in sorted(TERMS.glob("*/entry.v2.json")):
    eid = p.parent.name
    if eid in COHORT:
        continue
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if pre_shas.get(eid) != sha:
        off_changes.append(eid)
if off_changes:
    problems.append(f"gate1: off-worklist terms files changed: "
                    f"{off_changes[:5]} ({len(off_changes)})")
else:
    notes.append(f"gate1: off-worklist byte-identity over "
                 f"{len(pre_shas) - len(COHORT)} untouched files")

# ---- gate 2: counts + retired scan (written tree) ----------------------------
for eid in COHORT:
    live = json.loads((TERMS / eid / "entry.v2.json")
                      .read_text(encoding="utf-8-sig"))
    clone_counts = [len(s.get("Occurrences") or [])
                    for s in by_id[eid].get("Senses") or []]
    live_counts = [len(s.get("Occurrences") or [])
                   for s in live.get("Senses") or []]
    if live_counts != clone_counts or len(live["Senses"]) != len(
            by_id[eid]["Senses"]):
        problems.append(f"gate2: {eid} counts {live_counts} != "
                        f"{clone_counts}")
citing = []
for p in TERMS.glob("*/entry.v2.json"):
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    for s in data.get("Senses") or []:
        for o in (s.get("Occurrences") or []) + (s.get("ClaimAnchors")
                                                 or []):
            if o.get("RelPath") in RETIRED:
                citing.append((p.parent.name, o.get("RelPath")))
if citing:
    problems.append(f"gate2: retired citations in tree: {citing[:5]}")

# ---- gate 3: attribution convention + roster ---------------------------------
sys.path.insert(0, str(BUILD))
import audit_attribution as aa  # noqa: E402
roster = aa.roster_names()
if "Dongyang Dehui" not in roster:
    problems.append("gate3: 'Dongyang Dehui' not a roster name")
ea2 = json.loads((TERMS / "t_ea2a427c7aba" / "entry.v2.json")
                 .read_text(encoding="utf-8-sig"))
for oi in (1, 8, 9):
    o = ea2["Senses"][0]["Occurrences"][oi - 1]
    a = o.get("ActorAttribution") or {}
    label = str(a.get("ActorLabel") or "")
    ok = (o.get("MasterName") is None
          and o.get("ContextMasters")
          == [{"MasterName": "Dongyang Dehui", "Roles": ["compiler"]}]
          and a.get("Status") == "impersonal"
          and a.get("Kind") == "institutional procedure"
          and a.get("ActorRole") == "compiler"
          and label
          and label.casefold() in str(o.get("AttributionNote")).casefold())
    if not ok:
        problems.append(f"gate3: s1o{oi} convention law failed")
for s in ea2.get("Senses") or []:
    for o in s.get("Occurrences") or []:
        names = [o.get("MasterName")] + [
            cm.get("MasterName") for cm in o.get("ContextMasters") or []]
        if "Dehui" in names:
            problems.append("gate3: a 'Dehui' name survived in ea2")
if "Dehui" in ea2["Senses"][0].get("RelatedMasters", []):
    problems.append("gate3: RelatedMasters still has 'Dehui'")
if "Dongyang Dehui" not in ea2["Senses"][0].get("RelatedMasters", []):
    problems.append("gate3: RelatedMasters lacks 'Dongyang Dehui'")
for name in ("Dongyang Dehui",):
    for s in ea2["Senses"]:
        for o in s.get("Occurrences") or []:
            for cm in o.get("ContextMasters") or []:
                if cm.get("MasterName") == name and name not in roster:
                    problems.append(f"gate3: non-roster ContextMasters "
                                    f"{name!r}")

# ---- gates 4+5: audits PRE/POST ----------------------------------------------
paths = [str(TERMS / e / "entry.v2.json") for e in COHORT]


def run_audit(out_path: Path) -> dict:
    sys.argv = ["audit_attribution.py", "--json", "--output",
                str(out_path), *paths]
    _buf = io.StringIO()
    try:
        with redirect_stdout(_buf):
            runpy.run_path(str(BUILD / "audit_attribution.py"),
                           run_name="__main__")
    except SystemExit:
        pass
    return json.loads(out_path.read_text(encoding="utf-8"))


def run_depth(out_path: Path) -> dict:
    sys.argv = ["audit_depth_sense.py", "--report", str(out_path),
                "--paths", *paths]
    _buf = io.StringIO()
    try:
        with redirect_stdout(_buf):
            runpy.run_path(str(BUILD / "audit_depth_sense.py"),
                           run_name="__main__")
    except SystemExit:
        pass
    return json.loads(out_path.read_text(encoding="utf-8"))["results"]


def depth_items(doc) -> list[dict]:
    # audit_depth_sense "results" is a dict keyed by entryId
    res = doc.get("results") or {}
    return list(res.values()) if isinstance(res, dict) else list(res)


attr_post = run_audit(HERE / "r2-gate-attribution-post-20260903.json")
attr_pre = json.loads(
    (HERE / "r2-pre-attribution-pre-20260903.json").read_text("utf-8"))


def row_key(r):
    return (r.get("kind"), str(r.get("detail")))


pre_keys = {row_key(r) for r in attr_pre.get("failures", [])}
new_rows = [r for r in attr_post.get("failures", [])
            if row_key(r) not in pre_keys]
if new_rows:
    problems.append(f"gate4: NEW audit rows: "
                    f"{[row_key(r) for r in new_rows][:5]}")
else:
    notes.append(f"gate4: zero NEW attribution rows (pre "
                 f"{len(pre_keys)}, post "
                 f"{len(attr_post.get('failures', []))})")

depth_post = run_depth(HERE / "r2-gate-depth-post-20260903.json")
depth_pre_raw = json.loads(
    (HERE / "r2-pre-depth-pre-20260903.json").read_text("utf-8"))

pre_items = depth_items(depth_pre_raw)
post_items = depth_items({"results": depth_post})
pre_hard = {x.get("entryId") for x in pre_items if x.get("hardPass")}
post_map = {x.get("entryId"): x for x in post_items}
for eid in COHORT:
    if eid in pre_hard and not post_map.get(eid, {}).get("hardPass"):
        problems.append(f"gate5: hardPass true->false {eid}")
notes.append(f"gate5: depth pre hard {len(pre_hard)} / post "
             f"{sum(1 for x in post_items if x.get('hardPass'))}")

# ---- gate 6: anchoring + count claims ----------------------------------------
for eid, si in (("t_ea2a427c7aba", 1), ("t_057cc9ea8755", 1)):
    s = json.loads((TERMS / eid / "entry.v2.json")
                   .read_text(encoding="utf-8-sig"))["Senses"][si - 1]
    kwics = [str(o.get("Kwic") or "") for o in s.get("Occurrences") or []]
    kwics += [str(a.get("Kwic") or "") for a in s.get("ClaimAnchors") or []]
    prose = "\n".join(str(s.get(k) or "") for k in ("Explanation", "Note"))
    for quote in sorted(set(CJK_RE.findall(prose))):
        if not any(quote in k or k in quote for k in kwics if k):
            problems.append(f"gate6: {eid} s{si} dangles: {quote[:24]}")
claims = {
    "t_ea2a427c7aba": ("Note", "the headword has 1,207 exact occurrences "
                     "in 265 texts."),
    "t_057cc9ea8755": ("Explanation", "attested 141 times across 75 "
                       "texts"),
}
for eid, (field, needle) in claims.items():
    s = json.loads((TERMS / eid / "entry.v2.json")
                   .read_text(encoding="utf-8-sig"))["Senses"][0]
    if needle not in str(s.get(field) or ""):
        problems.append(f"gate6: {eid} count claim drifted: {needle!r}")

# ---- gate 7: sibling protection ----------------------------------------------
for eid in SIBLINGS:
    cur = (TERMS / eid / "entry.v2.json").read_text(encoding="utf-8-sig")
    if cur != canon(by_id[eid]):
        problems.append(f"gate7: sibling {eid} != clone canon")

# ---- gate 8: alias uniqueness ------------------------------------------------
alias = "一不成、二不是"
owners = []
for p in TERMS.glob("*/entry.v2.json"):
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    for s in data.get("Senses") or []:
        if alias in (s.get("SearchAliases") or []):
            owners.append(p.parent.name)
if sorted(set(owners)) != ["t_968a2f97c9ff"]:
    problems.append(f"gate8: alias owners {sorted(set(owners))} != "
                    "exactly [t_968a2f97c9ff]")
idx = json.loads((CLONE / "termbase.index.json").read_text("utf-8"))
if alias in (idx.get("Aliases") or {}):
    problems.append("gate8: alias already present in index Aliases")
if idx["Aliases"].get("one fails, two is wrong") != "一不成，二不是":
    problems.append("gate8: pre-existing English alias row missing")

# ---- gate 9: fleet regression -------------------------------------------------
fleet_out = HERE / "r2-fleet-attribution-post-20260903.json"
proc = subprocess.run(
    [sys.executable, "-X", "utf8", str(BUILD / "audit_attribution.py"),
     "--json", f"--output={fleet_out}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
if proc.returncode not in (0, 1):
    problems.append(f"gate9: fleet audit crashed rc={proc.returncode}: "
                    f"{proc.stderr[-500:]}")
else:
    post = json.loads(fleet_out.read_text(encoding="utf-8"))
    pre_fleet = json.loads(
        (HERE / "r1c-fleet-attribution-post-20260902.json")
        .read_text(encoding="utf-8"))
    post_keys = {row_key(r) for r in post.get("failures", [])}
    pre_fleet_keys = {row_key(r) for r in pre_fleet.get("failures", [])}
    grown = post_keys - pre_fleet_keys
    if grown:
        problems.append(f"gate9: NEW fleet rows: {list(grown)[:5]}")
    else:
        gone = pre_fleet_keys - post_keys
        notes.append(f"gate9: fleet zero NEW rows "
                     f"({len(post_keys)} rows; {len(gone)} resolved)")

# ---- receipt ------------------------------------------------------------------
receipt = {
    "schemaVersion": "r2-gates",
    "lane": "R2",
    "cloneHead": CLONE_HEAD_PIN,
    "verdict": "CLEAN" if not problems else "DIRTY",
    "problems": problems,
    "notes": notes,
    "gate4PostRows": attr_post.get("failures", []),
}
(HERE / "r2-gates-20260903.json").write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(f"R2 GATES: {receipt['verdict']}")
for n in notes:
    print(f"  note: {n}")
for p in problems:
    print(f"  PROBLEM: {p}")
sys.exit(0 if not problems else 1)
