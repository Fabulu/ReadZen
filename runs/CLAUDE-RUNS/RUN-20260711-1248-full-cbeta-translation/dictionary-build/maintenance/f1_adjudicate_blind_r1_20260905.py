#!/usr/bin/env python3
"""Adjudicate blind review round r1 for lane F1 (SPEC_F1_20260905.md §4).

Ladder (identical to R2 r1):

  - Canary coverage: every planted row must be flagged by EVERY
    reviewer. Any miss => verdict VOID (fresh round, fresh reviewers).
  - Honest-row flags are byte-adjudicated against the oracle: the row's
    full payload (minus rowId/rowSha) must equal the row rebuilt exactly
    as build_f1_blind_r1_20260905.py constructs honest rows — sourced
    from the CLONE pre-state via the engine and the FROZEN materials
    (f1-blind-r1-materials pre/post, sha-pinned in the rows header).
    Oracle-matching rows that a reviewer flagged need a coordinator
    ruling in f1-blind-r1-coordinator-rulings-20260905.json (refute-
    with-bytes or confirm); an unruled flag => PENDING; a confirmed flag
    is blocking (fix => fresh round).
  - Reviewer input integrity: rows-file sha256 recorded; every rowSha
    re-verifies; materialsPinsOk=false in any verdict is a problem.

Outputs maintenance/f1-blind-r1-adjudication-20260905.json. Exit 0 iff
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

MAT = HERE / "f1-blind-r1-materials"

_spec = importlib.util.spec_from_file_location(
    "f1_eng", HERE / "f1_transform_20260905.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

rows_doc = json.loads(
    (HERE / "f1-blind-r1-rows-20260905.json").read_text(encoding="utf-8"))
rows = rows_doc["rows"]
rows_by_id = {r["rowId"]: r for r in rows}
if len(rows_by_id) != len(rows):
    raise SystemExit("duplicate rowIds in rows file")

plants_doc = json.loads(
    (HERE / "f1-blind-r1-plants-20260905.json").read_text("utf-8"))
registry = plants_doc["registry"]


def body_json(r: dict) -> str:
    body = {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}
    return json.dumps(body, ensure_ascii=False, sort_keys=True)


def row_sha(r: dict) -> str:
    return hashlib.sha256(body_json(r).encode("utf-8")).hexdigest()


# ---- oracle: honest rows rebuilt exactly as the builder constructs them ------
by_id = eng.clone_state()
worklist = eng.derive(by_id)
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)

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


def sense(obj, eid, si):
    return obj[eid]["Senses"][si - 1]


oracle: list[str] = []
for rec in records:
    eid, si = rec["entry"], rec["si"]
    if rec["class"] == "occ-attribution":
        post_occs = sense(post_obj, eid, si).get("Occurrences") or []
        pre_occ = sense(pre_obj, eid, si)["Occurrences"][rec["oi"] - 1]
        oracle.append(body_json({
            "entry": eid, "class": "occ-attribution", "si": si,
            "oi": rec["oi"],
            "oldMasterName": rec["oldMasterName"],
            "oldContextMasters": pre_occ.get("ContextMasters"),
            "oldAttributionNote": pre_occ.get("AttributionNote"),
            "newMasterName": None,
            "newContextMasters": rec["newContextMasters"],
            "newActorAttribution": rec["newActorAttribution"],
            "newAttributionNote": rec["newAttributionNote"],
            "carriedRelPath": rec["carried"]["RelPath"],
            "carriedFromLb": rec["carried"]["FromLb"],
            "carriedToLb": rec["carried"]["ToLb"],
            "carriedKwic": rec["carried"]["Kwic"],
            "postOccurrenceRels": [x.get("RelPath") for x in post_occs],
            "postOccurrenceCount": len(post_occs),
        }))
    elif rec["class"] in ("explanation-rewrite", "note-rewrite",
                          "attributionnote-rewrite"):
        oracle.append(body_json({
            "entry": eid, "class": rec["class"], "si": si,
            "field": rec["field"], "oi": rec.get("oi"),
            "before": rec["before"], "after": rec["after"],
        }))
    elif rec["class"] == "relatedmasters-rename":
        oracle.append(body_json({
            "entry": eid, "class": rec["class"], "si": si,
            "renamed": rec["renamed"],
            "postRelatedMasters": rec["postRelatedMasters"],
        }))
    else:
        assert rec["class"] == "searchaliases-add", rec["class"]
        oracle.append(body_json({
            "entry": eid, "class": rec["class"], "si": si,
            "added": rec["added"],
            "postSearchAliases": rec["postSearchAliases"],
        }))
oracle_set = set(oracle)
if len(oracle) != plants_doc["honestRows"]:
    raise SystemExit(f"oracle {len(oracle)} != honestRows "
                     f"{plants_doc['honestRows']}")

problems: list[str] = []

for r in rows:
    if row_sha(r) != r.get("rowSha"):
        problems.append(f"{r['rowId']}: rowSha mismatch (rows file tampered)")

# ---- reviewer verdicts (flags-based schema) -----------------------------------
REVIEWER_FILES = {
    "reviewer1": HERE / "subagents" / "20260905-f1-blind-r1-reviewer-1"
                             / "verdicts.json",
    "reviewer2": HERE / "subagents" / "20260905-f1-blind-r1-reviewer-2"
                             / "verdicts.json",
}
reviewers = {}
verdict_maps = {}
flagged_full = {}
for name, p in REVIEWER_FILES.items():
    if not p.exists():
        raise SystemExit(f"missing reviewer verdicts {p} — the reviewer "
                         f"deliverable must be persisted verbatim")
    doc = json.loads(p.read_text(encoding="utf-8"))
    reviewers[name] = {
        "inputRowsSha256": hashlib.sha256(
            (HERE / "f1-blind-r1-rows-20260905.json").read_bytes()
        ).hexdigest(),
        "verdictsSha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "path": str(p),
        "schema": "flags-based",
    }
    if doc.get("materialsPinsOk") is False:
        problems.append(f"{name}: materials pins failed (tamper)")
    if doc.get("rowsChecked") != len(rows):
        problems.append(f"{name}: rowsChecked {doc.get('rowsChecked')} != "
                        f"{len(rows)} (incomplete check)")
    flagged: dict[str, list[dict]] = {}
    for f in doc.get("flags", []):
        rid = f.get("rowId")
        if rid not in rows_by_id:
            problems.append(f"{name}: unknown rowId {rid}")
            continue
        flagged.setdefault(rid, []).append(
            {"verdict": "flag", "reason": f.get("reason"),
             "law": f.get("law")})
    # a row is FLAGGED if any flag names it; a row may lawfully break
    # several laws at once (one flags entry per broken law)
    verdict_maps[name] = {
        rid: (flagged[rid][0] if rid in flagged
              else {"verdict": "accept", "reason": None})
        for rid in rows_by_id}
    flagged_full[name] = flagged
    reviewers[name]["flagCounts"] = {
        rid: len(fs) for rid, fs in sorted(flagged.items())}

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
            "law": v.get("law"),
            "allLaws": [f.get("law") for f in flagged_full[name][rid]],
            "row": {k: row[k] for k in ("entry", "class", "si", "oi")
                    if k in row},
            "oracleMatch": matches,
            "note": ("row bytes == engine/materials oracle" if matches
                     else "row bytes match NO oracle row — rows-file "
                          "defect")})

# ---- coordinator rulings (only needed when honest flags exist) ----------------
rulings_path = HERE / "f1-blind-r1-coordinator-rulings-20260905.json"
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
    "schemaVersion": "f1-blind-r1-adjudication",
    "lane": "F1", "round": "r1",
    "rowsFile": {"path": str(HERE / "f1-blind-r1-rows-20260905.json"),
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
(HERE / "f1-blind-r1-adjudication-20260905.json").write_text(
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
