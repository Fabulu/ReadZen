#!/usr/bin/env python3
"""Fact-check round 3:
  - zc windows of 水頭 / 浴主水頭 in the admitted code rels (does an
    admitted DEFINITIONAL witness exist for 水頭's concrete duty?)
  - zc.py count() internals (file-list helper)
  - corpus XML headers: X70n1399 (compiler 至柔?), T48n2025 (Dehui 德煇
    重編?)
  - titles.jsonl targeted search
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402

print("=" * 78)
print("G. admitted definitional witness for 水頭")
print("=" * 78)
for rel in ("T/T48/T48n2025.xml", "X/X63/X63n1250.xml"):
    for term in ("浴主水頭", "水頭"):
        try:
            rows = zc.find(rel, term, ctx=40, limit=8)
        except Exception as ex:
            print(f"zc.find({rel!r},{term!r}) failed: {ex}")
            continue
        print(f"\n{rel} :: {term!r} -> {len(rows)} windows (limit 8)")
        for r in rows:
            print(f"  {r['fromLb']}: {r['window']}")

print()
print("=" * 78)
print("H. zc.py count() internals")
print("=" * 78)
src = (BUILD / "zc.py").read_text(encoding="utf-8")
m = re.search(r"def count\(.*?(?=\ndef |\Z)", src, re.S)
print(m.group(0)[:1200] if m else "(miss)")
print(f"\nCORPUS = {zc.CORPUS!r}")
print(f"ALLOW size = {len(zc.ALLOW) if hasattr(zc.ALLOW, '__len__') else '?'}")

print()
print("=" * 78)
print("I. corpus XML headers (compiler metadata)")
print("=" * 78)
for rel, needle in (("X/X70/X70n1399.xml", ("至柔", "石屋")),
                    ("T/T48/T48n2025.xml", ("德煇", "德辉", "重編"))):
    p = Path(zc.CORPUS) / rel
    print(f"\n{rel}: exists={p.is_file()} ({p})")
    if not p.is_file():
        continue
    text = p.read_text(encoding="utf-8", errors="replace")[:40000]
    for nd in needle:
        for mm in list(re.finditer(nd, text))[:2]:
            a = max(0, mm.start() - 120)
            print(f"  {nd}: …{text[a:mm.end() + 120]}…".replace("\n", " "))

print()
print("=" * 78)
print("J. titles.jsonl targeted search")
print("=" * 78)
ps = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "$dirs = @('maintenance','scripts','fresh-build','fold-609',"
     "'.agents'); "
     f"foreach ($d in $dirs) {{ Get-ChildItem -Path "
     f"'{BUILD}\\$d' -Recurse -Filter titles.jsonl "
     "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty "
     "FullName }}"],
    capture_output=True, text=True).stdout.strip()
print(f"locations: {ps if ps else '(none)'}")
