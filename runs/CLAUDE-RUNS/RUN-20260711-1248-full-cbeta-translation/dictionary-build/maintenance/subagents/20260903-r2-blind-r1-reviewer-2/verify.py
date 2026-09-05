# -*- coding: utf-8 -*-
"""Blind review r2 / r1 -- reviewer 2 mechanical verification of the 16 change rows
against the frozen PRE/POST materials, per the laws in
r2-blind-r1-reviewer-task-20260903.md.

Run:  python -X utf8 verify.py
Writes verdicts.json next to this script and prints a full audit report.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAINT = HERE.parent.parent  # .../dictionary-build/maintenance
ROWS_PATH = MAINT / "r2-blind-r1-rows-20260903.json"
MATS = MAINT / "r2-blind-r1-materials"

CJK_RUN = re.compile(r"[㐀-鿿豈-﫿]+")  # per task: [㐀-鿿豈-﫿]+


def cp(s):
    """Codepoint dump of a short string."""
    return " ".join("U+%04X(%s)" % (ord(c), c) for c in s)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sense(entry, si):
    return entry["Senses"][si - 1]


def slot(entry, si, oi):
    return entry["Senses"][si - 1]["Occurrences"][oi - 1]


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_diff_window(a, b, width=6):
    """Locate first divergence between two strings; return a printable window."""
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    lo = max(0, i - width)
    wa = a[lo:i + width]
    wb = b[lo:i + width]
    return (i, wa, wb)


def diff_paths(a, b, path="$", out=None):
    """Inventory of JSON paths where a and b differ (for the notes section)."""
    if out is None:
        out = []
    if type(a) is not type(b):
        out.append(path + " [type change]")
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(path + "." + k + " [only in POST]")
            elif k not in b:
                out.append(path + "." + k + " [only in PRE]")
            else:
                diff_paths(a[k], b[k], path + "." + k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(path + " [len %d -> %d]" % (len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diff_paths(x, y, "%s[%d]" % (path, i), out)
    else:
        if a != b:
            out.append("%s  %r -> %r" % (path, a, b))
    return out


def main():
    report = []
    def say(s=""):
        report.append(s)
        print(s)

    rows_doc = load_json(ROWS_PATH)
    lane_law = rows_doc["laneLaw"]
    rows = rows_doc["rows"]

    # ---------- Step 0: integrity ----------
    say("== Step 0: materials sha256 pins ==")
    pins_ok = True
    for rel, want in sorted(rows_doc["materials"].items()):
        got = sha256_file(MATS / rel)
        ok = got == want
        pins_ok = pins_ok and ok
        say("  %-28s %s  %s" % (rel, "OK" if ok else "MISMATCH", got if not ok else ""))
    say("  materialsPinsOk = %s" % pins_ok)

    pre = {e: load_json(MATS / ("pre/%s.json" % e)) for e in
           ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")}
    post = {e: load_json(MATS / ("post/%s.json" % e)) for e in pre}

    flags = []

    def flag(row_id, law, reason):
        flags.append({"rowId": row_id, "law": law, "reason": reason})

    # ---------- Law A ----------
    say()
    say("== Law A: occ-attribution rows ==")
    a_rows = [r for r in rows if r["class"] == "occ-attribution"]
    covered_ois = {}  # entry -> si -> set(oi) covered by an occ-attribution row
    for r in a_rows:
        covered_ois.setdefault(r["entry"], {}).setdefault(r["si"], set()).add(r["oi"])

    for r in a_rows:
        rid, e, si, oi = r["rowId"], r["entry"], r["si"], r["oi"]
        say("-- %s %s si=%d oi=%d" % (rid, e, si, oi))
        pslot, qslot = slot(pre[e], si, oi), slot(post[e], si, oi)

        # A1 pre-slot identity
        fails = []
        if pslot.get("MasterName") != r["oldMasterName"]:
            fails.append("MasterName %r != oldMasterName %r" % (pslot.get("MasterName"), r["oldMasterName"]))
        if pslot.get("ContextMasters") != r["oldContextMasters"]:
            fails.append("ContextMasters %r != oldContextMasters %r" % (pslot.get("ContextMasters"), r["oldContextMasters"]))
        if pslot.get("AttributionNote") != r["oldAttributionNote"]:
            fails.append("AttributionNote != oldAttributionNote (pre len %d, row len %d)" %
                         (len(pslot.get("AttributionNote") or ""), len(r["oldAttributionNote"])))
        for f, key in (("carriedRelPath", "RelPath"), ("carriedFromLb", "FromLb"),
                       ("carriedToLb", "ToLb"), ("carriedKwic", "Kwic")):
            if pslot.get(key) != r[f]:
                i, wa, wb = first_diff_window(pslot.get(key) or "", r[f] or "")
                fails.append("%s: PRE %s=%r != row %s=%r (first diff at char %d: PRE %s vs row %s)" %
                             (key, key, (pslot.get(key) or "")[:40], f, (r[f] or "")[:40], i, cp(wa), cp(wb)))
        if fails:
            for m in fails:
                flag(rid, "A1", m)
                say("   A1 FLAG: " + m)
        else:
            say("   A1 ok")

        # A2 post-slot identity
        fails = []
        if qslot.get("MasterName") != r["newMasterName"]:
            fails.append("post slot MasterName = %r; row claims newMasterName = %r" %
                         (qslot.get("MasterName"), r["newMasterName"]))
        if qslot.get("ContextMasters") != r["newContextMasters"]:
            fails.append("post ContextMasters = %r; row claims %r" %
                         (qslot.get("ContextMasters"), r["newContextMasters"]))
        if qslot.get("AttributionNote") != r["newAttributionNote"]:
            i, wa, wb = first_diff_window(qslot.get("AttributionNote") or "", r["newAttributionNote"] or "")
            fails.append("post AttributionNote != newAttributionNote (first diff at char %d: post %r vs row %r)" %
                         (i, wa[:30], wb[:30]))
        if qslot.get("ActorAttribution") != r["newActorAttribution"]:
            pa, ra = qslot.get("ActorAttribution") or {}, r["newActorAttribution"] or {}
            for k in sorted(set(pa) | set(ra)):
                if pa.get(k) != ra.get(k):
                    fails.append("post ActorAttribution.%s = %r; row claims %r" % (k, pa.get(k), ra.get(k)))
        for f, key in (("carriedRelPath", "RelPath"), ("carriedFromLb", "FromLb"),
                       ("carriedToLb", "ToLb"), ("carriedKwic", "Kwic")):
            if qslot.get(key) != r[f]:
                i, wa, wb = first_diff_window(qslot.get(key) or "", r[f] or "")
                fails.append("carried %s: POST %s=%r != row %s=%r (first diff at char %d: POST %s vs row %s)" %
                             (key, key, (qslot.get(key) or "")[:40], f, (r[f] or "")[:40], i, cp(wa), cp(wb)))
        if fails:
            for m in fails:
                flag(rid, "A2", m)
                say("   A2 FLAG: " + m)
        else:
            say("   A2 ok")

        # A3 sense coverage (per row, against this entry/si)
        psense, qsense = sense(pre[e], si), sense(post[e], si)
        fails = []
        if len(psense["Occurrences"]) != len(qsense["Occurrences"]):
            fails.append("occurrence count %d -> %d" % (len(psense["Occurrences"]), len(qsense["Occurrences"])))
        else:
            for idx in range(len(psense["Occurrences"])):
                o_i = idx + 1
                if o_i in covered_ois.get(e, {}).get(si, set()):
                    continue
                if psense["Occurrences"][idx] != qsense["Occurrences"][idx]:
                    fails.append("uncovered occurrence oi=%d differs PRE->POST" % o_i)
        if r["postOccurrenceRels"] != [o["RelPath"] for o in qsense["Occurrences"]]:
            fails.append("postOccurrenceRels %r != POST rel paths %r" %
                         (r["postOccurrenceRels"], [o["RelPath"] for o in qsense["Occurrences"]]))
        if r["postOccurrenceCount"] != len(qsense["Occurrences"]):
            fails.append("postOccurrenceCount %r != POST count %d" % (r["postOccurrenceCount"], len(qsense["Occurrences"])))
        if fails:
            for m in fails:
                flag(rid, "A3", m)
                say("   A3 FLAG: " + m)
        else:
            say("   A3 ok")

    # ---------- Law B ----------
    say()
    say("== Law B: prose-rewrite rows ==")
    lawb_pairs = []  # (entry, si) touched
    for r in rows:
        if r["class"] in ("explanation-rewrite", "note-rewrite", "attributionnote-rewrite"):
            lawb_pairs.append((r["entry"], r["si"]))
            rid, e, si = r["rowId"], r["entry"], r["si"]
            field = r["field"]
            say("-- %s %s si=%d field=%s oi=%r" % (rid, e, si, field, r.get("oi")))
            if r["class"] == "attributionnote-rewrite":
                # field "OccAttributionNote" lives on the occurrence slot, not the sense
                pre_field = slot(pre[e], si, r["oi"]).get("AttributionNote")
                post_field = slot(post[e], si, r["oi"]).get("AttributionNote")
                say("   (field resolved to slot(%d,%d).AttributionNote for B1/B2)" % (si, r["oi"]))
            else:
                pre_field = sense(pre[e], si).get(field)
                post_field = sense(post[e], si).get(field)
            before, after = r["before"], r["after"]

            # B1
            m = None
            if pre_field is None or post_field is None:
                m = "field missing (pre=%r post=%r)" % (pre_field is not None, post_field is not None)
            else:
                nb, na = pre_field.count(before), post_field.count(after)
                if nb != 1:
                    m = "PRE field contains before %d times (need exactly 1)" % nb
                elif na != 1:
                    m = "POST field contains after %d times (need exactly 1)" % na
            if m:
                flag(rid, "B1", m)
                say("   B1 FLAG: " + m)
            else:
                say("   B1 ok (before x1 in PRE, after x1 in POST)")
            # B2
            m = None
            if pre_field is not None and post_field is not None:
                rebuilt = pre_field.replace(before, after, 1)
                if rebuilt != post_field:
                    i, wa, wb = first_diff_window(rebuilt, post_field)
                    m = ("one-replacement rebuild != POST field (first diff at char %d: rebuilt %r vs POST %r)" %
                         (i, wa[:40], wb[:40]))
            if m:
                flag(rid, "B2", m)
                say("   B2 FLAG: " + m)
            else:
                say("   B2 ok")
            # B3 (attributionnote-rewrite only) -- literal full equality
            if r["class"] == "attributionnote-rewrite":
                pnote = slot(pre[e], si, r["oi"]).get("AttributionNote")
                qnote = slot(post[e], si, r["oi"]).get("AttributionNote")
                m = None
                if pnote != before:
                    m = ("B3 literal: PRE slot AttributionNote (len %d) != before (len %d); "
                         "before is a fragment, not the full note (PRE starts %r, before starts %r)" %
                         (len(pnote or ""), len(before), (pnote or "")[:28], before[:28]))
                if qnote != after:
                    m2 = ("B3 literal: POST slot AttributionNote (len %d) != after (len %d)" %
                          (len(qnote or ""), len(after)))
                    m = (m + "; " + m2) if m else m2
                if m:
                    flag(rid, "B3", m)
                    say("   B3 FLAG: " + m)
                else:
                    say("   B3 ok")

    # B4 prose anchoring -- once per (entry, si) touched by a Law-B row
    say()
    say("== B4 prose anchoring ==")
    for (e, si) in sorted(set(lawb_pairs)):
        qsense = sense(post[e], si)
        text = qsense.get("Explanation", "") + "\n" + qsense.get("Note", "")
        kwics = [o.get("Kwic") for o in qsense.get("Occurrences", []) if o.get("Kwic")]
        kwics += [a.get("Kwic") for a in qsense.get("ClaimAnchors", []) if a.get("Kwic")]
        unanchored = []
        for run in CJK_RUN.findall(text):
            if not any((run in k or k in run) for k in kwics):
                unanchored.append(run)
        say("  (%s, si=%d): %d CJK runs, unanchored: %s" %
            (e, si, len(CJK_RUN.findall(text)), unanchored if unanchored else "none"))
        if unanchored:
            touched = [r["rowId"] for r in rows
                       if r["class"] in ("explanation-rewrite", "note-rewrite", "attributionnote-rewrite")
                       and r["entry"] == e and r["si"] == si]
            for rid in touched:
                flag(rid, "B4", "unanchored CJK run(s) %r in POST sense prose" % unanchored)

    # ---------- Law C ----------
    say()
    say("== Law C: relatedmasters-rename rows ==")
    roster = re.search(r"'([^']+)'", lane_law["t48n2025Class"]).group(1)
    say("  roster name parsed from t48n2025Class: %r" % roster)
    for r in rows:
        if r["class"] != "relatedmasters-rename":
            continue
        rid, e, si = r["rowId"], r["entry"], r["si"]
        old, new = r["renamed"]["old"], r["renamed"]["new"]
        pre_list = sense(pre[e], si).get("RelatedMasters")
        post_list = sense(post[e], si).get("RelatedMasters")
        say("-- %s %s si=%d %r -> %r" % (rid, e, si, old, new))
        fails = []
        if pre_list.count(old) != 1:
            fails.append("PRE RelatedMasters contains %r %d times (need exactly 1)" % (old, pre_list.count(old)))
        rebuilt = list(pre_list)
        if old in rebuilt:
            rebuilt[rebuilt.index(old)] = new
        if rebuilt != post_list:
            fails.append("PRE list with rename %r != POST list" % (rebuilt,))
        if r["postRelatedMasters"] != post_list:
            fails.append("postRelatedMasters != POST RelatedMasters")
        if fails:
            for m in fails:
                flag(rid, "C1", m)
                say("   C1 FLAG: " + m)
        else:
            say("   C1 ok")
        if new != roster:
            flag(rid, "C2", "renamed.new %r != roster name %r" % (new, roster))
            say("   C2 FLAG")
        else:
            say("   C2 ok")

    # ---------- Law D ----------
    say()
    say("== Law D: searchaliases-add rows ==")
    for r in rows:
        if r["class"] != "searchaliases-add":
            continue
        rid, e, si, added = r["rowId"], r["entry"], r["si"], r["added"]
        pre_al = sense(pre[e], si).get("SearchAliases")
        post_al = sense(post[e], si).get("SearchAliases")
        say("-- %s %s si=%d added=%r" % (rid, e, si, added))
        fails = []
        if list(pre_al) + [added] != list(post_al):
            fails.append("PRE aliases + [added] %r != POST aliases %r (divergence at appended element: "
                         "added=%s vs POST last=%s)" % (list(pre_al) + [added], post_al, cp(added), cp(post_al[-1] if post_al else "")))
        if r["postSearchAliases"] != post_al:
            fails.append("postSearchAliases %r != POST SearchAliases %r" % (r["postSearchAliases"], post_al))
        if fails:
            for m in fails:
                flag(rid, "D1", m)
                say("   D1 FLAG: " + m)
        else:
            say("   D1 ok")

    # ---------- Law E ----------
    say()
    say("== Law E: lane law ==")
    for e in pre:
        # E1
        bad = []
        for s_i, s in enumerate(post[e]["Senses"], 1):
            for o_i, o in enumerate(s.get("Occurrences", []), 1):
                if o.get("RelPath") in lane_law["retiredRels"]:
                    bad.append("sense %d occ %d RelPath %s" % (s_i, o_i, o["RelPath"]))
            for a_i, a in enumerate(s.get("ClaimAnchors", []), 1):
                if a.get("RelPath") in lane_law["retiredRels"]:
                    bad.append("sense %d anchor %d RelPath %s" % (s_i, a_i, a["RelPath"]))
        # E2
        e2 = []
        if len(pre[e]["Senses"]) != len(post[e]["Senses"]):
            e2.append("sense count %d -> %d" % (len(pre[e]["Senses"]), len(post[e]["Senses"])))
        for s_i in range(1, min(len(pre[e]["Senses"]), len(post[e]["Senses"])) + 1):
            a = len(sense(pre[e], s_i).get("Occurrences", []))
            b = len(sense(post[e], s_i).get("Occurrences", []))
            if a != b:
                e2.append("sense %d occ count %d -> %d" % (s_i, a, b))
        say("  %s: E1 %s | E2 %s" % (e, "clean" if not bad else "VIOLATIONS " + repr(bad),
                                     "clean" if not e2 else "VIOLATIONS " + repr(e2)))
        if bad or e2:
            entry_rows = [r["rowId"] for r in rows if r["entry"] == e]
            rid = entry_rows[0] if entry_rows else e
            law = "E1" if bad else "E2"
            flag(rid, law, ("retired rels present: " + repr(bad)) if bad else ("count drift: " + repr(e2)))

    # ---------- PRE->POST diff inventory (for notes) ----------
    say()
    say("== PRE->POST diff inventory ==")
    for e in pre:
        d = diff_paths(pre[e], post[e])
        say("  %s: %d differing paths" % (e, len(d)))
        for p in d:
            say("    " + p)

    # ---------- verdicts ----------
    # Curated one-line phrasings for the flags the mechanical checks raised.
    # Detection stays 100% mechanical; this table only rewords. Any override
    # pointing at a flag that was NOT raised is a hard error.
    REASON_OVERRIDES = {
        ("R0000", "A2"): "post slot(1,8) MasterName is null; row claims newMasterName 'Dongyang Dehui' "
                         "(also contradicts laneLaw.t48n2025Class: Dongyang Dehui is never a speaking master)",
        ("R0009", "A2"): "post slot(1,9) ContextMasters[0].Roles = ['compiler']; row claims ['utterer'] "
                         "(laneLaw.t48n2025Class: Dongyang Dehui is never a speaking master)",
        ("R0010", "A2"): "post slot(1,1) ActorAttribution.ActorLabel = \"the monastic code's institutional voice\"; "
                         "row claims \"the code compiler's editorial voice\"",
        ("R0011", "A1"): "PRE slot(1,8) Kwic[11] is 內 (U+5167) in '如尋常坐禪向內坐'; "
                         "row carriedKwic has 猫 (U+732B) there: '如尋常坐禪向猫坐'",
        ("R0011", "A2"): "POST slot(1,8) Kwic still has 內 (U+5167); the row's carriedKwic 猫 (U+732B) is not "
                         "the unchanged pre→post value the 'carried' claim asserts",
        ("R0012", "A1"): "PRE slot(1,1) FromLb = '1143a07'; row carriedFromLb = '1143a08'",
        ("R0012", "A2"): "POST slot(1,1) FromLb = '1143a07'; carriedFromLb '1143a08' is not unchanged pre→post",
        ("R0007", "B3"): "B3 as written requires full-string equality: PRE slot(1,3) AttributionNote is 366 chars, "
                         "before is a 48-char fragment; POST note is 400 chars, after is 82. Under the fragment "
                         "semantics of B1/B2 (field resolved to slot(1,3).AttributionNote) this row IS "
                         "byte-consistent with PRE and POST; the flag enforces B3's literal '=='.",
        ("R0014", "B1"): "POST Note does not contain after (0 occurrences, need exactly 1): after inserts "
                         "'(非攝非散)', which appears nowhere in the POST Note",
        ("R0014", "B2"): "one-replacement rebuild diverges from POST Note at char 537: rebuilt '...retains "
                         "(非攝非散) the ordinary...' vs POST '...retains the ordinary...'",
        ("R0015", "B1"): "POST slot(1,3) AttributionNote does not contain after (0 occurrences): after invents "
                         "compiler '百丈自編' where the POST note reads '至柔等編'",
        ("R0015", "B2"): "one-replacement rebuild diverges at char 99: rebuilt '...disciples "
                         "(百丈自編): in the verse' vs POST '...disciples (至柔等編): "
                         "in the verse'",
        ("R0015", "B3"): "B3 literal equality fails: before/after are fragments (48/82 chars) of the full PRE/POST "
                         "slot notes (366/400 chars)",
        ("R0013", "D1"): "PRE SearchAliases + ['一不成二不是'] != POST ['one fails, two is "
                         "wrong', '一不成、二不是']: the row's added string drops the "
                         "ideographic comma 、 (U+3001) after 成 (U+6210)",
    }
    applied = set()
    for f in flags:
        key = (f["rowId"], f["law"])
        if key in REASON_OVERRIDES:
            f["reason"] = REASON_OVERRIDES[key]
            applied.add(key)
    stray = set(REASON_OVERRIDES) - applied
    if stray:
        raise SystemExit("FATAL: reason overrides for flags not raised: %s" % sorted(stray))

    verdicts = {
        "reviewer": "reviewer2",
        "materialsPinsOk": pins_ok,
        "rowsChecked": len(rows),
        "flags": flags,
        "notes": (
            "All 6 material sha256 pins matched. Mechanical checks (verify.py, run with python -X utf8) plus a "
            "full manual Read of the rows file and all 6 materials. Field resolution note: attributionnote-rewrite "
            "rows carry field 'OccAttributionNote', which is not a sense-level key; for B1/B2 it was resolved to "
            "slot(entry,si,oi).AttributionNote; B3 was enforced literally (full-string equality of the slot note "
            "with before/after), which both attributionnote rows violate because they publish fragments, not full "
            "notes - under a substring reading R0007 is otherwise fully consistent with the frozen bytes while "
            "R0015 contradicts POST under every reading (claims compiler 百丈自編; POST says 至柔等編). B4 anchoring "
            "evaluated for (t_ea2a427c7aba, si1) and (t_057cc9ea8755, si1): all maximal CJK runs anchored, no flags. "
            "E1/E2 clean for all three entries. The PRE->POST diff inventory shows every changed byte path in all "
            "three entries (17 / 2 / 1 differing paths) is covered by at least one row-consistent edit - no "
            "unexplained lane changes. Row pairs R0000/R0002, R0001/R0010/R0012, R0003/R0009, R0006/R0014, "
            "R0007/R0015, R0008/R0013 describe the same edit; in each pair the flagged twin contradicts the frozen "
            "PRE or POST bytes. laneLaw.defectCensus names t_ab715aa474d5 and t_351fa42d396b, absent from the "
            "materials - unverifiable from the inputs; no law attaches to it. rowSha is not verified: no law "
            "defines its serialization. Unverifiable-from-inputs items: none besides those two."
        ),
    }
    out = HERE / "verdicts.json"
    out.write_text(json.dumps(verdicts, ensure_ascii=False, indent=2), encoding="utf-8")
    say()
    say("== %d flags across %d rows -> %s ==" %
        (len(flags), len(set(f["rowId"] for f in flags)), out.name))
    for f in flags:
        say("  %s %s: %s" % (f["rowId"], f["law"], f["reason"][:160]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
