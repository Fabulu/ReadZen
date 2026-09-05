#!/usr/bin/env python3
"""Render-only probe of the MAIN publish clone (C:\\programmieren\\
CbetaZenTranslations) ahead of the combined R2+F1 main publication.

Reads only. Reports, for the 5 lane products:
  - main's branch/HEAD/subject + termbase-scope cleanliness
  - per-product presence, canonical sha, occurrence counts
    (351fa expected ABSENT — the add case)
  - main-side census: MasterName == 'Dehui' rows anywhere in main's
    surface (disclosure class for the publication report; the agent
    clone's census law covers the agent tree, main's 347 main-only
    entries were never audited)
  - entry order: duplicate-SourceTerm families not Id-ordered in file
    order (predicts whole-file order churn when the current
    byTermThenId merger rewrites the surface)
"""
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

CLONE = Path(r"C:\programmieren\CbetaZenTranslations")
IDS = ["t_ab715aa474d5", "t_351fa42d396b", "t_ea2a427c7aba",
       "t_057cc9ea8755", "t_968a2f97c9ff"]


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


def git(*a: str) -> str:
    return subprocess.run(["git", "-C", str(CLONE), *a],
                          capture_output=True, text=True,
                          encoding="utf-8").stdout


print("branch:", git("rev-parse", "--abbrev-ref", "HEAD").strip())
print("head:", git("rev-parse", "HEAD").strip()[:12])
print("subject:", git("log", "-1", "--format=%s").strip())
st = git("status", "--porcelain", "--", "termbase.v2.json",
         "termbase.json", "termbase.index.json", "termbase").splitlines()
print("termbase-scope dirty:", st if st else "none")

tb = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
by_id = {e["Id"]: e for e in tb["Entries"]}
print("entries:", len(tb["Entries"]))
for eid in IDS:
    if eid in by_id:
        e = by_id[eid]
        occs = [len(s.get("Occurrences") or [])
                for s in e.get("Senses") or []]
        sha = hashlib.sha256(canon(e).encode("utf-8")).hexdigest()
        print(f"{eid} {e['SourceTerm']} sha {sha[:16]} occs {occs}")
    else:
        print(f"{eid} ABSENT on main")

dehui = []
for eid, e in sorted(by_id.items()):
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("MasterName") == "Dehui":
                dehui.append(f"{eid} {e['SourceTerm']} "
                             f"{o.get('RelPath')} {o.get('FromLb')}")
print("main Dehui MasterName rows:", len(dehui))
for d in dehui:
    print(" ", d)

c = Counter(e["SourceTerm"] for e in tb["Entries"])
dups = {t for t, n in c.items() if n > 1}
print("dup-term families:", len(dups))
bad = []
for i in range(1, len(tb["Entries"])):
    a, b = tb["Entries"][i - 1], tb["Entries"][i]
    if a["SourceTerm"] == b["SourceTerm"] and a["Id"] > b["Id"]:
        bad.append(a["SourceTerm"])
print("dup families NOT Id-ordered in file order:", sorted(set(bad)))
