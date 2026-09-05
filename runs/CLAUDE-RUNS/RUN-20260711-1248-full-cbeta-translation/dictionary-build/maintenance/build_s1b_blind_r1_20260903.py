#!/usr/bin/env python3
"""Build the S1-b/R blind-review round-1 rows file + canary registry.

Run ONLY after s1b-gates-20260903.json verdict == CLEAN.

Honest rows (112 — one per engine edit record, re-derived from the CLONE
pre-state via the engine, never from the receipt):
  anchor-remove (112)  the removed anchor's full ClaimText + Kwic, the
                       post occurrences covering that Kwic (relPath +
                       masterName), and the sense's post anchor shape
                       (survivor ClaimTexts; null when the key is gone).

Reviewer materials FROZEN under maintenance/s1b-blind-r1-materials/:
pre/<eid>.json (clone canon) and post/<eid>.json (terms bytes) for all
53 entries; shas pinned in the rows-file header.

Canary law (SPEC §5): 7 planted DEFECT rows bound by rowSha payload
identity, fixed-stride slots, every mutation detectable from the row +
frozen materials alone:
  P1 removed kwic mutated (contained in no pre anchor / post kwic)
  P2 coveredBy holder relpath swapped to an occurrence that does not
     contain the kwic
  P3 removedClaimText not matching the pre anchor at (si, aidx)
  P4 postSurvivorClaimTexts lists a survivor the post materials lack
  P5 aidx off-by-one (points at the wrong pre anchor)
  P6 si off-by-one (points at the wrong sense)
  P7 claims the well-formed survivor anchor of the one partial-removal
     sense was removed, with post shape fabricated to match

Outputs:
  maintenance/s1b-blind-r1-rows-20260903.json    (reviewer input)
  maintenance/s1b-blind-r1-plants-20260903.json  (coordinator registry)
  maintenance/s1b-blind-r1-materials/            (frozen verification set)
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

gates = json.loads((HERE / "s1b-gates-20260903.json").read_text(encoding="utf-8"))
if gates.get("verdict") != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates.get('verdict')} — blind round "
                     "may not start")

_spec = importlib.util.spec_from_file_location(
    "s1b_eng", HERE / "s1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

import copy  # noqa: E402
by_id = eng.clone_state()
worklist = eng.derive(by_id)[0]
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)
assert len(records) == 112 and len(worklist) == 53

# ---- materials: frozen pre/post entry copies ---------------------------------
MAT = HERE / "s1b-blind-r1-materials"
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
    eid, si, aidx = rec["entry"], rec["si"], rec["aidx"]
    a = (sense(pre_obj, eid, si).get("ClaimAnchors") or [])[aidx - 1]
    kw = str(a.get("Kwic") or "")
    holders = [{"relPath": o.get("RelPath"), "masterName": o.get("MasterName")}
               for o in sense(post_obj, eid, si).get("Occurrences") or []
               if kw and kw in str(o.get("Kwic") or "")]
    post_anchors = sense(post_obj, eid, si).get("ClaimAnchors")
    return {
        "entry": eid, "class": "anchor-remove", "si": si, "aidx": aidx,
        "removedClaimText": str(a.get("ClaimText") or ""),
        "removedKwic": kw,
        "coveredBy": holders,
        "postSurvivorClaimTexts": (None if post_anchors is None
                                   else [str(x.get("ClaimText") or "")
                                         for x in post_anchors]),
    }


rows = [honest_row(rec) for rec in records]
honest_count = len(rows)
assert honest_count == 112, honest_count


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


# P1: removed kwic mutated (one char changed inside)
def _p1(r):
    kw = list(r["removedKwic"])
    i = len(kw) // 2
    kw[i] = "猫" if kw[i] != "猫" else "狗"
    r["removedKwic"] = "".join(kw)


p1 = plant_from(rows[0], _p1)

# P2: coveredBy holder swapped to another occurrence of the same sense
# that does NOT contain the kwic (or fabricated when none exists)
def _p2(r):
    eid, si = r["entry"], r["si"]
    others = [o for o in sense(post_obj, eid, si).get("Occurrences") or []
              if r["removedKwic"] not in str(o.get("Kwic") or "")]
    r["coveredBy"] = [{"relPath": (others[0].get("RelPath")
                                   if others else "Z/Z99/Z99n9999.xml"),
                       "masterName": (others[0].get("MasterName")
                                      if others else "Someone Else")}]
    if others:
        # the planted holder must genuinely NOT contain the removed kwic
        kw = r["removedKwic"]
        assert kw not in str(next(
            o for o in sense(post_obj, eid, si)["Occurrences"]
            if o.get("RelPath") == r["coveredBy"][0]["relPath"]
        ).get("Kwic") or "")


p2 = plant_from(rows[3], _p2)

# P3: removedClaimText not matching the pre anchor at (si, aidx)
p3 = plant_from(rows[7], lambda r: r.__setitem__(
    "removedClaimText", "與原句不同的虛構引文"))

# P4: postSurvivorClaimTexts lists a survivor the post materials lack
p4 = plant_from(
    next(r for r in rows if r["postSurvivorClaimTexts"]),
    lambda r: r.__setitem__("postSurvivorClaimTexts",
                            r["postSurvivorClaimTexts"] + ["虛構的倖存錨點"]))

# P5: aidx off-by-one -> wrong pre anchor
def _p5(r):
    pre_a = sense(pre_obj, r["entry"], r["si"]).get("ClaimAnchors") or []
    assert len(pre_a) >= r["aidx"] + 1
    other = pre_a[r["aidx"]]
    r["aidx"] = r["aidx"] + 1
    r["removedClaimText"] = str(other.get("ClaimText") or "")
    r["removedKwic"] = str(other.get("Kwic") or "")


p5 = plant_from(next(r for r in rows
                     if len(sense(pre_obj, r["entry"], r["si"])
                            .get("ClaimAnchors") or []) > r["aidx"]
                     # P2's source (rows[3]) and its neighbors share the
                     # entry; re-targeting aidx there reconstructs P2's
                     # row and collides by rowSha
                     and r["entry"] != rows[3]["entry"]), _p5)

# P6: si off-by-one -> wrong sense
def _p6(r):
    e = pre_obj[r["entry"]]
    assert r["si"] + 1 <= len(e["Senses"])
    r["si"] = r["si"] + 1


p6 = plant_from(next(r for r in rows
                     if r["si"] + 1 <= len(pre_obj[r["entry"]]["Senses"])), _p6)

# P7: claims the well-formed SURVIVOR of the one partial-removal sense
# (t_cf6aac2f936b 一字關 s1) was removed, post shape fabricated
def _p7(r):
    eid = "t_cf6aac2f936b"
    pre_a = sense(pre_obj, eid, 1).get("ClaimAnchors") or []
    surv_idx = 4
    surv = pre_a[surv_idx - 1]
    r.update({"entry": eid, "si": 1, "aidx": surv_idx,
              "removedClaimText": str(surv.get("ClaimText") or ""),
              "removedKwic": str(surv.get("Kwic") or ""),
              "coveredBy": [], "postSurvivorClaimTexts": []})


p7 = plant_from(rows[10], _p7)

plants = [p1, p2, p3, p4, p5, p6, p7]
PLANT_NOTES = [
    "removed kwic mutated (contained in no pre anchor / post kwic)",
    "coveredBy holder does not contain the removed kwic",
    "removedClaimText mismatches the pre anchor at (si, aidx)",
    "postSurvivorClaimTexts lists a survivor the post materials lack",
    "aidx off-by-one (points at the wrong pre anchor)",
    "si off-by-one (points at the wrong sense)",
    "claims the well-formed partial-sense survivor was removed",
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
    "schemaVersion": "s1b-blind-r1-rows",
    "materialsDir": str(MAT),
    "materials": materials_pins,
    "rows": out_rows,
}
rows_path = HERE / "s1b-blind-r1-rows-20260903.json"
rows_path.write_text(json.dumps(rows_doc, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
plants_path = HERE / "s1b-blind-r1-plants-20260903.json"
plants_path.write_text(json.dumps({
    "schemaVersion": "s1b-blind-r1-plants",
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
