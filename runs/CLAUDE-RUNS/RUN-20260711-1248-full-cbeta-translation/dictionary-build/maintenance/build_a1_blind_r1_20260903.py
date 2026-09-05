#!/usr/bin/env python3
"""Build the A1 blind-review round-1 rows file + canary registry.

Run ONLY after a1-gates-20260903.json verdict == CLEAN.

Honest rows (116 — one per engine edit record, re-derived from the CLONE
pre-state via the engine, never from the receipt):
  muc-context-row (91)   appended ContextMasters row + the occurrence's
                         AttributionNote (role follows the note's verse
                         law)
  vague-reword (17)       field/find/replace prose repair
  dangling-anchor (1)     the new ClaimAnchor + anchored strings + zc
  performer-context-row (2)
  performer-grammar-proof (1)
  anon-monk-restructure (1)  full post occurrence
  grammar-evidence-repeat (1) before/after GrammarEvidence
  reviewed-fields (1)
  anchor-remove (1)       removed anchor + coverage claim

Reviewer materials FROZEN under maintenance/a1-blind-r1-materials/:
pre/<eid>.json (clone canon) and post/<eid>.json (terms bytes) for all
35 entries; shas pinned in the rows-file header.

Canary law (SPEC §5, carried from Q1..C1): 7 planted DEFECT rows bound
by rowSha payload identity, fixed-stride slots, every mutation
detectable from the row + materials (+ corpus) alone:
  P1 muc row with the wrong role (respondent instead of utterer)
  P2 muc row whose MasterName mismatches the occurrence bytes
  P3 prose reword that ADDS a claim (unevidenced master name)
  P4 unanchored Chinese survivor string (not in the anchor kwic)
  P5 performer bound to the wrong record's master
  P6 fabricated human ReviewedBy
  P7 claim text not present in the anchor kwic

Outputs:
  maintenance/a1-blind-r1-rows-20260903.json    (reviewer input)
  maintenance/a1-blind-r1-plants-20260903.json  (coordinator registry)
  maintenance/a1-blind-r1-materials/            (frozen verification set)
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
import zc  # noqa: E402

gates = json.loads((HERE / "a1-gates-20260903.json").read_text(encoding="utf-8"))
if gates.get("verdict") != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates.get('verdict')} — blind round "
                     "may not start")

_spec = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

import copy  # noqa: E402
by_id = eng.clone_state()
worklist = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8")
)["worklist"]
# transform() mutates by_id in place — freeze the true pre-state first
pre_state = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
eng.clone_snapshot.update(
    {eid: copy.deepcopy(by_id[eid]) for eid in worklist})
out, records = eng.transform(by_id)

# ---- materials: frozen pre/post entry copies ---------------------------------
MAT = HERE / "a1-blind-r1-materials"
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


def occ(obj, eid, si, oi):
    return obj[eid]["Senses"][si - 1]["Occurrences"][oi - 1]


def sense(obj, eid, si):
    return obj[eid]["Senses"][si - 1]


# ---- honest rows --------------------------------------------------------------
rows: list[dict] = []
for rec in records:
    cls, eid, si = rec["class"], rec["entry"], rec["si"]
    if cls.startswith("muc-"):
        o_pre = occ(pre_obj, eid, si, rec["oi"])
        rows.append({
            "entry": eid, "class": "muc-context-row", "si": si,
            "oi": rec["oi"], "masterName": rec["row"]["MasterName"],
            "roles": rec["row"]["Roles"],
            "attributionNote": str(o_pre.get("AttributionNote") or ""),
        })
    elif cls == "vague-reword":
        rows.append({
            "entry": eid, "class": "vague-reword", "si": si,
            "field": rec["field"], "find": rec["find"],
            "replace": rec["replace"],
        })
    elif cls == "dangling-anchor":
        anchor = json.loads(json.dumps(
            sense(post_obj, eid, si)["ClaimAnchors"][-1], ensure_ascii=False))
        v = zc.verify(anchor["RelPath"], anchor.get("Kwic") or "")
        assert v.get("ok") and v.get("count") == 1, v
        assert (anchor["FromLb"], anchor["ToLb"]) == (v["fromLb"], v["toLb"])
        rows.append({
            "entry": eid, "class": "dangling-anchor", "si": si,
            "strings": rec["strings"], "anchor": anchor,
            "zc": {"ok": True, "count": v["count"], "fromLb": v["fromLb"],
                   "toLb": v["toLb"]},
        })
    elif cls == "performer-context-row":
        rows.append({
            "entry": eid, "class": "performer-context-row", "si": si,
            "oi": rec["oi"], "row": rec["row"],
            "kwic": str(occ(pre_obj, eid, si, rec["oi"]).get("Kwic") or ""),
        })
    elif cls == "performer-grammar-proof":
        rows.append({
            "entry": eid, "class": "performer-grammar-proof", "si": si,
            "oi": rec["oi"], "sentence": rec["sentence"],
            "kwic": str(occ(pre_obj, eid, si, rec["oi"]).get("Kwic") or ""),
        })
    elif cls == "anon-monk-restructure":
        o_post = occ(post_obj, eid, si, rec["oi"])
        rows.append({
            "entry": eid, "class": "anon-monk-restructure", "si": si,
            "oi": rec["oi"], "respondentMaster": rec["respondentMaster"],
            "actorLabel": rec["actorLabel"],
            "occurrence": json.loads(json.dumps(o_post, ensure_ascii=False)),
        })
    elif cls == "grammar-evidence-repeat":
        o_pre, o_post = (occ(pre_obj, eid, si, rec["oi"]),
                         occ(post_obj, eid, si, rec["oi"]))
        rows.append({
            "entry": eid, "class": "grammar-evidence-repeat", "si": si,
            "oi": rec["oi"], "label": rec["label"],
            "before": str(o_pre["ActorAttribution"]["GrammarEvidence"]),
            "after": str(o_post["ActorAttribution"]["GrammarEvidence"]),
        })
    elif cls == "reviewed-fields":
        o_pre, o_post = (occ(pre_obj, eid, si, rec["oi"]),
                         occ(post_obj, eid, si, rec["oi"]))
        rows.append({
            "entry": eid, "class": "reviewed-fields", "si": si,
            "oi": rec["oi"], "beforeReviewedBy": o_pre["ActorAttribution"]
            .get("ReviewedBy"), "beforeReviewedUtc": o_pre["ActorAttribution"]
            .get("ReviewedUtc"),
            "reviewedBy": rec["reviewedBy"], "reviewedUtc":
                o_post["ActorAttribution"]["ReviewedUtc"],
        })
    elif cls == "anchor-remove":
        pre_anchors = sense(pre_obj, eid, si).get("ClaimAnchors") or []
        anchor = pre_anchors[rec["anchorIndex"]]
        holders = [o.get("RelPath") for o in post_obj[eid]["Senses"][si - 1]
                   ["Occurrences"]
                   if str(anchor.get("Kwic") or "").lstrip("。、，")
                   in str(o.get("Kwic") or "")]
        rows.append({
            "entry": eid, "class": "anchor-remove", "si": si,
            "removedRelPath": rec["removedRelPath"],
            "removedClaimText": rec["removedClaimText"],
            "removedKwic": str(anchor.get("Kwic") or ""),
            "postClaimAnchors": sense(post_obj, eid, si).get("ClaimAnchors"),
            "survivingHolders": holders,
        })
    else:
        raise SystemExit(f"unknown record class {cls}")
honest_count = len(rows)
assert honest_count == 116, honest_count
assert sum(1 for r in rows if r["class"] == "muc-context-row") == 91
assert sum(1 for r in rows if r["class"] == "vague-reword") == 17


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


muc_rows = [r for r in rows if r["class"] == "muc-context-row"]
vw_rows = [r for r in rows if r["class"] == "vague-reword"]
anchor_row = next(r for r in rows if r["class"] == "dangling-anchor")
perf_rows = [r for r in rows if r["class"] == "performer-context-row"]
rf_row = next(r for r in rows if r["class"] == "reviewed-fields")

# P1: muc row claims the WRONG role (respondent instead of the note-law role)
p1 = plant_from(muc_rows[0], lambda r: r.__setitem__(
    "roles", ["respondent"] if r["roles"] == ["utterer"] else ["utterer"]))
# P2: muc row whose MasterName mismatches the occurrence bytes (another
# fleet master's name entirely)
other_name = next(r["masterName"] for r in muc_rows
                  if r["masterName"] != muc_rows[3]["masterName"])
p2 = plant_from(muc_rows[3], lambda r: r.__setitem__("masterName", other_name))
# P3: prose reword that ADDS a claim — a master name evidenced nowhere in
# that entry's own bytes
p3_entry = vw_rows[2]["entry"]
P3_NAME = next(n for n in ("Hakuin Ekaku", "Tiantong Rujing",
                           "Dongshan Liangjie")
               if n not in eng.canon(pre_obj[p3_entry]))
p3 = plant_from(vw_rows[2], lambda r: r.__setitem__(
    "replace", r["replace"] + f" ({P3_NAME} confirms this)"))
# P4: unanchored Chinese survivor — a string in the anchored set that the
# anchor kwic does NOT contain
p4 = plant_from(anchor_row, lambda r: r.__setitem__(
    "strings", r["strings"] + ["拈花微笑"]))
# P5: performer bound to the wrong record's master
p5 = plant_from(perf_rows[0], lambda r: r.__setitem__(
    "row", {"MasterName": "Hanyue Fazang",
            "Roles": r["row"]["Roles"]}))
# P6: fabricated human ReviewedBy
p6 = plant_from(rf_row, lambda r: r.__setitem__(
    "reviewedBy", "Prof. Weirong Chen"))
# P7: claim text not present in the anchor kwic (wrong punctuation)
p7 = plant_from(anchor_row, lambda r: r["anchor"].__setitem__(
    "ClaimText", "萬法朗然！何思何慮？"))

plants = [p1, p2, p3, p4, p5, p6, p7]
PLANT_NOTES = [
    "muc row claims the wrong role (respondent/utterer swap)",
    "muc row MasterName mismatches the occurrence bytes",
    "prose reword ADDS a claim (unevidenced master name)",
    "unanchored Chinese survivor string (not in the anchor kwic)",
    "performer bound to the wrong record's master",
    "fabricated human ReviewedBy",
    "claim text not present in the anchor kwic",
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
    "schemaVersion": "a1-blind-r1-rows",
    "materialsDir": str(MAT),
    "materials": materials_pins,
    "rows": out_rows,
}
rows_path = HERE / "a1-blind-r1-rows-20260903.json"
rows_path.write_text(json.dumps(rows_doc, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
plants_path = HERE / "a1-blind-r1-plants-20260903.json"
plants_path.write_text(json.dumps({
    "schemaVersion": "a1-blind-r1-plants",
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
