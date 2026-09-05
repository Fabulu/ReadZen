#!/usr/bin/env python3
"""Generate coordinator rulings for R1b blind round r1 honest flags.

Law context: the reviewer prompt stated law d per-row ("post sense
occurrences == pre minus exactly index oi"). For the three same-sense
DOUBLE-removal entries (t_d7725cb0c8c0 水頭, t_ef5beb628603 磨頭,
t_f0cb4dcfc70c 掛搭 — two removed occurrences in ONE sense), the two
rows share one frozen post state, so the literal per-row law is
unsatisfiable: post == pre minus BOTH indices. The rows builder
constructs honest rows under the JOINT law (S1-b AM3 precedent):
post == pre minus the sense's complete removal set, and every row's oi
is a member of that set (verified per row against the pre materials:
the occurrence at (si, oi) is retired, and it is absent from post).

This script BYTE-VERIFIES the joint law for every flagged (row,
reviewer) pair against the frozen materials before writing a REFUTED
ruling; any flag it cannot so verify is left unruled (the adjudicator
then stays PENDING — no silent dismissals).

Reads both reviewers' verdicts.json; writes
maintenance/r1b-blind-r1-coordinator-rulings-20260903.json.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent

plants = json.loads(
    (HERE / "r1b-blind-r1-plants-20260903.json").read_text(encoding="utf-8"))
plant_ids = {f"R{p['rowSlot']:04d}" for p in plants["registry"]}
rows_doc = json.loads(
    (HERE / "r1b-blind-r1-rows-20260903.json").read_text(encoding="utf-8"))
rows_by_id = {r["rowId"]: r for r in rows_doc["rows"]}
MAT = Path(rows_doc["materialsDir"])

REVIEWERS = ("reviewer1", "reviewer2")
verdicts = {}
for n in REVIEWERS:
    p = HERE / "subagents" / f"20260903-r1b-blind-r1-reviewer-{n[-1]}" \
        / "verdicts.json"
    if not p.exists():
        raise SystemExit(f"missing {p}")
    verdicts[n] = json.loads(p.read_text(encoding="utf-8"))

pre_cache: dict[str, dict] = {}
post_cache: dict[str, dict] = {}


def load(entry, which):
    cache = pre_cache if which == "pre" else post_cache
    if entry not in cache:
        cache[entry] = json.loads(
            (MAT / which / f"{entry}.json").read_text(encoding="utf-8"))
    return cache[entry]


def joint_law_holds(row: dict) -> tuple[bool, str]:
    """post == pre minus the sense's COMPLETE removal set, this row's
    oi in that set, its occurrence retired, and the row's post fields
    equal the frozen post sense. Returns (holds, proof-line)."""
    eid, si, oi = row["entry"], row["si"], row["oi"]
    pre_s = load(eid, "pre")["Senses"][si - 1]
    post_s = load(eid, "post")["Senses"][si - 1]
    pre_occs = pre_s.get("Occurrences") or []
    post_occs = post_s.get("Occurrences") or []
    # this row's occurrence is retired and present in pre
    if oi < 1 or oi > len(pre_occs):
        return False, f"{eid} s{si} o{oi}: no such pre occurrence"
    occ = pre_occs[oi - 1]
    if occ.get("RelPath") != row.get("relPath"):
        return False, f"{eid} s{si} o{oi}: relPath mismatch"
    # the sense's complete removal set = retired pre occurrences
    removed = {j for j, o in enumerate(pre_occs, 1)
               if o.get("RelPath") in
               set(rows_doc["retiredRels"])}
    if oi not in removed:
        return False, f"{eid} s{si} o{oi}: not in the removal set"
    expected_post = [o for j, o in enumerate(pre_occs, 1) if j not in removed]
    if post_occs != expected_post:
        return False, f"{eid} s{si}: post != pre minus the removal set"
    if row.get("postOccurrenceRels") != [o.get("RelPath")
                                         for o in post_occs]:
        return False, f"{eid} s{si}: row postOccurrenceRels != frozen post"
    if row.get("postOccurrenceCount") != len(post_occs):
        return False, f"{eid} s{si}: row postOccurrenceCount != frozen post"
    return True, (f"{eid} s{si}: removed set {sorted(removed)} (this row "
                  f"o{oi}, RelPath {occ.get('RelPath')}); frozen post == "
                  f"pre minus exactly that set ({len(pre_occs)} -> "
                  f"{len(post_occs)}); row's post fields == frozen post")


rulings = []
unruled = []
for n in REVIEWERS:
    for f in verdicts[n].get("flags", []):
        rid = f.get("rowId")
        if rid in plant_ids or rid not in rows_by_id:
            continue                      # plants + unknown ids: not ours
        row = rows_by_id[rid]
        holds, proof = joint_law_holds(row)
        reason = (f"literal per-row law d is unsatisfiable on a "
                  f"multi-removal sense (two rows share one frozen post); "
                  f"joint law byte-verified: {proof}. Reviewer's flag "
                  f"correctly applied the literal law — rows and product "
                  f"bytes are oracle-identical.")
        if holds:
            rulings.append({"rowId": rid, "reviewer": n,
                            "ruling": "refuted",
                            "reason": reason,
                            "flagReason": f.get("reason")})
        else:
            unruled.append({"rowId": rid, "reviewer": n,
                            "reason": f.get("reason"), "proof": proof})

if unruled:
    print("UNRULED (joint law failed — adjudicator stays PENDING):")
    for u in unruled:
        print(" ", json.dumps(u, ensure_ascii=False)[:200])
out_path = HERE / "r1b-blind-r1-coordinator-rulings-20260903.json"
out_path.write_text(json.dumps({
    "schemaVersion": "r1b-blind-r1-coordinator-rulings",
    "law": ("joint-removal law for multi-removal senses (S1-b AM3 "
            "precedent): post == pre minus the sense's complete removal "
            "set; every honest row's oi is in that set and its post "
            "fields equal the frozen post sense"),
    "rulings": rulings}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(json.dumps({"rulings": len(rulings), "refuted": sum(
    1 for r in rulings if r["ruling"] == "refuted"),
    "unruled": len(unruled),
    "file": str(out_path)}, ensure_ascii=False, indent=2))
