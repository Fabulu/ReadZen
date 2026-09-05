#!/usr/bin/env python3
"""Probe: the three gate-1 defect sites, on CLONE pre-state bytes.

  1. t_1793c3514a69: every VAGUE_RE match on the s1 Explanation with
     context (the missed 'a master' site), + the details-file vague rows.
  2. t_2e77bc793d0c: the s1 ClaimAnchors rows (index, ClaimText, Kwic),
     the occurrence kwic heads, and the Explanation — to pick an honest
     headword-free ClaimText fragment for the recut anchor.
  3. t_057cc9ea8755: the s1 ClaimAnchors (pre-state has no new anchor)
     and the Explanation's Chinese-quote context.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location(
    "audit", HERE.parent / "audit_attribution.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

_spec2 = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(eng)

by_id = eng.clone_state()

# ---- 1. t_1793 vague sites -----------------------------------------------------
e = by_id["t_1793c3514a69"]
s1 = e["Senses"][0]
text = str(s1.get("Explanation") or "")
print("##### t_1793c3514a69 s1 VAGUE_RE matches (pre-state) #####")
for m in audit.VAGUE_RE.finditer(text):
    print(f"  [{m.start():5d}] {m.group(0)!r}: "
          f"…{text[max(0, m.start()-70):m.start()]}【{m.group(0)}】"
          f"{text[m.end():m.end()+70]}…")
print(f"  Note matches: {[m.group(0) for m in audit.VAGUE_RE.finditer(str(s1.get('Note') or ''))]}")

details = json.loads(
    (HERE / "a1-worklist-details-20260902.json").read_text(encoding="utf-8"))
print(f"  details vague rows: "
      f"{[d for k, d in details['stillFailing']['t_1793c3514a69'] if k == 'vague_attributor']}")

# ---- 2. t_2e77 anchors + occurrences ------------------------------------------
e = by_id["t_2e77bc793d0c"]
s1 = e["Senses"][0]
print("\n##### t_2e77bc793d0c s1 ClaimAnchors (pre-state) #####")
for i, a in enumerate(s1.get("ClaimAnchors") or []):
    print(f"  a[{i}] RelPath={a.get('RelPath')} {a.get('FromLb')}-{a.get('ToLb')}")
    print(f"      ClaimText: {a.get('ClaimText')!r}")
    print(f"      Kwic: {a.get('Kwic')!r}")
    print(f"      MasterName={a.get('MasterName')!r} Curated={a.get('Curated')}")
print("  occurrences:")
for oi, o in enumerate(s1.get("Occurrences") or [], 1):
    print(f"  o{oi} {o.get('RelPath')} {o.get('FromLb')}-{o.get('ToLb')} "
          f"MasterName={o.get('MasterName')!r} kwic={str(o.get('Kwic') or '')[:80]!r}")
expl = str(s1.get("Explanation") or "")
print(f"  Explanation:\n{expl}")
print(f"  Note:\n{s1.get('Note')}")
print(f"  VAGUE/PLACEHOLDER on t_2e77 prose: "
      f"{[m.group(0) for m in audit.VAGUE_RE.finditer(expl)]}")

# ---- 3. t_057 anchors ----------------------------------------------------------
e = by_id["t_057cc9ea8755"]
s1 = e["Senses"][0]
print("\n##### t_057cc9ea8755 s1 ClaimAnchors (pre-state) #####")
for i, a in enumerate(s1.get("ClaimAnchors") or []):
    print(f"  a[{i}] {a.get('RelPath')} ClaimText={a.get('ClaimText')!r}")
    print(f"      Kwic: {a.get('Kwic')!r}")
print(f"  occurrences: {len(s1.get('Occurrences') or [])}")
