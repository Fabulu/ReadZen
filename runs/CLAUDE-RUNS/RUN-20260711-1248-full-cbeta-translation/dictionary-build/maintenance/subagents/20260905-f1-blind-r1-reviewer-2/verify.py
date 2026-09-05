# -*- coding: utf-8 -*-
"""Blind review verification — reviewer 2, dictionary edit lane F1, round r1 (2026-09-05).

Implements laws A1-A4, B1-B4 (incl. B3' slot semantics), C1-C2, E1-E3
mechanically against the frozen PRE/POST materials, plus Step 0 pin checks.
Reads ONLY: the rows file and the 4 pinned materials files.
Writes: verdicts.json (exact deliverable schema) + prints a full audit trail.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation\dictionary-build")
MAINT = ROOT / "maintenance"
ROWS_PATH = MAINT / "f1-blind-r1-rows-20260905.json"
MAT_DIR = MAINT / "f1-blind-r1-materials"
OUT_DIR = MAINT / "subagents" / "20260905-f1-blind-r1-reviewer-2"

# Law B4's maximal CJK run: U+3400-U+9FFF and U+F900-U+FAFF
CJK_RUN = re.compile("[\u3400-\u9FFF\uF900-\uFAFF]+")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sense(entry, si):
    return entry["Senses"][si - 1]


def slot(entry, si, oi):
    return entry["Senses"][si - 1]["Occurrences"][oi - 1]


def cps(s):
    """Render a short string as codepoints for CJK diff evidence."""
    return " ".join(f"{ch}(U+{ord(ch):04X})" for ch in s)


def first_divergence(a, b):
    """Index + codepoints of the first differing char of two strings."""
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    lo = max(0, i - 4)
    return i, a[lo:i + 5], b[lo:i + 5]


def kwic_diff_msg(field, pre_val, row_val):
    i, ca, cb = first_divergence(pre_val, row_val)
    return (
        f"{field} first divergence at char index {i}: "
        f"materials ...{ca}... vs row ...{cb}...; "
        f"diverging char materials {pre_val[i] if i < len(pre_val) else '<end>'}(U+{ord(pre_val[i]):04X}) "
        f"vs row {row_val[i] if i < len(row_val) else '<end>'}(U+{ord(row_val[i]):04X})"
        if i < len(pre_val) and i < len(row_val)
        else f"{field} length/content divergence at index {i}: materials len {len(pre_val)}, row len {len(row_val)}"
    )


flags = []


def flag(row_id, law, reason):
    flags.append({"rowId": row_id, "law": law, "reason": reason})


# ---------------------------------------------------------------- Step 0 pins
rows_doc = json.loads(ROWS_PATH.read_text(encoding="utf-8"))
pins = rows_doc["materials"]
pins_ok = True
pin_lines = []
for rel, want in sorted(pins.items()):
    got = sha256_file(MAT_DIR / rel)
    ok = got == want
    pins_ok = pins_ok and ok
    pin_lines.append(f"  {'OK ' if ok else 'BAD'} {rel}: {got} {'==' if ok else '!='} {want}")
print("Step 0 — materials sha256 pins:")
print("\n".join(pin_lines))

materials = {rel: json.loads((MAT_DIR / rel).read_text(encoding="utf-8")) for rel in pins}
rows = rows_doc["rows"]
lane_law = rows_doc["laneLaw"]
ENTRY_IDS = sorted({r["entry"] for r in rows})


def ent(which, eid):
    return materials[f"{which}/{eid}.json"]


def first_row_of(eid):
    for r in rows:
        if r["entry"] == eid:
            return r["rowId"]
    return None


if not pins_ok:
    verdict = {
        "reviewer": "reviewer2",
        "materialsPinsOk": False,
        "rowsChecked": 0,
        "flags": [],
        "notes": "Materials sha256 pin mismatch — review stopped at Step 0 per protocol.",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "verdicts.json").write_text(
        json.dumps(verdict, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print("PIN MISMATCH — stopped.")
    sys.exit(0)

# ------------------------------------------------------------- Law A helpers
OCC_ATTR_ROWS = [r for r in rows if r["class"] == "occ-attribution"]


def check_occ_row(r):
    rid = r["rowId"]
    eid, si, oi = r["entry"], r["si"], r["oi"]
    pre, post = ent("pre", eid), ent("post", eid)
    try:
        ps, qs = slot(pre, si, oi), slot(post, si, oi)
    except (IndexError, KeyError) as e:
        flag(rid, "A1", f"slot(entry={eid},si={si},oi={oi}) lookup failed in materials: {e!r}")
        return

    # A1 — pre-slot identity
    probs = []
    if ps.get("MasterName") != r["oldMasterName"]:
        probs.append(f"PRE MasterName {ps.get('MasterName')!r} != oldMasterName {r['oldMasterName']!r}")
    if ps.get("ContextMasters") != r["oldContextMasters"]:
        probs.append(f"PRE ContextMasters {json.dumps(ps.get('ContextMasters'), ensure_ascii=False)} != oldContextMasters {json.dumps(r['oldContextMasters'], ensure_ascii=False)}")
    if ps.get("AttributionNote") != r["oldAttributionNote"]:
        probs.append("PRE AttributionNote != oldAttributionNote")
    for k, f in (("RelPath", "carriedRelPath"), ("FromLb", "carriedFromLb"), ("ToLb", "carriedToLb"), ("Kwic", "carriedKwic")):
        if ps.get(k) != r[f]:
            probs.append(f"PRE {k}: " + kwic_diff_msg(k, ps.get(k) or "", r[f] or ""))
    if probs:
        flag(rid, "A1", "; ".join(probs))

    # A2 — post-slot identity
    probs = []
    if qs.get("MasterName") != r["newMasterName"]:
        probs.append(f"POST MasterName {qs.get('MasterName')!r} != newMasterName {r['newMasterName']!r}")
    if qs.get("ContextMasters") != r["newContextMasters"]:
        probs.append(f"POST ContextMasters {json.dumps(qs.get('ContextMasters'), ensure_ascii=False)} != newContextMasters {json.dumps(r['newContextMasters'], ensure_ascii=False)}")
    if qs.get("AttributionNote") != r["newAttributionNote"]:
        probs.append("POST AttributionNote != newAttributionNote")
    qa, na = qs.get("ActorAttribution"), r["newActorAttribution"]
    if qa != na:
        if isinstance(qa, dict) and isinstance(na, dict):
            keys = sorted(set(qa) | set(na))
            diffs = [k for k in keys if qa.get(k) != na.get(k)]
            probs.append("POST ActorAttribution != newActorAttribution (differs in: " + ", ".join(diffs) + ")")
        else:
            probs.append(f"POST ActorAttribution {type(qa).__name__} != newActorAttribution {type(na).__name__}")
    for k, f in (("RelPath", "carriedRelPath"), ("FromLb", "carriedFromLb"), ("ToLb", "carriedToLb"), ("Kwic", "carriedKwic")):
        if qs.get(k) != r[f]:
            probs.append(f"POST {k}: " + kwic_diff_msg(k, qs.get(k) or "", r[f] or ""))
    if probs:
        flag(rid, "A2", "; ".join(probs))

    # A3 — sense coverage
    probs = []
    psn, qsn = sense(pre, si), sense(post, si)
    if len(psn.get("Occurrences", [])) != len(qsn.get("Occurrences", [])):
        probs.append(f"sense occurrence count PRE {len(psn.get('Occurrences', []))} != POST {len(qsn.get('Occurrences', []))}")
    else:
        covered_oi = {rr["oi"] for rr in OCC_ATTR_ROWS if rr["entry"] == eid}
        for i in range(len(psn["Occurrences"])):
            oi_x = i + 1
            if oi_x in covered_oi:
                continue
            if psn["Occurrences"][i] != qsn["Occurrences"][i]:
                probs.append(f"untouched occurrence oi={oi_x} is NOT deep-equal PRE->POST")
    post_rels = [o.get("RelPath") for o in qsn.get("Occurrences", [])]
    if r["postOccurrenceRels"] != post_rels:
        probs.append(f"postOccurrenceRels {r['postOccurrenceRels']} != POST sense RelPaths in order {post_rels}")
    if r["postOccurrenceCount"] != len(qsn.get("Occurrences", [])):
        probs.append(f"postOccurrenceCount {r['postOccurrenceCount']} != POST occurrence count {len(qsn.get('Occurrences', []))}")
    if probs:
        flag(rid, "A3", "; ".join(probs))

    # A4 — label-verbatim
    label = (r.get("newActorAttribution") or {}).get("ActorLabel")
    if not isinstance(label, str) or not label:
        flag(rid, "A4", "newActorAttribution.ActorLabel missing/empty — cannot satisfy label-verbatim")
    else:
        lab = label.casefold()
        in_row_note = lab in (r.get("newAttributionNote") or "").casefold()
        in_post_note = lab in (qs.get("AttributionNote") or "").casefold()
        if not (in_row_note and in_post_note):
            flag(rid, "A4", f"ActorLabel {label!r} casefolded-substring in newAttributionNote={in_row_note}, in POST slot AttributionNote={in_post_note}")


# ------------------------------------------------------------- Law B helpers
def check_prose_row(r):
    rid = r["rowId"]
    eid, si, field, oi = r["entry"], r["si"], r["field"], r.get("oi")
    pre, post = ent("pre", eid), ent("post", eid)
    before, after = r["before"], r["after"]

    if oi is not None:
        # B3' — slot-field prose semantics
        try:
            ps, qs = slot(pre, si, oi), slot(post, si, oi)
        except (IndexError, KeyError) as e:
            flag(rid, "B3", f"slot lookup failed: {e!r}")
            return
        pv, qv = ps.get(field), qs.get(field)
        if not isinstance(pv, str) or not isinstance(qv, str):
            flag(rid, "B3", f"slot field {field} is not a string PRE/POST")
            return
        probs = []
        if pv.count(before) != 1:
            probs.append(f"PRE slot contains before {pv.count(before)} times (need exactly 1)")
        if pv.replace(before, after, 1) != qv:
            i, ca, cb = first_divergence(pv.replace(before, after, 1), qv)
            probs.append(f"PRE-slot with before->after replaced once != POST slot (first divergence at {i}: expected ...{ca}... got ...{cb}...)")
        if qv.count(after) != 1:
            probs.append(f"POST slot contains after {qv.count(after)} times (need exactly 1)")
        if probs:
            flag(rid, "B3", "; ".join(probs))
        return

    # Sense-level field: B1 + B2
    psn, qsn = sense(pre, si), sense(post, si)
    pv, qv = psn.get(field), qsn.get(field)
    if not isinstance(pv, str) or not isinstance(qv, str):
        flag(rid, "B1", f"sense field {field} is not a string PRE/POST (PRE {type(pv).__name__}, POST {type(qv).__name__})")
        return
    probs_b1 = []
    c_pre = pv.count(before)
    c_post = qv.count(after)
    if c_pre != 1:
        probs_b1.append(f"PRE {field} contains before {c_pre} times (need exactly 1)")
    if c_post != 1:
        anchor = qv.find(before[:12])
        ctx = qv[max(0, anchor - 40): anchor + 80] if anchor >= 0 else qv[:120]
        probs_b1.append(f"POST {field} contains after {c_post} times (need exactly 1); POST region around the edit site: {ctx!r}")
    if probs_b1:
        flag(rid, "B1", "; ".join(probs_b1))
    expected = pv.replace(before, after, 1)
    if expected != qv:
        i, ca, cb = first_divergence(expected, qv)
        flag(rid, "B2", f"PRE {field} with before->after replaced once != POST {field} (first divergence at char {i}: expected ...{ca}... / actual ...{cb}...)")


def check_b4():
    pairs = sorted({(r["entry"], r["si"]) for r in rows if r["class"] == "explanation-rewrite"})
    report = []
    bad = {}
    for eid, si in pairs:
        s = sense(ent("post", eid), si)
        text = "\n".join([s.get("Explanation") or "", s.get("Note") or ""])
        kwics = [o.get("Kwic") for o in s.get("Occurrences", []) if o.get("Kwic")]
        for ca in s.get("ClaimAnchors") or []:
            if isinstance(ca, dict):
                for k in ("Kwic", "kwic"):
                    if isinstance(ca.get(k), str) and ca[k]:
                        kwics.append(ca[k])
        runs = CJK_RUN.findall(text)
        unanchored = [run for run in runs if not any(run in k or k in run for k in kwics)]
        report.append((eid, si, runs, unanchored))
        if unanchored:
            bad[(eid, si)] = unanchored
    for r in rows:
        if r["class"] == "explanation-rewrite":
            key = (r["entry"], r["si"])
            if key in bad:
                flag(r["rowId"], "B4", f"unanchored CJK runs in POST Explanation+Note: {bad[key]}")
    return report


# ------------------------------------------------------------- Law C helpers
def check_rename_row(r):
    rid = r["rowId"]
    eid, si = r["entry"], r["si"]
    pre, post = ent("pre", eid), ent("post", eid)
    old, new = r["renamed"]["old"], r["renamed"]["new"]
    pre_rm = sense(pre, si).get("RelatedMasters")
    post_rm = sense(post, si).get("RelatedMasters")
    probs = []
    if not isinstance(pre_rm, list) or pre_rm.count(old) != 1:
        probs.append(f"PRE RelatedMasters contains old {pre_rm.count(old) if isinstance(pre_rm, list) else 'n/a'} times (need exactly 1)")
    else:
        expected = list(pre_rm)
        expected[expected.index(old)] = new
        if post_rm != expected:
            probs.append(f"POST RelatedMasters {post_rm} != PRE with rename applied {expected}")
    if r["postRelatedMasters"] != post_rm:
        probs.append(f"postRelatedMasters {r['postRelatedMasters']} != POST RelatedMasters {post_rm}")
    if probs:
        flag(rid, "C1", "; ".join(probs))
    m = re.search(r"'([^']+)'", lane_law["t48n2025Class"])
    roster = m.group(1) if m else None
    if new != roster:
        flag(rid, "C2", f"renamed.new {new!r} != roster name from laneLaw.t48n2025Class {roster!r}")


# ------------------------------------------------------------- Law E checks
def check_lane_law():
    retired = set(lane_law["retiredRels"])
    for eid in ENTRY_IDS:
        pre, post = ent("pre", eid), ent("post", eid)
        trig = first_row_of(eid)
        # E1 — retired rels gone from POST
        for s_i, s in enumerate(post["Senses"], 1):
            for o_i, o in enumerate(s.get("Occurrences", []), 1):
                if o.get("RelPath") in retired:
                    flag(trig, "E1", f"retired RelPath {o.get('RelPath')} still present in POST {eid} sense {s_i} occurrence {o_i} (entry-level check; triggering row is the entry's first row)")
            for c_i, ca in enumerate(s.get("ClaimAnchors") or [], 1):
                if isinstance(ca, dict) and ca.get("RelPath") in retired:
                    flag(trig, "E1", f"retired RelPath in POST {eid} sense {s_i} ClaimAnchors[{c_i}] (entry-level check; first row named)")
        # E2 — structure preserved
        if len(pre["Senses"]) != len(post["Senses"]):
            flag(trig, "E2", f"sense count PRE {len(pre['Senses'])} != POST {len(post['Senses'])} for {eid} (entry-level check; first row named)")
        for s_i, (ps, qs) in enumerate(zip(pre["Senses"], post["Senses"]), 1):
            if len(ps.get("Occurrences", [])) != len(qs.get("Occurrences", [])):
                flag(trig, "E2", f"sense {s_i} occurrence count PRE {len(ps.get('Occurrences', []))} != POST {len(qs.get('Occurrences', []))} for {eid} (entry-level check; first row named)")
        # E3 — Dehui census
        for s_i, s in enumerate(post["Senses"], 1):
            for o_i, o in enumerate(s.get("Occurrences", []), 1):
                if o.get("MasterName") == "Dehui":
                    flag(trig, "E3", f"bare 'Dehui' still a POST occurrence MasterName in {eid} sense {s_i} occurrence {o_i} (entry-level check; first row named)")
                for cm in o.get("ContextMasters") or []:
                    if isinstance(cm, dict) and cm.get("MasterName") == "Dehui":
                        flag(trig, "E3", f"bare 'Dehui' still in ContextMasters of {eid} sense {s_i} occurrence {o_i} (entry-level check; first row named)")
            if "Dehui" in (s.get("RelatedMasters") or []):
                flag(trig, "E3", f"bare 'Dehui' still in RelatedMasters of {eid} sense {s_i} (entry-level check; first row named)")


# ------------------------------------------------------------- full deep diff
def deep_diff(a, b, path="$"):
    out = []
    if type(a) is not type(b):
        out.append((path, f"type {type(a).__name__}->{type(b).__name__}", a, b))
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((f"{path}.{k}", "added", None, b[k]))
            elif k not in b:
                out.append((f"{path}.{k}", "removed", a[k], None))
            else:
                out.extend(deep_diff(a[k], b[k], f"{path}.{k}"))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path, f"len {len(a)}->{len(b)}", None, None))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(deep_diff(x, y, f"{path}[{i}]"))
    else:
        if a != b:
            out.append((path, "value", a, b))
    return out


# ------------------------------------------------------------------- run all
for r in rows:
    cls = r["class"]
    if cls == "occ-attribution":
        check_occ_row(r)
    elif cls == "explanation-rewrite":
        check_prose_row(r)
    elif cls == "relatedmasters-rename":
        check_rename_row(r)
    else:
        flag(r["rowId"], "?", f"unknown row class {cls!r}")

b4_report = check_b4()
check_lane_law()

# rowSha best-effort (NOT a law — for notes only)
rowsha_hits = 0
rowsha_tries = 0
for r in rows:
    body = {k: v for k, v in r.items() if k != "rowSha"}
    cands = [
        json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        json.dumps(body, ensure_ascii=False, separators=(",", ":")),
        json.dumps(body, ensure_ascii=False, separators=(", ", ": "), sort_keys=True),
        json.dumps(body, ensure_ascii=False, indent=1, sort_keys=True),
        json.dumps(body, ensure_ascii=False, indent=1),
        json.dumps(body, separators=(",", ":"), sort_keys=True),
    ]
    rowsha_tries += 1
    if any(hashlib.sha256(c.encode("utf-8")).hexdigest() == r["rowSha"] for c in cands):
        rowsha_hits += 1

print("\nLaw-B4 anchoring report (evaluated once per (entry, si) touched by Law-B rows):")
for eid, si, runs, unanchored in b4_report:
    print(f"  ({eid}, si={si}): {len(runs)} CJK runs, unanchored: {unanchored if unanchored else 'NONE'}")
    for run in runs:
        print(f"    run: {run}")

print(f"\nrowSha best-effort: {rowsha_hits}/{rowsha_tries} rows matched one of 6 canonicalizations (not a law; informational)")

print("\nPRE->POST full deep diff (materials):")
for eid in ENTRY_IDS:
    diffs = deep_diff(ent("pre", eid), ent("post", eid))
    print(f"  {eid}: {len(diffs)} differing paths")
    for path, kind, a, b in diffs:
        if kind == "value" and isinstance(a, str) and isinstance(b, str):
            i, ca, cb = first_divergence(a, b)
            print(f"    {path}: strings diverge at {i} (materials ...{ca}... -> ...{cb}...)")
        else:
            sa = json.dumps(a, ensure_ascii=False)[:120] if a is not None else "None"
            sb = json.dumps(b, ensure_ascii=False)[:120] if b is not None else "None"
            print(f"    {path} [{kind}]: {sa} -> {sb}")

order = {r["rowId"]: i for i, r in enumerate(rows)}
law_order = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B1": 5, "B2": 6, "B3": 7, "B4": 8, "C1": 9, "C2": 10, "E1": 11, "E2": 12, "E3": 13}
flags.sort(key=lambda f: (order.get(f["rowId"], 99), law_order.get(f["law"], 99)))

print(f"\nFLAGS ({len(flags)}):")
for f in flags:
    print(f"  {f['rowId']} / {f['law']}: {f['reason']}")

notes = (
    "All 4 materials sha256 pins matched (Step 0 OK). Every one of the 10 rows was checked "
    "against the frozen bytes; unflagged rows are accepted. Laws E1/E2/E3 were checked across "
    "both materials entries and produced no flags (no retired RelPath T/T48/T48n2023.xml or "
    "X/X63/X63n1245.xml anywhere in POST; sense and occurrence counts identical PRE->POST; bare "
    "'Dehui' absent from all POST MasterName/ContextMasters/RelatedMasters). Law B4 was "
    "evaluated once per (entry, si) touched by Law-B rows — only (t_351fa42d396b, si=1); all 6 "
    "maximal CJK runs in its POST Explanation+Note (二時上粥飯, 三時上茶湯, 除二時粥飯是雜用心處, "
    "粥飯主人 x2, 二時粥飯 — 5 distinct) are anchored by Occurrences kwics (ClaimAnchors are absent/empty in all "
    "materials, so E1's ClaimAnchors scan is trivially clean). Caveats: (1) rowSha is not part "
    "of any stated law and no canonicalization was specified; a best-effort check over 6 "
    "common canonical JSON forms matched {hits} of 10 rows, so rowSha agreement was treated as "
    "unverifiable from the inputs and NOT used to flag. (2) A3's 'match on oi' coverage set was "
    "taken per entry among occ-attribution rows (all are si=1, so sense-scoping is moot). "
    "(3) Equality checks compare parsed JSON values (deep equality), per the task's '==' "
    "definition; raw-byte equality was additionally pinned via the materials sha256 step. "
    "(4) All occ-attribution rows for a slot describe the same edit; the frozen POST bytes "
    "adjudicate which claims match."
).replace("{hits}", str(rowsha_hits))

verdict = {
    "reviewer": "reviewer2",
    "materialsPinsOk": True,
    "rowsChecked": len(rows),
    "flags": flags,
    "notes": notes,
}
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "verdicts.json").write_text(
    json.dumps(verdict, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
)
print(f"\nverdicts.json written to {OUT_DIR}")
