#!/usr/bin/env python3
"""Scope the correction-arc record commit (ReadZen repo).

Includes a product's terms dir ONLY if its current bytes still match a
manifest pin from the arc (a1/r1b/s1b/r2/f1/r2f1-main) — separating
lane-approved bytes from the unrelated dirty term dirs (q3-20260901
residue, foreign sessions). Prints the verified term-dir list; exit 1
if any pinned product drifted.
"""
import hashlib
import json
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
MANIFESTS = [
    "a1-20260903-generic-manifest.json",
    "r1b-20260903-generic-manifest.json",
    "s1b-20260903-generic-manifest.json",
    "r2-20260903-generic-manifest.json",
    "f1-20260905-generic-manifest.json",
    "r2f1-main-20260905-generic-manifest.json",
]


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


pins: dict[str, list] = {}
for mf in MANIFESTS:
    doc = json.loads((BUILD / "maintenance" / mf).read_text(encoding="utf-8"))
    for p in doc["products"]:
        eid = p["id"] if "id" in p else p.get("entryId")
        pins.setdefault(eid, []).append(
            {"cohort": doc.get("cohort", mf), "sha": p["entrySha256"]})

problems = []
include = []
for eid, pin_list in sorted(pins.items()):
    f = BUILD / "terms" / eid / "entry.v2.json"
    if not f.is_file():
        problems.append(f"{eid}: terms file missing")
        continue
    raw = hashlib.sha256(f.read_bytes()).hexdigest()
    parsed = json.loads(f.read_text(encoding="utf-8-sig"))
    can = hashlib.sha256(canon(parsed).encode("utf-8")).hexdigest()
    # an entry may be a product of SEVERAL lanes in sequence (a1 -> r2 ->
    # r2f1-main): current bytes must match the pin of SOME cohort — the
    # latest one that touched it
    matched = [pp["cohort"] for pp in pin_list
               if raw == pp["sha"] or can == pp["sha"]]
    if matched:
        include.append(eid)
    else:
        problems.append(
            f"{eid}: bytes match NO pin across {[pp['cohort'] for pp in pin_list]} "
            f"(raw {raw[:12]}, canon {can[:12]}, pins "
            f"{[pp['sha'][:12] for pp in pin_list]})")

print(json.dumps({
    "manifests": MANIFESTS,
    "pinnedProducts": len(pins),
    "include": include,
    "problems": problems,
    "ok": not problems,
}, indent=2))
raise SystemExit(0 if not problems else 1)
