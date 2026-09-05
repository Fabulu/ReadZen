#!/usr/bin/env python3
"""Verify the R1b install in the agent clone (post-install).

Checks (S1-b mirror — replace-only, 43 products):
  1. every product: clone termbase bytes == terms bytes (canonical
     equality + sha vs manifest entrySha256).
  2. entry count unchanged HEAD -> live (no adds, no withdrawals).
  3. registry delta laws: termbase.index.json row count unchanged and
     every product's SourceTerm keeps its Terms row (rows are
     [term, gloss] — there is no id column); termbase.json legacy row
     count unchanged; Aliases map byte-equal to HEAD; shards that
     change must all hold at least one product id, every other shard
     byte-identical to HEAD.
  4. off-footprint protection: every entry outside the 43
     byte-identical to HEAD (git show HEAD:termbase.v2.json).
  5. clone git footprint confined to the termbase writer surface.
  6. staging integrity: staged entry/worksheet/WORK.md shas vs manifest.
  7. R1b-specific: NO entry in the installed clone cites either retired
     rel among the 43 products (occurrences AND ClaimAnchors), and the 2
     prose-gate BLOCKED entries remain byte-identical to HEAD (their
     retired occurrences intentionally survive).
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
BLOCKED = ("t_057cc9ea8755", "t_ea2a427c7aba")

mani = json.loads(
    (BUILD / "maintenance" / "r1b-20260903-generic-manifest.json")
    .read_text(encoding="utf-8"))
product_ids = [p["id"] for p in mani["products"]]
wl_set = set(product_ids)
live = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
live_by_id = {e["Id"]: e for e in live["Entries"]}
live_idx = json.loads((CLONE / "termbase.index.json")
                      .read_text(encoding="utf-8"))
live_leg = json.loads((CLONE / "termbase.json").read_text(encoding="utf-8"))


def git_show(path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(CLONE), "show", f"HEAD:{path}"],
        capture_output=True, text=True, encoding="utf-8").stdout


head_by_id = {e["Id"]: e for e in json.loads(
    git_show("termbase.v2.json"))["Entries"]}
head_idx = json.loads(git_show("termbase.index.json"))
head_leg = json.loads(git_show("termbase.json"))


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


problems = []

# 1. products byte-bound
for p in mani["products"]:
    eid = p["id"]
    terms_text = (BUILD / "terms" / eid / "entry.v2.json").read_text(
        encoding="utf-8")
    if eid not in live_by_id:
        problems.append(f"{eid}: absent from installed clone")
        continue
    if canon(live_by_id[eid]) != terms_text:
        problems.append(f"{eid}: installed bytes != terms bytes")
    sha = hashlib.sha256(canon(live_by_id[eid])
                         .encode("utf-8")).hexdigest()
    if sha != p["entrySha256"]:
        problems.append(f"{eid}: sha {sha[:8]} != manifest")

# 2. entry count unchanged
if len(live_by_id) != len(head_by_id):
    problems.append(f"entry count {len(head_by_id)} -> {len(live_by_id)} "
                    "(replace-only lane: must be unchanged)")

# 3. registry delta laws
# index Terms rows are [SourceTerm, gloss] (term-keyed, no id column)
live_terms = {r[0] for r in live_idx["Terms"]}
product_terms = {head_by_id[eid]["SourceTerm"] for eid in wl_set}
missing_rows = sorted(product_terms - live_terms)
if missing_rows:
    problems.append(f"index term rows lost for products: {missing_rows[:5]}")
if len(live_idx["Terms"]) != len(head_idx["Terms"]):
    problems.append(f"index count {len(live_idx['Terms'])} != "
                    f"{len(head_idx['Terms'])}")
if len(live_leg) != len(head_leg):
    problems.append(f"legacy count {len(live_leg)} != {len(head_leg)}")
if live_idx.get("Aliases") != head_idx.get("Aliases"):
    problems.append("Aliases map changed")
changed_shards = []
head_shard_ids: dict[str, set[str]] = {}
for pp in sorted((CLONE / "termbase").glob("*.json")):
    head_blob = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"HEAD:termbase/{pp.name}"],
        capture_output=True).stdout
    if pp.read_bytes() != head_blob:
        changed_shards.append(pp.name)
    head_shard_ids[pp.name] = {e.get("Id") for e in json.loads(
        head_blob.decode("utf-8"))["Entries"]}
bad_shards = [s for s in changed_shards
              if not (head_shard_ids.get(s, set()) & wl_set)]
if bad_shards:
    problems.append(f"shards changed without holding any product: "
                    f"{bad_shards}")

# 4. off-footprint protection
drift = [eid for eid, e in sorted(head_by_id.items())
         if eid not in wl_set
         and canon(e) != canon(live_by_id.get(eid))]
if drift:
    problems.append(f"off-footprint entries changed: {drift[:5]} "
                    f"({len(drift)})")

# 5. git footprint
st = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                    capture_output=True, text=True).stdout.splitlines()
changed = [l[3:] for l in st]
allowed_pat = re.compile(
    r"(^termbase(?:\.v2|\.index)?\.json$|^termbase/|termbase-shards/|"
    r"termbase-index|index/|\.idx$|shards?/|^terms/)")
unexpected = [f for f in changed if not allowed_pat.search(f)]
if unexpected:
    problems.append(f"unexpected clone changes: {unexpected[:10]}")
print(f"clone changed files: {len(changed)}")

# 6. staging integrity
for p in mani["products"]:
    src = BUILD / p["sourceDir"]
    for fname, key in (("entry.v2.json", "entrySha256"),
                       ("evidence.draft.json", "worksheetSha256"),
                       ("WORK.md", "workSha256")):
        f = src / fname
        if (not f.is_file()
                or hashlib.sha256(f.read_bytes()).hexdigest() != p[key]):
            problems.append(f"staging drift: {p['id']}/{fname}")

# 7. R1b-specific: retired rels gone from the 43; blocked pair untouched
leftover = []
for eid in wl_set:
    for s in (live_by_id.get(eid, {}).get("Senses") or []):
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") in RETIRED:
                leftover.append(f"{eid} occ {o.get('RelPath')}")
        for a in s.get("ClaimAnchors") or []:
            if a.get("RelPath") in RETIRED:
                leftover.append(f"{eid} anchor {a.get('RelPath')}")
if leftover:
    problems.append(f"retired rels still cited by products: "
                    f"{leftover[:5]} ({len(leftover)})")
for eid in BLOCKED:
    if canon(live_by_id.get(eid, {})) != canon(head_by_id.get(eid, {})):
        problems.append(f"blocked entry {eid} changed (must be untouched)")

print(json.dumps({
    "products": len(product_ids),
    "entriesHeadToLive": [len(head_by_id), len(live_by_id)],
    "indexRowsHeadToLive": [len(head_idx["Terms"]),
                            len(live_idx["Terms"])],
    "indexByteIdenticalToHead": (CLONE / "termbase.index.json")
    .read_bytes() == subprocess.run(
        ["git", "-C", str(CLONE), "show", "HEAD:termbase.index.json"],
        capture_output=True).stdout,
    "legacyRowsHeadToLive": [len(head_leg), len(live_leg)],
    "aliasesUnchanged": live_idx.get("Aliases") == head_idx.get("Aliases"),
    "changedShards": changed_shards,
    "offFootprintDrift": len(drift),
    "retiredLeftovers": len(leftover),
    "blockedPairUntouched": all(
        canon(live_by_id.get(e, {})) == canon(head_by_id.get(e, {}))
        for e in BLOCKED),
    "problems": problems, "ok": not problems,
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not problems else 1)
