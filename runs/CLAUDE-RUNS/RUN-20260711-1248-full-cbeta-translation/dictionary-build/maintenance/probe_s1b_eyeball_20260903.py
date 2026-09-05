#!/usr/bin/env python3
"""Probe: render the S1-b/R removals for coordinator eyeball (no writes).

Per sampled entry: the entry's term, the removed anchors (ClaimText /
Kwic head / coverage holder), the POST ClaimAnchors shape (survivors or
key absent), and — the evidentiary bottom line — every Chinese string the
Explanation/Note quotes with the surviving kwic that anchors it. Also
prints the distribution of full-vs-partial anchor-list removals across
the cohort.
"""
import collections
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")

receipt = json.loads(
    (HERE / "s1b-edit-receipt-20260903.json").read_text(encoding="utf-8"))
clone_v2 = json.loads(
    Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations\termbase.v2.json")
    .read_text(encoding="utf-8"))
pre_by_id = {e["Id"]: e for e in clone_v2["Entries"]}

by_entry = collections.defaultdict(list)
for rec in receipt["editRecords"]:
    by_entry[rec["entry"]].append(rec)

shapes = collections.Counter()
for eid, recs in sorted(by_entry.items()):
    per_sense = collections.Counter(r["si"] for r in recs)
    for si, n in per_sense.items():
        pre_n = len((pre_by_id[eid]["Senses"][si - 1].get("ClaimAnchors")) or [])
        shapes["full-removal" if n == pre_n else "partial"] += 1
print("removal shapes per (entry,sense):", dict(shapes))

sample = sorted(by_entry)[::max(1, len(by_entry) // 7)][:7]
for eid in sample:
    pre = pre_by_id[eid]
    post = json.loads((BUILD / "terms" / eid / "entry.v2.json")
                      .read_text(encoding="utf-8-sig"))
    term = pre["SourceTerm"]
    recs = sorted(by_entry[eid], key=lambda r: (r["si"], r["aidx"]))
    print(f"\n===== {eid}  term={term!r}  ({len(recs)} removals) =====")
    for r in recs:
        s = pre["Senses"][r["si"] - 1]
        a = (s.get("ClaimAnchors") or [])[r["aidx"] - 1]
        print(f"  s{r['si']} a{r['aidx']} removed: ClaimText="
              f"{str(a.get('ClaimText'))[:48]!r}")
        print(f"      kwic head: {str(a.get('Kwic'))[:60]!r}")
        print(f"      coveredBy: "
              f"{[m if m else '(unnamed occurrence)' for m in r['coveredBy']][:4]}")
    for si in sorted({r["si"] for r in recs}):
        post_s = post["Senses"][si - 1]
        anchors = post_s.get("ClaimAnchors")
        print(f"  POST s{si}: ClaimAnchors = "
              f"{'ABSENT' if anchors is None else f'{len(anchors)} survivor(s)'}")
        prose = "\n".join(str(post_s.get(k) or "")
                          for k in ("Explanation", "Note"))
        quotes = sorted(set(CJK_RE.findall(prose)))
        kwics = [str(o.get("Kwic") or "")
                 for o in (post_s.get("Occurrences") or [])]
        if anchors:
            kwics += [str(a.get("Kwic") or "") for a in anchors]
        for q in quotes[:4]:
            holder = next((k for k in kwics if q in k or k in q), None)
            print(f"      quote {q[:24]!r} anchored by: "
                  f"{holder[:36]!r}" if holder is not None
                  else f"      quote {q[:24]!r} ANCHOR-NOT-FOUND")

print(f"\n-- {len(by_entry)} entries, {len(receipt['editRecords'])} removals --")
