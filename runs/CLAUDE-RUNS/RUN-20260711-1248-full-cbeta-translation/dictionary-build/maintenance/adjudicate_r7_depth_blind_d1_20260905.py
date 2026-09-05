#!/usr/bin/env python3
"""Adjudicate the fresh10k-r7-depth blind d1 verdict against the plants
registry. First round for the depth lane (the original occurrences were
reviewed in the r7 lane; this deck covers the added occurrences + the
replace contract), so there is no deltaRepairsResolved set — PASS
requires materialsPinsOk, zero missed plants, zero honest-row flags.
On PASS writes fresh-build/fresh10k-r7-depth/
fresh10k-r7-depth-release-review.json (schema
fresh10k-r7-depth-release-review.v1) binding deck + verdicts + plants —
the record gen_r7_depth_release.py and the publisher gate on. Honest-row
flags -> REVIEW: adjudicate by hand, repair, rebuild deck (d2), re-review."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
SUB = BUILD / "subagents" / "20260905-1153-r7-blind-r1"

ROUND = "d1"          # verdicts file suffix (as instructed to the reviewer)
DECK_ROUND = "r1"     # deck builder's filename stamp for rows/plants files


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


verdicts = json.loads((SUB / f"verdicts-{ROUND}.json")
                      .read_text(encoding="utf-8-sig"))
plants = json.loads(
    (HERE / f"fresh10k-r7-depth-blind-{DECK_ROUND}-plants-20260905.json")
    .read_text(encoding="utf-8-sig"))
deck = json.loads(
    (HERE / f"fresh10k-r7-depth-blind-{DECK_ROUND}-rows-20260905.json")
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
for f in honest_flags:
    r = rows_by_id.get(f["rowId"], {})
    print(f"  {f['rowId']} law {f.get('law')} entry "
          f"{r.get('entry')} term {r.get('term')}: "
          f"{f.get('reason', '')[:120]}")

if verdicts.get("notes"):
    print(f"\nnotes: {verdicts['notes'][:600]}")

verdict = ("PASS" if (verdicts.get("materialsPinsOk")
                      and not missed and not honest_flags)
           else "REVIEW")
print(f"\nadjudication: {verdict}")

if verdict == "PASS":
    pmap_path = BUILD / "fresh-build" / "fresh10k-r7-depth" / "products" \
        / "product-map.json"
    pmap = json.loads(pmap_path.read_text(encoding="utf-8-sig"))
    rows = pmap["products"]
    assert len(rows) == 123, len(rows)
    deck_path = HERE / f"fresh10k-r7-depth-blind-{DECK_ROUND}-rows-20260905.json"
    plants_path = HERE / f"fresh10k-r7-depth-blind-{DECK_ROUND}-plants-20260905.json"
    verdicts_path = SUB / f"verdicts-{ROUND}.json"
    review = {
        "schemaVersion": "fresh10k-r7-depth-release-review.v1",
        "cohort": "fresh10k-r7-depth",
        "reviewer": (f"blind reviewer (resumed from r7 r1+r2+r3: "
                     f"{verdicts.get('reviewer')}) + coordinator canary "
                     f"adjudication"),
        "reviewedUtc": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS",
        "rounds": {
            "d1": "delta deck over the 123 depth products: baseline "
                  "occurrences anchored by terms/<id> sha; added "
                  "occurrences + replace contract law-swept; fresh "
                  "delta-tuned canary set",
        },
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
                             "dispositionSource": "r7-depth-blind-d1-adjudicated",
                             "evidence": "laws A-H+R+Z verified by the "
                                         "resumed blind reviewer on the "
                                         "depth delta deck; row not a "
                                         "flagged canary"}
                            for r in rows],
        "failures": [],
    }
    out = BUILD / "fresh-build" / "fresh10k-r7-depth" \
        / "fresh10k-r7-depth-release-review.json"
    out.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"release review written: {out}")
    print(f"  sha256: {sha(out)}")
