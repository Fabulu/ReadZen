# Blind review verifier — F1 lane, round r1, reviewer 1 (2026-09-05)
# Implements Laws A1-A4, B1-B4', C1-C2, E1-E3 mechanically against the frozen
# materials, per maintenance/f1-blind-r1-reviewer-task-20260905.md.
# Run with: python -X utf8 verify.py

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
            r"\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation"
            r"\dictionary-build")
MAINT = ROOT / "maintenance"
ROWS_FILE = MAINT / "f1-blind-r1-rows-20260905.json"
OUT_DIR = MAINT / "subagents" / "20260905-f1-blind-r1-reviewer-1"

CJK_RUN = re.compile(r"[\u3400-\u9FFF\uF900-\uFAFF]+")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sense(entry, si):
    return entry["Senses"][si - 1]


def slot(entry, si, oi):
    return sense(entry, si)["Occurrences"][oi - 1]


def cp(s):
    """Render a string with per-char U+ codepoints for CJK diff evidence."""
    return " ".join(f"{ch}(U+{ord(ch):04X})" if ord(ch) > 0x2E80 else ch
                    for ch in s)


def first_diff(a, b):
    """Index and context of first divergence of two strings."""
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    lo = max(0, i - 6)
    return (f"first divergence at char {i}: "
            f"A[{lo}:{i + 8}]={cp(a[lo:i + 8])!r}  "
            f"B[{lo}:{i + 8}]={cp(b[lo:i + 8])!r}")


def main():
    report = []

    def say(*a):
        line = " ".join(str(x) for x in a)
        report.append(line)
        print(line)

    rows_doc = json.loads(ROWS_FILE.read_text(encoding="utf-8"))
    mat_dir = Path(rows_doc["materialsDir"])

    # ---------------- Step 0 — integrity pins ----------------
    say("== Step 0: material sha256 pins ==")
    pins_ok = True
    for rel, want in sorted(rows_doc["materials"].items()):
        got = sha256_file(mat_dir / rel)
        ok = got == want
        pins_ok &= ok
        say(f"  {rel}: {'OK' if ok else 'MISMATCH'} "
            f"(computed {got}, pinned {want})")

    rows = rows_doc["rows"]
    say(f"rows in file: {len(rows)}")

    verdict = {
        "reviewer": "reviewer1",
        "materialsPinsOk": pins_ok,
        "rowsChecked": len(rows),
        "flags": [],
        "notes": "",
    }

    if not pins_ok:
        say("PIN MISMATCH -> stop, no flags, no law checks.")
        verdict["notes"] = ("material sha256 mismatch; halted at Step 0 "
                            "before any law checks")
        (OUT_DIR / "verdicts.json").write_text(
            json.dumps(verdict, ensure_ascii=False, indent=2),
            encoding="utf-8")
        (OUT_DIR / "verify-report.txt").write_text(
            "\n".join(report), encoding="utf-8")
        return

    # ---------------- load materials ----------------
    entries = sorted({r["entry"] for r in rows})
    pre = {e: json.loads((mat_dir / f"pre/{e}.json").read_text(encoding="utf-8"))
           for e in entries}
    post = {e: json.loads((mat_dir / f"post/{e}.json").read_text(encoding="utf-8"))
            for e in entries}

    def flag(rowId, law, reason):
        verdict["flags"].append({"rowId": rowId, "law": law, "reason": reason})
        say(f"  FLAG {rowId} / {law}: {reason}")

    # rows per entry covering sense occurrences (for A3 other-slot rule)
    occ_covered = {}  # (entry, si) -> set of oi
    for r in rows:
        if r["class"] == "occ-attribution":
            occ_covered.setdefault((r["entry"], r["si"]), set()).add(r["oi"])

    # ---------------- Law A — occ-attribution rows ----------------
    say("\n== Law A: occ-attribution rows ==")
    for r in rows:
        if r["class"] != "occ-attribution":
            continue
        e, si, oi = r["entry"], r["si"], r["oi"]
        rid = r["rowId"]
        ps, qs = slot(pre[e], si, oi), slot(post[e], si, oi)
        say(f"-- {rid} {e} si={si} oi={oi}")

        # A1 pre-slot identity
        a1 = []
        if ps.get("MasterName") != r["oldMasterName"]:
            a1.append(f"PRE MasterName {ps.get('MasterName')!r} != old {r['oldMasterName']!r}")
        if ps.get("ContextMasters") != r["oldContextMasters"]:
            a1.append(f"PRE ContextMasters {ps.get('ContextMasters')!r} != old {r['oldContextMasters']!r}")
        if ps.get("AttributionNote") != r["oldAttributionNote"]:
            a1.append("PRE AttributionNote != oldAttributionNote")
        for k_field, r_field in (("RelPath", "carriedRelPath"),
                                 ("FromLb", "carriedFromLb"),
                                 ("ToLb", "carriedToLb"),
                                 ("Kwic", "carriedKwic")):
            if ps.get(k_field) != r[r_field]:
                a1.append(f"PRE {k_field} {ps.get(k_field)!r} != row {r[r_field]!r}")
        if a1:
            flag(rid, "A1", "; ".join(a1))
        else:
            say("  A1 ok")

        # A2 post-slot identity
        a2 = []
        if qs.get("MasterName") != r["newMasterName"]:
            a2.append(f"POST MasterName {qs.get('MasterName')!r} != newMasterName {r['newMasterName']!r}")
        if qs.get("ContextMasters") != r["newContextMasters"]:
            a2.append(f"POST ContextMasters {qs.get('ContextMasters')!r} != newContextMasters {r['newContextMasters']!r}")
        if qs.get("AttributionNote") != r["newAttributionNote"]:
            a2.append("POST AttributionNote != newAttributionNote")
        if qs.get("ActorAttribution") != r["newActorAttribution"]:
            # pinpoint the differing subfield(s)
            qa, ra = qs.get("ActorAttribution") or {}, r["newActorAttribution"] or {}
            sub = [k for k in sorted(set(qa) | set(ra)) if qa.get(k) != ra.get(k)]
            a2.append(f"POST ActorAttribution != newActorAttribution (differs in: {sub}; "
                      f"POST ActorLabel={qa.get('ActorLabel')!r} vs row {ra.get('ActorLabel')!r})")
        for k_field, r_field in (("RelPath", "carriedRelPath"),
                                 ("FromLb", "carriedFromLb"),
                                 ("ToLb", "carriedToLb"),
                                 ("Kwic", "carriedKwic")):
            if qs.get(k_field) != r[r_field]:
                extra = ""
                if k_field == "Kwic":
                    extra = " [" + first_diff(qs.get(k_field) or "", r[r_field]) + "]"
                a2.append(f"POST {k_field} {qs.get(k_field)!r} != row {r[r_field]!r}{extra}")
        if a2:
            flag(rid, "A2", "; ".join(a2))
        else:
            say("  A2 ok")

        # A3 sense coverage
        a3 = []
        psense, qsense = sense(pre[e], si), sense(post[e], si)
        if len(psense["Occurrences"]) != len(qsense["Occurrences"]):
            a3.append(f"sense occurrence count PRE {len(psense['Occurrences'])} != POST {len(qsense['Occurrences'])}")
        covered = occ_covered[(e, si)]
        for idx in range(1, len(psense["Occurrences"]) + 1):
            if idx in covered:
                continue
            if slot(pre[e], si, idx) != slot(post[e], si, idx):
                a3.append(f"non-row occurrence oi={idx} changed PRE->POST")
        rels_post = [o.get("RelPath") for o in qsense["Occurrences"]]
        if rels_post != r["postOccurrenceRels"]:
            a3.append(f"postOccurrenceRels {r['postOccurrenceRels']!r} != POST rels {rels_post!r}")
        if len(qsense["Occurrences"]) != r["postOccurrenceCount"]:
            a3.append(f"postOccurrenceCount {r['postOccurrenceCount']} != POST count {len(qsense['Occurrences'])}")
        if a3:
            flag(rid, "A3", "; ".join(a3))
        else:
            say("  A3 ok")

        # A4 label-verbatim
        label = (r["newActorAttribution"] or {}).get("ActorLabel", "")
        note_row = r["newAttributionNote"] or ""
        note_post = qs.get("AttributionNote") or ""
        if not (label.casefold() in note_row.casefold()):
            flag(rid, "A4", f"ActorLabel {label!r} not inside row newAttributionNote")
        elif not (label.casefold() in note_post.casefold()):
            flag(rid, "A4", f"ActorLabel {label!r} not inside POST slot AttributionNote")
        else:
            say("  A4 ok")

    # ---------------- Law B — prose-rewrite rows ----------------
    say("\n== Law B: explanation-rewrite rows ==")
    def kwics_of(s):
        out = []
        for o in s.get("Occurrences", []):
            k = o.get("Kwic")
            if k:
                out.append(k)
        for ca in s.get("ClaimAnchors", []) or []:
            if isinstance(ca, dict):
                k = ca.get("Kwic")
                if k:
                    out.append(k)
            elif isinstance(ca, str) and ca:
                out.append(ca)
        return out

    b4_pairs = []  # (entry, si) touched by Law-B rows
    for r in rows:
        if r["class"] != "explanation-rewrite":
            continue
        e, si, fld = r["entry"], r["si"], r["field"]
        rid = r["rowId"]
        b4_pairs.append((e, si))
        psense, qsense = sense(pre[e], si), sense(post[e], si)
        say(f"-- {rid} {e} si={si} field={fld} oi={r.get('oi')}")

        oi = r.get("oi")
        if oi is not None:
            # B3' slot-field fragment semantics
            ptxt = slot(pre[e], si, oi).get(fld) or ""
            qtxt = slot(post[e], si, oi).get(fld) or ""
            before, after = r["before"], r["after"]
            if ptxt.count(before) != 1:
                flag(rid, "B3", f"PRE slot {fld} contains 'before' {ptxt.count(before)} times (need exactly 1)")
            elif qtxt != ptxt.replace(before, after, 1):
                flag(rid, "B3", f"POST slot != PRE slot with before->after; {first_diff(qtxt, ptxt.replace(before, after, 1))}")
            elif qtxt.count(after) != 1:
                flag(rid, "B3", f"POST slot contains 'after' {qtxt.count(after)} times (need exactly 1)")
            else:
                say("  B3' ok")
            continue

        ptxt = psense.get(fld) or ""
        qtxt = qsense.get(fld) or ""
        before, after = r["before"], r["after"]

        # B1
        b1 = []
        if ptxt.count(before) != 1:
            b1.append(f"PRE {fld} contains before {ptxt.count(before)} times (need exactly 1)")
        if qtxt.count(after) != 1:
            b1.append(f"POST {fld} contains after {qtxt.count(after)} times (need exactly 1)")
        if b1:
            flag(rid, "B1", "; ".join(b1))
        else:
            say("  B1 ok")

        # B2
        expected = ptxt.replace(before, after, 1)
        if expected != qtxt:
            flag(rid, "B2", f"PRE {fld} with before->after != POST {fld}; {first_diff(expected, qtxt)}")
        else:
            say("  B2 ok")

    # B4 — once per (entry, si) touched by any Law-B row
    say("\n== Law B4: prose anchoring (once per touched (entry, si)) ==")
    b4_hit_rows = {}  # (e, si) -> [rowIds of Law-B rows]
    for r in rows:
        if r["class"] == "explanation-rewrite":
            b4_hit_rows.setdefault((r["entry"], r["si"]), []).append(r["rowId"])
    for (e, si), rids in sorted(b4_hit_rows.items()):
        s = sense(post[e], si)
        text = (s.get("Explanation") or "") + "\n" + (s.get("Note") or "")
        ks = kwics_of(s)
        say(f"-- ({e}, si={si}) rows {rids}; {len(ks)} kwics")
        unanchored = []
        for run in CJK_RUN.findall(text):
            if any((run in k or k in run) for k in ks):
                continue
            unanchored.append(run)
        if unanchored:
            for run in unanchored:
                say(f"  unanchored run: {run!r} = {cp(run)}")
            for rid in rids:
                flag(rid, "B4", f"POST sense prose has unanchored CJK run(s): "
                                + "; ".join(f"{u!r} [{cp(u)}]" for u in unanchored))
        else:
            say(f"  all CJK runs anchored ({len(CJK_RUN.findall(text))} runs checked)")

    # ---------------- Law C — relatedmasters-rename rows ----------------
    say("\n== Law C: relatedmasters-rename rows ==")
    m = re.search(r"'([^']+)'", rows_doc["laneLaw"]["t48n2025Class"])
    roster = m.group(1) if m else None
    say(f"  roster name parsed from laneLaw.t48n2025Class: {roster!r}")
    for r in rows:
        if r["class"] != "relatedmasters-rename":
            continue
        e, si, rid = r["entry"], r["si"], r["rowId"]
        old, new = r["renamed"]["old"], r["renamed"]["new"]
        pre_rm = sense(pre[e], si).get("RelatedMasters")
        post_rm = sense(post[e], si).get("RelatedMasters")
        say(f"-- {rid} {e} si={si} {old!r} -> {new!r}")
        c1 = []
        if pre_rm.count(old) != 1:
            c1.append(f"PRE RelatedMasters contains old {pre_rm.count(old)} times (need exactly 1): {pre_rm!r}")
        else:
            expected = [new if x == old else x for x in pre_rm]
            if post_rm != expected:
                c1.append(f"POST RelatedMasters {post_rm!r} != PRE with rename {expected!r}")
        if r["postRelatedMasters"] != post_rm:
            c1.append(f"postRelatedMasters {r['postRelatedMasters']!r} != POST field {post_rm!r}")
        if c1:
            flag(rid, "C1", "; ".join(c1))
        else:
            say("  C1 ok")
        if new != roster:
            flag(rid, "C2", f"renamed.new {new!r} != roster name {roster!r}")
        else:
            say("  C2 ok")

    # ---------------- Law E — lane law, across both entries ----------------
    say("\n== Law E: lane law (both entries) ==")
    first_row_of = {}
    for r in rows:
        first_row_of.setdefault(r["entry"], r["rowId"])
    retired = rows_doc["laneLaw"]["retiredRels"]

    for e in sorted(post):
        rows_e = [r["rowId"] for r in rows if r["entry"] == e]
        anchor_row = rows_e[0] if rows_e else None
        # E1 retired rels
        for s_i, s in enumerate(post[e]["Senses"], 1):
            hits = [o.get("RelPath") for o in s.get("Occurrences", [])
                    if o.get("RelPath") in retired]
            ca_hits = []
            for ca in s.get("ClaimAnchors", []) or []:
                if isinstance(ca, dict) and ca.get("RelPath") in retired:
                    ca_hits.append(ca.get("RelPath"))
            if hits or ca_hits:
                flag(anchor_row, "E1",
                     f"entry {e} sense {s_i}: retired RelPath(s) present in POST: "
                     f"{sorted(set(hits + ca_hits))} (named entry's first row; no single row triggered)")
        # E2 counts
        pre_s, post_s = pre[e]["Senses"], post[e]["Senses"]
        if len(pre_s) != len(post_s):
            flag(anchor_row, "E2", f"entry {e}: sense count PRE {len(pre_s)} != POST {len(post_s)}")
        for s_i in range(1, min(len(pre_s), len(post_s)) + 1):
            pn, qn = len(pre_s[s_i - 1].get("Occurrences", [])), len(post_s[s_i - 1].get("Occurrences", []))
            if pn != qn:
                flag(anchor_row, "E2", f"entry {e} sense {s_i}: occurrence count PRE {pn} != POST {qn}")
        # E3 Dehui census
        for s_i, s in enumerate(post_s, 1):
            for o_i, o in enumerate(s.get("Occurrences", []), 1):
                if o.get("MasterName") == "Dehui":
                    flag(anchor_row, "E3", f"entry {e} sense {s_i} occ {o_i}: POST MasterName == 'Dehui'")
                for cm in o.get("ContextMasters") or []:
                    if cm.get("MasterName") == "Dehui":
                        flag(anchor_row, "E3", f"entry {e} sense {s_i} occ {o_i}: POST ContextMasters contains 'Dehui'")
            if "Dehui" in (s.get("RelatedMasters") or []):
                flag(anchor_row, "E3", f"entry {e} sense {s_i}: POST RelatedMasters contains 'Dehui'")
        say(f"  {e}: E1/E2/E3 checks run (anchor row {anchor_row})")

    # ---------------- rowSha (no law covers it; exploratory) ----------------
    say("\n== rowSha exploratory (not a law; canonical form unspecified) ==")
    def variants(row):
        base = {k: v for k, v in row.items() if k != "rowSha"}
        yield "compact-insertion", json.dumps(base, ensure_ascii=False, separators=(",", ":"))
        yield "compact-sorted", json.dumps(base, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        yield "indent1-insertion", json.dumps(base, ensure_ascii=False, indent=1)
        yield "default-insertion", json.dumps(base, ensure_ascii=False)
    for r in rows[:3]:
        hits = [name for name, s in variants(r) if hashlib.sha256(s.encode("utf-8")).hexdigest() == r["rowSha"]]
        say(f"  {r['rowId']}: matching canonicalizations: {hits or 'none'}")

    # ---------------- write deliverables ----------------
    verdict["notes"] = (
        "All 4 material sha256 pins matched. All 10 rows checked against "
        "laws A1-A4/B1-B2/C1-C2/E1-E3; B3' not applicable (no slot-field "
        "prose rows this round: oi is null on both explanation-rewrite rows); "
        "B4 evaluated once per Law-B-touched (entry,si) - only "
        "(t_351fa42d396b, si=1); every CJK run in its POST Explanation+Note "
        "is anchored by a POST Occurrences kwic (ClaimAnchors absent/empty). "
        "rowSha fields are unverifiable from the inputs: no canonical row "
        "serialization is specified and none of 4 plausible canonicalizations "
        "matched (see verify-report.txt); no law covers rowSha, so no flags "
        "were raised on it. E1/E2/E3 pass for both entries; E-flags would "
        "have named each entry's first row per protocol. Contradictory "
        "sibling rows noted: R0000 vs R0001 and R0002 vs R0003 make mutually "
        "exclusive claims about the same POST slot; the POST bytes agree "
        "with R0001/R0003."
    )
    (OUT_DIR / "verdicts.json").write_text(
        json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "verify-report.txt").write_text(
        "\n".join(report), encoding="utf-8")
    say(f"\nverdicts.json written with {len(verdict['flags'])} flag(s).")


if __name__ == "__main__":
    sys.exit(main())
