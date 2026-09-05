#!/usr/bin/env python3
"""Stage the fresh10k-r7-depth record commit: write the pathspec file
(the 123 terms dirs — already tracked, now carrying the REPLACED bytes —
+ the three tracked-by-precedent depth lane jsons + this lane's
maintenance scripts) and sanity-check that every terms dir carries
exactly entry.v2.json / WORK.md / STATUS."""
import json
import pathlib

BUILD = pathlib.Path(__file__).resolve().parents[1]
m = json.loads(
    (BUILD / "maintenance" / "fresh10k-r7-depth-generic-manifest.json")
    .read_text(encoding="utf-8-sig"))
ids = [p["id"] for p in m["products"]]
assert len(ids) == 123 and len(set(ids)) == 123, len(ids)

bad = []
lines = []
for tid in ids:
    d = BUILD / "terms" / tid
    names = sorted(p.name for p in d.iterdir()) if d.is_dir() else []
    if names != ["STATUS", "WORK.md", "entry.v2.json"]:
        bad.append((tid, names))
    lines.append(f"terms/{tid}")
assert not bad, bad[:3]

lines += [
    "maintenance/fresh10k-r7-depth-final-release-authority.json",
    "maintenance/fresh10k-r7-depth-generic-manifest.json",
    "maintenance/fresh10k-r7-depth-generic-install-receipt.json",
    "maintenance/promote_r7_depth_20260905.py",
    "maintenance/build_r7_depth_blind_deck_20260905.py",
    "maintenance/adjudicate_r7_depth_blind_d1_20260905.py",
    "maintenance/gen_r7_depth_release.py",
    "maintenance/verify_r7_depth_install_20260905.py",
    "maintenance/stage_r7_depth_record_20260905.py",
]
out = BUILD / "maintenance" / ".r7-depth-record-pathspec.txt"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{len(ids)} term dirs verified (3 files each); pathspec: {out.name}")
