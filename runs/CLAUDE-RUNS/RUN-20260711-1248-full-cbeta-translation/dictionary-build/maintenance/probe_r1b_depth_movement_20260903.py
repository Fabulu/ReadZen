#!/usr/bin/env python3
"""Render-only: summarize R1b depth flag movement kinds per entry.

Reads the pre-apply probe's real-audit depth pair
(maintenance/r1b-{pre,post}-depth-20260903.json) and prints, per moving
entry, the cleared/surfaced hard+review flag kinds. Writes nothing.
Used to freeze the gates' expected-movement law (SPEC AMENDMENT 2):
movement must consist ONLY of lawful consequences of removing retired
occurrences — clears on removed-occurrence verification flags, surfaces
of depth-consequence flags (below-frequency-floor and family) — with
hardPass true->false = 0.
"""
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "r1b-pre-depth-20260903.json")
                 .read_text(encoding="utf-8"))["results"]
post = json.loads((HERE / "r1b-post-depth-20260903.json")
                  .read_text(encoding="utf-8"))["results"]


def key(f):
    return json.dumps(f, ensure_ascii=False, sort_keys=True)


kind_hist = collections.Counter()
moves = {}
for eid in sorted(pre):
    a, b = pre[eid], post[eid]
    cl = [json.loads(x) for x in (collections.Counter(
        map(key, a["hardFlags"])) - collections.Counter(
        map(key, b["hardFlags"]))).elements()]
    su = [json.loads(x) for x in (collections.Counter(
        map(key, b["hardFlags"])) - collections.Counter(
        map(key, a["hardFlags"]))).elements()]
    clr = [json.loads(x) for x in (collections.Counter(
        map(key, a["reviewFlags"])) - collections.Counter(
        map(key, b["reviewFlags"]))).elements()]
    sur = [json.loads(x) for x in (collections.Counter(
        map(key, b["reviewFlags"])) - collections.Counter(
        map(key, a["reviewFlags"]))).elements()]
    if cl or su or clr or sur:
        moves[eid] = {"cleared": cl, "surfaced": su,
                      "clearedReview": clr, "surfacedReview": sur}
        for f in cl:
            kind_hist[f"cleared:{f['kind']}"] += 1
        for f in su:
            kind_hist[f"surfaced:{f['kind']}"] += 1
        for f in clr:
            kind_hist[f"clearedReview:{f['kind']}"] += 1
        for f in sur:
            kind_hist[f"surfacedReview:{f['kind']}"] += 1

print("kind histogram:")
for k, v in sorted(kind_hist.items()):
    print(f"  {k}: {v}")
print(f"\nmoving entries: {len(moves)}")
for eid, m in sorted(moves.items()):
    parts = []
    for bucket in ("cleared", "surfaced", "clearedReview", "surfacedReview"):
        if m[bucket]:
            parts.append(f"{bucket}=" + ",".join(
                sorted({f["kind"] for f in m[bucket]})))
    print(f"  {eid}: {'; '.join(parts)}")

below = sorted(e for e, m in moves.items()
               if any(f["kind"] == "below-frequency-floor"
                      for f in m["surfaced"]))
print(f"\nbelow-frequency-floor surfaced on {len(below)} entries:")
print(json.dumps(below, ensure_ascii=False, indent=1))

# sample one below-floor flag body + one cleared source flag body
for e, m in moves.items():
    for f in m["surfaced"]:
        if f["kind"] == "below-frequency-floor":
            print("\nsample below-floor body:",
                  json.dumps(f, ensure_ascii=False)[:300])
            break
    else:
        continue
    break
for e, m in moves.items():
    if m["cleared"]:
        print("sample cleared body:",
              json.dumps(m["cleared"][0], ensure_ascii=False)[:300])
        break
