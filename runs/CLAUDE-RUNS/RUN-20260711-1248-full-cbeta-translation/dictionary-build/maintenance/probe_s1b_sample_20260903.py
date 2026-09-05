#!/usr/bin/env python3
"""S1-b scoping probe: classify claim_anchor_contains_headword anchors.

For a sample of failing anchors, prints:
  - the anchor's ClaimText / Kwic heads (does the quote merely contain
    the headword inside a longer claim, or is it headword evidence?)
  - duplicate law: is the anchor kwic covered by a same-sense
    occurrence kwic (A1's t_2e77 removal shape)?
  - longest headword-free contiguous slice of ClaimText (recut
    feasibility) and whether prose Chinese strings stay anchored.
"""
import json
import re
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
d = json.loads((BUILD / "maintenance" / "a1-fleet-attribution-post-20260903.json")
               .read_text(encoding="utf-8"))
h = [f for f in d["failures"]
     if f["kind"] == "claim_anchor_contains_headword"]

by_entry = {}
for f in h:
    eid = re.search(r"t_[0-9a-f]{12}", f["entry"]).group(0)
    si, ai = map(int, re.search(r"s(\d+) a(\d+)", f["detail"]).groups())
    by_entry.setdefault(eid, []).append((si, ai, f["detail"].split(" s")[0]))

sample = sorted(by_entry)[::max(1, len(by_entry) // 6)][:6]
for eid in sample:
    e = json.loads((BUILD / "terms" / eid / "entry.v2.json")
                   .read_text(encoding="utf-8-sig"))
    term = e["SourceTerm"]
    print(f"\n===== {eid}  term={term!r}  "
          f"({len(by_entry[eid])} failing anchors) =====")
    for si, ai, _ in sorted(by_entry[eid])[:4]:
        s = e["Senses"][si - 1]
        occs = s.get("Occurrences") or []
        anchors = s.get("ClaimAnchors") or []
        # audit law: evidence_rows = occs + anchors, ONE merged counter —
        # "aN" means merged row N is an anchor: anchor index = N - len(occs)
        aidx = ai - len(occs)
        if aidx < 1 or aidx > len(anchors):
            print(f"  s{si} a{ai}: OUT OF RANGE (occs={len(occs)}, "
                  f"anchors={len(anchors)})")
            continue
        a = anchors[aidx - 1]
        ct = str(a.get("ClaimText") or "")
        kw = str(a.get("Kwic") or "")
        occs = s.get("Occurrences") or []
        dup = [o.get("MasterName") for o in occs
               if kw.lstrip("。、，") in str(o.get("Kwic") or "")]
        # longest headword-free contiguous slice of ClaimText
        best = ""
        for m in re.finditer(re.escape(term), ct):
            for side in (ct[:m.start()], ct[m.end():]):
                if len(side) > len(best):
                    best = side
        print(f"  s{si} a{ai}: ClaimText={ct[:70]!r}{'…' if len(ct)>70 else ''}")
        print(f"        kwic[:60]={kw[:60]!r}")
        print(f"        dup-covered-by={dup}; "
              f"headword-free-slice={best[:50]!r}")
