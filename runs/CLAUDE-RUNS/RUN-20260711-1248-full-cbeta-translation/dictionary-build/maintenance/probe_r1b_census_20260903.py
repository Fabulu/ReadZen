#!/usr/bin/env python3
"""R1b census re-derivation against the CURRENT clone (post-S1-b).

The decision package (r1b-decision-package-20260901.json) was derived at
clone ef9ec20 (post-Q1). A1 (5f0e127) and S1-b (87a6975) landed since —
the user-approved Option A facts MUST be re-derived before any engine
work. Writes only the census worksheet
(maintenance/r1b-census-20260903.json); reads terms/ never.

Checks, per the package's decision basis:
  1. occurrences whose RelPath is retired (T/T48/T48n2023.xml,
     X/X63/X63n1245.xml): count + entry census (package: 49 occs /
     45 entries).
  2. no-dies law: every affected sense keeps >=1 occurrence.
  3. floor consequences: per affected sense, surviving occurrences vs
     the depth floor (6) — package: 29 entries drop below, 16 survive.
  4. SourceTexts: which affected entries list a retired rel.
  5. Note count-claim sentences ("N exact occurrences from M distinct
     works") on affected senses — the Q1 B-class rewrite law's input.
  6. index-shift hazards: ClaimAnchors with OccurrenceIndex pointing
     past a removed occurrence on the same sense.
  7. attribution rows on the affected entries in the latest fleet
     artifact (s1b-fleet-attribution-post-20260903.json) — which clear
     by removal, which would survive (residual-rows law input).
  8. overlap with the S1-b cohort (53) and A1 worklist.
  9. zc.allowlist confirmation: both rels absent (they are retired).

NOTE (AM2 supersession): check 3's floor model (per-sense flat 6
over all occurrences) is the CENSUS's advisory model. The real
audit's law is entry-level and TIERED over deployment-class
representatives (audit_depth_sense.py) — it surfaces
below-frequency-floor on 20 of the 43, not the census's 15/29.
The gates freeze the real audit's movement set; this worksheet
keeps its fields as recorded history.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402

CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
CLONE_HEAD_PIN = "87a6975"
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
FLOOR = 6

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD {head[:7]} != pin {CLONE_HEAD_PIN}")
dirty = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                       capture_output=True, text=True).stdout.splitlines()
if dirty:
    raise SystemExit(f"clone dirty: {dirty[:5]}")

v2 = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
by_id = {e["Id"]: e for e in v2["Entries"]}

for rel in sorted(RETIRED):
    print(f"zc allowlist {rel}: {zc.is_allowed(rel)}")

SENT_RE = re.compile(
    r"(?P<n>\d+)\s+exact occurrences? from\s+(?P<m>\d+)\s+distinct works")

affected: dict[str, dict] = {}
blocked: dict[str, list] = {}
total_removed_all = 0
for eid, e in sorted(by_id.items()):
    hits = []
    for si, s in enumerate(e.get("Senses") or [], 1):
        occs = s.get("Occurrences") or []
        for oi, o in enumerate(occs, 1):
            if o.get("RelPath") in RETIRED:
                hits.append((si, oi, o))
    if not hits:
        continue
    total_removed_all += len(hits)
    # prose-anchoring gate (SPEC §3 — same law as the engine): a quote
    # anchored only by a removed kwic BLOCKS the entry (rebuild)
    for si, _oi, _o in hits:
        s = e["Senses"][si - 1]
        survivors = [str(o.get("Kwic") or "")
                     for o in s.get("Occurrences") or []
                     if o.get("RelPath") not in RETIRED]
        survivors += [str(a.get("Kwic") or "")
                      for a in s.get("ClaimAnchors") or []]
        prose = "\n".join(str(s.get(k) or "")
                          for k in ("Explanation", "Note"))
        for quote in sorted(set(re.findall(r"[㐀-鿿豈-﫿]+", prose))):
            if not any(quote in k or k in quote for k in survivors if k):
                blocked.setdefault(eid, []).append(
                    {"si": si, "quote": quote[:24]})
    if eid in blocked:
        continue
    per_sense = {}
    for si, oi, o in hits:
        per_sense.setdefault(si, []).append((oi, o))
    info = {"term": e["SourceTerm"], "removedBySense": {}, "floor": {},
            "noteSentences": {}, "shiftHazards": [], "sourceTexts": []}
    for si, s in enumerate(e.get("Senses") or [], 1):
        occs = s.get("Occurrences") or []
        removed = per_sense.get(si, [])
        survivors = [o for o in occs if o.get("RelPath") not in RETIRED]
        if si in per_sense:
            info["removedBySense"][si] = len(removed)
            info["floor"][si] = {
                "preOccs": len(occs), "postOccs": len(survivors),
                "belowFloorPost": len(survivors) < FLOOR,
                "alreadyBelowFloorPre": len(occs) < FLOOR,
            }
            if not survivors:
                info["floor"][si]["DIES"] = True
        # note count-claim on every sense of an affected entry
        note = str(s.get("Note") or "")
        m = SENT_RE.search(note)
        if m:
            info["noteSentences"][si] = {
                "claimedN": int(m["n"]), "claimedM": int(m["m"]),
                "actualOccs": len(occs),
                "actualDistinctRels": len({o.get("RelPath")
                                           for o in occs}),
                "sentence": m.group(0),
            }
        # index-shift hazards: anchors pointing past a removed occ
        removed_idx = {oi - 1 for oi, _ in removed}
        for ai, a in enumerate(s.get("ClaimAnchors") or [], 1):
            ptr = a.get("OccurrenceIndex")
            if isinstance(ptr, int):
                if any(ptr > k for k in removed_idx):
                    info["shiftHazards"].append(
                        f"s{si} a{ai} SHIFT ptr={ptr}")
                if ptr in removed_idx:
                    info["shiftHazards"].append(
                        f"s{si} a{ai} POINTS-AT-REMOVED ptr={ptr}")
            if a.get("RelPath") in RETIRED:
                info.setdefault("retiredAnchors", []).append({
                    "si": si, "ai": ai,
                    "kwicHead": str(a.get("Kwic") or "")[:24],
                    "claimText": str(a.get("ClaimText") or "")[:24],
                })
    st = e.get("SourceTexts") or []
    info["sourceTexts"] = [r for r in st if r in RETIRED]
    info["sourceTextsOther"] = len([r for r in st if r not in RETIRED])
    affected[eid] = info

# ---- attribution rows on affected entries (latest fleet artifact) ----
fleet = json.loads((BUILD / "maintenance" /
                    "s1b-fleet-attribution-post-20260903.json")
                   .read_text(encoding="utf-8"))
ROW_RE = re.compile(r"^(?P<term>.+?) s(?P<si>\d+) (?P<k>[oa])(?P<n>\d+)"
                    r"(?:[ :]|$)")
rows_on = {}
for f in fleet.get("failures", []):
    em = re.search(r"t_[0-9a-f]{12}", str(f.get("entry", "")))
    if not em or em.group(0) not in affected:
        continue
    eid = em.group(0)
    e = by_id[eid]
    m = ROW_RE.match(str(f.get("detail", "")))
    if not m:
        rows_on.setdefault(eid, []).append(
            {"kind": f["kind"], "site": "sense-level",
             "detail": str(f.get("detail", ""))[:60]})
        continue
    si = int(m["si"])
    s = e["Senses"][si - 1]
    removed_ois = {oi for oi, o in enumerate(s.get("Occurrences") or [], 1)
                   if o.get("RelPath") in RETIRED}
    rows_on.setdefault(eid, []).append({
        "kind": f["kind"], "site": f"s{si} {m['k']}{m['n']}",
        "onRemovedOcc": bool(m["k"] == "o" and int(m["n"]) in removed_ois),
        "detail": str(f.get("detail", ""))[:60]})

# ---- overlaps ----
s1b_products = set(json.loads(
    (BUILD / "maintenance" / "s1b-edit-receipt-20260903.json")
    .read_text(encoding="utf-8"))["products"])
a1_products = set(json.loads(
    (BUILD / "maintenance" / "a1-worklist-details-20260902.json")
    .read_text(encoding="utf-8"))["worklist"])
overlap_s1b = sorted(set(affected) & s1b_products)
overlap_a1 = sorted(set(affected) & a1_products)

dies = [eid for eid, i in affected.items()
        if any(v.get("DIES") for v in i["floor"].values())]
below = sorted(eid for eid, i in affected.items()
               if any(v["belowFloorPost"] and not v["alreadyBelowFloorPre"]
                      and not v.get("DIES") for v in i["floor"].values()))
already = sorted(eid for eid, i in affected.items()
                 if any(v["alreadyBelowFloorPre"]
                        for v in i["floor"].values()))
survivors_floor = sorted(set(affected) - set(below) - set(dies)
                         - {e for e in already
                            if e not in below and e not in dies})

shift = {eid: i["shiftHazards"] for eid, i in affected.items()
         if i["shiftHazards"]}
st_missing = [eid for eid, i in affected.items() if not i["sourceTexts"]]
st_listed = [eid for eid, i in affected.items() if i["sourceTexts"]]
note_have = sum(1 for i in affected.values() if i["noteSentences"])
residual_rows = {eid: [r for r in rows_on.get(eid, [])
                       if not r.get("onRemovedOcc")]
                 for eid in affected}
residual_any = {e: r for e, r in residual_rows.items() if r}

# removedBySense maps si -> occurrence COUNT; sum the values, not the
# keys (len() would count senses-with-removals and undercount entries
# whose two retired occurrences share one sense)
total_removed = sum(sum(v["removedBySense"].values())
                    for v in affected.values())
summary = {
    "cloneHead": head[:7], "removedOccurrencesTotal": total_removed,
    "removedOccurrencesAllIncludingBlocked": total_removed_all,
    "entriesAffected": len(affected),
    "blockedProseDangle": blocked,
    "blockedEntries": sorted(blocked),
    "dies": dies,
    "belowFloorNew": below, "belowFloorNewCount": len(below),
    "alreadyBelowFloorPre": already,
    "floorSurvivors": len(survivors_floor),
    "sourceTextsListedOn": st_listed, "sourceTextsMissingOn": st_missing,
    "noteSentencesOn": note_have,
    "shiftHazards": shift,
    "attributionRowsOnAffected": {k: len(v) for k, v in rows_on.items()},
    "attributionRowDetails": rows_on,
    "residualRowsWouldSurvive": {k: len(v)
                                 for k, v in residual_any.items()},
    "retiredAnchors": {eid: i["retiredAnchors"]
                       for eid, i in affected.items()
                       if i.get("retiredAnchors")},
    "noteSentenceSites": {eid: i["noteSentences"]
                          for eid, i in affected.items()
                          if i["noteSentences"]},
    "overlapWithS1b": overlap_s1b, "overlapWithA1": overlap_a1,
}
print(json.dumps(summary, ensure_ascii=False, indent=1))

out = {"schemaVersion": "r1b-census", "cloneHead": head[:7],
       "retired": sorted(RETIRED), "floor": FLOOR,
       "summary": summary, "entries": affected,
       "attributionRows": rows_on}
(BUILD / "maintenance" / "r1b-census-20260903.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8", newline="")
print(f"\ncensus worksheet: maintenance/r1b-census-20260903.json")
