#!/usr/bin/env python3
"""Build the F1 blind-review round-1 rows file + canary registry.

Run ONLY after f1-gates-20260905.json verdict == CLEAN.

Honest rows (5 — one per engine edit record, re-derived from the CLONE
pre-state via the engine, never from the receipt):
  occ-attribution (2)          old/new attribution identity at (si, oi)
                               with the carried relPath/fromLb/toLb/
                               kwic, post occurrence rels + count.
  explanation-rewrite (1)      field + [[before, after]] find-once.
  relatedmasters-rename (2)    rename + post RelatedMasters list.

Reviewer materials FROZEN under maintenance/f1-blind-r1-materials/:
pre/<eid>.json (clone canon) and post/<eid>.json (terms bytes) for the
two products; shas pinned in the rows-file header. Lane law published
in the header: T48n2025 is an institutional regulation compilation (元
德煇重編); the lane law names, not secrets: retired rels + the defect
census.

Canary law (SPEC §4): 5 planted DEFECT rows bound by rowSha payload
identity, fixed-stride slots, every mutation detectable from the row +
frozen materials alone:
  P1 MasterName kept as the fabricated speaker (post slot is null)
  P2 ContextMasters role corrupted compiler->utterer (post contradicts)
  P3 ActorLabel swapped to a voice absent from the new note (post
     contradicts; label-verbatim law)
  P4 kwic mutated (post slot contradicts)
  P5 fabricated CJK quote injected into the Explanation after-string
     (not in POST field; ALSO unanchored over post kwics — asserted)

Outputs:
  maintenance/f1-blind-r1-rows-20260905.json    (reviewer input)
  maintenance/f1-blind-r1-plants-20260905.json  (coordinator registry)
  maintenance/f1-blind-r1-materials/            (frozen verification set)
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

gates = json.loads((HERE / "f1-gates-20260905.json").read_text("utf-8"))
if gates.get("verdict") != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates.get('verdict')} — blind "
                     "round may not start")

_spec = importlib.util.spec_from_file_location(
    "f1_eng", HERE / "f1_transform_20260905.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)
RETIRED = sorted(eng.RETIRED)
E_AB = "t_ab715aa474d5"
E_Z = "t_351fa42d396b"

import copy  # noqa: E402
by_id = eng.clone_state()          # pins 8457672 + clean
worklist = eng.derive(by_id)
assert worklist == list(eng.COHORT), worklist
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, records = eng.transform(snapshot)
assert len(records) == 5, len(records)

MAT = HERE / "f1-blind-r1-materials"
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
    if rec["class"] == "occ-attribution":
        post_occs = sense(post_obj, eid, si).get("Occurrences") or []
        pre_occ = sense(pre_obj, eid, si)["Occurrences"][rec["oi"] - 1]
        return {
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
        }
    if rec["class"] in ("explanation-rewrite", "note-rewrite",
                        "attributionnote-rewrite"):
        return {
            "entry": eid, "class": rec["class"], "si": si,
            "field": rec["field"], "oi": rec.get("oi"),
            "before": rec["before"], "after": rec["after"],
        }
    if rec["class"] == "relatedmasters-rename":
        return {
            "entry": eid, "class": "relatedmasters-rename", "si": si,
            "renamed": rec["renamed"],
            "postRelatedMasters": rec["postRelatedMasters"],
        }
    assert rec["class"] == "searchaliases-add", rec["class"]
    return {
        "entry": eid, "class": "searchaliases-add", "si": si,
        "added": rec["added"],
        "postSearchAliases": rec["postSearchAliases"],
    }


rows = [honest_row(rec) for rec in records]
honest_count = len(rows)
assert honest_count == 5, honest_count

by_key = {}
for r in rows:
    by_key.setdefault((r["entry"], r["class"]), r)
occ_ab = next(r for r in rows if r["class"] == "occ-attribution"
              and r["carriedFromLb"] == "1144b03")
occ_z = next(r for r in rows if r["class"] == "occ-attribution"
             and r["carriedFromLb"] == "1127c04")
expl_z = by_key[(E_Z, "explanation-rewrite")]


def body_json(r: dict) -> str:
    body = {k: v for k, v in r.items() if k not in ("rowId", "rowSha")}
    return json.dumps(body, ensure_ascii=False, sort_keys=True)


def row_sha(r: dict) -> str:
    return hashlib.sha256(body_json(r).encode("utf-8")).hexdigest()


def plant_from(src: dict, mutate) -> dict:
    r = json.loads(json.dumps(src, ensure_ascii=False))
    mutate(r)
    return r


def post_slot(eid, si, oi):
    return sense(post_obj, eid, si)["Occurrences"][oi - 1]


def post_field(eid, si, field):
    return str(sense(post_obj, eid, si).get(field) or "")


def all_post_kwics(eid):
    out_k = []
    for s in post_obj[eid].get("Senses") or []:
        for o in s.get("Occurrences") or []:
            out_k.append(str(o.get("Kwic") or ""))
        for a in s.get("ClaimAnchors") or []:
            out_k.append(str(a.get("Kwic") or ""))
    return out_k


# P1: MasterName kept as the fabricated speaker (post slot is null)
def _p1(r):
    r["newMasterName"] = "Dongyang Dehui"


p1 = plant_from(occ_ab, _p1)
assert post_slot(E_AB, p1["si"], p1["oi"])["MasterName"] \
    != p1["newMasterName"]

# P2: ContextMasters role corrupted compiler->utterer (post contradicts)
def _p2(r):
    r["newContextMasters"] = [
        {"MasterName": "Dongyang Dehui", "Roles": ["utterer"]}]


p2 = plant_from(occ_z, _p2)
assert post_slot(E_Z, p2["si"], p2["oi"])["ContextMasters"] \
    != p2["newContextMasters"]

# P3: ActorLabel swapped to a voice absent from the new note
def _p3(r):
    r["newActorAttribution"] = dict(r["newActorAttribution"])
    r["newActorAttribution"]["ActorLabel"] = \
        "the code compiler's editorial voice"


p3 = plant_from(occ_ab, _p3)
_p3_label = p3["newActorAttribution"]["ActorLabel"]
assert _p3_label not in p3["newAttributionNote"]
assert _p3_label not in json.dumps(
    post_slot(E_AB, p3["si"], p3["oi"]).get("ActorAttribution"),
    ensure_ascii=False)

# P4: kwic mutated (post slot contradicts)
def _p4(r):
    kw = list(r["carriedKwic"])
    i = len(kw) // 2
    kw[i] = "猫" if kw[i] != "猫" else "狗"
    r["carriedKwic"] = "".join(kw)


p4 = plant_from(occ_z, _p4)
assert post_slot(E_Z, p4["si"], p4["oi"])["Kwic"] != p4["carriedKwic"]

# P5: fabricated CJK quote injected into the Explanation after-string
FAB = "非粥非飯"


def _p5(r):
    r["after"] = r["after"].replace(
        "Dongyang Dehui", "Dongyang Dehui (" + FAB + ")", 1)


p5 = plant_from(expl_z, _p5)
assert FAB in p5["after"]
assert FAB not in post_field(E_Z, 1, "Explanation")
assert not any(FAB in k for k in all_post_kwics(E_Z)), \
    "P5 fabrication accidentally anchored"

plants = [p1, p2, p3, p4, p5]
PLANT_NOTES = [
    "MasterName kept as fabricated speaker (post slot is null)",
    "ContextMasters role corrupted compiler->utterer (post contradicts)",
    "ActorLabel absent from the new note (label-verbatim law)",
    "kwic mutated (post slot contradicts)",
    "fabricated CJK quote injected into Explanation (not in POST; "
    "unanchored)",
]

total = honest_count + len(plants)
slots = sorted((i * 4 + 2) % total for i in range(len(plants)))
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
    "schemaVersion": "f1-blind-r1-rows",
    "laneLaw": {
        "retiredRels": RETIRED,
        "t48n2025Class": ("institutional regulation compilation; the "
                          "redactor Dongyang Dehui is never a speaking "
                          "master; roster name is 'Dongyang Dehui'"),
        "defectCensus": eng.DEFECT_CENSUS,
    },
    "materialsDir": str(MAT),
    "materials": materials_pins,
    "rows": out_rows,
}
rows_path = HERE / "f1-blind-r1-rows-20260905.json"
rows_path.write_text(json.dumps(rows_doc, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
plants_path = HERE / "f1-blind-r1-plants-20260905.json"
plants_path.write_text(json.dumps({
    "schemaVersion": "f1-blind-r1-plants",
    "honestRows": honest_count, "plants": len(plants),
    "slots": slots,
    "registry": plant_registry}, ensure_ascii=False, indent=1),
    encoding="utf-8", newline="")
print(json.dumps({
    "rows": len(out_rows), "honest": honest_count, "plants": len(plants),
    "slots": slots,
    "rowsSha256": hashlib.sha256(rows_path.read_bytes())
    .hexdigest()[:16],
    "plantsSha256": hashlib.sha256(plants_path.read_bytes())
    .hexdigest()[:16],
}, ensure_ascii=False, indent=2))
