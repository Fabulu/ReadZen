#!/usr/bin/env python3
"""Build the R1b blind-review round-1 rows file + canary registry.

Run ONLY after r1b-gates-20260903.json verdict == CLEAN.

Honest rows (47 — one per engine edit record, re-derived from the CLONE
pre-state via the engine, never from the receipt):
  occ-remove-retired (46)  the removed occurrence's relPath + full Kwic
                           + masterName at (si, oi) in the pre materials,
                           plus the sense's POST occurrence relPath list
                           (reviewer law: post == pre minus exactly the
                           row's occurrence; relPath must be one of the
                           two retired rels).
  note-count-rewrite (1)   before/after count sentence + the live POST
                           occurrence count and distinct-rel count.

Reviewer materials FROZEN under maintenance/r1b-blind-r1-materials/:
pre/<eid>.json (clone canon) and post/<eid>.json (terms bytes) for all
43 entries; shas pinned in the rows-file header. The retired pair is
published in the rows header (it is lane law, not a secret).

Canary law (SPEC §5): 7 planted DEFECT rows bound by rowSha payload
identity, fixed-stride slots, every mutation detectable from the row +
frozen materials alone:
  P1 relPath swapped to the OTHER retired rel (mismatches pre at si,oi)
  P2 oi off-by-one (row points at a surviving occurrence)
  P3 si off-by-one (row points into the wrong sense)
  P4 removedKwic mutated (mismatches the pre occurrence)
  P5 note after-sentence count inflated (contradicts POST materials)
  P6 fabricated removal of a SURVIVOR (post still holds the occurrence)
  P7 masterName mutated (mismatches the pre occurrence)

Outputs:
  maintenance/r1b-blind-r1-rows-20260903.json    (reviewer input)
  maintenance/r1b-blind-r1-plants-20260903.json  (coordinator registry)
  maintenance/r1b-blind-r1-materials/            (frozen verification set)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))

gates = json.loads((HERE / "r1b-gates-20260903.json").read_text(encoding="utf-8"))
if gates.get("verdict") != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates.get('verdict')} — blind round "
                     "may not start")

_spec = importlib.util.spec_from_file_location(
    "r1b_eng", HERE / "r1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)
RETIRED = sorted(eng.RETIRED)

import copy  # noqa: E402
by_id = eng.clone_state()
worklist = eng.derive(by_id)[0]
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)
assert len(records) == 47 and len(worklist) == 43

# ---- materials: frozen pre/post entry copies ---------------------------------
MAT = HERE / "r1b-blind-r1-materials"
if MAT.exists():
    shutil.rmtree(MAT)
(MAT / "pre").mkdir(parents=True)
(MAT / "post").mkdir(parents=True)
for eid in worklist:
    (MAT / "pre" / f"{eid}.json").write_text(eng.canon(pre_state[eid]),
                                             encoding="utf-8", newline="")
    terms_bytes = (BUILD / "terms" / eid / "entry.v2.json").read_bytes()
    assert terms_bytes == out[eid].encode("utf-8"), f"terms drift {eid}"
    (MAT / "post" / f"{eid}.json").write_bytes(terms_bytes)

pre_obj = {eid: json.loads((MAT / "pre" / f"{eid}.json").read_text(
    encoding="utf-8")) for eid in worklist}
post_obj = {eid: json.loads((MAT / "post" / f"{eid}.json").read_text(
    encoding="utf-8")) for eid in worklist}


def sense(obj, eid, si):
    return obj[eid]["Senses"][si - 1]


def honest_row(rec: dict) -> dict:
    eid, si = rec["entry"], rec["si"]
    if rec["class"] == "occ-remove-retired":
        o = (sense(pre_obj, eid, si).get("Occurrences") or [])[rec["oi"] - 1]
        post_occs = sense(post_obj, eid, si).get("Occurrences") or []
        return {
            "entry": eid, "class": "occ-remove-retired", "si": si,
            "oi": rec["oi"], "relPath": o.get("RelPath"),
            "removedKwic": str(o.get("Kwic") or ""),
            "masterName": o.get("MasterName"),
            "postOccurrenceRels": [x.get("RelPath") for x in post_occs],
            "postOccurrenceCount": len(post_occs),
        }
    note = str(sense(post_obj, eid, si).get("Note") or "")
    after = next(r for r in eng.SENT_RE.findall(note))
    post_occs = sense(post_obj, eid, si).get("Occurrences") or []
    return {
        "entry": eid, "class": "note-count-rewrite", "si": si,
        "before": rec["before"], "after": after,
        "postOccurrences": len(post_occs),
        "postDistinctRels": len({x.get("RelPath") for x in post_occs}),
    }


rows = [honest_row(rec) for rec in records]
honest_count = len(rows)
assert honest_count == 47, honest_count
note_row_idx = next(i for i, r in enumerate(rows)
                    if r["class"] == "note-count-rewrite")


# ---- payload binding ----------------------------------------------------------
def body_json(r: dict) -> str:
    body = {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}
    return json.dumps(body, ensure_ascii=False, sort_keys=True)


def row_sha(r: dict) -> str:
    return hashlib.sha256(body_json(r).encode("utf-8")).hexdigest()


# ---- plants (payload-bound canaries) ------------------------------------------
def plant_from(src: dict, mutate) -> dict:
    r = json.loads(json.dumps(src, ensure_ascii=False))
    mutate(r)
    return r


# P1: relPath swapped to the OTHER retired rel (pre bytes contradict)
def _p1(r):
    r["relPath"] = next(x for x in RETIRED if x != r["relPath"])


p1 = plant_from(rows[0], _p1)

# P2: oi off-by-one -> points at a surviving occurrence of the sense
def _p2(r):
    pre_occs = sense(pre_obj, r["entry"], r["si"]).get("Occurrences") or []
    assert r["oi"] + 1 <= len(pre_occs)
    r["oi"] = r["oi"] + 1


p2 = plant_from(next(r for r in rows
                     if r["class"] == "occ-remove-retired"
                     and r["oi"] + 1 <= len(
                         sense(pre_obj, r["entry"], r["si"])
                         .get("Occurrences") or [])), _p2)

# P3: si off-by-one -> wrong sense
def _p3(r):
    assert r["si"] + 1 <= len(pre_obj[r["entry"]]["Senses"])
    r["si"] = r["si"] + 1


p3 = plant_from(next(r for r in rows
                     if r["class"] == "occ-remove-retired"
                     and r["si"] + 1 <= len(
                         pre_obj[r["entry"]]["Senses"])), _p3)

# P4: removedKwic mutated (one char changed inside)
def _p4(r):
    kw = list(r["removedKwic"])
    i = len(kw) // 2
    kw[i] = "猫" if kw[i] != "猫" else "狗"
    r["removedKwic"] = "".join(kw)


p4 = plant_from(rows[5], _p4)

# P5: note after-sentence count inflated (contradicts POST materials)
def _p5(r):
    n = r["postOccurrences"] + 1
    r["after"] = (f"{n} exact occurrences from "
                  f"{r['postDistinctRels']} distinct works")


p5 = plant_from(rows[note_row_idx], _p5)

# P6: fabricated removal of a SURVIVOR (post still holds the occurrence)
def _p6(r):
    eid = next(e for e in worklist
               if len(sense(post_obj, e, 1).get("Occurrences") or []) >= 2)
    post_occs = sense(post_obj, eid, 1).get("Occurrences") or []
    victim = post_occs[0]
    r.update({"entry": eid, "si": 1, "oi": 1,
              "relPath": victim.get("RelPath"),
              "removedKwic": str(victim.get("Kwic") or ""),
              "masterName": victim.get("MasterName"),
              "postOccurrenceRels": [x.get("RelPath")
                                     for x in post_occs],
              "postOccurrenceCount": len(post_occs)})


p6 = plant_from(rows[11], _p6)

# P7: masterName mutated (mismatches the pre occurrence at si,oi)
def _p7(r):
    r["masterName"] = "虛構禪師"


p7 = plant_from(rows[16], _p7)

plants = [p1, p2, p3, p4, p5, p6, p7]
PLANT_NOTES = [
    "relPath swapped to the other retired rel (pre bytes contradict)",
    "oi off-by-one (row points at a surviving occurrence)",
    "si off-by-one (row points into the wrong sense)",
    "removedKwic mutated (mismatches the pre occurrence)",
    "note after-sentence count inflated (contradicts POST materials)",
    "fabricated removal of a survivor (post still holds it)",
    "masterName mutated (mismatches the pre occurrence)",
]

total = honest_count + len(plants)
slots = sorted((i * 7919) % total for i in range(len(plants)))
assert len(set(slots)) == len(plants), slots

out_rows: list[dict] = []
plant_registry = []
ri = 0
for slot in range(total):
    if slot in slots:
        idx = slots.index(slot)
        p = plants[idx]
        p["rowId"] = f"R{slot:04d}"
        p["rowSha"] = row_sha(p)
        plant_registry.append({
            "plantId": f"P{idx + 1}", "rowSlot": slot,
            "bindPayloadKind": "rowSha", "bindPayloadSha256": p["rowSha"],
            "entry": p["entry"], "class": p["class"],
            "defect": PLANT_NOTES[idx],
        })
        out_rows.append(p)
    else:
        r = rows[ri]
        ri += 1
        r["rowId"] = f"R{slot:04d}"
        r["rowSha"] = row_sha(r)
        out_rows.append(r)
assert ri == honest_count

seen: dict[str, str] = {}
for r in out_rows:
    assert r["rowSha"] not in seen, (r["rowId"], seen.get(r["rowSha"]))
    seen[r["rowSha"]] = r["rowId"]
for p in plant_registry:
    assert seen[p["bindPayloadSha256"]] == f"R{p['rowSlot']:04d}"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


materials_pins = {}
for eid in worklist:
    materials_pins[f"pre/{eid}.json"] = sha(MAT / "pre" / f"{eid}.json")
    materials_pins[f"post/{eid}.json"] = sha(MAT / "post" / f"{eid}.json")

rows_doc = {
    "schemaVersion": "r1b-blind-r1-rows",
    "retiredRels": RETIRED,
    "materialsDir": str(MAT),
    "materials": materials_pins,
    "rows": out_rows,
}
rows_path = HERE / "r1b-blind-r1-rows-20260903.json"
rows_path.write_text(json.dumps(rows_doc, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
plants_path = HERE / "r1b-blind-r1-plants-20260903.json"
plants_path.write_text(json.dumps({
    "schemaVersion": "r1b-blind-r1-plants",
    "honestRows": honest_count, "plants": len(plants),
    "slots": slots,
    "registry": plant_registry}, ensure_ascii=False, indent=1),
    encoding="utf-8", newline="")
print(json.dumps({
    "rows": len(out_rows), "honest": honest_count, "plants": len(plants),
    "slots": slots,
    "rowsSha256": hashlib.sha256(rows_path.read_bytes()).hexdigest()[:16],
    "plantsSha256": hashlib.sha256(plants_path.read_bytes())
    .hexdigest()[:16],
}, ensure_ascii=False, indent=2))
