#!/usr/bin/env python3
"""SPEC_S1b_20260903.md §2-3: the ClaimAnchor-removal engine (lane S1-b/R).

Input is the CLONE pre-state at pinned HEAD 5f0e127 (confinement law:
engine(clone) == terms bytes after apply, asserted before writing). One
edit source, fully mechanical — the frozen census
maintenance/s1b-anchor-census-20260903.json — which the engine
RE-DERIVES from first principles and asserts byte-equal before applying:

  derivation (SPEC §1): per entry in the fleet artifact
  a1-fleet-attribution-post-20260903.json —
    - map every failure row to its evidence row via the audit's merged
      enumeration (occurrences first, then anchors, one counter);
    - failing anchors = anchors carrying a structure kind
      (invalid_claim_anchor, claim_anchor_missing_claim_text,
      claim_text_absent_from_kwic, claim_anchor_contains_headword);
    - removal law per failing anchor:
        pointer  OccurrenceIndex in range AND (ClaimText a substring of
                 the target occurrence's Kwic, OR the ClaimText stays
                 anchored over surviving kwics)  -> anchor-remove-pointer
        dup      non-empty Kwic inside a same-sense occurrence's Kwic
                                                 -> anchor-remove-dup
        otherwise                                 rebuild (not this lane)
    - entry eligibility: every fleet row on the entry maps to an anchor
      row; all failing anchors removal-eligible; the simulated post
      state anchors every CJK string of Explanation/Note over the
      surviving kwics (dangling_chinese law).

  apply: remove the failing anchors (list filter by 1-based index);
  empty list -> del sense["ClaimAnchors"] (the A1 anchor-remove
  byte-shape). Identity bytes are re-asserted at apply time (pointer:
  OccurrenceIndex + ClaimText; dup: the Kwic containment law re-checked
  against the surviving occurrences), so census/clone drift aborts.

Path-scope law (§4.6): ONLY Senses[i].ClaimAnchors may differ between
clone pre-state and output; anything else aborts before write.
Determinism: pure function of the clone bytes + frozen artifacts (no
wall-clock, no randomness).

Receipt: maintenance/s1b-edit-receipt-20260903.json, written ONLY by
main() (importers — gates, blind builder, adjudicator, manifest — call
transform() for the oracle and must not clobber the receipt's applied
flag). Run with --apply to write terms bytes; without it, dry. The
pre-apply drift check tolerates entries whose current bytes already
equal the engine's deterministic output (idempotent re-apply); any
other drift aborts.
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
CLONE_HEAD_PIN = "5f0e127"
FLEET = "a1-fleet-attribution-post-20260903.json"
CENSUS = "s1b-anchor-census-20260903.json"
RECEIPT = "s1b-edit-receipt-20260903.json"

STRUCTURE_KINDS = {
    "invalid_claim_anchor", "claim_anchor_missing_claim_text",
    "claim_text_absent_from_kwic", "claim_anchor_contains_headword",
}
ROW_RE = re.compile(r"^(?P<term>.+?) s(?P<si>\d+) (?P<k>[oa])(?P<n>\d+)(?:[ :]|$)")
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
# §4.6 path-scope law: only the anchor list may change.
ALLOWED_PATH_RES = (
    re.compile(r"^Senses\[\d+\]\.ClaimAnchors(?:[.\[]|$)"),
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


def derive(by_id: dict[str, dict]) -> tuple[list[str], dict]:
    """Re-derive the cohort + per-anchor actions from first principles.

    Returns (cohort_entry_ids, actions) where actions maps
    (eid, si, aidx) -> "anchor-remove-dup" | "anchor-remove-pointer".
    Mirrors probe_s1b_census_20260903.py exactly.
    """
    fleet = json.loads((HERE / FLEET).read_text(encoding="utf-8"))
    rows_by_entry: dict[str, list[dict]] = {}
    sense_level_rows: set[str] = set()
    for f in fleet["failures"]:
        em = re.search(r"t_[0-9a-f]{12}", str(f.get("entry", "")))
        if not em:
            continue
        m = ROW_RE.match(str(f.get("detail", "")))
        if not m:
            # sense-level row (no evidence-row label in the detail):
            # blocks eligibility per SPEC §1, never maps to an anchor
            sense_level_rows.add(em.group(0))
            continue
        rows_by_entry.setdefault(em.group(0), []).append({
            "kind": f["kind"],
            "si": int(m["si"]),
            "mergedN": int(m["n"]),
        })

    cohort: list[str] = []
    actions: dict[tuple, str] = {}
    for eid in sorted(rows_by_entry):
        e = by_id.get(eid)
        if e is None:
            continue
        senses = e.get("Senses") or []
        blocked = eid in sense_level_rows
        failing: dict[tuple, set] = {}
        for rec in rows_by_entry[eid]:
            si = rec["si"]
            if si < 1 or si > len(senses):
                blocked = True
                continue
            s = senses[si - 1]
            n_occs = len(s.get("Occurrences") or [])
            if rec["mergedN"] <= n_occs:
                blocked = True          # occurrence-row failure
                continue
            aidx = rec["mergedN"] - n_occs
            anchors = s.get("ClaimAnchors") or []
            if aidx < 1 or aidx > len(anchors):
                blocked = True
                continue
            if rec["kind"] in STRUCTURE_KINDS:
                failing.setdefault((si, aidx), set()).add(rec["kind"])
        if not failing:
            continue                     # no structure-failing anchor
        removable: set = set()
        anchor_row_sites: set = set()
        for rec in rows_by_entry[eid]:
            si = rec["si"]
            if 1 <= si <= len(senses):
                s0 = senses[si - 1]
                n = len(s0.get("Occurrences") or [])
                if rec["mergedN"] > n:
                    anchor_row_sites.add((si, rec["mergedN"] - n))
        for (si, aidx), kinds in sorted(failing.items()):
            s = senses[si - 1]
            anchors = s.get("ClaimAnchors") or []
            a = anchors[aidx - 1]
            ct = str(a.get("ClaimText") or "")
            kw = _kwic(a)
            occs = s.get("Occurrences") or []
            ptr = a.get("OccurrenceIndex")
            pointer = isinstance(ptr, int) and 0 <= ptr < len(occs)
            mirror = bool(pointer and ct and ct in _kwic(occs[ptr]))
            dup = bool(kw and any(kw in _kwic(o) for o in occs))
            survivors = [k for k in
                         ([_kwic(o) for o in occs] +
                          [_kwic(x) for x in anchors])
                         if k != kw or not kw]
            claim_ok = (not ct) or _anchored(ct, survivors)
            if pointer and (mirror or claim_ok):
                actions[(eid, si, aidx)] = "anchor-remove-pointer"
                removable.add((si, aidx))
            elif dup:
                actions[(eid, si, aidx)] = "anchor-remove-dup"
                removable.add((si, aidx))
            else:
                blocked = True          # rebuild — not this lane
        # every fleet row must sit on an anchor the lane removes; rows on
        # surviving anchors (note/actor hygiene on structurally valid
        # anchors) do not clear by removal (pre-apply finding 2026-09-02)
        if anchor_row_sites - removable:
            blocked = True
        if blocked:
            continue
        # simulated post state must anchor every prose CJK string
        for si, s in enumerate(senses, 1):
            occs = s.get("Occurrences") or []
            anchors = s.get("ClaimAnchors") or []
            survivors = [_kwic(o) for o in occs] + [
                _kwic(a) for j, a in enumerate(anchors, 1)
                if (si, j) not in removable]
            prose = "\n".join(str(s.get(k) or "")
                              for k in ("Explanation", "Note"))
            for quote in set(CJK_RE.findall(prose)):
                if not _anchored(quote, survivors):
                    blocked = True
                    break
            if blocked:
                break
        if not blocked:
            cohort.append(eid)
    # actions only for cohort entries (blocked entries' actions would
    # otherwise linger in the dict and never be applied)
    cohort_set = set(cohort)
    actions = {k: v for k, v in actions.items() if k[0] in cohort_set}
    return cohort, actions


def transform(by_id: dict[str, dict]) -> tuple[dict[str, str], list[dict]]:
    """Apply the removals; return {eid: canon bytes} + edit records."""
    census = json.loads((HERE / CENSUS).read_text(encoding="utf-8"))
    cohort, actions = derive(by_id)

    # ---- frozen-census assertions (SPEC §3) ---------------------------------
    if sorted(cohort) != sorted(census["cohortR"]):
        raise SystemExit(
            f"derivation drift: cohort {len(cohort)} != census "
            f"{len(census['cohortR'])}; missing "
            f"{sorted(set(census['cohortR']) - set(cohort))[:5]}; extra "
            f"{sorted(set(cohort) - set(census['cohortR']))[:5]}")
    # census remove-actions RESTRICTED to cohort R (the census also
    # classifies remove-actions on blocked entries the lane must not take)
    cohort_set = set(cohort)
    census_actions = {(a["entry"], a["si"], a["aidx"]):
                      "anchor-" + a["action"]
                      for a in census["anchors"]
                      if a["action"].startswith("remove")
                      and a["entry"] in cohort_set}
    for key, act in sorted(actions.items()):
        expect = census_actions.get(key)
        if expect != act:
            raise SystemExit(f"derivation drift: {key} {act} != {expect}")
    if len(actions) != len(census_actions):
        raise SystemExit(f"derivation drift: {len(actions)} actions != "
                         f"census {len(census_actions)}")

    records: list[dict] = []
    out: dict[str, str] = {}
    pre_flat_by_entry: dict[str, dict] = {}
    for eid in cohort:
        e = by_id[eid]
        # path-scope needs the PRE bytes — e is mutated below
        pre_flat_by_entry[eid] = dict(flat(e))
        per_entry: dict[int, set] = {}
        for (eid2, si, aidx), act in sorted(actions.items()):
            if eid2 == eid:
                per_entry.setdefault(si, set()).add(aidx)
        for si in sorted(per_entry):
            s = e["Senses"][si - 1]
            occs = s.get("Occurrences") or []
            anchors = s.get("ClaimAnchors")
            assert isinstance(anchors, list) and anchors, (
                f"{eid} s{si}: no ClaimAnchors to remove")
            keep = []
            for j, a in enumerate(anchors, 1):
                if j in per_entry[si]:
                    act = actions[(eid, si, j)]
                    ct = str(a.get("ClaimText") or "")
                    kw = _kwic(a)
                    if act == "anchor-remove-pointer":
                        ptr = a.get("OccurrenceIndex")
                        assert isinstance(ptr, int) and 0 <= ptr < len(occs), (
                            f"{eid} s{si} a{j}: bad OccurrenceIndex {ptr!r}")
                        assert ct and ct in _kwic(occs[ptr]) or _anchored(
                            ct, [_kwic(o) for o in occs] +
                            [_kwic(x) for x in anchors if x is not a]), (
                            f"{eid} s{si} a{j}: pointer claim not covered")
                        records.append({
                            "class": act, "entry": eid, "si": si, "aidx": j,
                            "mergedLabel": f"a{len(occs) + j}",
                            "occurrenceIndex": ptr,
                            "removedClaimText": ct,
                            "mirror": ct in _kwic(occs[ptr]),
                        })
                    else:
                        holders = [o.get("MasterName") for o in occs
                                   if kw and kw in _kwic(o)]
                        assert holders, (
                            f"{eid} s{si} a{j}: dup law fails on live bytes")
                        records.append({
                            "class": act, "entry": eid, "si": si, "aidx": j,
                            "mergedLabel": f"a{len(occs) + j}",
                            "removedKwicHead": kw[:24],
                            "removedClaimText": ct[:60],
                            "coveredBy": holders,
                        })
                else:
                    keep.append(a)
            if keep:
                s["ClaimAnchors"] = keep
            else:
                del s["ClaimAnchors"]
        out[eid] = canon(e)

    # ---- path-scope law (§4.6) ----------------------------------------------
    for eid in cohort:
        pre_flat = pre_flat_by_entry[eid]
        post_map = dict(flat(json.loads(out[eid])))
        for path, leaf in post_map.items():
            if pre_flat.get(path) != leaf and not any(
                    rx.search(path) for rx in ALLOWED_PATH_RES):
                raise SystemExit(f"path-scope escape: {eid} {path}")
        # a pure deletion must also shrink nothing outside ClaimAnchors
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
        "schemaVersion": "s1b-edit-receipt",
        "lane": "S1-b/R",
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
