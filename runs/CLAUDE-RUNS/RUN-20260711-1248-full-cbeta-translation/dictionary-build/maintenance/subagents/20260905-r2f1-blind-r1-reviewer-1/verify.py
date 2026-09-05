# -*- coding: utf-8 -*-
"""Blind review r1 (reviewer1) mechanical checker.

Implements the laws of task brief r2f1-main-blind-r1-reviewer-task-20260905.md
against the frozen materials, byte-exactly:

  occ-attribution : A1, A2, B1, B2, C1, C2, C3, E1
  note-provenance : provenance flags + excerpt + 至柔等編 presence, E1
  alias-add       : old/new sense-0 SearchAliases + addedAlias, E1
  surface-census  : D1, D2, D3, D4

Run:  python -X utf8 verify.py
Writes verify-report.txt and verdicts.json next to this script.
Only permitted inputs are opened (rows file + materials dir).
"""

import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
MAINT = os.path.dirname(os.path.dirname(BASE))
ROWS_PATH = os.path.join(MAINT, "r2f1-main-blind-r1-rows-20260905.json")
MATS_DIR = os.path.join(MAINT, "r2f1-main-blind-r1-materials-20260905")

IDS = [
    "t_057cc9ea8755",
    "t_351fa42d396b",
    "t_968a2f97c9ff",
    "t_ab715aa474d5",
    "t_ea2a427c7aba",
]

PROVENANCE_MARKER = "至柔等編"


def load_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def diff_bytes(label, claimed, actual):
    """Return a one-line byte-level divergence description for two str values."""
    if claimed == actual:
        return ""
    if not isinstance(claimed, str) or not isinstance(actual, str):
        return "%s: claimed %r != actual %r" % (label, claimed, actual)
    n = min(len(claimed), len(actual))
    i = 0
    while i < n and claimed[i] == actual[i]:
        i += 1
    ctx = 12
    lo = max(0, i - ctx)
    c_frag = claimed[lo:i + ctx]
    a_frag = actual[lo:i + ctx]
    c_ch = claimed[i] if i < len(claimed) else "<end>"
    a_ch = actual[i] if i < len(actual) else "<end>"
    def info(ch):
        if not isinstance(ch, str) or len(ch) != 1:
            return ch
        return "%s U+%04X utf8=%s" % (ch, ord(ch), ch.encode("utf-8").hex(" ").upper())
    return (
        "%s: first divergence at char index %d: claimed %s | actual %s "
        "| claimed ctx %r | actual ctx %r"
        % (label, i, info(c_ch), info(a_ch), c_frag, a_frag)
    )


def find_occurrences(entry, rel_path, from_lb):
    """All occurrences (any sense) with RelPath+FromLb equal to the locator."""
    out = []
    if not isinstance(entry, dict) or entry.get("__absent__"):
        return out
    for sense in entry.get("Senses", []):
        for occ in sense.get("Occurrences", []):
            if occ.get("RelPath") == rel_path and occ.get("FromLb") == from_lb:
                out.append(occ)
    return out


def staged_occ(entry, si, oi):
    senses = entry.get("Senses", [])
    if not (1 <= si <= len(senses)):
        return None
    occs = senses[si - 1].get("Occurrences", [])
    if not (1 <= oi <= len(occs)):
        return None
    return occs[oi - 1]


def dehui_rows(entry):
    """MasterName == 'Dehui' occurrences formatted like the census rows."""
    rows = []
    if not isinstance(entry, dict) or entry.get("__absent__"):
        return rows
    for sense in entry.get("Senses", []):
        for occ in sense.get("Occurrences", []):
            if occ.get("MasterName") == "Dehui":
                rows.append("%s %s %s" % (entry.get("Id"), occ.get("RelPath"), occ.get("FromLb")))
    return rows


def main():
    report = []
    rep = report.append

    # ------------------------------------------------------------------ pins
    rows_doc = json.loads(load_bytes(ROWS_PATH).decode("utf-8"))
    pins = rows_doc["materialsPins"]
    pins_ok = True
    rep("=" * 78)
    rep("MATERIALS PIN VERIFICATION (sha256 over raw bytes)")
    rep("=" * 78)
    for name, expected in pins.items():
        path = os.path.join(MATS_DIR, name)
        actual = hashlib.sha256(load_bytes(path)).hexdigest()
        ok = actual == expected
        pins_ok = pins_ok and ok
        rep("%s  %s" % ("OK " if ok else "FAIL", name))
        if not ok:
            rep("     expected %s" % expected)
            rep("     actual   %s" % actual)
    rep("materialsPinsOk = %s" % pins_ok)
    rep("")

    rows = rows_doc["rows"]
    rep("rows in deck: %d (R0000..R%04d)" % (len(rows), len(rows) - 1))
    rep("")

    materials = {}
    for eid in IDS:
        materials["main-head-" + eid] = json.loads(
            load_bytes(os.path.join(MATS_DIR, "main-head-%s.json" % eid)).decode("utf-8")
        )
        materials["staged-" + eid] = json.loads(
            load_bytes(os.path.join(MATS_DIR, "staged-%s.json" % eid)).decode("utf-8")
        )
    facts = json.loads(load_bytes(os.path.join(MATS_DIR, "surface-facts.json")).decode("utf-8"))
    # raw main-head bytes of 057 for the "absent in the old" provenance check
    raw_057_main = load_bytes(os.path.join(MATS_DIR, "main-head-t_057cc9ea8755.json")).decode("utf-8")

    absent_mains = {eid for eid in IDS if materials["main-head-" + eid].get("__absent__")}
    diff_ids = {
        eid for eid in IDS if materials["main-head-" + eid] != materials["staged-" + eid]
    }

    flags = []
    row_status = {}

    def check(row_id, law, ok, claim, actual, diverging):
        return {"law": law, "ok": bool(ok), "claim": claim, "actual": actual,
                "diverging": diverging if not ok else ""}

    for idx, row in enumerate(rows):
        rid = "R%04d" % idx
        kind = row.get("kind")
        results = []
        rep("=" * 78)
        rep("%s  kind=%s  entry=%s" % (rid, kind, row.get("entry")))
        rep("=" * 78)

        # ---------------------------------------------------------------- E1
        if "entry" in row:
            ok = row["entry"] in IDS
            results.append(check(rid, "E1", ok,
                                 "entry %r in 5 material ids" % row["entry"],
                                 "material ids %r" % (IDS,),
                                 "entry %r not among material ids" % row["entry"] if not ok else ""))

        if kind == "occ-attribution":
            eid = row["entry"]
            st = materials["staged-" + eid]
            mh = materials["main-head-" + eid]
            occ = staged_occ(st, row["si"], row["oi"])

            # ------------------------------------------------------------- A1
            a1_ok = occ is not None and occ.get("RelPath") == row["relPath"] \
                and occ.get("FromLb") == row["fromLb"] and occ.get("ToLb") == row["toLb"]
            a1_div = ""
            if occ is None:
                a1_div = "Senses[%d].Occurrences[%d] does not exist in staged-%s.json" % (
                    row["si"] - 1, row["oi"] - 1, eid)
            else:
                for k, rk in (("RelPath", "relPath"), ("FromLb", "fromLb"), ("ToLb", "toLb")):
                    if occ.get(k) != row[rk]:
                        a1_div = diff_bytes("A1 %s" % k, row[rk], occ.get(k))
                        break
            results.append(check(rid, "A1", a1_ok,
                                 "locator si=%d oi=%d relPath=%r fromLb=%r toLb=%r" % (
                                     row["si"], row["oi"], row["relPath"], row["fromLb"], row["toLb"]),
                                 "staged occurrence: %r" % (occ and {k: occ.get(k) for k in ("RelPath", "FromLb", "ToLb")},),
                                 a1_div))

            # ------------------------------------------------------------- A2
            kwic = occ.get("Kwic") if occ else None
            a2_ok = kwic is not None and row["carriedKwic"] == kwic
            results.append(check(rid, "A2", a2_ok,
                                 "carriedKwic %r" % row["carriedKwic"],
                                 "staged Kwic %r" % kwic,
                                 diff_bytes("A2 carriedKwic", row["carriedKwic"], kwic or "")))

            # ------------------------------------------------------------- B1
            mains = find_occurrences(mh, row["relPath"], row["fromLb"])
            present = len(mains) > 0
            b1_ok = row["oldWindowPresent"] == present
            results.append(check(rid, "B1", b1_ok,
                                 "oldWindowPresent=%s" % row["oldWindowPresent"],
                                 "main-head-%s.json %s an occurrence RelPath=%r FromLb=%r" % (
                                     eid, "contains" if present else "does NOT contain",
                                     row["relPath"], row["fromLb"]),
                                 "row claims oldWindowPresent=%s but main-head material %s the window" % (
                                     row["oldWindowPresent"], "contains" if present else "does not contain")))

            # ------------------------------------------------------------- B2
            if present:
                mo = mains[0]
                b2_ok = row["oldMasterName"] == mo.get("MasterName") \
                    and row["oldContextMasters"] == mo.get("ContextMasters") \
                    and row["oldAttributionNote"] == mo.get("AttributionNote")
                divs = []
                if row["oldMasterName"] != mo.get("MasterName"):
                    divs.append(diff_bytes("B2 oldMasterName", repr(row["oldMasterName"]), repr(mo.get("MasterName"))))
                if row["oldContextMasters"] != mo.get("ContextMasters"):
                    divs.append("B2 oldContextMasters: claimed %r != main %r" % (
                        row["oldContextMasters"], mo.get("ContextMasters")))
                if row["oldAttributionNote"] != mo.get("AttributionNote"):
                    divs.append(diff_bytes("B2 oldAttributionNote", row["oldAttributionNote"], mo.get("AttributionNote") or ""))
            else:
                b2_ok = row["oldMasterName"] is None and row["oldContextMasters"] is None \
                    and row["oldAttributionNote"] is None
                divs = ["row claims oldMasterName=%r oldContextMasters=%r oldAttributionNote=%r "
                        "but window is absent on main so all three must be null" % (
                            row["oldMasterName"], row["oldContextMasters"],
                            (row["oldAttributionNote"] or "")[:80])]
            results.append(check(rid, "B2", b2_ok,
                                 "oldMasterName=%r oldContextMasters=%r oldAttributionNote=%r" % (
                                     row["oldMasterName"], row["oldContextMasters"], row["oldAttributionNote"]),
                                 "main-head occurrence fields: MasterName=%r ContextMasters=%r AttributionNote=%r" % (
                                     mains[0].get("MasterName"), mains[0].get("ContextMasters"),
                                     mains[0].get("AttributionNote")) if present else "no main-head occurrence",
                                 "; ".join(divs)))

            # ------------------------------------------------------------- C1
            c1_ok = occ is not None and row["newMasterName"] == occ.get("MasterName") \
                and row["newContextMasters"] == occ.get("ContextMasters") \
                and row["newAttributionNote"] == occ.get("AttributionNote")
            c1_divs = []
            if occ is not None:
                if row["newMasterName"] != occ.get("MasterName"):
                    c1_divs.append(diff_bytes("C1 newMasterName", repr(row["newMasterName"]), repr(occ.get("MasterName"))))
                if row["newContextMasters"] != occ.get("ContextMasters"):
                    c1_divs.append("C1 newContextMasters: claimed %r != staged %r" % (
                        row["newContextMasters"], occ.get("ContextMasters")))
                if row["newAttributionNote"] != occ.get("AttributionNote"):
                    c1_divs.append(diff_bytes("C1 newAttributionNote", row["newAttributionNote"], occ.get("AttributionNote") or ""))
            results.append(check(rid, "C1", c1_ok,
                                 "newMasterName=%r newContextMasters=%r newAttributionNote=%r" % (
                                     row["newMasterName"], row["newContextMasters"], row["newAttributionNote"]),
                                 "staged occurrence fields: MasterName=%r ContextMasters=%r AttributionNote=%r" % (
                                     occ and occ.get("MasterName"), occ and occ.get("ContextMasters"),
                                     occ and occ.get("AttributionNote")),
                                 "; ".join(c1_divs)))

            # ------------------------------------------------------------- C2
            actor = (occ or {}).get("ActorAttribution") or {}
            c2_ok = all(row["newActor"].get(k) == actor.get(k)
                        for k in ("Status", "Kind", "ActorLabel", "ActorRole"))
            c2_divs = [diff_bytes("C2 newActor.%s" % k, repr(row["newActor"].get(k)), repr(actor.get(k)))
                       for k in ("Status", "Kind", "ActorLabel", "ActorRole")
                       if row["newActor"].get(k) != actor.get(k)]
            results.append(check(rid, "C2", c2_ok,
                                 "newActor=%r" % row["newActor"],
                                 "staged ActorAttribution(Status/Kind/ActorLabel/ActorRole)=%r" % {
                                     k: actor.get(k) for k in ("Status", "Kind", "ActorLabel", "ActorRole")},
                                 "; ".join(c2_divs)))

            # ------------------------------------------------------------- C3
            c3_ok = row["newActor"]["ActorLabel"].casefold() in (row["newAttributionNote"] or "").casefold()
            results.append(check(rid, "C3", c3_ok,
                                 "newActor.ActorLabel %r inside newAttributionNote (case-insensitive)" % row["newActor"]["ActorLabel"],
                                 "newAttributionNote %r" % (row["newAttributionNote"] or "")[:120],
                                 "ActorLabel not found in newAttributionNote"))

        elif kind == "note-provenance":
            eid = row["entry"]
            st = materials["staged-" + eid]
            mh = materials["main-head-" + eid]
            rel = row["relPath"]
            st_occs = [o for s in st.get("Senses", []) for o in s.get("Occurrences", [])
                       if o.get("RelPath") == rel]
            mh_occs = [o for s in mh.get("Senses", []) for o in s.get("Occurrences", [])
                       if o.get("RelPath") == rel]
            st_note = st_occs[0].get("AttributionNote") if st_occs else None

            st_has = st_note is not None and PROVENANCE_MARKER in st_note
            st_exact = st_note is not None and st_note.count(PROVENANCE_MARKER) == 1
            mh_has = any(PROVENANCE_MARKER in (o.get("AttributionNote") or "") for o in mh_occs)
            mh_raw_has = PROVENANCE_MARKER in raw_057_main

            old_flag_ok = row["oldNoteHasProvenance"] == mh_has and not mh_raw_has
            new_flag_ok = row["newNoteHasProvenance"] == st_has and st_exact
            excerpt_ok = st_note is not None and st_note.startswith(row["newNoteExcerpt"])

            results.append(check(rid, "NP-old", old_flag_ok,
                                 "oldNoteHasProvenance=%s" % row["oldNoteHasProvenance"],
                                 "main-head-%s.json X70n1399 occurrences: %d; %s in any old note: %s; in whole main-head file: %s" % (
                                     eid, len(mh_occs), PROVENANCE_MARKER, mh_has, mh_raw_has),
                                 "old flag must be false with %s absent from the old material" % PROVENANCE_MARKER))
            results.append(check(rid, "NP-new", new_flag_ok,
                                 "newNoteHasProvenance=%s" % row["newNoteHasProvenance"],
                                 "staged X70n1399 note contains %s: %s (count=%s)" % (
                                     PROVENANCE_MARKER, st_has, st_note.count(PROVENANCE_MARKER) if st_note else None),
                                 "new flag must be true with %s present exactly once in the staged note" % PROVENANCE_MARKER))
            results.append(check(rid, "NP-excerpt", excerpt_ok,
                                 "newNoteExcerpt=%r" % row["newNoteExcerpt"],
                                 "staged note starts with the excerpt: %s" % excerpt_ok,
                                 "staged AttributionNote does not start with the claimed excerpt"))

        elif kind == "alias-add":
            eid = row["entry"]
            st = materials["staged-" + eid]
            mh = materials["main-head-" + eid]
            old_actual = mh.get("Senses", [{}])[0].get("SearchAliases")
            new_actual = st.get("Senses", [{}])[0].get("SearchAliases")
            old_ok = row["oldAliases"] == old_actual
            new_ok = row["newAliases"] == new_actual
            added_ok = row["addedAlias"] in (new_actual or []) and row["addedAlias"] not in (old_actual or [])
            results.append(check(rid, "AL-old", old_ok,
                                 "oldAliases=%r" % row["oldAliases"],
                                 "main-head sense-0 SearchAliases=%r" % old_actual,
                                 "oldAliases != main-head sense-0 SearchAliases"))
            results.append(check(rid, "AL-new", new_ok,
                                 "newAliases=%r" % row["newAliases"],
                                 "staged sense-0 SearchAliases=%r" % new_actual,
                                 "newAliases != staged sense-0 SearchAliases"))
            results.append(check(rid, "AL-added", added_ok,
                                 "addedAlias=%r in new but not old" % row["addedAlias"],
                                 "in new: %s; in old: %s" % (
                                     row["addedAlias"] in (new_actual or []),
                                     row["addedAlias"] in (old_actual or [])),
                                 "addedAlias membership claim fails"))

        elif kind == "surface-census":
            # ------------------------------------------------------------- D1
            ec = row["entryCount"]
            d1_ok = (ec == facts["entryCount"]
                     and facts["entryCount"]["after"] == facts["entryCount"]["before"] + 1
                     and ec["after"] == ec["before"] + len(absent_mains)
                     and set(facts["addedSet"]) == absent_mains)
            results.append(check(rid, "D1", d1_ok,
                                 "entryCount=%r" % ec,
                                 "surface-facts entryCount=%r; absent-on-main material set=%r (=addedSet) implies after=before+1" % (
                                     facts["entryCount"], sorted(absent_mains)),
                                 "row after=%d but surface-facts after=%d (before %d + 1 added entry %r)" % (
                                     ec["after"], facts["entryCount"]["after"],
                                     facts["entryCount"]["before"], sorted(absent_mains))))

            # ------------------------------------------------------------- D2
            d2_expect = diff_ids == set(IDS)
            d2_ok = row["changedSetEqualsWorklist"] == d2_expect
            results.append(check(rid, "D2", d2_ok,
                                 "changedSetEqualsWorklist=%s" % row["changedSetEqualsWorklist"],
                                 "ids differing between main-head and staged materials: %r (worklist=%r)" % (
                                     sorted(diff_ids), sorted(IDS)),
                                 "materials show all 5 product ids differ, so the claim must be true"
                                 if d2_expect else "materials do not show all 5 differing"))

            # ------------------------------------------------------------- D3
            before_recomputed_inside_products = sorted(
                r for eid in IDS for r in dehui_rows(materials["main-head-" + eid]))
            after_staged_dehui = sorted(
                r for eid in IDS for r in dehui_rows(materials["staged-" + eid]))
            d3_ok = (row["dehuiCensusBefore"] == facts["dehuiCensus"]["before"]
                     and row["dehuiCensusAfter"] == facts["dehuiCensus"]["after"]
                     and row["dehuiCensusBefore"] == before_recomputed_inside_products
                     and len(row["dehuiCensusBefore"]) == 1
                     and row["dehuiCensusAfter"] == []
                     and after_staged_dehui == [])
            results.append(check(rid, "D3", d3_ok,
                                 "dehuiCensusBefore=%r dehuiCensusAfter=%r" % (
                                     row["dehuiCensusBefore"], row["dehuiCensusAfter"]),
                                 "surface-facts census=%r; MasterName=='Dehui' recomputed over main-head materials=%r; over staged materials=%r" % (
                                     facts["dehuiCensus"], before_recomputed_inside_products, after_staged_dehui),
                                 "census rows disagree with the frozen record / material recompute"))

            # ------------------------------------------------------------- D4
            d4_ok = (row["nonProductRegression"] == [] == facts["nonProductRegression"]
                     and row["aliasLostCount"] == len(facts["aliasLost"]))
            results.append(check(rid, "D4", d4_ok,
                                 "nonProductRegression=%r aliasLostCount=%r" % (
                                     row["nonProductRegression"], row["aliasLostCount"]),
                                 "surface-facts nonProductRegression=%r len(aliasLost)=%d" % (
                                     facts["nonProductRegression"], len(facts["aliasLost"])),
                                 "nonProductRegression must be [] and aliasLostCount must equal len(aliasLost)"))

        # ------------------------------------------------------------- verdict
        for r in results:
            rep("%s  %-10s %s" % (rid, r["law"], "PASS" if r["ok"] else "FAIL"))
            if not r["ok"]:
                rep("       claim : %s" % r["claim"])
                rep("       actual: %s" % r["actual"])
                rep("       diverg: %s" % r["diverging"])
        bad = [r for r in results if not r["ok"]]
        row_status[rid] = [r["law"] for r in bad]
        if bad:
            flags.append({
                "row": rid,
                "laws": [r["law"] for r in bad],
                "claim": " | ".join(r["claim"] for r in bad),
                "actual": " | ".join(r["actual"] for r in bad),
                "divergingBytes": " | ".join(r["diverging"] for r in bad),
            })
        rep("")

    verdicts = {
        "reviewer": "reviewer1",
        "materialsPinsOk": pins_ok,
        "rowsChecked": len(rows),
        "flags": flags,
        "notes": (
            "All 11 materialsPins verified by sha256 over raw bytes before review. "
            "Rows identified by deck position R0000..R0010. rowSha ignored per instructions. "
            "Clean rows: %s. Flagged: %s." % (
                ", ".join(r for r in sorted(row_status) if not row_status[r]) or "none",
                ", ".join("%s(%s)" % (r, ",".join(row_status[r])) for r in sorted(row_status) if row_status[r]) or "none",
            )
        ),
    }

    rep("=" * 78)
    rep("SUMMARY")
    rep("=" * 78)
    rep("materialsPinsOk : %s" % pins_ok)
    rep("rowsChecked     : %d" % len(rows))
    for rid in sorted(row_status):
        rep("%s : %s" % (rid, "CLEAN" if not row_status[rid] else "FLAGGED " + ",".join(row_status[rid])))

    text = "\n".join(report) + "\n"
    with open(os.path.join(BASE, "verify-report.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open(os.path.join(BASE, "verdicts.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(verdicts, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
