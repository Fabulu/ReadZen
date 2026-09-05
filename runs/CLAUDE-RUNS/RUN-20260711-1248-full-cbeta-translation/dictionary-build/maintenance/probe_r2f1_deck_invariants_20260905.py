#!/usr/bin/env python3
"""Prove the r2f1-main blind deck is well-formed BEFORE reviewers see it.

Laws (all must hold, else the round is void by construction):
  1. binding: for every registry plant, sha256(jcanon(deck row minus
     rowSha)) == bindPayloadSha256, AND the deck row's own rowSha equals
     that same value (rowSha must be the sha of its body, not of a body
     already carrying a rowSha:null member).
  2. self-consistency: every deck row's rowSha == sha256(jcanon(row
     minus rowSha)) — the property the adjudicator's row_sha() relies on.
  3. no-op detection: no plant payload equals ANY honest row (a plant
     whose mutation was a string no-op would be indistinguishable from
     an honest row and would void the canary).
  4. no markers: the rows file bytes contain no "[plant]" leakage.
  5. deck shape: 11 rows; plants at slots 1/4/7; kinds census matches
     5 occ-attribution + 1 note-provenance + 1 alias-add + 1
     surface-census honest rows.
Exit 0 iff all laws hold.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows_path = HERE / "r2f1-main-blind-r1-rows-20260905.json"
plants_path = HERE / "r2f1-main-blind-r1-plants-20260905.json"

rows_bytes = rows_path.read_bytes()
doc = json.loads(rows_bytes.decode("utf-8"))
deck = doc["rows"]
reg = json.loads(plants_path.read_text(encoding="utf-8"))["registry"]


def jcanon(o) -> str:
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def body(r: dict) -> dict:
    return {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}


problems = []

# 4. no markers
if b"[plant]" in rows_bytes:
    problems.append("rows file leaks '[plant]' marker")

# 5. deck shape
if len(deck) != 11:
    problems.append(f"deck has {len(deck)} rows, expected 11")
plant_slots = {p["slot"] for p in reg}
if plant_slots != {1, 4, 7}:
    problems.append(f"plant slots {sorted(plant_slots)} != [1, 4, 7]")
if len(reg) != 3:
    problems.append(f"registry has {len(reg)} plants, expected 3")
honest = [r for i, r in enumerate(deck) if i not in plant_slots]
kind_counts = {}
for r in honest:
    kind_counts[r["kind"]] = kind_counts.get(r["kind"], 0) + 1
if kind_counts != {"occ-attribution": 5, "note-provenance": 1,
                   "alias-add": 1, "surface-census": 1}:
    problems.append(f"honest kind census {kind_counts} unexpected")

# 2. self-consistency
for i, r in enumerate(deck):
    want = hashlib.sha256(jcanon(body(r)).encode("utf-8")).hexdigest()
    if r.get("rowSha") != want:
        problems.append(f"R{i:04d}: rowSha is not sha256(body)")

# 1 + 3. binding + no-op detection
honest_shas = {r.get("rowSha") for r in honest}
for p in reg:
    row = deck[p["slot"]]
    body_sha = hashlib.sha256(jcanon(body(row)).encode("utf-8")).hexdigest()
    if body_sha != p["bindPayloadSha256"]:
        problems.append(f"{p['label']}: payload binding mismatch "
                        f"({body_sha[:12]} != {p['bindPayloadSha256'][:12]})")
    if p["bindPayloadSha256"] in honest_shas:
        problems.append(f"{p['label']}: NO-OP plant — payload identical "
                        "to an honest row")

# p1 kwic divergence, explicitly
p1 = next(p for p in reg if p["label"] == "kwic-mutation-ab715")
p1_row = deck[p1["slot"]]
ab715_honest = next(r for r in honest if r.get("entry") == "t_ab715aa474d5"
                    and r["kind"] == "occ-attribution")
if p1_row.get("carriedKwic") == ab715_honest.get("carriedKwic"):
    problems.append("p1 kwic identical to honest ab715 kwic — mutation "
                    "was a no-op")
else:
    print(f"p1 kwic: honest={ab715_honest['carriedKwic']!r} "
          f"planted={p1_row['carriedKwic']!r}")

print(json.dumps({
    "rows": len(deck), "plants": len(reg),
    "plantSlots": sorted(plant_slots),
    "rowsSha256": hashlib.sha256(rows_bytes).hexdigest(),
    "problems": problems, "ok": not problems,
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not problems else 1)
