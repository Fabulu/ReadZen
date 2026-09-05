# -*- coding: utf-8 -*-
"""Blind reviewer 1 — mechanical verification of r2-blind-r1 rows against frozen materials.

Laws implemented exactly as specified in the task file
(r2-blind-r1-reviewer-task-20260903.md). One deviation, documented in
verdicts.json notes + FINDINGS.md: Law B3's literal `==` reading is vacuous
for the attributionnote-rewrite rows here (before/after are fragments by
design, as under B1/B2), so B1/B2 are applied at the pinned slot
(slot(entry,si,oi).AttributionNote) and B3 is evaluated both literally
(reported) and as containment (adjudicated).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

BASE = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation\dictionary-build\maintenance")
ROWS_PATH = BASE / "r2-blind-r1-rows-20260903.json"
MAT = BASE / "r2-blind-r1-materials"
OUT = BASE / "subagents" / "20260903-r2-blind-r1-reviewer-1"

CJK_RUN = re.compile("[\u3400-\u9fff\uf900-\ufaff]+")

flags = []          # list of {"rowId","law","reason"}
notes_bits = []


def flag(row_id, law, reason):
    flags.append({"rowId": row_id, "law": law, "reason": reason})


def cp(s):
    """codepoint dump of a short string"""
    return " ".join("U+%04X(%s)" % (ord(c), c) for c in s)


def sdiff(a, b, ctx=10):
    """first divergence of two strings -> human line with codepoints"""
    if a == b:
        return "identical"
    i = 0
    n = min(len(a), len(b))
    while i < n and a[i] == b[i]:
        i += 1
    ca = a[i] if i < len(a) else "<EOF>"
    cb = b[i] if i < len(b) else "<EOF>"
    return ("first divergence at char %d: row=%s material=%s | row ctx ...%s | material ctx ...%s"
            % (i, cp(ca), cp(cb), a[max(0, i - ctx):i + ctx], b[max(0, i - ctx):i + ctx]))


def jdump(v):
    return json.dumps(v, ensure_ascii=False)


# ---------------------------------------------------------------- step 0
rows_doc = json.loads(ROWS_PATH.read_text(encoding="utf-8-sig"))
pins = rows_doc["materials"]

pin_report = []
pins_ok = True
for rel in sorted(pins):
    want = pins[rel]
    got = hashlib.sha256((MAT / rel).read_bytes()).hexdigest()
    ok = (got == want)
    pin_report.append((rel, ok, want, got))
    if not ok:
        pins_ok = False

print("== Step 0: sha256 pins ==")
for rel, ok, want, got in pin_report:
    print("%-32s %s" % (rel, "OK" if ok else "MISMATCH want=%s got=%s" % (want, got)))

if not pins_ok:
    verdict = {
        "reviewer": "reviewer1",
        "materialsPinsOk": False,
        "rowsChecked": 0,
        "flags": [],
        "notes": "materials sha256 pin mismatch: " + "; ".join(
            "%s want=%s got=%s" % (r, w, g) for r, ok, w, g in pin_report if not ok),
    }
    (OUT / "verdicts.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding="utf-8")
    print("PIN MISMATCH -> verdicts.json written, stopped.")
    sys.exit(0)

# ---------------------------------------------------------------- load materials
entries = {}
for rel in pins:
    side, name = rel.split("/", 1)
    entry_id = name[:-5]
    entries.setdefault(entry_id, {})[side] = json.loads((MAT / rel).read_text(encoding="utf-8-sig"))

pre = {k: v["pre"] for k, v in entries.items()}
post = {k: v["post"] for k, v in entries.items()}

rows = rows_doc["rows"]
assert len(rows) == 16, len(rows)
lane_law = rows_doc["laneLaw"]
retired = lane_law["retiredRels"]


def slot(doc, entry, si, oi):
    try:
        return doc[entry]["Senses"][si - 1]["Occurrences"][oi - 1]
    except (IndexError, KeyError):
        return None


def sense(doc, entry, si):
    try:
        return doc[entry]["Senses"][si - 1]
    except (IndexError, KeyError):
        return None


# covered (entry, oi) from occ-attribution rows, for A3
covered = set()
for r in rows:
    if r["class"] == "occ-attribution":
        covered.add((r["entry"], r["oi"]))

# ---------------------------------------------------------------- Law A
def law_a(r):
    rid = r["rowId"]
    entry, si, oi = r["entry"], r["si"], r["oi"]
    ps, qs = sense(pre, entry, si), sense(post, entry, si)
    if ps is None or qs is None:
        flag(rid, "A1", "sense %d out of range" % si)
        return
    po = slot(pre, entry, si, oi)
    qo = slot(post, entry, si, oi)

    # ---- A1 pre-slot identity
    a1 = []
    if po is None:
        a1.append("PRE has no occurrence oi=%d (sense has %d occurrences)" % (oi, len(ps["Occurrences"])))
    else:
        for f, claim in (("MasterName", r["oldMasterName"]),
                         ("AttributionNote", r["oldAttributionNote"])):
            if po.get(f) != claim:
                a1.append("PRE slot %s != old field. %s" % (f, sdiff(claim if isinstance(claim, str) else jdump(claim),
                                                                     po.get(f) if isinstance(po.get(f), str) else jdump(po.get(f)))))
        if po.get("ContextMasters") != r["oldContextMasters"]:
            a1.append("PRE slot ContextMasters != oldContextMasters. row=%s material=%s"
                      % (jdump(r["oldContextMasters"]), jdump(po.get("ContextMasters"))))
        for f, claim in (("RelPath", r["carriedRelPath"]), ("FromLb", r["carriedFromLb"]),
                         ("ToLb", r["carriedToLb"]), ("Kwic", r["carriedKwic"])):
            if po.get(f) != claim:
                a1.append("PRE slot %s != carried. %s" % (f, sdiff(claim, po.get(f) or "")))
    if a1:
        flag(rid, "A1", "pre-slot identity broken: " + " || ".join(a1))

    # ---- A2 post-slot identity
    a2 = []
    if qo is None:
        a2.append("POST has no occurrence oi=%d" % oi)
    else:
        if qo.get("MasterName") != r["newMasterName"]:
            a2.append("POST slot MasterName=%r != row newMasterName=%r" % (qo.get("MasterName"), r["newMasterName"]))
        if qo.get("ContextMasters") != r["newContextMasters"]:
            a2.append("POST slot ContextMasters=%s != row newContextMasters=%s"
                      % (jdump(qo.get("ContextMasters")), jdump(r["newContextMasters"])))
        if qo.get("AttributionNote") != r["newAttributionNote"]:
            a2.append("POST slot AttributionNote != row newAttributionNote. %s"
                      % sdiff(r["newAttributionNote"], qo.get("AttributionNote") or ""))
        if qo.get("ActorAttribution") != r["newActorAttribution"]:
            rowa, mata = r["newActorAttribution"], qo.get("ActorAttribution")
            diffs = []
            if isinstance(mata, dict) and isinstance(rowa, dict):
                for k in sorted(set(rowa) | set(mata)):
                    if rowa.get(k) != mata.get(k):
                        diffs.append("%s: row=%s material=%s" % (k, jdump(rowa.get(k)), jdump(mata.get(k))))
            else:
                diffs.append("row=%s material=%s" % (jdump(rowa), jdump(mata)))
            a2.append("POST slot ActorAttribution != row newActorAttribution [" + "; ".join(diffs) + "]")
        for f, claim in (("RelPath", r["carriedRelPath"]), ("FromLb", r["carriedFromLb"]),
                         ("ToLb", r["carriedToLb"]), ("Kwic", r["carriedKwic"])):
            if qo.get(f) != claim:
                a2.append("POST slot %s != carried (not unchanged). %s" % (f, sdiff(claim, qo.get(f) or "")))
    if a2:
        flag(rid, "A2", "post-slot identity broken: " + " || ".join(a2))

    # ---- A3 sense coverage
    a3 = []
    if len(ps["Occurrences"]) != len(qs["Occurrences"]):
        a3.append("occurrence count PRE=%d POST=%d" % (len(ps["Occurrences"]), len(qs["Occurrences"])))
    else:
        for i in range(len(ps["Occurrences"])):
            if (entry, i + 1) in covered:
                continue
            if ps["Occurrences"][i] != qs["Occurrences"][i]:
                a3.append("uncovered occurrence oi=%d differs PRE->POST" % (i + 1))
    post_rels = [o["RelPath"] for o in qs["Occurrences"]]
    if r["postOccurrenceRels"] != post_rels:
        a3.append("postOccurrenceRels row=%s != POST rels=%s" % (jdump(r["postOccurrenceRels"]), jdump(post_rels)))
    if r["postOccurrenceCount"] != len(qs["Occurrences"]):
        a3.append("postOccurrenceCount row=%s != POST count=%d" % (r["postOccurrenceCount"], len(qs["Occurrences"])))
    if a3:
        flag(rid, "A3", "sense coverage broken: " + " || ".join(a3))


# ---------------------------------------------------------------- Law B
b_rows_by_entry_si = {}
b3_literal_report = []

def law_b(r):
    rid = r["rowId"]
    entry, si = r["entry"], r["si"]
    ps, qs = sense(pre, entry, si), sense(post, entry, si)
    before, after, field = r["before"], r["after"], r["field"]
    b_rows_by_entry_si.setdefault((entry, si), []).append(r)

    if r["class"] == "attributionnote-rewrite":
        oi = r["oi"]
        po, qo = slot(pre, entry, si, oi), slot(post, entry, si, oi)
        if po is None or qo is None:
            flag(rid, "B3", "slot oi=%d missing PRE or POST" % oi)
            return
        pre_val, post_val = po.get("AttributionNote"), qo.get("AttributionNote")
        # literal B3 (documented; vacuous for fragment before/after)
        b3_literal_report.append((rid, po.get("AttributionNote") == before and qo.get("AttributionNote") == after))
    else:
        if field not in ps or field not in qs:
            flag(rid, "B1", "sense has no field %r" % field)
            return
        pre_val, post_val = ps[field], qs[field]

    # B1 containment exactly once
    b1 = []
    c1 = pre_val.count(before)
    c2 = post_val.count(after)
    if c1 != 1:
        b1.append("PRE %s contains before %d times (need exactly 1)" % (field, c1))
    if c2 != 1:
        b1.append("POST %s contains after %d times (need exactly 1)%s" % (field, c2, "" if c2 else ""))
    if b1:
        flag(rid, "B1", " || ".join(b1) + (" | after fragment absent from POST material; nearest POST text: ...%s..." % post_val[:120] if c2 == 0 else ""))

    # B2 single replacement equals POST byte-for-byte
    replaced = pre_val.replace(before, after, 1)
    if replaced != post_val:
        flag(rid, "B2", "PRE %s with before->after (one replacement) != POST %s. %s" % (field, field, sdiff(replaced, post_val)))


def b4_check():
    """B4: CJK runs of POST Explanation+Note anchored by kwics; flag Law-B rows of that (entry,si)."""
    for (entry, si), rlist in sorted(b_rows_by_entry_si.items()):
        qs = sense(post, entry, si)
        text = (qs.get("Explanation") or "") + "\n" + (qs.get("Note") or "")
        kwics = [o.get("Kwic") for o in qs.get("Occurrences", [])]
        kwics += [c.get("Kwic") for c in qs.get("ClaimAnchors", [])]
        kwics = [k for k in kwics if k]
        unanchored = [run for run in CJK_RUN.findall(text)
                      if not any((run in k or k in run) for k in kwics)]
        if unanchored:
            for r in rlist:
                flag(r["rowId"], "B4",
                     "unanchored CJK run(s) in POST sense prose: %s" % " / ".join("%s [%s]" % (u, cp(u)) for u in unanchored))
        print("B4 %s si=%d: %d runs, %d unanchored" % (entry, si, len(CJK_RUN.findall(text)), len(unanchored)))


# ---------------------------------------------------------------- Law C
def law_c(r):
    rid = r["rowId"]
    entry, si = r["entry"], r["si"]
    ps, qs = sense(pre, entry, si), sense(post, entry, si)
    old, new = r["renamed"]["old"], r["renamed"]["new"]
    pre_rm, post_rm = ps.get("RelatedMasters", []), qs.get("RelatedMasters", [])
    n = sum(1 for x in pre_rm if x == old)
    c1 = []
    if n != 1:
        c1.append("PRE RelatedMasters contains %r %d times (need exactly 1): %s" % (old, n, jdump(pre_rm)))
    expected = [new if x == old else x for x in pre_rm]
    if n == 1 and post_rm != expected:
        c1.append("POST RelatedMasters != PRE with %r->%r. %s" % (old, new, jdump(post_rm)))
    if r["postRelatedMasters"] != post_rm:
        c1.append("postRelatedMasters row=%s != POST=%s" % (jdump(r["postRelatedMasters"]), jdump(post_rm)))
    if c1:
        flag(rid, "C1", " || ".join(c1))
    m = re.search(r"roster name is '([^']+)'", lane_law["t48n2025Class"])
    roster = m.group(1) if m else None
    if new != roster:
        flag(rid, "C2", "renamed.new=%r != roster name %r in laneLaw.t48n2025Class" % (new, roster))


# ---------------------------------------------------------------- Law D
def law_d(r):
    rid = r["rowId"]
    entry, si = r["entry"], r["si"]
    ps, qs = sense(pre, entry, si), sense(post, entry, si)
    pre_sa, post_sa = ps.get("SearchAliases", []), qs.get("SearchAliases", [])
    d1 = []
    if pre_sa + [r["added"]] != post_sa:
        d1.append("PRE SearchAliases + [added] != POST SearchAliases. PRE=%s added=%r -> %s; POST=%s"
                  % (jdump(pre_sa), r["added"], jdump(pre_sa + [r["added"]]), jdump(post_sa)))
    if r["postSearchAliases"] != post_sa:
        d1.append("postSearchAliases row=%s != POST=%s" % (jdump(r["postSearchAliases"]), jdump(post_sa)))
    if d1:
        flag(rid, "D1", " || ".join(d1))


# ---------------------------------------------------------------- Law E
def law_e():
    e_problems = []
    for entry in sorted(post):
        p, q = pre[entry], post[entry]
        # E1 retired rels
        for si, s in enumerate(q["Senses"], 1):
            for kind, arr in (("Occurrences", s.get("Occurrences", [])), ("ClaimAnchors", s.get("ClaimAnchors", []))):
                for o in arr:
                    if o.get("RelPath") in retired:
                        e_problems.append((entry, "E1", "retired RelPath %s still in POST %s si=%d" % (o["RelPath"], kind, si)))
        # E2 structure identity
        if len(p["Senses"]) != len(q["Senses"]):
            e_problems.append((entry, "E2", "sense count PRE=%d POST=%d" % (len(p["Senses"]), len(q["Senses"]))))
            continue
        for si in range(len(q["Senses"])):
            a, b = p["Senses"][si], q["Senses"][si]
            if len(a.get("Occurrences", [])) != len(b.get("Occurrences", [])):
                e_problems.append((entry, "E2", "si=%d occurrence count PRE=%d POST=%d"
                                   % (si + 1, len(a.get("Occurrences", [])), len(b.get("Occurrences", [])))))
    if e_problems:
        for entry, law, msg in e_problems:
            entry_rows = [r for r in rows if r["entry"] == entry]
            rid = entry_rows[0]["rowId"] if entry_rows else entry
            flag(rid, law, "%s: %s (no specific row triggered; entry's first row named per task instructions)" % (entry, msg)
                 if not entry_rows else "%s: %s" % (entry, msg))
    print("E1/E2: %d problems" % len(e_problems))


# ---------------------------------------------------------------- full PRE->POST diff (notes only)
def deep_diff(a, b, path, out):
    if type(a) != type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        out.append("%s: type %s vs %s" % (path, type(a).__name__, type(b).__name__))
        return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append("%s.%s: added in POST" % (path, k))
            elif k not in b:
                out.append("%s.%s: removed in POST" % (path, k))
            else:
                deep_diff(a[k], b[k], "%s.%s" % (path, k), out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append("%s: len %d vs %d" % (path, len(a), len(b)))
        for i in range(min(len(a), len(b))):
            deep_diff(a[i], b[i], "%s[%d]" % (path, i), out)
    else:
        if a != b:
            out.append("%s: differs" % path)


# ---------------------------------------------------------------- run
for r in rows:
    cls = r["class"]
    if cls == "occ-attribution":
        law_a(r)
    elif cls in ("explanation-rewrite", "note-rewrite", "attributionnote-rewrite"):
        law_b(r)
    elif cls == "relatedmasters-rename":
        law_c(r)
    elif cls == "searchaliases-add":
        law_d(r)
    else:
        flag(r["rowId"], "?", "unknown row class %r" % cls)

b4_check()
law_e()

print("\n== B3 literal ==-reading (fragment before/after make it vacuous):")
for rid, ok in b3_literal_report:
    print("  %s: PRE==before and POST==after -> %s" % (rid, ok))

print("\n== full PRE->POST structural diff (all changes, for cross-check) ==")
for entry in sorted(post):
    out = []
    deep_diff(pre[entry], post[entry], entry, out)
    print(" %s: %d changed paths" % (entry, len(out)))
    for line in out:
        print("   %s" % line)

# ---------------------------------------------------------------- verdicts
flags.sort(key=lambda f: (f["rowId"], f["law"]))
row_count = len(rows)

notes_lines = [
    "Method: verify.py implements laws A1-A3, B1-B4, C1-C2, D1, E1-E2 mechanically "
    "(python -X utf8, deep equality of parsed JSON); rows file and all 6 materials were "
    "additionally read in full and eyeballed; every flag re-derived with first-divergence "
    "codepoints printed.",
    "Law B3 adjudication: B3's literal reading (PRE slot AttributionNote == before, POST == after) "
    "is vacuous for attributionnote-rewrite rows because before/after are fragments (as under B1/B2 "
    "semantics); the rows' field name 'OccAttributionNote' does not exist at sense level. I therefore "
    "applied B1 (containment exactly once) and B2 (single-replacement equality) at the pinned slot "
    "slot(entry,si,oi).AttributionNote and treated B3 as that slot-pin. Literal B3 results for the "
    "record: %s. This choice does not change which rows carry real defects: R0015's after "
    "('百丈自編') is absent from POST under either reading; R0007's after ('至柔等編') is present in POST."
    % "; ".join("%s=%s" % (rid, ok) for rid, ok in b3_literal_report),
    "rowSha fields of the rows could not be verified: the canonical serialization they hash is not "
    "specified in the inputs; treated as metadata, not a materials claim.",
    "laneLaw.defectCensus names t_ab715aa474d5 and t_351fa42d396b, which are not in the materials "
    "set; unverifiable from the inputs and not law-checked.",
    "E-laws clean for all three entries: no retired RelPath (T/T48/T48n2023.xml, X/X63/X63n1245.xml) "
    "in any POST Occurrence/ClaimAnchor; sense counts and per-sense occurrence counts identical PRE->POST.",
    "Full PRE->POST structural diff was computed; all differences are covered by the row claims "
    "(attribution rewrites on t_ea2a427c7aba oi=1/8/9, RelatedMasters rename, Explanation fragment; "
    "Note + oi=3 AttributionNote fragments on t_057cc9ea8755; SearchAliases append on t_968a2f97c9ff). "
    "No unlisted changes detected.",
    "B4 anchoring: all maximal CJK runs in POST Explanation+Note of both Law-B-touched senses "
    "(t_ea2a427c7aba si=1, t_057cc9ea8755 si=1) are anchored by kwics; no B4 flags.",
]

verdict = {
    "reviewer": "reviewer1",
    "materialsPinsOk": True,
    "rowsChecked": row_count,
    "flags": flags,
    "notes": " ".join(notes_lines),
}

(OUT / "verdicts.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n== FLAGS (%d) ==" % len(flags))
for f in flags:
    print("  %s %s: %s" % (f["rowId"], f["law"], f["reason"]))
print("\nrowsChecked=%d, flags=%d -> verdicts.json written" % (row_count, len(flags)))
