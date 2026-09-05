#!/usr/bin/env python3
"""Adjudicate blind review round r1 for lane A1 (SPEC_A1_20260902.md §5).

Laws (carried from Q1/Q2/P1/Q3/C1):
  - Canary coverage: every planted row must be flagged by EVERY reviewer.
    Any miss => verdict VOID (round must be re-run with fresh reviewers).
  - Honest-row flags are byte-adjudicated against the engine oracle: the
    row's full payload (minus rowId/rowSha) must equal the row rebuilt
    exactly as the rows builder constructs honest rows — sourced from the
    CLONE pre-state via the engine and the FROZEN materials
    (a1-blind-r1-materials pre/post, sha-pinned in the rows header).
    Oracle-matching rows that a reviewer flagged need a coordinator
    ruling in a1-blind-r1-coordinator-rulings-20260903.json
    (refute-with-bytes or confirm); an unruled flag => PENDING; a
    confirmed flag is blocking (fix => fresh round).
  - Reviewer input integrity: rows-file sha256 recorded; every rowId
    exactly once per reviewer verdict list; every rowSha re-verifies.

Reviewer format: verdicts.json is an object {reviewer, materialsPinsOk,
rows: [{rowId, verdict: accept|flag, reason}]}; "ok" normalized to
"accept"; materialsPinsOk=false in any reviewer verdict is a problem
(VOID).

Outputs maintenance/a1-blind-r1-adjudication-20260903.json. Exit 0 iff
verdict == PASS.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402

MAT = HERE / "a1-blind-r1-materials"

_spec = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

rows_doc = json.loads(
    (HERE / "a1-blind-r1-rows-20260903.json").read_text(encoding="utf-8"))
rows = rows_doc["rows"]
rows_by_id = {r["rowId"]: r for r in rows}
if len(rows_by_id) != len(rows):
    raise SystemExit("duplicate rowIds in rows file")

plants_doc = json.loads(
    (HERE / "a1-blind-r1-plants-20260903.json").read_text(encoding="utf-8"))
registry = plants_doc["registry"]


def body_json(r: dict) -> str:
    body = {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}
    return json.dumps(body, ensure_ascii=False, sort_keys=True)


def row_sha(r: dict) -> str:
    return hashlib.sha256(body_json(r).encode("utf-8")).hexdigest()


# ---- oracle: honest rows rebuilt exactly as the builder constructs them ------
worklist = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8")
)["worklist"]
by_id = eng.clone_state()
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
eng.clone_snapshot.update(
    {eid: copy.deepcopy(by_id[eid]) for eid in worklist})
out, records = eng.transform(by_id)

for eid in worklist:
    assert out[eid].encode("utf-8") == (MAT / "post" / f"{eid}.json"
                                        ).read_bytes(), f"post drift {eid}"
    assert eng.canon(pre_state[eid]) == (MAT / "pre" / f"{eid}.json"
                                         ).read_text(encoding="utf-8"), \
        f"pre drift {eid}"

pre_obj = {eid: json.loads((MAT / "pre" / f"{eid}.json").read_text(
    encoding="utf-8")) for eid in worklist}
post_obj = {eid: json.loads((MAT / "post" / f"{eid}.json").read_text(
    encoding="utf-8")) for eid in worklist}


def occ(obj, eid, si, oi):
    return obj[eid]["Senses"][si - 1]["Occurrences"][oi - 1]


def sense(obj, eid, si):
    return obj[eid]["Senses"][si - 1]


oracle: list[str] = []
for rec in records:
    cls, eid, si = rec["class"], rec["entry"], rec["si"]
    if cls.startswith("muc-"):
        o_pre = occ(pre_obj, eid, si, rec["oi"])
        oracle.append(body_json({
            "entry": eid, "class": "muc-context-row", "si": si,
            "oi": rec["oi"], "masterName": rec["row"]["MasterName"],
            "roles": rec["row"]["Roles"],
            "attributionNote": str(o_pre.get("AttributionNote") or ""),
        }))
    elif cls == "vague-reword":
        oracle.append(body_json({
            "entry": eid, "class": "vague-reword", "si": si,
            "field": rec["field"], "find": rec["find"],
            "replace": rec["replace"],
        }))
    elif cls == "dangling-anchor":
        anchor = json.loads(json.dumps(
            sense(post_obj, eid, si)["ClaimAnchors"][-1], ensure_ascii=False))
        v = zc.verify(anchor["RelPath"], anchor.get("Kwic") or "")
        assert v.get("ok") and v.get("count") == 1, v
        assert (anchor["FromLb"], anchor["ToLb"]) == (v["fromLb"], v["toLb"])
        oracle.append(body_json({
            "entry": eid, "class": "dangling-anchor", "si": si,
            "strings": rec["strings"], "anchor": anchor,
            "zc": {"ok": True, "count": v["count"], "fromLb": v["fromLb"],
                   "toLb": v["toLb"]},
        }))
    elif cls == "performer-context-row":
        oracle.append(body_json({
            "entry": eid, "class": "performer-context-row", "si": si,
            "oi": rec["oi"], "row": rec["row"],
            "kwic": str(occ(pre_obj, eid, si, rec["oi"]).get("Kwic") or ""),
        }))
    elif cls == "performer-grammar-proof":
        oracle.append(body_json({
            "entry": eid, "class": "performer-grammar-proof", "si": si,
            "oi": rec["oi"], "sentence": rec["sentence"],
            "kwic": str(occ(pre_obj, eid, si, rec["oi"]).get("Kwic") or ""),
        }))
    elif cls == "anon-monk-restructure":
        o_post = occ(post_obj, eid, si, rec["oi"])
        oracle.append(body_json({
            "entry": eid, "class": "anon-monk-restructure", "si": si,
            "oi": rec["oi"], "respondentMaster": rec["respondentMaster"],
            "actorLabel": rec["actorLabel"],
            "occurrence": json.loads(json.dumps(o_post, ensure_ascii=False)),
        }))
    elif cls == "grammar-evidence-repeat":
        o_pre, o_post = (occ(pre_obj, eid, si, rec["oi"]),
                         occ(post_obj, eid, si, rec["oi"]))
        oracle.append(body_json({
            "entry": eid, "class": "grammar-evidence-repeat", "si": si,
            "oi": rec["oi"], "label": rec["label"],
            "before": str(o_pre["ActorAttribution"]["GrammarEvidence"]),
            "after": str(o_post["ActorAttribution"]["GrammarEvidence"]),
        }))
    elif cls == "reviewed-fields":
        o_pre, o_post = (occ(pre_obj, eid, si, rec["oi"]),
                         occ(post_obj, eid, si, rec["oi"]))
        oracle.append(body_json({
            "entry": eid, "class": "reviewed-fields", "si": si,
            "oi": rec["oi"], "beforeReviewedBy": o_pre["ActorAttribution"]
            .get("ReviewedBy"), "beforeReviewedUtc": o_pre["ActorAttribution"]
            .get("ReviewedUtc"),
            "reviewedBy": rec["reviewedBy"],
            "reviewedUtc": o_post["ActorAttribution"]["ReviewedUtc"],
        }))
    elif cls == "anchor-remove":
        pre_anchors = sense(pre_obj, eid, si).get("ClaimAnchors") or []
        anchor = pre_anchors[rec["anchorIndex"]]
        holders = [o.get("RelPath") for o in post_obj[eid]["Senses"][si - 1]
                   ["Occurrences"]
                   if str(anchor.get("Kwic") or "").lstrip("。、，")
                   in str(o.get("Kwic") or "")]
        oracle.append(body_json({
            "entry": eid, "class": "anchor-remove", "si": si,
            "removedRelPath": rec["removedRelPath"],
            "removedClaimText": rec["removedClaimText"],
            "removedKwic": str(anchor.get("Kwic") or ""),
            "postClaimAnchors": sense(post_obj, eid, si).get("ClaimAnchors"),
            "survivingHolders": holders,
        }))
    else:
        raise SystemExit(f"unknown record class {cls}")
oracle_set = set(oracle)
if len(oracle) != plants_doc["honestRows"]:
    raise SystemExit(f"oracle {len(oracle)} != honestRows "
                     f"{plants_doc['honestRows']}")

problems: list[str] = []

for r in rows:
    if row_sha(r) != r.get("rowSha"):
        problems.append(f"{r['rowId']}: rowSha mismatch (rows file tampered)")

# ---- reviewer verdicts --------------------------------------------------------
REVIEWER_FILES = {
    "reviewer1": BUILD / "subagents" / "20260903-a1-blind-r1-reviewer-1"
                             / "verdicts.json",
    "reviewer2": BUILD / "subagents" / "20260903-a1-blind-r1-reviewer-2"
                             / "verdicts.json",
}
reviewers = {}
verdict_maps = {}
for name, p in REVIEWER_FILES.items():
    if not p.exists():
        raise SystemExit(f"missing reviewer verdicts {p} — the reviewer "
                         f"deliverable must be persisted verbatim")
    doc = json.loads(p.read_text(encoding="utf-8"))
    vlist = doc["rows"] if isinstance(doc, dict) else doc
    reviewers[name] = {
        "inputRowsSha256": hashlib.sha256(
            (HERE / "a1-blind-r1-rows-20260903.json").read_bytes()
        ).hexdigest(),
        "verdictsSha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "path": str(p),
    }
    if isinstance(doc, dict) and doc.get("materialsPinsOk") is False:
        problems.append(f"{name}: materials pins failed (tamper)")
    vmap = {}
    for v in vlist:
        rid, verdict = v.get("rowId"), v.get("verdict")
        if verdict == "ok":
            verdict = "accept"
        if rid not in rows_by_id:
            problems.append(f"{name}: unknown rowId {rid}")
            continue
        if rid in vmap:
            problems.append(f"{name}: duplicate verdict {rid}")
        if verdict not in ("accept", "flag"):
            problems.append(f"{name}: bad verdict {rid}={verdict!r}")
        vmap[rid] = {"verdict": verdict, "reason": v.get("reason")}
    missing = sorted(set(rows_by_id) - set(vmap))
    if missing:
        problems.append(f"{name}: {len(missing)} rows without verdict "
                        f"({missing[:5]})")
    verdict_maps[name] = vmap

# ---- canary coverage ----------------------------------------------------------
canary_results = []
misses = []
for p in registry:
    rid = f"R{p['rowSlot']:04d}"
    row = rows_by_id[rid]
    if row.get("rowSha") != p["bindPayloadSha256"]:
        problems.append(f"{p['plantId']}: rowSha binding mismatch at {rid}")
        continue
    caught_by = [n for n in sorted(verdict_maps)
                 if verdict_maps[n].get(rid, {}).get("verdict") == "flag"]
    canary_results.append({
        "plantId": p["plantId"], "rowId": rid, "class": p["class"],
        "defect": p.get("defect"),
        "caughtBy": caught_by, "missedBy": [n for n in sorted(verdict_maps)
                                            if n not in caught_by]})
    if len(caught_by) < len(verdict_maps):
        misses.append({"plantId": p["plantId"], "rowId": rid,
                       "missedBy": canary_results[-1]["missedBy"]})

# ---- honest-row flags ----------------------------------------------------------
plant_ids = {f"R{p['rowSlot']:04d}" for p in registry}
honest_flags = []
for name in sorted(verdict_maps):
    for rid, v in verdict_maps[name].items():
        if rid in plant_ids or v["verdict"] != "flag":
            continue
        row = rows_by_id[rid]
        matches = body_json(row) in oracle_set
        honest_flags.append({
            "rowId": rid, "reviewer": name, "reason": v["reason"],
            "row": {k: row[k] for k in ("entry", "class", "si", "oi")
                    if k in row},
            "oracleMatch": matches,
            "note": ("row bytes == engine/materials oracle" if matches
                     else "row bytes match NO oracle row — rows-file "
                          "defect")})

# ---- coordinator rulings (only needed when honest flags exist) ----------------
rulings_path = HERE / "a1-blind-r1-coordinator-rulings-20260903.json"
rulings = {}
confirmed = []
unruled = []
if honest_flags:
    if not rulings_path.exists():
        unruled = honest_flags
    else:
        rulings = {r["rowId"] + "@" + r["reviewer"]: r
                   for r in json.loads(
                       rulings_path.read_text(encoding="utf-8"))["rulings"]}
        for f in honest_flags:
            k = f["rowId"] + "@" + f["reviewer"]
            if k not in rulings:
                unruled.append(f)
            elif rulings[k]["ruling"] == "confirmed":
                confirmed.append({**f, "ruling": rulings[k]})

if problems:
    verdict = "VOID"
elif misses:
    verdict = "VOID"
elif confirmed:
    verdict = "FINDINGS"
elif unruled:
    verdict = "PENDING"
else:
    verdict = "PASS"

out = {
    "schemaVersion": "a1-blind-r1-adjudication",
    "lane": "A1", "round": "r1",
    "rowsFile": {"path": str(HERE / "a1-blind-r1-rows-20260903.json"),
                 "sha256": reviewers["reviewer1"]["inputRowsSha256"]},
    "reviewers": reviewers,
    "canaries": {
        "plants": len(registry),
        "requiredCaughtBy": "every reviewer",
        "results": canary_results,
        "misses": misses,
    },
    "honestFlags": honest_flags,
    "coordinatorRulings": {
        "file": str(rulings_path) if rulings_path.exists() else None,
        "refuted": [f["rowId"] + "@" + f["reviewer"] for f in honest_flags
                    if f["rowId"] + "@" + f["reviewer"] in rulings
                    and rulings[f["rowId"] + "@" + f["reviewer"]]["ruling"]
                    == "refuted"],
        "confirmed": [f["rowId"] + "@" + f["reviewer"] for f in confirmed],
        "unruled": [f["rowId"] + "@" + f["reviewer"] for f in unruled],
    },
    "confirmedFindings": confirmed,
    "problems": problems,
    "verdict": verdict,
}
(HERE / "a1-blind-r1-adjudication-20260903.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(json.dumps({
    "verdict": verdict,
    "canaryMisses": len(misses),
    "honestFlags": len(honest_flags),
    "oracleMatches": sum(1 for f in honest_flags if f["oracleMatch"]),
    "confirmed": len(confirmed), "unruled": len(unruled),
    "problems": problems,
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if verdict == "PASS" else 1)
