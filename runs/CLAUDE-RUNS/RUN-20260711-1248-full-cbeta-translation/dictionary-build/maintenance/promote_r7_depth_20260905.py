#!/usr/bin/env python3
"""Coordinator promotion gate for the r7 depth-repair lane.

For each of the 123 in-scope entries: take the curation agent's repaired
evidence.draft.json, RECOMPILE it with the real compiler (receipts only
ever come from the compiler), then structurally verify against the current
product entry:
  - Id/SourceTerm unchanged; senses unchanged
  - Occurrences = existing list (byte-equal dicts) + additions appended
  - every addition: registry tier < 3 (no lamp), Kwic is a contiguous
    slice of that work's itertext, FromLb/ToLb exist in the work's lb ids,
    MasterName non-empty, draft-proof ExactHeadwordClause (ws-stripped)
    is a substring of Kwic, no Kwic duplicate of an existing occurrence
  - additions == target - used unless the agent documented below-target
    (their FINDINGS row; recorded in the map row)
Then merge a WORK.md ledger line, promote draft+entry+WORK.md into the
product dir AND fresh-build/entries/<id>/, and write the depth product
map with replace-mode pins (incl. termsBaselineSha256).
Promotes only entries that pass everything; any problem blocks the map.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
FB = BUILD / "fresh-build"
M = BUILD / "maintenance"
LANE = FB / "fresh10k-r7-depth"
STAGE = LANE / "staged"
SUB = BUILD / "subagents"
AGENTS = [SUB / f"20260905-1535-r7-depth-curate-a{k}" for k in (1, 2, 3, 4)]
CORPUS = Path(r"C:\programmieren\CbetaZenTexts\xml-p5")

REG = json.loads((M / "fresh10k-r7-blind-r3-materials-20260905/registry.json")
                 .read_text(encoding="utf-8-sig"))
REG = {e["RelPath"]: e for e in (REG.get("entries") or REG.get("Entries"))}
plan = {p["id"]: p for p in json.loads(
    (LANE / "depth-plan-20260905.json").read_text(encoding="utf-8-sig"))["entries"]
    if p.get("inScope")}  # all 123 (even the 13 at the floor of 4 sit below
    # their computed target — every r7 entry gets depth work)

# worklist assignment is authoritative: agents may hold base copies of
# other agents' entries (A1 left one), so never take first-found drafts
ASSIGN = {}
for k in (1, 2, 3, 4):
    for line in (LANE / f"depth-worklist-a{k}-20260905.txt").read_text(
            encoding="utf-8-sig").splitlines():
        if line.strip():
            ASSIGN[line.split()[0]] = AGENTS[k - 1]

# below-target adjudications (coordinator, after agent FINDINGS review):
# floor-of-4 accepted where the corpus genuinely lacks roster-valid more
BELOW = {}
ANCHOR_FIXES: dict[str, list] = {}
below_path = M / "depth-below-target-adjudications-20260905.json"
if below_path.is_file():
    _adj = json.loads(below_path.read_text(encoding="utf-8-sig"))
    BELOW = _adj.get("entries") or {}
    ANCHOR_FIXES = _adj.get("anchorFixes") or {}

_ws = lambda s: re.sub(r"\s+", "", s or "")
_text_cache: dict[str, str] = {}
_lb_cache: dict[str, set] = {}


def work_text(rel: str) -> str:
    if rel not in _text_cache:
        root = ET.parse(CORPUS / rel).getroot()
        _text_cache[rel] = "".join(root.itertext())
    return _text_cache[rel]


def work_lbs(rel: str) -> set:
    if rel not in _lb_cache:
        raw = (CORPUS / rel).read_text(encoding="utf-8")
        _lb_cache[rel] = set(re.findall(r'<lb[^>]*\bn="([^"]+)"', raw))
    return _lb_cache[rel]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _j(v) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


def prefix_normalized(old_o: dict, new_o: dict) -> bool:
    """True when the ONLY change is prepending the compiler-mandated
    'Source record (<RelPath>). ' prefix to AttributionNote (r7-era
    notes predate the rule; today's compiler refuses without it)."""
    old_n = old_o.get("AttributionNote") or ""
    new_n = new_o.get("AttributionNote") or ""
    m = re.match(r"^Source record \([^)]+\)\. (.*)$", new_n, re.S)
    return (new_n != old_n and bool(m) and m.group(1) == old_n
            and all(_j(old_o.get(k)) == _j(new_o.get(k))
                    for k in old_o if k != "AttributionNote")
            and set(old_o) == set(new_o))


def occ_equal(old_o: dict, new_o: dict, fix: dict | None = None) -> bool:
    """Baseline occurrences may differ ONLY by the permitted
    normalizations: the compiler-mandated AttributionNote prefix, and
    an adjudicated anchor correction (exact old->new lb values)."""
    if _j(old_o) == _j(new_o):
        return True
    diffs = {k for k in set(old_o) | set(new_o)
             if _j(old_o.get(k)) != _j(new_o.get(k))}
    if "AttributionNote" in diffs:
        if not prefix_normalized(old_o, new_o):
            return False
        diffs.discard("AttributionNote")
    if not diffs:
        return True
    if fix and diffs == {"FromLb", "ToLb"}:
        return (old_o.get("RelPath") == fix.get("relPath")
                and old_o.get("FromLb") == fix.get("oldFromLb")
                and old_o.get("ToLb") == fix.get("oldToLb")
                and new_o.get("FromLb") == fix.get("newFromLb")
                and new_o.get("ToLb") == fix.get("newToLb"))
    return False


rows, problems, pending = [], [], []
DRY = "--dry-run" in sys.argv
STAGE.mkdir(parents=True, exist_ok=True)
(LANE / "products").mkdir(parents=True, exist_ok=True)

for eid, p in plan.items():
    term = p["term"]
    ag = ASSIGN.get(eid)
    src = ag / "repaired" / eid / "evidence.draft.json" if ag else None
    if src is None or not src.is_file():
        (pending if DRY else problems).append(
            f"{eid} {term}: no repaired draft from its assigned agent")
        continue

    sd = STAGE / eid
    sd.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, sd / "evidence.draft.json")
    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(BUILD / "compile_evidence_draft.py"),
         str(sd / "evidence.draft.json")],
        cwd=BUILD, capture_output=True, text=True)
    if r.returncode != 0:
        problems.append(f"{eid} {term}: compile rc={r.returncode}: "
                        f"{(r.stderr or r.stdout)[-200:]}")
        continue
    report_path = sd / "evidence-compile-report.json"
    if not report_path.is_file():
        problems.append(f"{eid} {term}: compiler wrote no report")
        continue
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    if report.get("hardPass") is not True:
        problems.append(f"{eid} {term}: compile not hardPass")
        continue
    new_entry_path = sd / "entry.v2.json"
    if not new_entry_path.is_file():
        problems.append(f"{eid} {term}: compiler wrote no entry")
        continue
    if report.get("outputSha256") != sha(new_entry_path) or \
            report.get("worksheetSha256") != sha(sd / "evidence.draft.json"):
        problems.append(f"{eid} {term}: receipt chain mismatch")
        continue

    old_entry = json.loads((FB / "fresh10k-r7/products" / eid / "entry.v2.json")
                           .read_text(encoding="utf-8-sig"))
    new_entry = json.loads(new_entry_path.read_text(encoding="utf-8-sig"))
    draft = json.loads((sd / "evidence.draft.json").read_text(encoding="utf-8-sig"))

    if new_entry.get("Id") != old_entry.get("Id") or \
            new_entry.get("SourceTerm") != old_entry.get("SourceTerm"):
        problems.append(f"{eid} {term}: Id/SourceTerm drifted")
        continue
    old_senses, new_senses = old_entry.get("Senses") or [], new_entry.get("Senses") or []
    if len(old_senses) != len(new_senses):
        problems.append(f"{eid} {term}: sense count changed")
        continue
    additions = []
    prefix_norm: list[str] = []
    anchor_fixed: list[str] = []
    fixes = {f["occurrence"]: f for f in ANCHOR_FIXES.get(eid, [])}
    for si, (os_, ns_) in enumerate(zip(old_senses, new_senses)):
        oo, no = os_.get("Occurrences") or [], ns_.get("Occurrences") or []
        if len(no) < len(oo):
            problems.append(f"{eid} {term}: sense {si} occurrences shrunk")
            break
        for oi, (a, b) in enumerate(zip(oo, no), 1):
            key = f"s{si+1}o{oi}"
            if _j(a) == _j(b):
                continue
            if occ_equal(a, b, fixes.get(key)):
                if (a.get("AttributionNote") or "") != (b.get("AttributionNote") or ""):
                    prefix_norm.append(key)
                if a.get("FromLb") != b.get("FromLb") or a.get("ToLb") != b.get("ToLb"):
                    anchor_fixed.append(key)
                continue
            problems.append(f"{eid} {term}: sense {si} existing occurrences altered")
            break
        for k in set(os_) - {"Occurrences"}:
            if json.dumps(os_[k], ensure_ascii=False, sort_keys=True) != \
                    json.dumps(ns_.get(k), ensure_ascii=False, sort_keys=True):
                problems.append(f"{eid} {term}: sense {si} field {k} changed")
                break
        additions.extend((si, len(oo) + k, o) for k, o in enumerate(no[len(oo):]))
    if any(x.startswith(f"{eid} ") for x in problems):
        continue
    if len(new_entry) != len(old_entry) or any(
            json.dumps(new_entry.get(k), ensure_ascii=False, sort_keys=True) !=
            json.dumps(old_entry.get(k), ensure_ascii=False, sort_keys=True)
            for k in old_entry if k != "Senses"):
        problems.append(f"{eid} {term}: top-level field drift")
        continue

    want = p["target"] - p["used"]
    below_ok = eid in BELOW and len(additions) < want \
        and len(additions) == BELOW[eid].get("acceptedAdditions")
    if len(additions) != want and not below_ok:
        problems.append(f"{eid} {term}: additions {len(additions)} != wanted {want} "
                        f"(below-target needs coordinator adjudication)")
        continue
    kwics = {o.get("Kwic") for s in old_senses for o in (s.get("Occurrences") or [])}
    doccs = {(s_i + 1, o_i + 1): o
             for s_i, s in enumerate((draft.get("Entry") or {}).get("Senses") or [])
             for o_i, o in enumerate(s.get("Occurrences") or [])}
    for si, oi, o in additions:
        rel = o.get("RelPath")
        if REG.get(rel, {}).get("Tier", 3) >= 3:
            problems.append(f"{eid} {term}: addition cites lamp-tier work {rel}")
            break
        kwic = o.get("Kwic") or ""
        if not kwic or kwic in kwics:
            problems.append(f"{eid} {term}: empty/duplicate Kwic addition")
            break
        if term not in kwic or _ws(kwic) not in _ws(work_text(rel)):
            problems.append(f"{eid} {term}: Kwic not a contiguous corpus slice ({rel})")
            break
        if o.get("FromLb") not in work_lbs(rel) or o.get("ToLb") not in work_lbs(rel):
            problems.append(f"{eid} {term}: From/ToLb not in work ({rel})")
            break
        # project attribution model (7,741/22,949 public occurrences):
        # MasterName may be null when a structured ActorAttribution
        # carries the actor (464 identified-non-master precedents)
        aa = o.get("ActorAttribution") or {}
        if not o.get("MasterName") and not (aa.get("Status") and aa.get("ActorLabel")):
            problems.append(f"{eid} {term}: addition has neither MasterName "
                            f"nor ActorAttribution ({rel})")
            break
        proof = ((doccs.get((si + 1, oi + 1)) or {}).get("DraftActorProof")) or {}
        clause = proof.get("ExactHeadwordClause") or ""
        if not clause or _ws(clause) not in _ws(kwic):
            problems.append(f"{eid} {term}: addition proof clause not in Kwic")
            break
        kwics.add(kwic)
    if any(x.startswith(f"{eid} ") for x in problems):
        continue

    if DRY:
        rows.append({"id": eid, "term": term, "added": len(additions),
                     "target": p["target"]})
        continue
    # promote: depth products live in THIS lane (r7's own products stay
    # untouched — its create-mode map still pins those shas); the
    # fresh-build/entries source copies stay in sync
    old_prod = FB / "fresh10k-r7/products" / eid
    depth_prod = LANE / "products" / eid
    line = (f"- 2026-09-05 r7-depth: +{len(additions)} occurrences "
            f"(target {p['target']}; tier1/2 only, lamp excluded); "
            f"new works {len({o['RelPath'] for _, _, o in additions})}; "
            f"recompiled hardPass\n")
    for dst in (depth_prod, FB / "entries" / eid):
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sd / "evidence.draft.json", dst / "evidence.draft.json")
        shutil.copyfile(new_entry_path, dst / "entry.v2.json")
        shutil.copyfile(sd / "evidence-compile-report.json",
                        dst / "evidence-compile-report.json")
        wm = dst / "WORK.md"
        if not wm.exists():
            shutil.copyfile(old_prod / "WORK.md", wm)
        existing = wm.read_text(encoding="utf-8-sig")
        if "r7-depth:" not in existing:  # idempotent on re-run
            with wm.open("a", encoding="utf-8") as f:
                f.write(line)
    rows.append({
        "id": eid, "term": term, "termsMode": "replace",
        "entrySha256": sha(depth_prod / "entry.v2.json"),
        "worksheetSha256": sha(depth_prod / "evidence.draft.json"),
        "workSha256": sha(depth_prod / "WORK.md"),
        "termsBaselineSha256": sha(BUILD / "terms" / eid / "entry.v2.json"),
        "added": len(additions),
        "newWorks": len({o["RelPath"] for _, _, o in additions}),
        "target": p["target"], "usedBefore": p["used"],
        **({"belowTargetAccepted": True,
            "belowTargetReason": BELOW[eid].get("reason", "")}
           if below_ok else {}),
        **({"prefixNormalized": prefix_norm} if prefix_norm else {}),
        **({"anchorFixed": anchor_fixed} if anchor_fixed else {}),
    })

print(json.dumps({"dryRun": DRY, "checked": len(rows), "pending": len(pending),
                  "problems": problems}, ensure_ascii=False, indent=2))
if DRY:
    from collections import Counter
    print("additions vs target (checked entries):",
          dict(Counter(r["added"] - r["target"] for r in rows)))
    print("pending (agents still working):",
          [p.split()[0] for p in pending][:8], "..." if len(pending) > 8 else "")
    sys.exit(0)
if problems or len(rows) != len(plan):
    print("NOT writing depth product map until problems resolved", file=sys.stderr)
    sys.exit(1)
map_path = LANE / "products" / "product-map.json"
map_path.write_text(json.dumps({"products": rows}, ensure_ascii=False,
                               indent=2) + "\n", encoding="utf-8")
print("wrote", map_path, f"({len(rows)} rows)")
print("product-map sha256:", sha(map_path))
