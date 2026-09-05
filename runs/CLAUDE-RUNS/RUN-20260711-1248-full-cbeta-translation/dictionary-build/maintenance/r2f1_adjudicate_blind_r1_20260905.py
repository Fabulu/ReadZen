#!/usr/bin/env python3
"""Adjudicate blind review round r1 for the combined R2+F1 MAIN
publication (the reviewer brief
r2f1-main-blind-r1-reviewer-task-20260905.md).

Ladder (identical in structure to the F1/R2 lanes):

  - Canary coverage: every planted row must be flagged by EVERY
    reviewer. Any miss => verdict VOID (fresh round, fresh reviewers).
  - Honest-row flags are byte-adjudicated against the oracle: the row's
    full payload (minus rowSha) must equal the row rebuilt exactly as
    build_r2f1_blind_r1_20260905.py constructs honest rows — sourced
    ONLY from the FROZEN materials
    (r2f1-main-blind-r1-materials-20260905/, sha-pinned in the rows
    header), never from a clone or git (the publish clone's HEAD moves
    on after the publication commit; the materials are the record).
    Oracle-matching rows that a reviewer flagged need a coordinator
    ruling in r2f1-main-blind-r1-coordinator-rulings-20260905.json
    (refute-with-bytes or confirm); an unruled flag => PENDING; a
    confirmed flag is blocking (fix => fresh round).
  - Reviewer input integrity: rows-file sha256 recorded; every deck
    rowSha re-verifies (deck tamper check); materialsPinsOk=false in
    any verdict is a problem; rowsChecked must equal the deck size.

Outputs maintenance/r2f1-main-blind-r1-adjudication-20260905.json.
Exit 0 iff verdict == PASS.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATS = HERE / "r2f1-main-blind-r1-materials-20260905"
ROWS_PATH = HERE / "r2f1-main-blind-r1-rows-20260905.json"
PLANTS_PATH = HERE / "r2f1-main-blind-r1-plants-20260905.json"

IDS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff",
       "t_ab715aa474d5", "t_351fa42d396b")
PRODUCTS_WITH_WINDOWS = {
    "t_ea2a427c7aba": [("T/T48/T48n2025.xml", "1113a21"),
                       ("T/T48/T48n2025.xml", "1143a07"),
                       ("T/T48/T48n2025.xml", "1143a12")],
    "t_ab715aa474d5": [("T/T48/T48n2025.xml", "1144b03")],
    "t_351fa42d396b": [("T/T48/T48n2025.xml", "1127c04")],
}


def jcanon(o) -> str:
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def body(r: dict) -> dict:
    return {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}


def body_json(r: dict) -> str:
    return jcanon(body(r))


def row_sha(r: dict) -> str:
    return hashlib.sha256(body_json(r).encode("utf-8")).hexdigest()


rows_doc = json.loads(ROWS_PATH.read_text(encoding="utf-8"))
deck = rows_doc["rows"]
if len(deck) != 11:
    raise SystemExit(f"deck has {len(deck)} rows, expected 11")
plants_doc = json.loads(PLANTS_PATH.read_text(encoding="utf-8"))
registry = plants_doc["registry"]

# the materials pins in the rows header must still match the materials
# on disk (the reviewers verified these same pins)
for fname, sha in rows_doc["materialsPins"].items():
    if hashlib.sha256((MATS / fname).read_bytes()).hexdigest() != sha:
        raise SystemExit(f"materials pin drift: {fname}")

problems: list[str] = []
deck_ids = [f"R{i:04d}" for i in range(len(deck))]
deck_by_id = dict(zip(deck_ids, deck))

for rid, r in deck_by_id.items():
    if r.get("rowSha") != row_sha(r):
        problems.append(f"{rid}: rowSha is not sha256(body) "
                        "(deck tampered after build)")

# ---- oracle: honest rows rebuilt exactly as the builder constructs them
main_by_id = {}
staged_by_id = {}
for eid in IDS:
    main_doc = json.loads((MATS / f"main-head-{eid}.json")
                          .read_text(encoding="utf-8"))
    if main_doc.get("__absent__") is True:
        main_by_id[eid] = None
    else:
        main_by_id[eid] = main_doc
    staged_by_id[eid] = json.loads((MATS / f"staged-{eid}.json")
                                   .read_text(encoding="utf-8"))
surface_facts = json.loads((MATS / "surface-facts.json")
                           .read_text(encoding="utf-8"))


def find_occ(entry, rel: str, lb: str):
    if not entry:
        return None, None, None
    for si, s in enumerate(entry.get("Senses") or [], start=1):
        for oi, o in enumerate(s.get("Occurrences") or [], start=1):
            if o.get("RelPath") == rel and o.get("FromLb") == lb:
                return si, oi, o
    return None, None, None


oracle_rows: list[dict] = []
for eid, windows in PRODUCTS_WITH_WINDOWS.items():
    for rel, lb in windows:
        old_o = find_occ(main_by_id.get(eid), rel, lb)[2]
        si, oi, new_o = find_occ(staged_by_id[eid], rel, lb)
        assert new_o is not None, (eid, lb)
        new_aa = new_o.get("ActorAttribution") or {}
        oracle_rows.append({
            "kind": "occ-attribution",
            "note": "publication diff row (main HEAD -> staged)",
            "entry": eid, "relPath": rel, "fromLb": lb,
            "oldWindowPresent": old_o is not None,
            "oldMasterName": old_o.get("MasterName") if old_o else None,
            "oldContextMasters": (old_o.get("ContextMasters")
                                  if old_o else None),
            "oldAttributionNote": (old_o.get("AttributionNote")
                                   if old_o else None),
            "si": si, "oi": oi,
            "newMasterName": new_o.get("MasterName"),
            "newContextMasters": new_o.get("ContextMasters"),
            "newActor": {k: new_aa.get(k) for k in
                         ("Status", "Kind", "ActorLabel", "ActorRole")},
            "newAttributionNote": new_o.get("AttributionNote"),
            "carriedKwic": new_o.get("Kwic"),
            "toLb": new_o.get("ToLb"),
        })

old057 = main_by_id["t_057cc9ea8755"]
new057 = staged_by_id["t_057cc9ea8755"]
old_note = next((o.get("AttributionNote") or ""
                 for s in old057.get("Senses") or []
                 for o in s.get("Occurrences") or []
                 if o.get("RelPath") == "X/X70/X70n1399.xml"), "")
new_note = next((o.get("AttributionNote") or ""
                 for s in new057.get("Senses") or []
                 for o in s.get("Occurrences") or []
                 if o.get("RelPath") == "X/X70/X70n1399.xml"), "")
oracle_rows.append({
    "kind": "note-provenance",
    "note": "057 occ-3 note gains the compiled-by-disciples provenance",
    "entry": "t_057cc9ea8755",
    "relPath": "X/X70/X70n1399.xml",
    "oldNoteHasProvenance": "至柔等編" in old_note,
    "newNoteHasProvenance": "至柔等編" in new_note,
    "newNoteExcerpt": new_note[:160],
})
old968 = main_by_id["t_968a2f97c9ff"]
new968 = staged_by_id["t_968a2f97c9ff"]
oracle_rows.append({
    "kind": "alias-add",
    "note": "968 gains the withdrawn-ID replacement search alias",
    "entry": "t_968a2f97c9ff",
    "oldAliases": old968["Senses"][0].get("SearchAliases") or [],
    "newAliases": new968["Senses"][0].get("SearchAliases") or [],
    "addedAlias": "一不成、二不是",
})
oracle_rows.append({
    "kind": "surface-census",
    "note": "publication surface laws",
    "entryCount": {"before": surface_facts["entryCount"]["before"],
                   "after": surface_facts["entryCount"]["after"]},
    "changedSetEqualsWorklist":
        surface_facts["changedSet"] == sorted(IDS),
    "dehuiCensusBefore": surface_facts["dehuiCensus"]["before"],
    "dehuiCensusAfter": surface_facts["dehuiCensus"]["after"],
    "nonProductRegression": surface_facts["nonProductRegression"],
    "aliasLostCount": len(surface_facts["aliasLost"]),
})
oracle_set = {body_json(r) for r in oracle_rows}
if len(oracle_rows) != plants_doc["honestRows"]:
    raise SystemExit(f"oracle {len(oracle_rows)} != honestRows "
                     f"{plants_doc['honestRows']}")
# every oracle row must actually be present in the deck (builder sanity)
for r in oracle_rows:
    if body_json(r) not in {body_json(x) for x in deck}:
        raise SystemExit(f"oracle row missing from deck: "
                         f"{r.get('kind')} {r.get('entry')}")

# ---- reviewer verdicts -------------------------------------------------------
REVIEWER_FILES = {
    "reviewer1": HERE / "subagents" / "20260905-r2f1-blind-r1-reviewer-1"
                             / "verdicts.json",
    "reviewer2": HERE / "subagents" / "20260905-r2f1-blind-r1-reviewer-2"
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
        "inputRowsSha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
        "verdictsSha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "path": str(p),
        "schema": "flags-based",
    }
    if doc.get("materialsPinsOk") is False:
        problems.append(f"{name}: materials pins failed (tamper)")
    if doc.get("rowsChecked") != len(deck):
        problems.append(f"{name}: rowsChecked {doc.get('rowsChecked')} != "
                        f"{len(deck)} (incomplete check)")
    flagged: dict[str, list[dict]] = {}
    for f in doc.get("flags", []):
        rid = f.get("row") or f.get("rowId")
        if rid not in deck_by_id:
            problems.append(f"{name}: unknown row {rid}")
            continue
        flagged.setdefault(rid, []).append(
            {"verdict": "flag", "reason": f.get("reason") or f.get("claim"),
             "law": f.get("law") or f.get("laws")})
    verdict_maps[name] = {
        rid: (flagged[rid][0] if rid in flagged
              else {"verdict": "accept", "reason": None})
        for rid in deck_by_id}
    flagged_full[name] = flagged
    reviewers[name]["flagCounts"] = {
        rid: len(fs) for rid, fs in sorted(flagged.items())}

# ---- canary coverage ---------------------------------------------------------
canary_results = []
misses = []
for p in registry:
    rid = f"R{p['slot']:04d}"
    row = deck_by_id[rid]
    if row.get("rowSha") != p["bindPayloadSha256"]:
        problems.append(f"{p['label']}: payload binding mismatch at {rid}")
        continue
    caught_by = [n for n in sorted(verdict_maps)
                 if verdict_maps[n].get(rid, {}).get("verdict") == "flag"]
    canary_results.append({
        "plant": p["label"], "rowId": rid, "slotKind": p["slotKind"],
        "caughtBy": caught_by, "missedBy": [n for n in sorted(verdict_maps)
                                            if n not in caught_by]})
    if len(caught_by) < len(verdict_maps):
        misses.append({"plant": p["label"], "rowId": rid,
                       "missedBy": canary_results[-1]["missedBy"]})

# ---- honest-row flags --------------------------------------------------------
plant_ids = {f"R{p['slot']:04d}" for p in registry}
honest_flags = []
for name in sorted(verdict_maps):
    for rid, v in verdict_maps[name].items():
        if rid in plant_ids or v["verdict"] != "flag":
            continue
        row = deck_by_id[rid]
        matches = body_json(row) in oracle_set
        honest_flags.append({
            "rowId": rid, "reviewer": name, "reason": v["reason"],
            "law": v.get("law"),
            "allLaws": [f.get("law") for f in flagged_full[name][rid]],
            "row": {k: row[k] for k in ("entry", "kind", "si", "oi")
                    if k in row},
            "oracleMatch": matches,
            "note": ("row bytes == materials oracle" if matches
                     else "row bytes match NO oracle row — rows-file "
                          "defect")})

# ---- coordinator rulings (only needed when honest flags exist) ---------------
rulings_path = HERE / "r2f1-main-blind-r1-coordinator-rulings-20260905.json"
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
    "schemaVersion": "r2f1-main-blind-r1-adjudication",
    "cohort": "r2f1-main-20260905", "round": "r1",
    "rowsFile": {"path": str(ROWS_PATH),
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
(HERE / "r2f1-main-blind-r1-adjudication-20260905.json").write_text(
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
