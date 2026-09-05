#!/usr/bin/env python3
"""R2 semantics probe: the note-law regex sources + one canonical
institutional ActorAttribution block to copy conventions from."""
import json
import re
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BUILD))
import audit_attribution as aa  # noqa: E402

src = (BUILD / "audit_attribution.py").read_text(encoding="utf-8")
lines = src.splitlines()


def excerpt(pat, before=2, after=30, tag=""):
    m = re.search(pat, src)
    print(f"\n--- {tag or pat} ({'found' if m else 'MISS'})")
    if not m:
        return
    a = max(0, m.start() - 0)
    # print whole function: backtrack to 'def '
    d = src.rfind("\ndef ", 0, m.start())
    seg = src[d:m.end() + 1400] if d >= 0 else src[a:m.end() + 1400]
    print(seg[:2200])


print("=" * 78)
print("A. roster_name_pattern construction")
print("=" * 78)
for i, l in enumerate(lines, 1):
    if "roster_name_pattern" in l and "=" in l and "findall" not in l:
        print(f"@{i}: {l.strip()[:160]}")
m = re.search(r"roster_name_pattern\s*=.*?(?=\n(?:ROSTER|PLACEHOLDER|VAGUE|DUPLICATED|def )|\Z)",
              src, re.S)
print(m.group(0)[:1500] if m else "(regex miss)")

print()
print("=" * 78)
print("B. does roster_name_pattern match Fayun Yuantong / Baizhang Huaihai?")
print("=" * 78)
pat = getattr(aa, "roster_name_pattern", None)
print(f"pattern object: {pat!r}")
probe_notes = [
    "the code directs sitting and records Fayun Yuantong's rebuke of "
    "sitting with closed eyes",
    "The Baizhang monastic code redacted by Dongyang Dehui gives an "
    "observable hall convention",
    "imperially re-edited by Dongyang Dehui",
]
if pat is not None:
    for n in probe_notes:
        hits = pat.findall(n)
        print(f"  {hits!r} <- {n[:60]}")
else:
    for n in probe_notes:
        for tok in ("Fayun Yuantong", "Baizhang Huaihai", "Dongyang Dehui"):
            pass
    names = aa.roster_names()
    print(f"  'Fayun Yuantong' in roster_names: {'Fayun Yuantong' in names}")
    print(f"  'Baizhang Huaihai' in roster_names: "
          f"{'Baizhang Huaihai' in names}")
    print(f"  'Dongyang Dehui' in roster_names: "
          f"{'Dongyang Dehui' in names}")

print()
print("=" * 78)
print("C. hygiene / vague / placeholder regex laws")
print("=" * 78)
excerpt(r"def attribution_note_hygiene_failures", tag="attribution_note_hygiene_failures")
excerpt(r"def heading_attribution_failures", tag="heading_attribution_failures")
for name in ("PLACEHOLDER_ACTOR_RE", "VAGUE_RE", "DUPLICATED_NOTE_PREFIX_RE",
             "DUPLICATED_SOURCE_PREFIX_RE"):
    m2 = re.search(rf"{name}\s*=\s*(.+)", src)
    print(f"{name} = {m2.group(1)[:200] if m2 else '(miss)'}")
    if m2:
        try:
            rx = eval(m2.group(1).strip())
            for probe in ("his disciples", "compiled by his disciples",
                          "Shiwu Qinggong's verse", "the monastic code's "
                          "institutional voice", "someone", "a master"):
                if rx.search(probe):
                    print(f"    MATCHES {probe!r}")
        except Exception as ex:
            print(f"    (eval failed: {ex})")

print()
print("=" * 78)
print("D. canonical institutional ActorAttribution blocks (T48n2025, "
      "MasterName null)")
print("=" * 78)
from pathlib import Path as P2
CLONE = P2(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
live = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
shown = 0
field_names = {}
for e in live["Entries"]:
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            aa2 = o.get("ActorAttribution")
            if (isinstance(aa2, dict) and o.get("RelPath")
                    == "T/T48/T48n2025.xml" and not o.get("MasterName")):
                for k in aa2:
                    field_names[k] = field_names.get(k, 0) + 1
                label = str(aa2.get("ActorLabel") or "")
                if ("institutional voice" in label or shown == 0) and shown < 3:
                    shown += 1
                    print(f"\n{e['Id']} {e.get('SourceTerm')} "
                          f"[{o.get('FromLb')}] label={label!r}")
                    print(json.dumps(aa2, ensure_ascii=False, indent=1))
                    print(f"  note: {o.get('AttributionNote')}")
print(f"\nActorAttribution field histogram on T48n2025 null-master rows: "
      f"{field_names}")

print()
print("=" * 78)
print("E. ContextMasters Roles vocabulary (compiler precedent count)")
print("=" * 78)
roles = {}
n_context = 0
for e in live["Entries"]:
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            for cm in o.get("ContextMasters") or []:
                n_context += 1
                for r in cm.get("Roles") or []:
                    roles[r] = roles.get(r, 0) + 1
print(f"ContextMasters blocks: {n_context}; roles histogram: "
      f"{dict(sorted(roles.items(), key=lambda kv: -kv[1])[:15])}")
for e in live["Entries"]:
    if e["Id"] == "t_3f7a6ab74b68":
        for s in e.get("Senses") or []:
            for o in s.get("Occurrences") or []:
                if any(cm.get("MasterName") == "Dongyang Dehui"
                       for cm in o.get("ContextMasters") or []):
                    print(f"\nprecedent t_3f7a6ab74b68 "
                          f"[{o.get('RelPath')} {o.get('FromLb')}]:")
                    print(f"  MasterName={o.get('MasterName')!r}")
                    print(f"  ContextMasters={o.get('ContextMasters')}")
                    print(f"  ActorAttribution="
                          f"{json.dumps(o.get('ActorAttribution'), ensure_ascii=False)}")
                    print(f"  note: {o.get('AttributionNote')}")
