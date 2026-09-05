#!/usr/bin/env python3
"""Read-only fact check of the external review verdict (2026-09-03).

Verifies, against local authorities (never the reviewer's wording):
  A. zen-source-authority.json classification of T48n2025 (compiled /
     multi-voice / machine-authority) + records for X70n1399, T48n2023,
     X63n1245, and any person record for Dehui / Zhirou.
  B. Termbase conventions for regulation-text occurrences: all
     occurrences citing T48n2025 (MasterName histogram, sample notes);
     global count of MasterName-null occurrences + what their notes look
     like (the null/ editorial precedent); union of occurrence-level
     field names (Role/Voice/... support).
  C. t_d7725cb0c8c0 (水頭) full current state — do the 2 survivors
     support the public prose?
  D. zc: definitional witness for 水頭 among ADMITTED rels
     (浴主水頭 / 水頭 in T48n2025 etc.).
  E. X70n1399 + T48n2025 title metadata (compiler 至柔等編?).
  F. C1: Aliases state, withdrawal record, publisher script named by the
     install receipt/manifest.
"""
import json
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
REPO = BUILD.parents[3]
sys_reg = REPO / "Assets" / "Data" / "zen-source-authority.json"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def find_key(obj, needle, path="$"):
    """Yield (path, value) for every dict key or string leaf containing needle."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if needle in str(k):
                yield (f"{path}.{k}", v)
            yield from find_key(v, needle, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from find_key(v, needle, f"{path}[{i}]")
    elif isinstance(obj, str) and needle in obj:
        yield (path, obj)


print("=" * 78)
print("A. zen-source-authority.json")
print("=" * 78)
print(f"file: {sys_reg} exists={sys_reg.is_file()}")
reg = load(sys_reg)
print(f"top-level keys: {list(reg)[:20]}")
for needle in ("T48n2025", "X70n1399", "T48n2023", "X63n1245"):
    hits = list(find_key(reg, needle))
    print(f"\n--- {needle}: {len(hits)} hits")
    for p, v in hits[:3]:
        s = json.dumps(v, ensure_ascii=False)
        print(f"  {p}: {s[:500]}")

print()
print("=" * 78)
print("B. Termbase conventions (clone termbase.v2.json)")
print("=" * 78)
live = load(CLONE / "termbase.v2.json")
t48n2025_rows, null_master, field_names = [], [], set()
for e in live["Entries"]:
    for si, s in enumerate(e.get("Senses") or []):
        for oi, o in enumerate(s.get("Occurrences") or []):
            field_names.update(o.keys())
            if o.get("RelPath") == "T/T48/T48n2025.xml":
                t48n2025_rows.append(
                    (e["Id"], e.get("SourceTerm"), si, oi,
                     o.get("MasterName"), (o.get("AttributionNote")
                                            or "")[:110]))
            if not o.get("MasterName"):
                null_master.append(
                    (e["Id"], o.get("RelPath"), (o.get("AttributionNote")
                                                 or "")[:110]))
print(f"occurrence-level field names across termbase: "
      f"{sorted(field_names)}")
from collections import Counter
mn = Counter(r[4] for r in t48n2025_rows)
print(f"\nT48n2025 occurrences: {len(t48n2025_rows)} across "
      f"{len({r[0] for r in t48n2025_rows})} entries; "
      f"MasterName histogram: {dict(mn)}")
print("samples:")
for r in t48n2025_rows[:6]:
    print(f"  {r[0]} {r[1]} s{r[2]+1}o{r[3]+1} [{r[4]}] {r[5]}")
print(f"\nMasterName-null occurrences termbase-wide: {len(null_master)}")
for r in null_master[:5]:
    print(f"  {r[0]} {r[1]} | {r[2]}")

print()
print("=" * 78)
print("C. 水頭 t_d7725cb0c8c0 current state")
print("=" * 78)
e = next(x for x in live["Entries"] if x["Id"] == "t_d7725cb0c8c0")
print(f"SourceTerm: {e.get('SourceTerm')}")
for si, s in enumerate(e.get("Senses") or []):
    print(f"--- sense {si + 1}")
    for k in ("Translation", "Definition", "Gloss", "Note",
              "Explanation"):
        if s.get(k):
            print(f"  {k}: {s[k]}")
    for oi, o in enumerate(s.get("Occurrences") or []):
        print(f"  occ{oi + 1}: {o.get('RelPath')} {o.get('FromLb')}"
              f"->{o.get('ToLb')} [{o.get('MasterName')}]")
        print(f"        kwic: {(o.get('Kwic') or '')[:90]}")
        print(f"        note: {(o.get('AttributionNote') or '')[:200]}")

print()
print("=" * 78)
print("D. zc — definitional witness for 水頭 among admitted rels")
print("=" * 78)
import sys
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402
print(f"zc public names: {[n for n in dir(zc) if not n.startswith('_')]}")
for term in ("浴主水頭", "水頭"):
    try:
        c = zc.count(term)
        print(f"zc.count({term!r}) = {c.get('hits')} hits / "
              f"{c.get('files')} files")
    except Exception as ex:
        print(f"zc.count({term!r}) failed: {ex}")
for fn in ("locate", "files", "search", "hits", "find"):
    if hasattr(zc, fn):
        try:
            out = getattr(zc, fn)("浴主水頭")
            print(f"zc.{fn}('浴主水頭') -> "
                  f"{json.dumps(out, ensure_ascii=False)[:800]}")
        except Exception as ex:
            print(f"zc.{fn}('浴主水頭') failed: {ex}")

print()
print("=" * 78)
print("E. titles metadata for X70n1399 / T48n2025")
print("=" * 78)
cands = list(BUILD.glob("titles.jsonl")) + \
    list(BUILD.glob("*/titles.jsonl")) + \
    list((BUILD / "maintenance").glob("titles*.jsonl"))
print(f"titles.jsonl candidates: {[str(c) for c in cands]}")
if cands:
    for line in cands[0].read_text(encoding="utf-8").splitlines():
        if any(n in line for n in ("X70n1399", "T48n2025")):
            print("  " + line[:400])

print()
print("=" * 78)
print("F. C1 — aliases, withdrawal, publisher path")
print("=" * 78)
idx = load(CLONE / "termbase.index.json")
al = idx.get("Aliases") or {}
hits = {k: v for k, v in al.items() if "一不成" in k or "一不成" in str(v)}
print(f"Aliases entries touching 一不成: {hits}")
ids = {x["Id"] for x in live["Entries"]}
print(f"t_1a6cdc16c248 in live: {'t_1a6cdc16c248' in ids}; "
      f"t_968a2f97c9ff in live: {'t_968a2f97c9ff' in ids}")
c1 = load(BUILD / "maintenance" / "c1-20260902-generic-manifest.json")
print(f"manifest.node: {json.dumps(c1.get('node'), ensure_ascii=False)}"
      f"[:400]")
print(f"manifest.integrityCommand: "
      f"{json.dumps(c1.get('integrityCommand'), ensure_ascii=False)}")
