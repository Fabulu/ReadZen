#!/usr/bin/env python3
"""Fact-check round 2: registry records in full, ActorAttribution
vocabulary, the admitted 浴主水頭 witness, titles.jsonl, publisher
ID_REPLACEMENTS, and the pre-existing [Dehui] rows in 坐禪."""
import json
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
REPO = BUILD.parents[3]
sys_reg = REPO / "Assets" / "Data" / "zen-source-authority.json"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


print("=" * 78)
print("A2. full registry records")
print("=" * 78)
reg = load(sys_reg)
for ent in reg["entries"]:
    if ent.get("RelPath") in ("T/T48/T48n2025.xml", "X/X70/X70n1399.xml"):
        print(f"\n--- {ent['RelPath']}")
        print(json.dumps(ent, ensure_ascii=False, indent=1)[:1800])
pol = reg.get("policy")
if pol:
    print("\npolicy (head): "
          + json.dumps(pol, ensure_ascii=False)[:900])

print()
print("=" * 78)
print("B2. ActorAttribution vocabulary + institutional-voice rows")
print("=" * 78)
live = load(CLONE / "termbase.v2.json")
from collections import Counter
aa_all, aa_null, aa_t48 = Counter(), Counter(), Counter()
inst_samples = []
def aakey(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True) \
        if isinstance(v, (dict, list)) else repr(v)


for e in live["Entries"]:
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            v = aakey(o.get("ActorAttribution"))
            aa_all[v] += 1
            if not o.get("MasterName"):
                aa_null[v] += 1
            if o.get("RelPath") == "T/T48/T48n2025.xml":
                aa_t48[v] += 1
                if (o.get("ActorAttribution")
                        and len(inst_samples) < 3
                        and "institutional" in (o.get("AttributionNote")
                                                or "")):
                    inst_samples.append((e["Id"],
                                         o.get("ActorAttribution"),
                                         o.get("AttributionNote")))
print(f"ActorAttribution all: {dict(aa_all.most_common(12))}")
print(f"ActorAttribution where MasterName null: "
      f"{dict(aa_null.most_common(12))}")
print(f"ActorAttribution on T48n2025 rows: {dict(aa_t48)}")
for s in inst_samples:
    print(f"  sample {s[0]} "
          f"ActorAttribution={json.dumps(s[1], ensure_ascii=False)}"
          f"\n    note: {s[2]}")

print()
print("=" * 78)
print("B3. all 5 [Dehui] T48n2025 rows + 坐禪 1113a21 row in full")
print("=" * 78)
for e in live["Entries"]:
    for si, s in enumerate(e.get("Senses") or []):
        for oi, o in enumerate(s.get("Occurrences") or []):
            if (o.get("RelPath") == "T/T48/T48n2025.xml"
                    and o.get("MasterName") == "Dehui"):
                print(f"\n{e['Id']} {e.get('SourceTerm')} s{si+1}o{oi+1} "
                      f"{o.get('FromLb')}->{o.get('ToLb')}")
                print(f"  ActorAttribution: {o.get('ActorAttribution')}")
                print(f"  EvidenceRole: {o.get('EvidenceRole')}")
                print(f"  note: {o.get('AttributionNote')}")
                print(f"  kwic: {(o.get('Kwic') or '')[:70]}")

print()
print("=" * 78)
print("B4. 坐禪 prose sentences naming Dehui (current live)")
print("=" * 78)
e = next(x for x in live["Entries"] if x["Id"] == "t_ea2a427c7aba")
for si, s in enumerate(e.get("Senses") or []):
    for k in ("Note", "Explanation"):
        for sent in re.split(r"(?<=[.!?]) ", s.get(k) or ""):
            if "Dehui" in sent or "Zongze" in sent:
                print(f"  s{si+1} {k}: {sent}")

print()
print("=" * 78)
print("D2. zc.find signature + admitted 浴主水頭 witness")
print("=" * 78)
import sys
sys.path.insert(0, str(BUILD))
import zc  # noqa: E402
import inspect
print(f"find signature: {inspect.signature(zc.find)}")
print(f"find doc: {(zc.find.__doc__ or '').strip()[:300]}")
src = Path(BUILD / "zc.py").read_text(encoding="utf-8")
m = re.search(r"def find\(.*?\n(?:.*?\n)*?(?=def |\Z)", src)
print("zc.py find() source:")
print(m.group(0)[:900] if m else "  (regex miss)")

print()
print("=" * 78)
print("E2. titles.jsonl location + X70n1399/T48n2025 rows")
print("=" * 78)
out = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     f"Get-ChildItem -Path '{BUILD}' -Recurse -Depth 3 -Filter "
     f"titles.jsonl -ErrorAction SilentlyContinue | Select-Object "
     f"-ExpandProperty FullName"],
    capture_output=True, text=True).stdout.strip()
print(f"locations: {out}")
for loc in out.splitlines()[:1]:
    for line in Path(loc).read_text(encoding="utf-8").splitlines():
        if any(n in line for n in ("X70n1399", "T48n2025")):
            print("  " + line[:500])

print()
print("=" * 78)
print("F2. merge-dict-entries.js ID_REPLACEMENTS")
print("=" * 78)
js = REPO / "eng" / "tools" / "merge-dict-entries.js"
print(f"exists={js.is_file()}")
text = js.read_text(encoding="utf-8", errors="replace")
m = re.search(r"ID_REPLACEMENTS[^;]*;", text, re.S)
print(m.group(0)[:600] if m else "ID_REPLACEMENTS literal not found")
hits = [(i + 1, l.strip()[:100]) for i, l in enumerate(text.splitlines())
        if "t_1a6cdc16c248" in l or "t_968a2f97c9ff" in l]
print(f"lines naming the C1 pair: {hits[:10]}")
