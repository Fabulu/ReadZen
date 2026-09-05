#!/usr/bin/env python3
"""R2 design probe: the last facts frozen into r2_transform_20260903.py.

  A. audit_attribution.py note-law semantics (exact code excerpts):
     actor_marker / represented / named-in-prose scan — which note field,
     which name set, from which offset; is RelatedMasters roster-checked?
  B. ea2 (坐禪) current bytes: sense-1 occurrences 1/8/9 in full;
     RelatedMasters; the Dehui Explanation sentence.
  C. 057 (攝心): the "own record" Note sentence; s1o3 AttributionNote.
  D. 968 (一不成，二不是): terms dir presence; which sense holds
     SearchAliases; current list; entry Id/SourceTerm.
  E. roster: "Dongyang Dehui" membership; every ea2 RelatedMasters name.
  F. clone HEAD + porcelain; terms/ presence for the 3 products.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BUILD = ROOT
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


print("=" * 78)
print("A. audit_attribution.py note-law semantics (excerpts)")
print("=" * 78)
src = (BUILD / "audit_attribution.py").read_text(encoding="utf-8")
lines = src.splitlines()
for lo, hi, tag in ((920, 990, "actor_marker/represented"),
                    (990, 1100, "note laws"),
                    (540, 575, "strict_roster_here"),
                    (360, 380, "roster_names")):
    print(f"\n--- lines {lo}-{hi} ({tag})")
    for i in range(lo - 1, min(hi, len(lines))):
        print(f"{i + 1:5d} {lines[i]}")
# RelatedMasters roster validation?
for i, l in enumerate(lines, 1):
    if "RelatedMasters" in l:
        print(f"RM@{i}: {l.strip()[:120]}")

print()
print("=" * 78)
print("F. clone state")
print("=" * 78)
head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
por = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                     capture_output=True, text=True).stdout.splitlines()
print(f"HEAD={head[:10]} porcelain={por[:5]} ({len(por)})")

print()
print("=" * 78)
print("B. ea2 sense-1 occurrences 1/8/9 + RelatedMasters + Dehui prose")
print("=" * 78)
canon = lambda v: json.dumps(v, ensure_ascii=False, indent=2) + "\n"
e = load(ROOT / "terms" / "t_ea2a427c7aba" / "entry.v2.json")
live = {x["Id"]: x for x in
        load(CLONE / "termbase.v2.json")["Entries"]}
print(f"terms==clone: "
      f"{canon(e) == canon(live['t_ea2a427c7aba'])}")
s1 = e["Senses"][0]
print(f"sense counts: {[len(s['Occurrences']) for s in e['Senses']]}")
print(f"RelatedMasters: {s1.get('RelatedMasters')}")
for oi in (1, 8, 9):
    o = s1["Occurrences"][oi - 1]
    print(f"\n--- s1o{oi}")
    print(json.dumps(o, ensure_ascii=False, indent=1))
for k in ("Explanation", "Note"):
    for sent in re.split(r"(?<=[.!?]) ", s1.get(k) or ""):
        if "Dehui" in sent:
            print(f"\n{s1[k == 'Explanation' and 'Explanation' or 'Note']}"
                  f" sentence: {sent}")

print()
print("=" * 78)
print("C. 057 'own record' sentence + s1o3 AttributionNote")
print("=" * 78)
e57 = load(ROOT / "terms" / "t_057cc9ea8755" / "entry.v2.json")
print(f"terms==clone: "
      f"{canon(e57) == canon(live['t_057cc9ea8755'])}")
s57 = e57["Senses"][0]
n = s57.get("Note") or ""
i = n.find("own record")
print(f"Note around 'own record': …{n[max(0, i - 120):i + 160]}…")
print(f"\ns1o3 AttributionNote:\n{s57['Occurrences'][2].get('AttributionNote')}")
print(f"s1o3 MasterName={s57['Occurrences'][2].get('MasterName')!r} "
      f"ContextMasters={s57['Occurrences'][2].get('ContextMasters')}")

print()
print("=" * 78)
print("D. 968 terms dir + SearchAliases")
print("=" * 78)
p968 = ROOT / "terms" / "t_968a2f97c9ff" / "entry.v2.json"
print(f"terms/t_968a2f97c9ff exists: {p968.is_file()}")
if p968.is_file():
    e968 = load(p968)
    print(f"Id={e968['Id']} SourceTerm={e968['SourceTerm']!r}")
    print(f"terms==clone: "
          f"{canon(e968) == canon(live['t_968a2f97c9ff'])}")
    for si, s in enumerate(e968.get("Senses") or [], 1):
        sa = s.get("SearchAliases")
        print(f"s{si} SearchAliases={sa!r} "
              f"(occ={len(s.get('Occurrences') or [])})")
        if sa is None:
            # any other field mentioning 一不成?
            for k, v in s.items():
                if isinstance(v, str) and "一不成" in v:
                    print(f"   s{si}.{k} contains 一不成")

print()
print("=" * 78)
print("E. roster membership")
print("=" * 78)
import sys
sys.path.insert(0, str(BUILD))
import audit_attribution as aa  # noqa: E402
names = aa.roster_names()
alias = aa.roster_aliases() if hasattr(aa, "roster_aliases") else {}
targets = ["Dongyang Dehui", "Dehui", "Shiwu Qinggong", "Changlu Zongze"]
targets += list((load(ROOT / "terms" / "t_ea2a427c7aba"
                      / "entry.v2.json")["Senses"][0]
                 .get("RelatedMasters") or []))
for t in sorted(set(targets)):
    print(f"  {t!r}: names={t in names} alias_of="
          f"{alias.get(t.casefold())!r}")
