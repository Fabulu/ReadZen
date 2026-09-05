#!/usr/bin/env python3
"""Coordinator eyeball of the STAGED public surface (pre-install).

Renders human-readable pre->post deltas for the four authored-edit
archetypes against the clone HEAD bytes, prints shard-change stats
(every changed shard must hold >=1 product), and confirms entry count.
"""
import json
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
STAGE = BUILD / "fresh-build" / "a1-20260903" / "publication-stage"

mani = json.loads((BUILD / "maintenance" / "a1-20260903-generic-manifest.json")
                  .read_text(encoding="utf-8"))
wl = [p["id"] for p in mani["products"]]
wl_set = set(wl)

staged = json.loads((STAGE / "public" / "termbase.v2.json")
                    .read_text(encoding="utf-8"))
staged_by_id = {e["Id"]: e for e in staged["Entries"]}


def git_show(path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(CLONE), "show", f"HEAD:{path}"],
        capture_output=True, text=True, encoding="utf-8").stdout


head_by_id = {e["Id"]: e for e in json.loads(
    git_show("termbase.v2.json"))["Entries"]}
print(f"entries: HEAD {len(head_by_id)} -> staged {len(staged_by_id)}")

changed_entries = [eid for eid in wl
                   if json.dumps(head_by_id.get(eid), sort_keys=True)
                   != json.dumps(staged_by_id.get(eid), sort_keys=True)]
other_drift = [eid for eid in staged_by_id
               if eid not in wl_set
               and json.dumps(head_by_id.get(eid), sort_keys=True)
               != json.dumps(staged_by_id[eid], sort_keys=True)]
print(f"changed among products: {len(changed_entries)}/35; "
      f"off-worklist drift: {len(other_drift)}")


def flat(v, prefix="", out=None):
    if out is None:
        out = []
    if isinstance(v, dict):
        for k in sorted(v):
            flat(v[k], f"{prefix}.{k}" if prefix else k, out)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            flat(x, f"{prefix}[{i}]", out)
    else:
        out.append((prefix, v))
    return out


def show(eid, si, focus):
    a = flat(head_by_id[eid]["Senses"][si - 1])
    b = flat(staged_by_id[eid]["Senses"][si - 1])
    da, db = dict(a), dict(b)
    print(f"\n== {eid} s{si} — {focus} ==")
    for k in sorted(set(da) | set(db)):
        if da.get(k) != db.get(k):
            print(f"  {k}")
            print(f"    HEAD : {str(da.get(k))[:300]}")
            print(f"    STAGE: {str(db.get(k))[:300]}")


# archetypes: the new claim anchor; the anchor removal + grammar proof;
# the R0117 performer binding; one vague reword
show("t_057cc9ea8755", 1, "new ClaimAnchor")
show("t_2e77bc793d0c", 1, "anchor removal + Action-performer sentence")
show("t_f6631a24e33e", 1, "performer ContextMasters row (Huitang Zuxin)")
show("t_1793c3514a69", 0 or 1, "vague reword (Note)")

# shard law
changed_shards = []
for pp in sorted((STAGE / "public" / "termbase").glob("*.json")):
    head_blob = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"HEAD:termbase/{pp.name}"],
        capture_output=True).stdout
    if pp.read_bytes() != head_blob:
        ids = {e.get("Id") for e in json.loads(
            head_blob.decode("utf-8"))["Entries"]}
        changed_shards.append((pp.name, sorted(ids & wl_set)))
bad = [s for s in changed_shards if not s[1]]
print(f"\nchanged shards: {len(changed_shards)}; "
      f"without a product: {len(bad)}")
for name, hits in changed_shards[:8]:
    print(f"  {name}: {len(hits)} products")
print("OK" if len(changed_entries) == 35 and not other_drift and not bad
      else "PROBLEM")
