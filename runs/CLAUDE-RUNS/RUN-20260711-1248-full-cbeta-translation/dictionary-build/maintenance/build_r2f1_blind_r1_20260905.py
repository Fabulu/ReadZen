#!/usr/bin/env python3
"""Build the blind r1 round for the combined R2+F1 MAIN publication.

The two lanes' blind rounds verified the PRODUCT BYTES (every claim
re-derived from engine+materials both directions). This round covers
the publication step's own novel claims:
  - the OLD (main-HEAD) state of each product slot — including the two
    ABSENT claims (t_351fa42d396b absent as an entry; 1143a07/1143a12
    absent as occurrences of t_ea2a427c7aba);
  - the NEW (staged surface) state of the 5 repaired/added rows;
  - the surface census numbers (entry count, Dehui census, non-product
    regression, alias delta).

8 honest rows + 3 payload-bound canaries at fixed-stride slots. Rows
are re-derived from the frozen materials (never from the receipt):
  materials/r2f1-main-blind/main-head-<eid>.json  (5 files; sentinel
    {"__absent__": true} for t_351fa42d396b)
  materials/r2f1-main-blind/staged-<eid>.json     (5 files)
  materials/r2f1-main-blind/surface-facts.json    (before/after numbers)

Every row carries rowSha = sha256 of its canonical JSON (sort_keys) —
the canary payload binding.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MAIN = r"C:\programmieren\CbetaZenTranslations"
STAGE_PUBLIC = (ROOT / "fresh-build" / "r2f1-main-20260905"
                / "publication-stage" / "public")
MATS = HERE / "r2f1-main-blind-r1-materials-20260905"
IDS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff",
       "t_ab715aa474d5", "t_351fa42d396b")
PRODUCTS_WITH_WINDOWS = {
    "t_ea2a427c7aba": [("T/T48/T48n2025.xml", "1113a21"),
                       ("T/T48/T48n2025.xml", "1143a07"),
                       ("T/T48/T48n2025.xml", "1143a12")],
    "t_ab715aa474d5": [("T/T48/T48n2025.xml", "1144b03")],
    "t_351fa42d396b": [("T/T48/T48n2025.xml", "1127c04")],
}


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


def jcanon(o) -> str:
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def git_show_main(path: str) -> str:
    return subprocess.run(
        ["git", "-C", MAIN, "show", f"HEAD:{path}"],
        capture_output=True, text=True, encoding="utf-8").stdout


def find_occ(entry: dict, rel: str, lb: str):
    for si, s in enumerate(entry.get("Senses") or [], start=1):
        for oi, o in enumerate(s.get("Occurrences") or [], start=1):
            if o.get("RelPath") == rel and o.get("FromLb") == lb:
                return si, oi, o
    return None, None, None


# ---- freeze materials -------------------------------------------------------
MATS.mkdir(parents=True, exist_ok=True)
main_head = json.loads(git_show_main("termbase.v2.json"))
main_by_id = {e["Id"]: e for e in main_head["Entries"]}
staged = json.loads((STAGE_PUBLIC / "termbase.v2.json")
                    .read_text(encoding="utf-8"))
staged_by_id = {e["Id"]: e for e in staged["Entries"]}
main_idx = json.loads(git_show_main("termbase.index.json"))
staged_idx = json.loads((STAGE_PUBLIC / "termbase.index.json")
                        .read_text(encoding="utf-8"))

for eid in IDS:
    (MATS / f"main-head-{eid}.json").write_text(
        canon(main_by_id.get(eid, {"__absent__": True})), encoding="utf-8")
    (MATS / f"staged-{eid}.json").write_text(
        canon(staged_by_id[eid]), encoding="utf-8")

wl = set(IDS)


def changed_ids():
    out = []
    for eid in staged_by_id:
        if eid not in main_by_id:
            out.append(eid)
        elif canon(staged_by_id[eid]) != canon(main_by_id[eid]):
            out.append(eid)
    return sorted(out)


def dehui_rows(by_id):
    return sorted(f"{eid} {o.get('RelPath')} {o.get('FromLb')}"
                  for eid, e in by_id.items()
                  for s in e.get("Senses") or []
                  for o in s.get("Occurrences") or []
                  if o.get("MasterName") == "Dehui")


def regression_ids():
    return sorted(eid for eid, e in main_by_id.items()
                  if eid not in wl
                  and canon(e) != canon(staged_by_id.get(eid, {})))


surface_facts = {
    "entryCount": {"before": len(main_by_id),
                   "after": len(staged_by_id)},
    "changedSet": changed_ids(),
    "addedSet": sorted(eid for eid in staged_by_id if eid not in main_by_id),
    "dehuiCensus": {"before": dehui_rows(main_by_id),
                    "after": dehui_rows(staged_by_id)},
    "nonProductRegression": regression_ids(),
    "aliasAdded": sorted(set(staged_idx.get("Aliases") or {})
                         - set(main_idx.get("Aliases") or {})),
    "aliasLost": sorted(set(main_idx.get("Aliases") or {})
                        - set(staged_idx.get("Aliases") or {})),
}
(MATS / "surface-facts.json").write_text(canon(surface_facts),
                                         encoding="utf-8")

materials_pins = {f: hashlib.sha256((MATS / f).read_bytes()).hexdigest()
                  for f in sorted(p.name for p in MATS.iterdir())}

# ---- honest rows ------------------------------------------------------------
rows = []


def occ_row(entry_id, rel, lb, note):
    si, oi, old_o = find_occ(main_by_id.get(entry_id, {}), rel, lb)
    _, _, new_o = find_occ(staged_by_id[entry_id], rel, lb)
    assert new_o is not None, (entry_id, lb)
    new_aa = new_o.get("ActorAttribution") or {}
    return {
        "kind": "occ-attribution",
        "note": note,
        "entry": entry_id,
        "relPath": rel,
        "fromLb": lb,
        "oldWindowPresent": old_o is not None,
        "oldMasterName": old_o.get("MasterName") if old_o else None,
        "oldContextMasters": (old_o.get("ContextMasters")
                              if old_o else None),
        "oldAttributionNote": (old_o.get("AttributionNote")
                               if old_o else None),
        "si": 1, "oi": oi if False else None,   # oi filled below from new
        "newMasterName": new_o.get("MasterName"),
        "newContextMasters": new_o.get("ContextMasters"),
        "newActor": {k: new_aa.get(k) for k in
                     ("Status", "Kind", "ActorLabel", "ActorRole")},
        "newAttributionNote": new_o.get("AttributionNote"),
        "carriedKwic": new_o.get("Kwic"),
        "toLb": new_o.get("ToLb"),
    }


for eid, windows in PRODUCTS_WITH_WINDOWS.items():
    for rel, lb in windows:
        rows.append(occ_row(eid, rel, lb,
                            "publication diff row (main HEAD -> staged)"))

# 057 provenance row
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
rows.append({
    "kind": "note-provenance",
    "note": "057 occ-3 note gains the compiled-by-disciples provenance",
    "entry": "t_057cc9ea8755",
    "relPath": "X/X70/X70n1399.xml",
    "oldNoteHasProvenance": "至柔等編" in old_note,
    "newNoteHasProvenance": "至柔等編" in new_note,
    "newNoteExcerpt": new_note[:160],
})

# 968 alias row
old_al = old057  # placeholder to keep linters quiet; real below
old968 = main_by_id["t_968a2f97c9ff"]
new968 = staged_by_id["t_968a2f97c9ff"]
rows.append({
    "kind": "alias-add",
    "note": "968 gains the withdrawn-ID replacement search alias",
    "entry": "t_968a2f97c9ff",
    "oldAliases": old968["Senses"][0].get("SearchAliases") or [],
    "newAliases": new968["Senses"][0].get("SearchAliases") or [],
    "addedAlias": "一不成、二不是",
})

# surface census row
rows.append({
    "kind": "surface-census",
    "note": "publication surface laws",
    "entryCount": {"before": surface_facts["entryCount"]["before"],
                   "after": surface_facts["entryCount"]["after"]},
    "changedSetEqualsWorklist": surface_facts["changedSet"] == sorted(IDS),
    "dehuiCensusBefore": surface_facts["dehuiCensus"]["before"],
    "dehuiCensusAfter": surface_facts["dehuiCensus"]["after"],
    "nonProductRegression": surface_facts["nonProductRegression"],
    "aliasLostCount": len(surface_facts["aliasLost"]),
})

# fix si/oi for occ rows from the STAGED entry (window locator)
for r in rows:
    if r["kind"] != "occ-attribution":
        continue
    si, oi, _ = find_occ(staged_by_id[r["entry"]], r["relPath"], r["fromLb"])
    r["si"], r["oi"] = si, oi
assert len(rows) == 8, len(rows)

# ---- plants (payload-bound canaries) ----------------------------------------
plants = []


def bind(row):
    row["rowSha"] = hashlib.sha256(
        jcanon(row).encode("utf-8")).hexdigest()
    return row


def plant(base_name, mutate, label):
    idx = next(i for i, r in enumerate(rows) if r["kind"] == base_name)
    r = json.loads(jcanon(rows[idx]))
    mutate(r)
    plants.append({"slotKind": base_name, "rowIndex": idx, "label": label,
                   "payload": r,
                   "bindPayloadSha256": hashlib.sha256(
                       jcanon(r).encode("utf-8")).hexdigest()})


def p1(r):
    # kwic mutation: 齊 -> 兼 (one CJK char of the carried kwic)
    r["carriedKwic"] = r["carriedKwic"].replace("並宜齊赴", "並宜兼赴", 1)


def p2(r):
    r["entryCount"]["after"] = r["entryCount"]["before"]   # hides the add
    r["changedSetEqualsWorklist"] = False


def p3(r):
    # claims the 1143a07 window already existed on main with a fabricated
    # old note — main lacks the occurrence entirely
    r["oldWindowPresent"] = True
    r["oldMasterName"] = "Dehui"
    r["oldAttributionNote"] = ("Source record (T/T48/T48n2025.xml). "
                               "Imperially Commissioned Baizhang Monastic "
                               "Regulations: the fabricated pre-publication "
                               "main note")


plant("occ-attribution", p1, "kwic-mutation-ab715")
# steer p1 to the ab715 row: pick by entry
plants[-1]["rowIndex"] = next(i for i, r in enumerate(rows)
                              if r["kind"] == "occ-attribution"
                              and r["entry"] == "t_ab715aa474d5")
plants[-1]["payload"] = json.loads(jcanon(rows[plants[-1]["rowIndex"]]))
p1(plants[-1]["payload"])
plants[-1]["bindPayloadSha256"] = hashlib.sha256(
    jcanon(plants[-1]["payload"]).encode("utf-8")).hexdigest()

plant("surface-census", p2, "count-hides-add")
plant("occ-attribution", p3, "fabricated-old-window-ea2-1143a07")
plants[-1]["rowIndex"] = next(i for i, r in enumerate(rows)
                              if r["kind"] == "occ-attribution"
                              and r["entry"] == "t_ea2a427c7aba"
                              and r["fromLb"] == "1143a07")
plants[-1]["payload"] = json.loads(jcanon(rows[plants[-1]["rowIndex"]]))
p3(plants[-1]["payload"])
plants[-1]["bindPayloadSha256"] = hashlib.sha256(
    jcanon(plants[-1]["payload"]).encode("utf-8")).hexdigest()

# honest rows get their rowSha last (post-plant construction)
for r in rows:
    bind(r)

# interleave plants at fixed-stride slots over the final deck
total = len(rows) + len(plants)
slots = sorted((i * 3 + 1) % total for i in range(len(plants)))
deck = list(rows)
for slot, p in zip(slots, plants):
    payload = dict(p["payload"])
    payload.pop("rowSha", None)  # rowSha must hash the body only, else
    # the deck rowSha != bindPayloadSha256 and the adjudicator's
    # row_sha() self-consistency law fails on every planted row
    payload["rowSha"] = hashlib.sha256(
        jcanon(payload).encode("utf-8")).hexdigest()
    deck.insert(slot, payload)
    p["slot"] = slot

rows_doc = {
    "cohort": "r2f1-main-20260905",
    "round": "r1",
    "lawNote": (
        "Laws: A (window locator: si/oi/relPath/fromLb/toLb/kwic must "
        "byte-match the STAGED occurrence); B (old-state truth: every "
        "old* field must equal main-HEAD bytes, with ABSENT claims "
        "matching actual absence); C (new-state truth: new* fields must "
        "equal staged bytes; ActorLabel verbatim inside the new note); "
        "D (surface: census numbers must equal surface-facts.json and "
        "be independently recomputable from the materials); E (scope: "
        "every row's entry in the 5-product worklist)."),
    "materialsPins": materials_pins,
    "rows": deck,
}
rows_path = HERE / "r2f1-main-blind-r1-rows-20260905.json"
rows_path.write_text(canon(rows_doc), encoding="utf-8")

plants_doc = {
    "cohort": "r2f1-main-20260905",
    "round": "r1",
    "honestRows": len(rows),
    "registry": [{"label": p["label"], "slot": p["slot"],
                  "slotKind": p["slotKind"],
                  "bindPayloadSha256": p["bindPayloadSha256"]}
                 for p in plants],
}
(HERE / "r2f1-main-blind-r1-plants-20260905.json").write_text(
    canon(plants_doc), encoding="utf-8")

print(json.dumps({
    "rows": len(deck), "honest": len(rows), "plants": len(plants),
    "plantSlots": slots,
    "rowsSha256": hashlib.sha256(rows_path.read_bytes()).hexdigest(),
    "plantsSha256": hashlib.sha256(
        (HERE / "r2f1-main-blind-r1-plants-20260905.json")
        .read_bytes()).hexdigest(),
    "materials": len(materials_pins),
}, indent=2))
