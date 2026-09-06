#!/usr/bin/env python3
"""Lane-generic blind-review adjudicator (campaign-1000, r9+).

Parameterized clone of adjudicate_r8_blind_r1_20260906.py:

    python -X utf8 lane_blind_adjudicate.py <cohort> <round> <reviewer-subdir>

Create lanes have no delta repairs, so PASS requires: materialsPinsOk,
zero missed plants, and every honest-row flag adjudicated. On PASS writes
fresh-build/<cohort>/<cohort>-release-review.json (schema
<cohort>-release-review.v1) binding deck + verdicts + plants — the
record the release generator and the publisher gate on. Honest-row
flags -> REVIEW: adjudicate by hand, repair, rebuild deck (next round),
re-review. One adjudication is machine-checkable: a law-P flag whose
row entry + roster name appear in maintenance/<cohort>-prose-
adjudications.json (the lane prose-evidence whitelist, evidence quoted
in the file) is recorded as an adjudicated flag and does not force
REVIEW; anything else does. Multi-round: an existing release-review's
"rounds" map is carried forward when adjudicating r2+.
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]

if len(sys.argv) != 4:
    sys.exit(__doc__)
COHORT, ROUND, SUBREL = sys.argv[1], sys.argv[2], sys.argv[3]
LANE = BUILD / "fresh-build" / COHORT
SUB = BUILD / SUBREL


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


verdicts = json.loads((SUB / f"verdicts-{ROUND}.json")
                      .read_text(encoding="utf-8-sig"))
plants = json.loads((LANE / f"blind-{ROUND}-plants.json")
                    .read_text(encoding="utf-8-sig"))
deck = json.loads((LANE / f"blind-{ROUND}-rows.json")
                  .read_text(encoding="utf-8-sig"))

rows_by_id = {r["rowId"]: r for r in deck["rows"]}
plant_by_slot = {p["slot"]: p for p in plants["registry"]}
plant_row_ids = {f"r{p['slot']:03d}" for p in plants["registry"]}

print(f"reviewer: {verdicts.get('reviewer')}")
print(f"round: {verdicts.get('round')}")
print(f"materialsPinsOk: {verdicts.get('materialsPinsOk')}")
print(f"rowsChecked: {verdicts.get('rowsChecked')} of {len(rows_by_id)}")
flags = verdicts.get("flags") or []
flagged = {f["rowId"] for f in flags}

detected = sorted(flagged & plant_row_ids)
missed = sorted(plant_row_ids - flagged)
honest_flags = [f for f in flags if f["rowId"] not in plant_row_ids]

print(f"\nflags total: {len(flags)}")
print(f"plants detected: {len(detected)}/{len(plant_row_ids)}  {detected}")
for rid in detected:
    p = plant_by_slot[int(rid[1:])]
    fl = next(f for f in flags if f["rowId"] == rid)
    print(f"  {rid} [{p['label']}] flagged law {fl.get('law')}: "
          f"{fl.get('reason', '')[:90]}")
print(f"plants MISSED: {len(missed)}  {missed}")
for rid in missed:
    p = plant_by_slot[int(rid[1:])]
    print(f"  {rid} [{p['label']}] NOT flagged")
print(f"honest-row flags (adjudicate by hand): {len(honest_flags)}")
wl_path = BUILD / "maintenance" / f"{COHORT}-prose-adjudications.json"
PROSE_WL = (json.loads(wl_path.read_text(encoding="utf-8-sig"))
            if wl_path.is_file() else {})
adjudicated, unadjudicated = [], []
for f in honest_flags:
    r = rows_by_id.get(f["rowId"], {})
    eid = r.get("entry")
    covered = None
    if f.get("law") == "P" and eid in PROSE_WL:
        for w in PROSE_WL[eid]:
            if re.search(rf"(?<![A-Za-z]){re.escape(w['name'])}(?![A-Za-z])",
                         f.get("reason", "")):
                covered = w
                break
    if covered:
        adjudicated.append((f, r, covered))
        print(f"  {f['rowId']} law {f.get('law')} entry {eid} term "
              f"{r.get('term')}: ADJUDICATED (prose whitelist: "
              f"{covered['name']}) {f.get('reason', '')[:100]}")
    else:
        unadjudicated.append((f, r))
        print(f"  {f['rowId']} law {f.get('law')} entry "
              f"{eid} term {r.get('term')}: "
              f"{f.get('reason', '')[:120]}")

if verdicts.get("notes"):
    print(f"\nnotes: {verdicts['notes'][:600]}")

verdict = ("PASS" if (verdicts.get("materialsPinsOk")
                      and not missed and not unadjudicated)
           else "REVIEW")
print(f"\nadjudication: {verdict}")

if verdict == "PASS":
    pmap_path = LANE / "products" / "product-map.json"
    pmap = json.loads(pmap_path.read_text(encoding="utf-8-sig"))
    rows = pmap["products"]
    assert len(rows) == len(json.loads(
        (LANE / f"{COHORT}-plan.json").read_text(encoding="utf-8-sig"))
        ["entries"]), "product-map size != plan size"
    deck_path = LANE / f"blind-{ROUND}-rows.json"
    plants_path = LANE / f"blind-{ROUND}-plants.json"
    verdicts_path = SUB / f"verdicts-{ROUND}.json"
    rounds_desc = {ROUND: f"full create-mode deck over the {len(rows)} new "
                          f"products: laws A-H+P+Z swept, "
                          f"{len(plant_row_ids)}-plant canary set"}
    prev_path = LANE / f"{COHORT}-release-review.json"
    if prev_path.is_file():
        prev = json.loads(prev_path.read_text(encoding="utf-8-sig"))
        rounds_desc = {**prev.get("rounds", {}), **rounds_desc}
    review = {
        "schemaVersion": f"{COHORT}-release-review.v1",
        "cohort": COHORT,
        "reviewer": (f"blind reviewer ({verdicts.get('reviewer')}) + "
                     f"coordinator canary adjudication"),
        "reviewedUtc": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS",
        "rounds": rounds_desc,
        "boundProducts": [{"id": r["id"], "term": r["term"],
                           "sha256": r["entrySha256"]} for r in rows],
        "constructionBindings": {
            "productMap": {"path": str(pmap_path), "sha256": sha(pmap_path)},
            "blindDeckRows": {"path": str(deck_path), "sha256": sha(deck_path)},
            "blindVerdicts": {"path": str(verdicts_path),
                              "sha256": sha(verdicts_path)},
            "plantsRegistry": {"path": str(plants_path),
                               "sha256": sha(plants_path)},
            "plantsDetected": len(detected),
            "plantsTotal": len(plant_row_ids),
            "rowsChecked": verdicts.get("rowsChecked"),
            "hardPass": True,
            "publicMutation": False,
        },
        "perProductTrace": [{"id": r["id"],
                             "dispositionSource": f"{COHORT}-blind-{ROUND}-adjudicated",
                             "evidence": "laws A-H+P+Z verified by the blind "
                                         "reviewer on the create-mode deck; "
                                         "row not a flagged canary"
                                         + ("" if r["id"] not in
                                            {a[1].get("entry") for a in adjudicated}
                                            else "; law-P flag adjudicated via "
                                                 + wl_path.name)}
                            for r in rows],
        "adjudicatedHonestFlags": [
            {"rowId": f["rowId"], "law": f.get("law"), "entry": r.get("entry"),
             "term": r.get("term"), "reason": f.get("reason"),
             "whitelistName": w["name"], "whitelistReason": w.get("reason"),
             "source": str(wl_path)}
            for f, r, w in adjudicated],
        "failures": [],
    }
    out = LANE / f"{COHORT}-release-review.json"
    out.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"release review written: {out}")
    print(f"  sha256: {sha(out)}")
