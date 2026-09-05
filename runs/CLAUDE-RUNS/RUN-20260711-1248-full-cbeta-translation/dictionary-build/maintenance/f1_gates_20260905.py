#!/usr/bin/env python3
"""SPEC_F1_20260905.md §3: post-apply gates. Run AFTER
f1_transform_20260905.py --apply and f1_pre_apply_20260905.py.

(clone = CLONE below; F1_CLONE_DIR may re-point it to a detached
worktree of the pin commit for the archive bundle's post-commit
re-run — the HEAD-pin and clean-status laws then hold there.)

  gate 1  identity: clone HEAD == 8457672 clean; terms bytes of the 2
          products == engine canon (recomputed); every OTHER terms file
          byte-identical to its pre-apply sha (off-worklist
          protection) — including R2's three products.
  gate 2  counts: sense + per-sense occurrence counts unchanged vs
          clone; retired rels absent from Occurrences/ClaimAnchors
          fleet-wide (direct scan of the written terms tree).
  gate 3  attribution convention (SPEC §3.3) on the 2 repaired rows
          (ab715 s1o2, 351fa s1o1) + roster membership ("Dongyang
          Dehui" in roster_names(); exact "Dehui" absent from every
          name-bearing field of both entries).
  gate 4  audit_attribution PRE/POST on the products: zero NEW failure
          rows (PRE = f1-pre-attribution-pre-20260905.json).
  gate 5  audit_depth_sense PRE/POST: no hardPass true -> false.
  gate 6  prose-anchoring + count-claims on the edited sense (351fa
          s1): anchor gate recomputed from the WRITTEN bytes;
          Explanation == pre bytes with exactly the frozen find-once
          rewrite; every PRE count-claim sentence byte-present.
  gate 7  R2-product protection: ea2/057/968 terms bytes == clone
          canon (untouched by F1).
  gate 8  DROPPED (SPEC §3.8: no SearchAliases edit this lane).
  gate 9  fleet regression: full-tree audit_attribution POST vs the R2
          fleet artifact — zero NEW rows — plus the SPEC §7 census
          law: zero MasterName == "Dehui" rows anywhere in the written
          tree.

Writes maintenance/f1-gates-20260905.json (machine receipt; exit 0
only if every gate is CLEAN).
"""
from __future__ import annotations

import copy
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
# F1_CLONE_DIR: see f1_transform_20260905.py (archive-bundle worktree
# re-run; unchanged default = the agent clone).
CLONE = Path(os.environ.get(
    "F1_CLONE_DIR", r"C:\temp\NewTranslationrepos\CbetaZenTranslations"))
CLONE_HEAD_PIN = "8457672"
COHORT = ("t_ab715aa474d5", "t_351fa42d396b")
R2_PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
SENT_RE = re.compile(r"[^.。]*\.")
COUNT_HINT_RE = re.compile(
    r"\b(?:occurrences?|times|texts?)\b")
DIGIT_RE = re.compile(r"\d[\d,]*")
problems: list[str] = []
notes: list[str] = []

sys.path.insert(0, str(HERE))
import f1_transform_20260905 as f1  # noqa: E402


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
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in COHORT}
out, records = f1.transform(snapshot)
for eid in COHORT:
    cur = (TERMS / eid / "entry.v2.json").read_text(encoding="utf-8-sig")
    if cur != out[eid]:
        problems.append(f"gate1: terms bytes != engine output for {eid}")

pre_shas = json.loads(
    (HERE / "f1-pre-terms-shas-20260905.json").read_text("utf-8"))
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
                 f"{len(pre_shas) - len(COHORT)} untouched files "
                 f"(R2 products protected)")

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
REPAIRED = (("t_ab715aa474d5", 1, 2), ("t_351fa42d396b", 1, 1))
for eid, si, oi in REPAIRED:
    e = json.loads((TERMS / eid / "entry.v2.json")
                   .read_text(encoding="utf-8-sig"))
    o = e["Senses"][si - 1]["Occurrences"][oi - 1]
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
        problems.append(f"gate3: {eid} s{si}o{oi} convention law failed")
for eid in COHORT:
    e = json.loads((TERMS / eid / "entry.v2.json")
                   .read_text(encoding="utf-8-sig"))
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            names = [o.get("MasterName")] + [
                cm.get("MasterName") for cm in o.get("ContextMasters")
                or []]
            if "Dehui" in names:
                problems.append(f"gate3: a 'Dehui' name survived in {eid}")
        if "Dehui" in (s.get("RelatedMasters") or []):
            problems.append(f"gate3: {eid} RelatedMasters still has "
                            "'Dehui'")
    # the rename law is scoped to the EDITED sense (Senses[0]); other
    # senses of multi-sense entries lawfully carry neither name
    if "Dongyang Dehui" not in (e["Senses"][0].get("RelatedMasters")
                                or []):
        problems.append(f"gate3: {eid} s1 RelatedMasters lacks "
                        "'Dongyang Dehui'")
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            for cm in o.get("ContextMasters") or []:
                name = cm.get("MasterName")
                if name == "Dongyang Dehui" and name not in roster:
                    problems.append("gate3: non-roster ContextMasters "
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


attr_post = run_audit(HERE / "f1-gate-attribution-post-20260905.json")
attr_pre = json.loads(
    (HERE / "f1-pre-attribution-pre-20260905.json").read_text("utf-8"))


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

depth_post = run_depth(HERE / "f1-gate-depth-post-20260905.json")
depth_pre_raw = json.loads(
    (HERE / "f1-pre-depth-pre-20260905.json").read_text("utf-8"))

pre_items = depth_items(depth_pre_raw)
post_items = depth_items({"results": depth_post})
pre_hard = {x.get("entryId") for x in pre_items if x.get("hardPass")}
post_map = {x.get("entryId"): x for x in post_items}
for eid in COHORT:
    if eid in pre_hard and not post_map.get(eid, {}).get("hardPass"):
        problems.append(f"gate5: hardPass true->false {eid}")
notes.append(f"gate5: depth pre hard {len(pre_hard)} / post "
             f"{sum(1 for x in post_items if x.get('hardPass'))}")

# ---- gate 6: anchoring + count claims (edited sense: 351fa s1) ----------------
eid, si = "t_351fa42d396b", 1
s_post = json.loads((TERMS / eid / "entry.v2.json")
                    .read_text(encoding="utf-8-sig"))["Senses"][si - 1]
s_pre = json.loads((PRE_JSON := HERE / "f1-pre-entries-20260905" / eid
                    / "entry.v2.json").read_text(encoding="utf-8-sig")
                   )["Senses"][si - 1]
REWRITE = f1.PROSE_EDITS["t_351fa42d396b"][0]
expl_pre = str(s_pre.get(REWRITE["field"]) or "")
expl_post = str(s_post.get(REWRITE["field"]) or "")
if expl_post != expl_pre.replace(REWRITE["old"], REWRITE["new"], 1):
    problems.append("gate6: Explanation != pre bytes with exactly the "
                    "frozen rewrite")
kwics = [str(o.get("Kwic") or "") for o in s_post.get("Occurrences") or []]
kwics += [str(a.get("Kwic") or "") for a in s_post.get("ClaimAnchors")
          or []]
prose = "\n".join(str(s_post.get(k) or "") for k in ("Explanation", "Note"))
for quote in sorted(set(CJK_RE.findall(prose))):
    if not any(quote in k or k in quote for k in kwics if k):
        problems.append(f"gate6: {eid} s{si} dangles: {quote[:24]}")
pre_prose = "\n".join(str(s_pre.get(k) or "") for k in ("Explanation",
                                                        "Note"))
for sent in SENT_RE.findall(pre_prose):
    if DIGIT_RE.search(sent) and COUNT_HINT_RE.search(sent):
        if sent not in prose:
            problems.append(f"gate6: count claim lost: {sent[:60]!r}")
notes.append("gate6: anchoring + count-claim preservation recomputed "
             "from written bytes")

# ---- gate 7: R2-product protection -------------------------------------------
for eid in R2_PRODUCTS:
    cur = (TERMS / eid / "entry.v2.json").read_text(encoding="utf-8-sig")
    if cur != canon(by_id[eid]):
        problems.append(f"gate7: R2 product {eid} != clone canon")

# ---- gate 8: DROPPED (SPEC §3.8) ----------------------------------------------
notes.append("gate8: dropped — no SearchAliases edit this lane")

# ---- gate 9: fleet regression + SPEC §7 census ---------------------------------
fleet_out = HERE / "f1-fleet-attribution-post-20260905.json"
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
        (HERE / "r2-fleet-attribution-post-20260903.json")
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
dehui_rows = []
for p in TERMS.glob("*/entry.v2.json"):
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    for s in data.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("MasterName") == "Dehui":
                dehui_rows.append((p.parent.name, o.get("FromLb")))
if dehui_rows:
    problems.append(f"gate9: SPEC §7 census law violated — MasterName "
                    f"'Dehui' rows remain: {dehui_rows[:5]} "
                    f"({len(dehui_rows)})")
else:
    notes.append("gate9: census law holds — zero MasterName 'Dehui' "
                 "rows in the written tree")

# ---- receipt ------------------------------------------------------------------
receipt = {
    "schemaVersion": "f1-gates",
    "lane": "F1",
    "cloneHead": CLONE_HEAD_PIN,
    "verdict": "CLEAN" if not problems else "DIRTY",
    "problems": problems,
    "notes": notes,
    "gate4PostRows": attr_post.get("failures", []),
}
(HERE / "f1-gates-20260905.json").write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(f"F1 GATES: {receipt['verdict']}")
for n in notes:
    print(f"  note: {n}")
for p in problems:
    print(f"  PROBLEM: {p}")
sys.exit(0 if not problems else 1)
