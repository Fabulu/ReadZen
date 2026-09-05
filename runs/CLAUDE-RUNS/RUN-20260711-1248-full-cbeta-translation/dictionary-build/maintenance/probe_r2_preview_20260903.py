#!/usr/bin/env python3
"""R2 dry-run preview: unified diffs of the three products + the
changed-path ledger (path-scope evidence), straight from the engine."""
import copy
import difflib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r2_transform_20260903 as r2  # noqa: E402

by_id = r2.clone_state()
wl = r2.derive(by_id)
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in wl}
out, records = r2.transform(snapshot)

for eid in wl:
    pre = r2.canon(by_id[eid]).splitlines()
    post = out[eid].splitlines()
    diff = list(difflib.unified_diff(
        pre, post, fromfile=f"{eid}/entry.v2.json@145b090",
        tofile=f"{eid}/entry.v2.json@R2", lineterm="", n=2))
    print("=" * 78)
    print(f"{eid}  ({len(diff)} diff lines)")
    print("=" * 78)
    for line in diff:
        print(line)
    print()

# changed-path ledger (independent recomputation)
for eid in wl:
    pre_map = dict(r2.flat(by_id[eid]))
    post_map = dict(r2.flat(snapshot[eid]))
    changed = sorted(p for p in set(pre_map) | set(post_map)
                     if pre_map.get(p) != post_map.get(p))
    print(f"changed paths {eid}:")
    for p in changed:
        print(f"   {p}")
