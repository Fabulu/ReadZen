#!/usr/bin/env python3
"""S1-b census: shape-classify the anchor-defect complex.

Reads terms/ and the fleet artifact; writes only the census worksheet
(maintenance/s1b-anchor-census-20260903.json) — never terms/.

Universe: entries carrying at least one anchor that fails an
anchor-STRUCTURE kind in the fleet artifact
a1-fleet-attribution-post-20260903.json (invalid_claim_anchor,
claim_anchor_missing_claim_text, claim_text_absent_from_kwic,
claim_anchor_contains_headword — audit_attribution.py lines 576-920).
Other kinds firing on those same anchors are side effects that removal
also clears; anchors failing ONLY non-structure kinds are NOT in this
lane (e.g. a noncanonical_master_name anchor keeps its evidence).

For every anchor in the universe the probe:
  1. re-derives the audit's merged evidence-row enumeration
     (occurrences first, then anchors, one counter — lines 571-575) so
     fleet rows whose labels hardcode "o{oi}" (e.g. line 924) are
     attributed to the anchor they actually belong to;
  2. classifies the anchor's shape (pointer / mirror / empty kwic /
     dup-covered / coords / occurrence-grade fields);
  3. simulates removal of all removal-eligible anchors per sense and
     re-checks dangling_chinese (chinese_strings = CJK_RE.findall,
     lines 443-451; anchor law line 1084-1087) over surviving kwics.

Suggested action per failing anchor:
  remove-pointer  OccurrenceIndex pointer whose target occurrence
                  holds the ClaimText (mirror) or keeps it anchored
                  after removal
  remove-dup      standalone anchor whose Kwic sits inside a same-sense
                  occurrence's Kwic (the A1 AMENDMENT 3 shape)
  rebuild         removal loses evidence — recut/promotion is authored
                  work for a later cohort
  manual-review   no law fit (recorded, not silently dropped)

Entry eligibility for the removal cohort R: every fleet row on the
entry maps to an anchor (no occurrence-row or sense-level rows), every
failing anchor is removal-eligible, every fleet row sits on an anchor
the lane REMOVES (rows on surviving anchors — e.g. note/actor hygiene
on a structurally valid anchor — do not clear by removal), and the
simulated post state dangles nothing.

Writes maintenance/s1b-anchor-census-20260903.json; prints histograms.
"""
import collections
import json
import re
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
TERMS = BUILD / "terms"
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
STRUCTURE_KINDS = {
    "invalid_claim_anchor", "claim_anchor_missing_claim_text",
    "claim_text_absent_from_kwic", "claim_anchor_contains_headword",
}
ROW_RE = re.compile(r"^(?P<term>.+?) s(?P<si>\d+) (?P<k>[oa])(?P<n>\d+)(?:[ :]|$)")

fleet = json.loads(
    (BUILD / "maintenance" / "a1-fleet-attribution-post-20260903.json")
    .read_text(encoding="utf-8"))

# ---- fleet rows -> (entry, sense, is-anchor, anchor-index | occurrence-index)
rows_by_entry = collections.defaultdict(list)
kind_hist = collections.Counter()
for f in fleet["failures"]:
    eid = re.search(r"t_[0-9a-f]{12}", str(f.get("entry", "")))
    if not eid:
        continue
    eid = eid.group(0)
    m = ROW_RE.match(str(f.get("detail", "")))
    rec = {"kind": f["kind"], "detail": str(f.get("detail", "")),
           "rowLabel": None, "isAnchor": False, "aidx": None,
           "isSenseLevel": m is None}
    if m:
        rec["rowLabel"] = f"{m['k']}{m['n']}"
        rec["si"] = int(m["si"])
        rec["mergedN"] = int(m["n"])
        rec["kindIsALabel"] = m["k"] == "a"
    rows_by_entry[eid].append(rec)
    kind_hist[f["kind"]] += 1

# resolve anchor/occurrence membership per entry (needs sense structure)
universe: dict[str, dict] = {}
for eid, rows in sorted(rows_by_entry.items()):
    entry_path = TERMS / eid / "entry.v2.json"
    if not entry_path.is_file():
        continue
    e = json.loads(entry_path.read_text(encoding="utf-8-sig"))
    term = e.get("SourceTerm") or ""
    senses = e.get("Senses") or []
    for rec in rows:
        if rec.get("isSenseLevel"):
            continue
        si = rec["si"]
        if si < 1 or si > len(senses):
            rec["isSenseLevel"] = True
            continue
        s = senses[si - 1]
        n_occs = len(s.get("Occurrences") or [])
        if rec["mergedN"] > n_occs:
            rec["isAnchor"] = True
            rec["aidx"] = rec["mergedN"] - n_occs   # 1-based within anchors
        else:
            rec["isOccurrence"] = True
    anchor_rows = [r for r in rows if r.get("isAnchor")]
    structure_hits = [r for r in anchor_rows
                      if r["kind"] in STRUCTURE_KINDS]
    if structure_hits:
        universe[eid] = {"term": term}

anchors_out = []
entry_reports = {}
cohort_r = []
action_hist = collections.Counter()
blocker_hist = collections.Counter()

for eid in sorted(universe):
    e = json.loads((TERMS / eid / "entry.v2.json").read_text(
        encoding="utf-8-sig"))
    term = e["SourceTerm"]
    senses = e.get("Senses") or []
    rows = rows_by_entry[eid]
    blockers = []

    failing_anchors: dict[tuple, list] = collections.defaultdict(list)
    for r in rows:
        if r.get("isAnchor") and r["kind"] in STRUCTURE_KINDS:
            failing_anchors[(r["si"], r["aidx"])].append(r["kind"])

    # sense-level rows and occurrence rows block eligibility
    for r in rows:
        if not r.get("isAnchor"):
            why = ("sense-level row" if r.get("isSenseLevel")
                   else f"occurrence row {r.get('rowLabel')}")
            blockers.append(f"{r['kind']}@{why}")

    sim_remove: dict[int, set] = {}          # si -> anchor idxs to remove
    entry_anchor_report = []
    for si, s in enumerate(senses, 1):
        occs = s.get("Occurrences") or []
        anchors = s.get("ClaimAnchors") or []
        prose = "\n".join(str(s.get(k) or "") for k in ("Explanation", "Note"))
        all_kwics = [str(o.get("Kwic") or "") for o in occs] + \
                    [str(a.get("Kwic") or "") for a in anchors if a.get("Kwic")]
        for aidx, a in enumerate(anchors, 1):
            kinds = failing_anchors.get((si, aidx), [])
            if not kinds:
                continue
            ct = str(a.get("ClaimText") or "")
            kw = str(a.get("Kwic") or "")
            ptr = a.get("OccurrenceIndex")
            pointer = isinstance(ptr, int) and 0 <= ptr < len(occs)
            mirror = bool(pointer and ct and ct in str(occs[ptr].get("Kwic") or ""))
            dup = bool(kw and any(kw in str(o.get("Kwic") or "") for o in occs))
            has_coords = all(a.get(k) for k in ("RelPath", "FromLb", "ToLb"))
            occ_grade = bool(a.get("MasterName") or a.get("ActorAttribution")
                             or a.get("AttributionNote"))
            # survival of every Chinese string the Explanation quotes
            survivors = [k for k in all_kwics if k != kw] if kw else all_kwics
            claim_still_anchored = (not ct) or any(
                ct in k or k in ct for k in survivors if k)
            if pointer and mirror:
                action = "remove-pointer"
            elif pointer and claim_still_anchored:
                action = "remove-pointer"      # held by another kwic
            elif dup:
                action = "remove-dup"
            else:
                action = "rebuild"
            rec = {"entry": eid, "term": term, "si": si, "aidx": aidx,
                   "mergedLabel": f"a{len(occs) + aidx}", "kinds": sorted(kinds),
                   "shape": {
                       "pointer": pointer,
                       "pointerTargetOk": bool(pointer),
                       "mirror": mirror,
                       "kwicEmpty": not kw,
                       "termEqClaim": ct == term,
                       "claimEmpty": not ct,
                       "claimInOwnKwic": bool(ct and kw and ct in kw),
                       "dupCovered": dup,
                       "hasCoords": has_coords,
                       "occGradeFields": occ_grade,
                       "claimAnchoredAfterRemoval": claim_still_anchored,
                   },
                   "claimText": ct[:60], "action": action}
            anchors_out.append(rec)
            action_hist[action] += 1
            entry_anchor_report.append(rec)
            if action.startswith("remove"):
                sim_remove.setdefault(si, set()).add(aidx)
            else:
                blockers.append(f"anchor s{si} a{aidx} needs {action}")

        # dangling simulation over surviving kwics
        if sim_remove.get(si):
            survivors = [str(o.get("Kwic") or "") for o in occs] + [
                str(a.get("Kwic") or "")
                for j, a in enumerate(anchors, 1)
                if j not in sim_remove[si] and a.get("Kwic")]
            for quote in sorted(set(CJK_RE.findall(prose))):
                if not any(quote in k or k in quote for k in survivors if k):
                    blockers.append(
                        f"simulated dangling after removal: {quote[:30]}")

    # AMENDMENT-law (pre-apply finding 2026-09-02): every fleet row on the
    # entry must sit on an anchor this lane REMOVES. A row on a surviving
    # anchor (e.g. note/actor hygiene on a structurally valid anchor) does
    # not clear by removal and blocks the entry.
    removable = {(a["si"], a["aidx"]) for a in entry_anchor_report
                 if a["action"].startswith("remove")}
    for r in rows:
        if r.get("isAnchor") and (r["si"], r["aidx"]) not in removable:
            blockers.append(f"{r['kind']}@surviving anchor s{r['si']} "
                            f"a{r['aidx']}")

    eligible = not blockers
    entry_reports[eid] = {
        "term": term,
        "failingAnchors": len(failing_anchors),
        "totalRows": len(rows),
        "eligibleForCohortR": eligible,
        "blockers": blockers[:8],
    }
    if eligible:
        cohort_r.append(eid)
    for b in blockers:
        blocker_hist[b.split(" s")[0].split(":")[0][:40]] += 1

out = {
    "schemaVersion": "s1b-anchor-census",
    "fleetArtifact": "a1-fleet-attribution-post-20260903.json",
    "laws": {
        "mergedEnumeration": "audit_attribution.py:571-575 "
                             "(occurrences first, then anchors, one counter)",
        "danglingChineselaw": "audit_attribution.py:1084-1087 with "
                              "chinese_strings = CJK_RE.findall (443-451)",
        "structureKinds": sorted(STRUCTURE_KINDS),
    },
    "universe": {"entries": len(universe)},
    "kindHistogram": dict(kind_hist.most_common()),
    "actionHistogram": dict(action_hist),
    "blockerHistogram": dict(blocker_hist.most_common(15)),
    "cohortR": cohort_r,
    "anchors": anchors_out,
    "entries": entry_reports,
}
(BUILD / "maintenance" / "s1b-anchor-census-20260903.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")

print(f"universe entries: {len(universe)} (with structure-failing anchors)")
print(f"failing anchors classified: {len(anchors_out)}")
print("actions:", dict(action_hist))
print(f"cohort R (pure removal, entry-eligible): {len(cohort_r)} entries")
print("top blockers:",
      dict(blocker_hist.most_common(10)))
for eid in cohort_r[:8]:
    r = entry_reports[eid]
    print(f"  R {eid} {r['term']!r} anchors={r['failingAnchors']} "
          f"rows={r['totalRows']}")
