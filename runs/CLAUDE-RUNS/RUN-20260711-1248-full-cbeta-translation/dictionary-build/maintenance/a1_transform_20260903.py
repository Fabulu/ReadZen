#!/usr/bin/env python3
"""SPEC_A1_20260902.md §4: the attribution-repair engine (lane A1).

Input is the CLONE pre-state at pinned HEAD 20c9011 (confinement law:
engine(clone) == terms bytes after apply, asserted and re-proved at gate
time). Two edit sources:

  1. mechanical derivation (§2.1): re-derived inline from the clone
     occurrence bytes with the frozen law — VERSE_RE over the
     AttributionNote — and asserted byte-equal to the frozen probe table
     maintenance/a1-muc-derivation-20260902.json before applying
     ContextMasters += {"MasterName": <exact existing string>,
                        "Roles": [<utterer|verse-author>]}.
  2. the authored worksheet maintenance/a1-repairs-20260903.json (§2.2–
     2.7 + AMENDMENT 3): prose rewords (Explanation and Note), the
     dangling anchor, performer bindings, the 僧問 restructure, the
     survivor field fixes, and the duplicate-anchor removal. Every
     record is strictly asserted against the bytes it edits
     (find-string occurs exactly once, anchor kwic contains the string,
     removed anchor matches its pinned RelPath + ClaimText, …).

Path-scope law (§4.6 + AMENDMENTS 1–2): only Senses[i].Explanation /
.Note / .ClaimAnchors and Senses[i].Occurrences[j].ContextMasters /
.ContextActors / .ActorAttribution / .AttributionNote /
.GrammarEvidence / .MasterName (the one anon-monk clear) may differ;
anything else aborts before write. Determinism: the engine
re-derives twice and requires byte-identical canon output (authored
ReviewedUtc values are constants in the worksheet, not wall-clock).

Receipt: maintenance/a1-edit-receipt-20260903.json. Run with --apply to
write terms bytes (asserts current terms == canon(clone pre-state)
first); without it, dry.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
CLONE_HEAD_PIN = "20c9011"
DERIVATION = "a1-muc-derivation-20260902.json"
WORKSHEET = "a1-repairs-20260903.json"
RECEIPT = "a1-edit-receipt-20260903.json"

VERSE_RE = re.compile(
    r"偈|頌|歌|verse|song|gatha|ode|encomium|eulogy|inscription",
    re.IGNORECASE)
# §4.6 path-scope law as regexes over flat() paths: a changed path is
# in-scope iff it matches one of these (the leaf or anything under it).
ALLOWED_PATH_RES = (
    re.compile(r"^Senses\[\d+\]\.(?:Explanation|Note|ClaimAnchors)(?:[.\[]|$)"),
    re.compile(r"^Senses\[\d+\]\.Occurrences\[\d+\]\."
               r"(?:ContextMasters|ContextActors|ActorAttribution|"
               r"AttributionNote|GrammarEvidence|MasterName)(?:[.\[]|$)"),
)
ACTION_PERFORMER_PROOF_RE = re.compile(
    r"\bAction performer:\s*[^.;]{3,100}\s*\("
    r"(?:identified-unlinked-master|identified-non-master|reviewed-unnamed)",
    re.IGNORECASE)
ATTRIBUTION_RUNGS = ["line", "expanded-context", "section-header",
                     "book-title", "tei-header", "parallel-passage"]


def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def clone_state() -> dict[str, dict]:
    head = subprocess.run(
        ["git", "-C", str(CLONE), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    if head[:7] != CLONE_HEAD_PIN:
        raise SystemExit(f"clone HEAD {head[:7]} != pin {CLONE_HEAD_PIN}")
    dirty = subprocess.run(
        ["git", "-C", str(CLONE), "status", "--porcelain"],
        capture_output=True, text=True).stdout.splitlines()
    if dirty:
        raise SystemExit(f"clone dirty: {dirty[:5]}")
    v2 = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
    return {e["Id"]: e for e in v2["Entries"]}


def flat(value, prefix: str = "", out: list | None = None) -> list:
    """Flatten to (path, canonical-leaf-bytes) pairs for path-scope diff."""
    if out is None:
        out = []
    if isinstance(value, dict):
        for k in sorted(value):
            flat(value[k], f"{prefix}.{k}" if prefix else k, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            flat(v, f"{prefix}[{i}]", out)
    else:
        out.append((prefix, canon(value)))
    return out


def derive_muc(by_id: dict[str, dict]) -> list[dict]:
    """Re-derive the §2.1 mechanical rows from the CLONE bytes.

    Mirrors probe_a1_derive_20260902.py exactly: one row per flagged
    missing_utterer_context pair (MasterName set, no exact actor
    context), role = verse-author iff VERSE_RE hits the note.
    """
    details = json.loads(
        (HERE / "a1-worklist-details-20260902.json")
        .read_text(encoding="utf-8"))["stillFailing"]
    rows = []
    for eid in sorted(details):
        d = by_id[eid]
        for si, sense in enumerate(d.get("Senses", []), 1):
            for oi, occ in enumerate(sense.get("Occurrences") or [], 1):
                flagged_masters = [
                    det.split(": ", 1)[1].strip()
                    for kind, det in details[eid]
                    if kind == "missing_utterer_context"]
                if str(occ.get("MasterName") or "") not in flagged_masters:
                    continue
                note = str(occ.get("AttributionNote") or "")
                hit = VERSE_RE.search(note)
                if hit:
                    s = max(0, hit.start() - 60)
                    role, ev = "verse-author", note[s:hit.end() + 60]
                else:
                    role, ev = "utterer", ""
                rows.append({"entry": eid, "term": d.get("SourceTerm"),
                             "si": si, "oi": oi,
                             "master": occ.get("MasterName"), "role": role,
                             "evidence": ev})
    return rows


def apply_muc(by_id: dict[str, dict], rows: list[dict]) -> list[dict]:
    records = []
    for r in rows:
        occ = (by_id[r["entry"]]["Senses"][r["si"] - 1]
               ["Occurrences"][r["oi"] - 1])
        assert occ.get("MasterName") == r["master"], (
            f"{r['entry']} s{r['si']} o{r['oi']}: derivation master "
            f"{r['master']!r} != clone bytes {occ.get('MasterName')!r}")
        cm = occ.setdefault("ContextMasters", [])
        assert isinstance(cm, list), "ContextMasters must be a list"
        assert not any(isinstance(c, dict) and c.get("MasterName") == r["master"]
                       for c in cm), f"row already present: {r}"
        row = {"MasterName": r["master"], "Roles": [r["role"]]}
        cm.append(row)
        records.append({"class": f"muc-{r['role']}",
                        "entry": r["entry"], "si": r["si"], "oi": r["oi"],
                        "row": row})
    return records


def sense_of(entry: dict, si: int) -> dict:
    return entry["Senses"][si - 1]


def occ_of(entry: dict, si: int, oi: int) -> dict:
    return sense_of(entry, si)["Occurrences"][oi - 1]


def prose_edit(entry: dict, rec: dict) -> dict:
    si = rec.get("si")
    if si is None:
        # resolve the UNIQUE sense whose field contains the find-string
        hits = [k for k, s in enumerate(entry.get("Senses", []), 1)
                if rec["find"] in str(s.get(rec["field"]) or "")]
        assert len(hits) == 1, (
            f"{rec['class']} {rec['entry']}: find-string in "
            f"{len(hits)} senses' {rec['field']}, expected exactly 1")
        si = hits[0]
        rec = dict(rec, si=si)
    s = sense_of(entry, si)
    text = str(s.get(rec["field"]) or "")
    assert text.count(rec["find"]) == 1, (
        f"{rec['class']} {rec['entry']} s{si} {rec['field']}: "
        f"find-string count {text.count(rec['find'])} != 1")
    s[rec["field"]] = text.replace(rec["find"], rec["replace"])
    return rec


def apply_worksheet(by_id: dict[str, dict], sheet: list[dict]) -> list[dict]:
    records = []
    for rec in sheet:
        cls = rec["class"]
        e = by_id[rec["entry"]]
        if cls in ("vague-reword", "dangling-remove"):
            rec = prose_edit(e, rec)
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "field": rec["field"],
                            "find": rec["find"], "replace": rec["replace"]})
        elif cls == "dangling-anchor":
            s = sense_of(e, rec["si"])
            anchors = s.setdefault("ClaimAnchors", [])
            anchor = copy.deepcopy(rec["anchor"])
            strings = rec.get("strings", [rec.get("string")])
            for st in strings:
                assert st and st in str(anchor.get("Kwic") or ""), (
                    f"dangling-anchor {rec['entry']}: anchor kwic does not "
                    f"contain the dangling string {st!r}")
                assert any(st in str(s.get(f) or "")
                           for f in ("Explanation", "Note")), (
                    f"dangling-anchor {rec['entry']}: {st!r} not in prose")
            anchors.append(anchor)
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "anchorSha256": hashlib.sha256(
                                canon(anchor).encode("utf-8")).hexdigest(),
                            "strings": strings})
        elif cls == "performer-context-row":
            occ = occ_of(e, rec["si"], rec["oi"])
            row = copy.deepcopy(rec["row"])
            assert row.get("MasterName") and set(row.get("Roles") or []) & {
                "performer", "action-performer"}, f"bad performer row: {row}"
            cm = occ.setdefault("ContextMasters", [])
            assert not any(isinstance(c, dict)
                           and c.get("MasterName") == row["MasterName"]
                           for c in cm), f"row already present: {row}"
            cm.append(row)
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "oi": rec["oi"], "row": row})
        elif cls == "performer-grammar-proof":
            occ = occ_of(e, rec["si"], rec["oi"])
            assert ACTION_PERFORMER_PROOF_RE.search(rec["sentence"]), (
                f"sentence fails ACTION_PERFORMER_PROOF_RE: "
                f"{rec['sentence']!r}")
            # the audit reads the ACTOR's GrammarEvidence (occ loop passes
            # actor.get("GrammarEvidence") into
            # has_governed_action_performer_context)
            actor = occ.get("ActorAttribution")
            assert isinstance(actor, dict), "no ActorAttribution"
            ge = actor.get("GrammarEvidence")
            assert isinstance(ge, str) and ge.strip(), "no GrammarEvidence"
            assert rec["sentence"] not in ge, "proof already present"
            actor["GrammarEvidence"] = ge.rstrip() + " " + rec["sentence"].strip()
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "oi": rec["oi"],
                            "sentence": rec["sentence"]})
        elif cls == "anon-monk-restructure":
            occ = occ_of(e, rec["si"], rec["oi"])
            assert occ.get("MasterName"), "MasterName already cleared"
            respondent = rec["respondentMaster"]
            note = str(occ.get("AttributionNote") or "")
            speakers = re.findall(r"Speaker: ([^.]*)\.", note)
            assert len(speakers) == 1, f"speaker segments: {speakers}"
            cm = occ.setdefault("ContextMasters", [])
            mine = [c for c in cm if isinstance(c, dict)
                    and c.get("MasterName") == respondent]
            if mine:
                # the master was wrongly bound as utterer; he owns only
                # the responses in this exchange
                assert len(mine) == 1 and mine[0].get("Roles") == ["utterer"], (
                    f"unexpected existing respondent row: {mine}")
                mine[0]["Roles"] = ["respondent"]
            else:
                cm.append({"MasterName": respondent,
                           "Roles": ["respondent"]})
            occ["MasterName"] = None
            actor = copy.deepcopy(rec["actor"])
            assert actor.get("Status") == "reviewed-unnamed"
            assert actor.get("ActorRole") == "questioner"
            assert list(actor.get("RungsChecked") or []) == ATTRIBUTION_RUNGS
            assert re.search(r"(?:僧問|問 introduces|"
                             r"headword-bearing question)",
                             str(actor.get("GrammarEvidence") or ""),
                             re.IGNORECASE)
            assert actor.get("ReviewedBy") and actor.get("ReviewedUtc")
            occ["ActorAttribution"] = actor
            occ["AttributionNote"] = note.replace(
                f"Speaker: {speakers[0]}.",
                f"Speaker: {rec['noteSpeaker']}.")
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "oi": rec["oi"],
                            "respondentMaster": respondent,
                            "actorLabel": actor.get("ActorLabel")})
        elif cls == "grammar-evidence-repeat":
            occ = occ_of(e, rec["si"], rec["oi"])
            ge = occ.get("ActorAttribution", {})
            assert isinstance(ge, dict) and ge.get("GrammarEvidence"), "no AA"
            text = str(ge["GrammarEvidence"])
            assert text.count(rec["find"]) == 1, (
                f"grammar find count {text.count(rec['find'])} != 1")
            assert rec["label"] in rec["replace"], "label not repeated"
            ge["GrammarEvidence"] = text.replace(rec["find"],
                                                 rec["replace"])
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "oi": rec["oi"],
                            "label": rec["label"]})
        elif cls == "reviewed-fields":
            aa = occ_of(e, rec["si"], rec["oi"]).get("ActorAttribution")
            assert isinstance(aa, dict), "no ActorAttribution"
            assert not aa.get("ReviewedBy") and not aa.get("ReviewedUtc"), (
                "reviewed fields already set")
            aa["ReviewedBy"] = rec["reviewedBy"]
            aa["ReviewedUtc"] = rec["reviewedUtc"]
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"], "oi": rec["oi"],
                            "reviewedBy": rec["reviewedBy"]})
        elif cls == "anchor-remove":
            # AMENDMENT 3: a[0] is a strict duplicate of occurrence o1
            # (same record, kwic ⊂ o1's window) — remove rather than recut
            # (audit law: ClaimText may not contain the headword)
            s = sense_of(e, rec["si"])
            anchors = s.get("ClaimAnchors")
            assert isinstance(anchors, list) and anchors, "no ClaimAnchors"
            anchor = anchors[rec["anchorIndex"]]
            assert anchor.get("RelPath") == rec["expectRelPath"], (
                f"anchor-remove {rec['entry']}: RelPath "
                f"{anchor.get('RelPath')!r} != {rec['expectRelPath']!r}")
            assert anchor.get("ClaimText") == rec["expectClaimText"], (
                f"anchor-remove {rec['entry']}: ClaimText "
                f"{anchor.get('ClaimText')!r} != expected")
            anchors.pop(rec["anchorIndex"])
            if not anchors:
                del s["ClaimAnchors"]
            records.append({"class": cls, "entry": rec["entry"],
                            "si": rec["si"],
                            "anchorIndex": rec["anchorIndex"],
                            "removedRelPath": rec["expectRelPath"],
                            "removedClaimText": rec["expectClaimText"]})
        else:
            raise SystemExit(f"unknown worksheet class {cls!r}")
    return records


def transform(by_id: dict[str, dict]) -> tuple[dict[str, str], list[dict]]:
    """Apply everything; return {eid: canon bytes} + edit records."""
    worklist = json.loads(
        (HERE / "a1-worklist-details-20260902.json")
        .read_text(encoding="utf-8"))["worklist"]
    assert len(worklist) == 35, f"worklist size {len(worklist)} != 35"

    frozen = json.loads((HERE / DERIVATION).read_text(encoding="utf-8"))
    derived = derive_muc(by_id)
    assert derived == frozen, (
        "inline §2.1 derivation != frozen table — bytes or law drifted")

    sheet = json.loads((HERE / WORKSHEET).read_text(encoding="utf-8"))
    assert isinstance(sheet, list) and sheet, "worksheet missing/empty"

    records = apply_muc(by_id, derived) + apply_worksheet(by_id, sheet)

    out = {}
    for eid in worklist:
        before_paths = dict(flat(clone_snapshot[eid]))
        after_paths = dict(flat(by_id[eid]))
        changed = {p for p in set(before_paths) | set(after_paths)
                   if before_paths.get(p) != after_paths.get(p)}
        escaped = {p for p in changed
                   if not any(rx.search(p) for rx in ALLOWED_PATH_RES)}
        assert changed, f"{eid}: no changes produced"
        assert not escaped, (
            f"{eid}: diff escaped the allowed paths: {sorted(escaped)}")
        out[eid] = canon(by_id[eid])
    return out, records


clone_snapshot: dict[str, dict] = {}


def main() -> None:
    apply_mode = "--apply" in sys.argv
    by_id = clone_state()
    worklist = json.loads(
        (HERE / "a1-worklist-details-20260902.json")
        .read_text(encoding="utf-8"))["worklist"]
    clone_snapshot.clear()
    clone_snapshot.update({eid: copy.deepcopy(by_id[eid]) for eid in worklist})

    out, records = transform(by_id)

    # determinism: a second full derivation from fresh clone bytes must
    # produce byte-identical output
    by_id2 = clone_state()
    clone_snapshot.clear()
    clone_snapshot.update(
        {eid: copy.deepcopy(by_id2[eid]) for eid in worklist})
    out2, _ = transform(by_id2)
    assert out2 == out, "engine not deterministic"

    counts: dict[str, int] = {}
    for r in records:
        counts[r["class"]] = counts.get(r["class"], 0) + 1

    if apply_mode:
        for eid in worklist:
            terms_p = ROOT / "terms" / eid / "entry.v2.json"
            current = terms_p.read_text(encoding="utf-8")
            if current != canon(clone_snapshot[eid]):
                raise SystemExit(
                    f"{eid}: terms bytes != canon(clone pre-state) — "
                    "refusing to apply onto drifted bytes")
        for eid in worklist:
            terms_p = ROOT / "terms" / eid / "entry.v2.json"
            terms_p.write_text(out[eid], encoding="utf-8", newline="")

    receipt = {
        "schemaVersion": "a1-edit-receipt",
        "cloneHead": CLONE_HEAD_PIN,
        "products": worklist,
        "productsCount": len(worklist),
        "editClassCounts": counts,
        "editRecords": records,
        "entryShas": {eid: hashlib.sha256(out[eid].encode("utf-8"))
                      .hexdigest() for eid in worklist},
        "preStateShas": {eid: hashlib.sha256(
            canon(clone_snapshot[eid]).encode("utf-8")).hexdigest()
            for eid in worklist},
        "applied": apply_mode,
    }
    if apply_mode:
        (HERE / RECEIPT).write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="")
    print(json.dumps({"applied": apply_mode, "classCounts": counts,
                      "products": len(worklist)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
