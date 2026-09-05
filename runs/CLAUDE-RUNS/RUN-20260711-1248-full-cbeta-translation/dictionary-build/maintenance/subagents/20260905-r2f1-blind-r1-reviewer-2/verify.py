# -*- coding: utf-8 -*-
"""
Blind review r2f1-main round r1 — mechanical checker (reviewer 2).

Implements the laws from the task brief byte-exactly against the frozen
materials:

  occ-attribution : A1 A2 B1 B2 C1 C2 C3 (+E1)
  note-provenance : old/new provenance flags + excerpt (+E1)
  alias-add       : oldAliases/newAliases/addedAlias (+E1)
  surface-census  : D1 D2 D3 D4

Steps:
  1. sha256-verify every materialsPins entry over raw bytes (abort on fail)
  2. check all 11 rows (identified by deck position R0000..R0010)
  3. write verdicts.json + verify-report.txt

Run: python -X utf8 verify.py
"""

import hashlib
import json
import sys
from pathlib import Path

BASE = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS"
            r"\RUN-20260711-1248-full-cbeta-translation\dictionary-build\maintenance")
MATS = BASE / "r2f1-main-blind-r1-materials-20260905"
ROWS_FILE = BASE / "r2f1-main-blind-r1-rows-20260905.json"
OUTDIR = BASE / "subagents" / "20260905-r2f1-blind-r1-reviewer-2"

EIDS = ["t_057cc9ea8755", "t_351fa42d396b", "t_968a2f97c9ff",
        "t_ab715aa474d5", "t_ea2a427c7aba"]

report = []
flags = []


def say(line=""):
    report.append(line)
    print(line)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- step 1: pins
rows_doc = load_json(ROWS_FILE)
pins = rows_doc["materialsPins"]
materials_pins_ok = True
say("=" * 78)
say("STEP 1 — materialsPins sha256 verification (raw bytes)")
say("=" * 78)
for name, expected in pins.items():
    data = (MATS / name).read_bytes()
    got = hashlib.sha256(data).hexdigest()
    ok = (got == expected)
    materials_pins_ok = materials_pins_ok and ok
    say(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if not ok:
        say(f"        expected {expected}")
        say(f"        actual   {got}")
say(f"materialsPinsOk = {materials_pins_ok}")
say()

if not materials_pins_ok:
    verdict = {
        "reviewer": "reviewer2",
        "materialsPinsOk": False,
        "rowsChecked": 0,
        "flags": [],
        "notes": "ABORTED: at least one materialsPins sha256 failed; no row checks performed.",
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "verdicts.json").write_text(
        json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTDIR / "verify-report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    sys.exit(1)

# ------------------------------------------------------------- load materials
main = {eid: load_json(MATS / f"main-head-{eid}.json") for eid in EIDS}
staged = {eid: load_json(MATS / f"staged-{eid}.json") for eid in EIDS}
facts = load_json(MATS / "surface-facts.json")

rows = rows_doc["rows"]


def is_absent(doc):
    return isinstance(doc, dict) and doc.get("__absent__") is True


def iter_occurrences(doc):
    """Yield (sense_index_1based, occ_index_1based, occ) over all senses."""
    if is_absent(doc):
        return
    for si, sense in enumerate(doc.get("Senses", []), start=1):
        for oi, occ in enumerate(sense.get("Occurrences", []), start=1):
            yield si, oi, occ


def find_occurrence(doc, rel_path, from_lb):
    """All occurrences in doc with matching RelPath+FromLb (any sense)."""
    return [occ for _, _, occ in iter_occurrences(doc)
            if occ.get("RelPath") == rel_path and occ.get("FromLb") == from_lb]


def get_occurrence(doc, si, oi):
    senses = doc.get("Senses", [])
    if not (1 <= si <= len(senses)):
        return None
    occs = senses[si - 1].get("Occurrences", [])
    if not (1 <= oi <= len(occs)):
        return None
    return occs[oi - 1]


def first_diff(a, b):
    """Human-readable first-divergence for two strings."""
    if a == b:
        return None
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    def frag(s):
        lo, hi = max(0, i - 12), min(len(s), i + 12)
        return f"...{s[lo:hi]}...[len={len(s)}]"
    ca = f"U+{ord(a[i]):04X}({a[i]})" if i < len(a) else "EOF"
    cb = f"U+{ord(b[i]):04X}({b[i]})" if i < len(b) else "EOF"
    return (f"first differing offset {i}: row={ca} vs material={cb}\n"
            f"        row:      {frag(a)}\n"
            f"        material: {frag(b)}")


def dehui_census(doc, eid):
    out = []
    for _, _, occ in iter_occurrences(doc):
        if occ.get("MasterName") == "Dehui":
            out.append(f"{eid} {occ.get('RelPath')} {occ.get('FromLb')}")
    return out


# recomputations shared by the census rows
changed_ids = [eid for eid in EIDS if main[eid] != staged[eid]]
changed_equals_worklist = sorted(changed_ids) == sorted(EIDS)
census_before = sorted(x for eid in EIDS for x in dehui_census(main[eid], eid))
census_after = sorted(x for eid in EIDS for x in dehui_census(staged[eid], eid))
facts_added_present = (len(facts.get("addedSet", [])) == 1
                       and is_absent(main[facts["addedSet"][0]])
                       and not is_absent(staged[facts["addedSet"][0]]))

say("Recomputed surface quantities from the 10 material files:")
say(f"  changed ids main-head -> staged : {changed_ids}")
say(f"  changedSetEqualsWorklist        : {changed_equals_worklist}")
say(f"  Dehui census before (materials) : {census_before}")
say(f"  Dehui census after  (materials) : {census_after}")
say(f"  surface-facts entryCount        : {facts['entryCount']}")
say(f"  surface-facts addedSet          : {facts.get('addedSet')} "
    f"(absent on main, present staged: {facts_added_present})")
say(f"  len(surface-facts.aliasLost)    : {len(facts.get('aliasLost', []))}")
say()


# ------------------------------------------------------------------ row checks
def check_row(rid, row):
    violated = []
    claims = []
    kind = row.get("kind")

    def fail(laws, claim, actual, diverging):
        violated.extend(laws)
        flags.append({
            "row": rid,
            "laws": laws,
            "claim": claim,
            "actual": actual,
            "divergingBytes": diverging,
        })

    # E1 — scope (rows that carry an entry)
    entry = row.get("entry")
    if entry is not None and entry not in EIDS:
        fail(["E1"], f"row entry {entry!r} is one of the 5 material ids",
             f"entry {entry!r} is not in the 5-id worklist",
             f"row entry={entry!r} vs worklist={EIDS}")

    if kind == "occ-attribution":
        eid = row["entry"]
        s_doc, m_doc = staged[eid], main[eid]
        occ = get_occurrence(s_doc, row["si"], row["oi"])

        # A1 — locator resolves to a real staged occurrence with matching window
        if occ is None:
            fail(["A1"],
                 f"Senses[{row['si']}].Occurrences[{row['oi']}] exists in staged-{eid}.json",
                 "index out of range in staged material",
                 f"si={row['si']} oi={row['oi']} vs staged sense/occ counts "
                 f"{[len(s.get('Occurrences', [])) for s in s_doc.get('Senses', [])]}")
        else:
            if occ.get("RelPath") != row["relPath"] or occ.get("FromLb") != row["fromLb"] \
                    or occ.get("ToLb") != row["toLb"]:
                fail(["A1"],
                      f"staged occurrence window == row relPath/fromLb/toLb "
                      f"({row['relPath']} @ {row['fromLb']}-{row['toLb']})",
                      f"staged window is {occ.get('RelPath')} @ "
                      f"{occ.get('FromLb')}-{occ.get('ToLb')}",
                      f"row relPath/fromLb/toLb={row['relPath']}/{row['fromLb']}/"
                      f"{row['toLb']} vs staged={occ.get('RelPath')}/{occ.get('FromLb')}/"
                      f"{occ.get('ToLb')}")
        # A2 — carriedKwic byte-exact
        if occ is not None and occ.get("Kwic") != row["carriedKwic"]:
            fail(["A2"], "carriedKwic == staged occurrence Kwic (byte-exact)",
                  "staged Kwic differs",
                  "carriedKwic vs staged Kwic — " + str(first_diff(row["carriedKwic"],
                                                                   occ.get("Kwic", ""))))
        # B1 — oldWindowPresent truth
        matches = find_occurrence(m_doc, row["relPath"], row["fromLb"]) \
            if not is_absent(m_doc) else []
        actually_present = bool(matches)
        if row["oldWindowPresent"] != actually_present:
            fail(["B1"],
                  f"oldWindowPresent == {row['oldWindowPresent']} "
                  f"(occurrence {row['relPath']}@{row['fromLb']} exists in main-head-{eid}.json)",
                  f"main-head occurrence exists = {actually_present}",
                  f"row oldWindowPresent={row['oldWindowPresent']} vs actual="
                  f"{actually_present}")
        # B2 — old-state fields byte-exact (or all-null when absent)
        if actually_present:
            mo = matches[0]
            for key, mkey in (("oldMasterName", "MasterName"),
                              ("oldContextMasters", "ContextMasters"),
                              ("oldAttributionNote", "AttributionNote")):
                if row.get(key) != mo.get(mkey):
                    fail(["B2"], f"{key} == main-HEAD {mkey} (byte-exact)",
                          f"main-HEAD {mkey} = {mo.get(mkey)!r}",
                          f"row {key}={row.get(key)!r} vs main-head={mo.get(mkey)!r}")
        else:
            for key in ("oldMasterName", "oldContextMasters", "oldAttributionNote"):
                if row.get(key) is not None:
                    fail(["B2"], f"{key} is null (old window absent on main HEAD)",
                          f"row carries {key}={row.get(key)!r}",
                          f"row {key}={row.get(key)!r} vs required null")
        # C1 — new-state fields byte-exact
        if occ is not None:
            for key, skey in (("newMasterName", "MasterName"),
                              ("newContextMasters", "ContextMasters"),
                              ("newAttributionNote", "AttributionNote")):
                if row.get(key) != occ.get(skey):
                    fail(["C1"], f"{key} == staged {skey} (byte-exact)",
                          f"staged {skey} = {occ.get(skey)!r}",
                          f"row {key}={row.get(key)!r} vs staged={occ.get(skey)!r}")
            # C2 — newActor equals ActorAttribution's four fields
            aa = occ.get("ActorAttribution") or {}
            actor = row.get("newActor") or {}
            for f in ("Status", "Kind", "ActorLabel", "ActorRole"):
                if actor.get(f) != aa.get(f):
                    fail(["C2"], f"newActor.{f} == staged ActorAttribution.{f}",
                          f"staged ActorAttribution.{f} = {aa.get(f)!r}",
                          f"row newActor.{f}={actor.get(f)!r} vs staged={aa.get(f)!r}")
            # C3 — ActorLabel verbatim (case-insensitive) inside the new note
            label = actor.get("ActorLabel") or ""
            note = row.get("newAttributionNote") or ""
            if label and label.lower() not in note.lower():
                fail(["C3"], f"newActor.ActorLabel {label!r} appears inside newAttributionNote",
                      "label not found in the row's newAttributionNote",
                      f"ActorLabel={label!r} not a substring of newAttributionNote")

    elif kind == "note-provenance":
        eid = row["entry"]
        s_doc, m_doc = staged[eid], main[eid]
        s_occ = find_occurrence(s_doc, row["relPath"], None)  # by RelPath
        s_occ = [o for o in s_occ] or []
        target = None
        for o in iter_occurrences(s_doc):
            if o[2].get("RelPath") == row["relPath"]:
                target = o[2]
        m_hits = [] if is_absent(m_doc) else \
            [o for _, _, o in iter_occurrences(m_doc) if o.get("RelPath") == row["relPath"]]
        old_note = m_hits[0].get("AttributionNote") if m_hits else None
        new_note = target.get("AttributionNote") if target else None
        marker = "至柔等編"
        if row["oldNoteHasProvenance"] != (marker in (old_note or "")):
            fail(["note-provenance"],
                 f"oldNoteHasProvenance == {row['oldNoteHasProvenance']}",
                 f"main-head X70n1399 note contains {marker!r}: "
                 f"{marker in (old_note or '')} (old note exists: {bool(m_hits)})",
                 f"row oldNoteHasProvenance={row['oldNoteHasProvenance']} vs actual="
                 f"{marker in (old_note or '')}")
        if row["newNoteHasProvenance"] != (marker in (new_note or "")):
            fail(["note-provenance"],
                 f"newNoteHasProvenance == {row['newNoteHasProvenance']}",
                 f"staged X70n1399 note contains {marker!r}: {marker in (new_note or '')}",
                 f"row newNoteHasProvenance={row['newNoteHasProvenance']} vs actual="
                 f"{marker in (new_note or '')}")
        if not (new_note or "").startswith(row["newNoteExcerpt"]) \
                and row["newNoteExcerpt"] not in (new_note or ""):
            fail(["note-provenance"],
                 "newNoteExcerpt matches the staged X70n1399 AttributionNote byte-exactly",
                 f"staged note = {new_note!r}",
                 "excerpt vs staged note — " + str(first_diff(row["newNoteExcerpt"],
                                                              new_note or "")))

    elif kind == "alias-add":
        eid = row["entry"]
        old_aliases = (main[eid].get("Senses") or [{}])[0].get("SearchAliases")
        new_aliases = (staged[eid].get("Senses") or [{}])[0].get("SearchAliases")
        if row["oldAliases"] != old_aliases:
            fail(["alias-add"], f"oldAliases == main-head sense-0 SearchAliases {old_aliases!r}",
                 f"main-head sense-0 SearchAliases = {old_aliases!r}",
                 f"row oldAliases={row['oldAliases']!r} vs main-head={old_aliases!r}")
        if row["newAliases"] != new_aliases:
            fail(["alias-add"], f"newAliases == staged sense-0 SearchAliases {new_aliases!r}",
                 f"staged sense-0 SearchAliases = {new_aliases!r}",
                 f"row newAliases={row['newAliases']!r} vs staged={new_aliases!r}")
        added = row["addedAlias"]
        if not (added in (new_aliases or []) and added not in (old_aliases or [])):
            fail(["alias-add"], f"addedAlias {added!r} is in new but not old",
                 f"in new: {added in (new_aliases or [])}; in old: {added in (old_aliases or [])}",
                 f"addedAlias={added!r}; old={old_aliases!r}; new={new_aliases!r}")

    elif kind == "surface-census":
        ec = row.get("entryCount", {})
        f_ec = facts["entryCount"]
        # D1
        if not (ec.get("before") == f_ec["before"] and ec.get("after") == f_ec["after"]
                and f_ec["after"] == f_ec["before"] + 1 and facts_added_present):
            fail(["D1"],
                 f"entryCount == surface-facts {{before: {f_ec['before']}, "
                 f"after: {f_ec['before'] + 1}}} (after = before + 1; addedSet is the one "
                 f"absent-on-main id)",
                 f"surface-facts entryCount = {f_ec}; addedSet ok = {facts_added_present}",
                 f"row entryCount={ec} vs surface-facts={f_ec} "
                 f"(after must be {f_ec['before'] + 1})")
        # D2
        if row["changedSetEqualsWorklist"] != changed_equals_worklist:
            fail(["D2"],
                 f"changedSetEqualsWorklist == {changed_equals_worklist} "
                 f"(exactly the 5 product ids differ between main-head and staged)",
                 f"recomputed changed ids = {changed_ids}",
                 f"row changedSetEqualsWorklist={row['changedSetEqualsWorklist']} vs "
                 f"recomputed={changed_equals_worklist} (changed ids: {changed_ids})")
        # D3
        if row["dehuiCensusBefore"] != census_before or row["dehuiCensusAfter"] != census_after \
                or row["dehuiCensusBefore"] != facts["dehuiCensus"]["before"] \
                or row["dehuiCensusAfter"] != facts["dehuiCensus"]["after"]:
            fail(["D3"],
                 f"dehuiCensusBefore/After == recomputed MasterName=='Dehui' census "
                 f"{census_before} / {census_after}",
                 f"surface-facts dehuiCensus = {facts['dehuiCensus']}",
                 f"row before={row['dehuiCensusBefore']} after={row['dehuiCensusAfter']} vs "
                 f"recomputed {census_before} / {census_after}")
        if not (len(census_before) == 1 and census_before[0].split()[0] in EIDS
                and census_after == []):
            say(f"  NOTE [{rid}] D3 internal-consistency anomaly: "
                f"before={census_before} after={census_after}")
        # D4
        if not (row["nonProductRegression"] == [] == facts.get("nonProductRegression")):
            fail(["D4"], "nonProductRegression == [] (and == surface-facts)",
                 f"row={row['nonProductRegression']!r}; facts={facts.get('nonProductRegression')!r}",
                 f"row nonProductRegression={row['nonProductRegression']!r} vs required []")
        if row["aliasLostCount"] != len(facts.get("aliasLost", [])):
            fail(["D4"], f"aliasLostCount == len(surface-facts.aliasLost) "
                 f"== {len(facts.get('aliasLost', []))}",
                 f"surface-facts.aliasLost has {len(facts.get('aliasLost', []))} entries",
                 f"row aliasLostCount={row['aliasLostCount']} vs "
                 f"len(aliasLost)={len(facts.get('aliasLost', []))}")
    else:
        fail(["schema"], f"row kind {kind!r} is a known kind", "unknown kind", repr(kind))

    return violated


say("=" * 78)
say("STEP 2 — row-by-row law checks (rows identified by deck position)")
say("=" * 78)
row_violations = {}
for i, row in enumerate(rows):
    rid = f"R{i:04d}"
    say(f"[{rid}] kind={row.get('kind')} entry={row.get('entry', '(none)')}")
    violated = check_row(rid, row)
    row_violations[rid] = violated
    if violated:
        say(f"    FLAGGED: laws {sorted(set(violated))}")
    else:
        say("    clean: all applicable laws pass")
say()

# ------------------------------------------------------------------- verdicts
flagged_rows = sorted({f["row"] for f in flags})
verdict = {
    "reviewer": "reviewer2",
    "materialsPinsOk": materials_pins_ok,
    "rowsChecked": len(rows),
    "flags": flags,
    "notes": (
        "All 11 materialsPins sha256 verified over raw bytes before any row check. "
        f"11 rows checked by deck position R0000..R{len(rows)-1:04d}. "
        f"Flagged rows: {', '.join(flagged_rows) if flagged_rows else 'none'}. "
        "R0001 violates A2 (carriedKwic 兼 vs staged 齊). "
        "R0004 violates D1 (after=4715 vs 4716) and D2 (changedSetEqualsWorklist=false "
        "vs recomputed true; all 5 product ids differ). "
        "R0007 violates B1/B2 (claims an old window at T48n2025 1143a07 on main HEAD; "
        "main-head-t_ea2a427c7aba.json has no such occurrence, so oldWindowPresent must "
        "be false and all old* null). "
        "The two surface-census rows carry no 'entry' field (schema of that kind); E1 "
        "was applied to every row that carries an entry. rowSha ignored per the brief. "
        "String comparisons are codepoint-exact over JSON-decoded values."
    ),
}

OUTDIR.mkdir(parents=True, exist_ok=True)
(OUTDIR / "verdicts.json").write_text(
    json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

say("=" * 78)
say("STEP 3 — verdict summary")
say("=" * 78)
say(f"materialsPinsOk : {materials_pins_ok}")
say(f"rowsChecked     : {len(rows)}")
say(f"flagged rows    : {flagged_rows if flagged_rows else 'none'}")
for f in flags:
    say(f"  {f['row']} {f['laws']}: {f['claim']}")
say()
say("verdicts.json + verify-report.txt written to " + str(OUTDIR))

(OUTDIR / "verify-report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
