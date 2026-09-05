#!/usr/bin/env python3
"""Adjudicate the combined-main staged alias delta (render-only).

For every alias LOST vs main HEAD: its main-HEAD owners must all be
products (the replaced entries' old alias sets), or it must be newly
AMBIGUOUS (a staged product also claims it, so the merger omits it).
For every alias ADDED: some staged product must carry it.
"""
import json
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
MAIN = r"C:\programmieren\CbetaZenTranslations"
PRODS = {"t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff",
         "t_ab715aa474d5", "t_351fa42d396b"}

head = subprocess.run(
    ["git", "-C", MAIN, "show", "HEAD:termbase.v2.json"],
    capture_output=True, text=True, encoding="utf-8").stdout
hb = {e["Id"]: e for e in json.loads(head)["Entries"]}
staged = json.loads(
    (BUILD / "fresh-build" / "r2f1-main-20260905" / "publication-stage"
     / "public" / "termbase.v2.json").read_text(encoding="utf-8"))
sb = {e["Id"]: e for e in staged["Entries"]}


def alias_map(by_id):
    owners = {}
    for eid, e in by_id.items():
        term = e["SourceTerm"]
        for s in e.get("Senses") or []:
            for a in s.get("SearchAliases") or []:
                a = a.strip()
                if not a or a == term:
                    continue
                if a not in owners:
                    owners[a] = {term}
                else:
                    owners[a].add(term)
    return {a: next(iter(t)) if len(t) == 1 else None
            for a, t in owners.items()}


ha = alias_map(hb)
sa = alias_map(sb)
lost = sorted(set(ha) - set(sa))
added = sorted(set(sa) - set(ha))

bad = []
for a in lost:
    main_owners = sorted({eid for eid, e in hb.items()
                          for s in e.get("Senses") or []
                          if a in (s.get("SearchAliases") or [])})
    staged_owners = sorted({eid for eid, e in sb.items()
                            for s in e.get("Senses") or []
                            if a in (s.get("SearchAliases") or [])})
    ok = (set(main_owners) <= PRODS
          or len(staged_owners) >= 2)   # newly ambiguous -> omitted
    print(f"LOST {a!r}: main owners {main_owners} "
          f"(all products: {set(main_owners) <= PRODS}); "
          f"staged owners {staged_owners} "
          f"(newly ambiguous: {len(staged_owners) >= 2}) -> "
          f"{'OK' if ok else 'UNEXPLAINED'}")
    if not ok:
        bad.append(a)

for a in added:
    staged_owners = sorted({eid for eid, e in sb.items()
                            for s in e.get("Senses") or []
                            if a in (s.get("SearchAliases") or [])})
    ok = set(staged_owners) & PRODS
    print(f"ADDED {a!r}: staged owners {staged_owners} "
          f"(product: {bool(ok)}) -> {'OK' if ok else 'UNEXPLAINED'}")
    if not ok:
        bad.append(a)

print(f"\nlost {len(lost)}, added {len(added)}, "
      f"unexplained: {bad} -> {'OK' if not bad else 'FAIL'}")
raise SystemExit(0 if not bad else 1)
