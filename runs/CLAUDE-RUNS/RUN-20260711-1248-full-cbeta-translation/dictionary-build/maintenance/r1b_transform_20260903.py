#!/usr/bin/env python3
"""SPEC_R1b_20260903.md §2-3: the retired-source removal engine (lane R1b).

Input is the CLONE pre-state at pinned HEAD 87a6975 (confinement law:
engine(clone) == terms bytes after apply, asserted before writing).
Fully mechanical, derived from first principles off the clone bytes
alone; the census r1b-census-20260903.json is the recording of the same
derivation, and transform() cross-checks cohort + counts against it:

  derivation (SPEC §3): per entry —
    - affected = >=1 occurrence whose RelPath is in RETIRED
      {T/T48/T48n2023.xml, X/X63/X63n1245.xml};
    - per affected sense: remove exactly those occurrences
      (occ-remove-retired), asserting RelPath byte-equality at apply;
    - prose-anchoring gate: every CJK string of the sense's
      Explanation/Note must stay anchored (quote in kwic or kwic in
      quote) over surviving occurrence kwics + surviving anchor kwics;
      an entry whose quote would dangle is BLOCKED (rebuild territory,
      disclosed — never silently removed; the census cross-check then
      aborts, forcing a SPEC amendment + fresh census);
    - note-count-rewrite (exactly one entry, t_50d75aeeeef1 s1): the
      count sentence "N exact occurrences from M distinct works" is
      rewritten to the survivor arithmetic under a find-once law
      (asserted pre N/M == live counts).

Path-scope law (§4.3): ONLY Senses[i].Occurrences and the one rewritten
Senses[0].Note of t_50d75aeeeef1 may differ between clone pre-state and
output; anything else aborts before write. Determinism: pure function
of the clone bytes (no wall-clock, no randomness).

Receipt maintenance/r1b-edit-receipt-20260903.json is written ONLY by
main() (importers — pre-apply, gates, blind builder, adjudicator,
manifest — call transform() for the oracle and must not clobber the
receipt's applied flag). Run with --apply to write terms bytes; without
it, dry. The pre-apply drift check tolerates entries whose current
bytes equal the engine's deterministic output (idempotent re-apply).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
CLONE_HEAD_PIN = "87a6975"
RECEIPT = "r1b-edit-receipt-20260903.json"
CENSUS = "r1b-census-20260903.json"
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
NOTE_ENTRY = "t_50d75aeeeef1"
SENT_RE = re.compile(r"\d+\s+exact occurrences? from\s+\d+\s+distinct works")
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
ALLOWED_PATH_RES = (
    re.compile(r"^Senses\[\d+\]\.Occurrences(?:[.\[]|$)"),
    re.compile(r"^Senses\[0\]\.Note$"),
)


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


def _kwic(occ) -> str:
    return str(occ.get("Kwic") or "")


def _anchored(quote: str, kwics: list[str]) -> bool:
    return any(quote in k or k in quote for k in kwics if k)


def derive(by_id: dict[str, dict]) -> tuple[list[str], list[tuple]]:
    """Re-derive the cohort + removal sites from first principles.

    Returns (cohort_entry_ids, removals) where removals is a list of
    (eid, si, oi) 1-based occurrence sites. Entries whose prose would
    dangle post-removal are BLOCKED (printed, excluded — the census
    cross-check in transform() then aborts, per SPEC §3).
    """
    cohort: list[str] = []
    removals: list[tuple] = []
    blocked: list[dict] = []
    for eid, e in sorted(by_id.items()):
        sites: list[tuple] = []
        for si, s in enumerate(e.get("Senses") or [], 1):
            occs = s.get("Occurrences") or []
            sites.extend((eid, si, oi) for oi, o in enumerate(occs, 1)
                         if o.get("RelPath") in RETIRED)
        if not sites:
            continue
        ok = True
        for (_eid, si, _oi) in sites:
            s = e["Senses"][si - 1]
            survivors = [_kwic(o) for o in s.get("Occurrences") or []
                         if o.get("RelPath") not in RETIRED]
            survivors += [_kwic(a) for a in s.get("ClaimAnchors") or []]
            prose = "\n".join(str(s.get(k) or "")
                              for k in ("Explanation", "Note"))
            for quote in sorted(set(CJK_RE.findall(prose))):
                if not _anchored(quote, survivors):
                    ok = False
                    blocked.append({"entry": eid, "si": si,
                                    "quote": quote[:24]})
        if not ok:
            continue
        cohort.append(eid)
        removals.extend(sites)
    if blocked:
        print(json.dumps({"blockedProseDangle": blocked},
                         ensure_ascii=False, indent=1))
    return cohort, removals


def transform(by_id: dict[str, dict]) -> tuple[dict[str, str], list[dict]]:
    """Apply the removals; return {eid: canon bytes} + edit records."""
    cohort, removals = derive(by_id)
    census = json.loads((HERE / CENSUS).read_text(encoding="utf-8"))
    census_entries = sorted(census["entries"])
    if sorted(cohort) != census_entries:
        raise SystemExit(
            f"derivation drift: cohort {len(cohort)} != census "
            f"{len(census_entries)}; missing "
            f"{sorted(set(census_entries) - set(cohort))[:5]}; extra "
            f"{sorted(set(cohort) - set(census_entries))[:5]}")
    if len(removals) != census["summary"]["removedOccurrencesTotal"]:
        raise SystemExit(f"derivation drift: {len(removals)} removals != "
                         f"census {census['summary']['removedOccurrencesTotal']}")

    records: list[dict] = []
    out: dict[str, str] = {}
    pre_flat_by_entry: dict[str, dict] = {}
    per_entry: dict[str, dict[int, set]] = {}
    for (eid, si, oi) in removals:
        per_entry.setdefault(eid, {}).setdefault(si, set()).add(oi)
    for eid in cohort:
        e = by_id[eid]
        pre_flat_by_entry[eid] = dict(flat(e))
        for si, ois in sorted(per_entry[eid].items()):
            s = e["Senses"][si - 1]
            occs = s.get("Occurrences") or []
            keep: list = []
            drop: list[tuple[int, dict]] = []
            for j, o in enumerate(occs, 1):
                if j in ois:
                    assert o.get("RelPath") in RETIRED, (
                        f"{eid} s{si} o{j}: RelPath {o.get('RelPath')!r} "
                        "not retired (identity drift)")
                    drop.append((j, o))
                else:
                    keep.append(o)
            assert keep, f"{eid} s{si}: removal would empty the sense"
            for j, o in drop:
                records.append({
                    "class": "occ-remove-retired", "entry": eid, "si": si,
                    "oi": j, "relPath": o.get("RelPath"),
                    "kwicHead": _kwic(o)[:24],
                    "masterName": o.get("MasterName"),
                })
            s["Occurrences"] = keep
        # note-count-rewrite (exactly one entry, asserted)
        if eid == NOTE_ENTRY:
            assert set(per_entry[eid]) == {1}, (
                f"{eid}: note rewrite law assumes all removals in s1")
            s = e["Senses"][0]
            note = str(s.get("Note") or "")
            matches = SENT_RE.findall(note)
            assert len(matches) == 1, (
                f"{eid}: count sentence matches {len(matches)} != 1")
            core = SENT_RE.search(note).group(0)
            occs = s.get("Occurrences") or []          # already filtered
            pre_occs = len(occs) + len(per_entry[eid][1])
            # pre distinct rels must count the removed occurrence's rel
            # too — recover it from the dropped records
            dropped_rels = {r["relPath"] for r in records
                            if r["entry"] == eid and r["class"]
                            == "occ-remove-retired" and r["si"] == 1}
            pre_rels = {o.get("RelPath") for o in occs} | dropped_rels
            assert re.search(rf"(\d+)\s+exact", core).group(1) == str(
                pre_occs), f"{eid}: claimed N != {pre_occs}"
            assert re.search(r"from\s+(\d+)\s+distinct", core).group(
                1) == str(len(pre_rels)), f"{eid}: claimed M != {len(pre_rels)}"
            new_core = (f"{len(occs)} exact occurrences from "
                        f"{len({o.get('RelPath') for o in occs})} "
                        f"distinct works")
            s["Note"] = note.replace(core, new_core, 1)
            records.append({
                "class": "note-count-rewrite", "entry": eid, "si": 1,
                "before": core, "after": new_core,
                "postOccurrences": len(occs),
                "postDistinctRels": len({o.get("RelPath")
                                         for o in occs}),
            })
        out[eid] = canon(e)

    # ---- path-scope law (§4.3) ----------------------------------------------
    for eid in cohort:
        pre_flat = pre_flat_by_entry[eid]
        post_map = dict(flat(json.loads(out[eid])))
        for path, leaf in post_map.items():
            if pre_flat.get(path) != leaf and not any(
                    rx.search(path) for rx in ALLOWED_PATH_RES):
                raise SystemExit(f"path-scope escape: {eid} {path}")
        for path in pre_flat:
            if path not in post_map and not any(
                    rx.search(path) for rx in ALLOWED_PATH_RES):
                raise SystemExit(f"path-scope deletion escape: {eid} {path}")

    return out, records


def write_receipt(out: dict[str, str], records: list[dict],
                  cohort: list[str]) -> None:
    counts: dict[str, int] = {}
    for r in records:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    receipt = {
        "schemaVersion": "r1b-edit-receipt",
        "lane": "R1b",
        "cloneHead": CLONE_HEAD_PIN,
        "engine": Path(__file__).name,
        "applied": "--apply" in sys.argv,
        "products": cohort,
        "editClassCounts": counts,
        "editRecords": records,
        "entryShas": {},
    }
    for eid in cohort:
        receipt["entryShas"][eid] = hashlib.sha256(
            out[eid].encode("utf-8")).hexdigest()
    (HERE / RECEIPT).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="")


def main() -> None:
    by_id = clone_state()
    worklist = derive(by_id)[0]
    snapshot = {eid: json.loads(canon(by_id[eid])) for eid in worklist}
    out, records = transform(snapshot)
    if "--apply" in sys.argv:
        drift = []
        for p in sorted((ROOT / "terms").glob("*/entry.v2.json")):
            eid = p.parent.name
            if eid in by_id:
                cur = p.read_text(encoding="utf-8")
                if (cur != canon(by_id[eid])
                        and not (eid in out and cur == out[eid])):
                    drift.append(eid)
        if drift:
            raise SystemExit(f"terms != canon(clone) (and not this "
                             f"engine's output): {drift[:5]} ({len(drift)})")
        for eid, text in out.items():
            (ROOT / "terms" / eid / "entry.v2.json").write_text(
                text, encoding="utf-8", newline="")
        write_receipt(out, records, worklist)
        print(f"APPLIED {len(records)} edits over {len(out)} entries")
    else:
        write_receipt(out, records, worklist)
        print(f"DRY {len(records)} edits over {len(out)} entries; "
              f"classes={sorted(set(r['class'] for r in records))}")


if __name__ == "__main__":
    main()
