#!/usr/bin/env python3
"""Verify the R2 install in the agent clone (post-install).

Every "HEAD" reference below is BASE = R2_VERIFY_BASE env (default
"HEAD" = the install-time run; the archive bundle re-runs post-commit
with "HEAD^", where HEAD is the R2 commit and the pin lives at HEAD^).

Checks (R1c mirror — replace-only, 3 products; R2-specific laws 7f-7g):
  1. every product: clone termbase bytes == terms bytes (canonical
     equality + sha vs manifest entrySha256).
  2. entry count unchanged HEAD -> live (no adds, no withdrawals).
  3. registry delta laws: termbase.index.json Terms row count unchanged
     and every product's SourceTerm keeps its Terms row; termbase.json
     legacy row count unchanged; Aliases delta == exactly ONE new row
     ("一不成、二不是" -> the 968 SourceTerm); shards that change must all
     hold at least one product id, every other shard byte-identical to
     HEAD.
  4. off-footprint protection: every entry outside the 3
     byte-identical to HEAD (git show HEAD:termbase.v2.json).
  5. clone git footprint confined to the termbase writer surface.
  6. staging integrity: staged entry/worksheet/WORK.md shas vs manifest.
  7. R2-specific (correction-lane laws):
     a. global: NO entry in the installed clone cites either retired
        rel among occurrences or ClaimAnchors; SourceTexts leftovers
        reported informationally (the known pre-existing ~49).
     b. the 3 products carry NO retired rel anywhere (occurrences,
        anchors, SourceTexts).
     c. occurrence counts preserved vs HEAD (坐禪 9 + 3; 攝心 6;
        一不成，二不是 10).
     d. the 3 repaired T48n2025 windows present with the correction
        landed (MasterName null, Dongyang Dehui [compiler] in
        ContextMasters).
     e. all 3 product entries differ from HEAD (the repair landed).
     f. alias row installed exactly once (index Aliases delta law).
     g. follow-up-lane protection: t_ab715aa474d5 and t_351fa42d396b
        byte-identical to HEAD (their [Dehui] rows are the user-assigned
        follow-up lane, untouched by R2).
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
# R2_VERIFY_BASE re-points the git reference for every live-vs-baseline
# comparison below. Default "HEAD" reproduces the install-time run
# (installed working tree vs HEAD = the pinned pre-state commit, which
# was true while the install was uncommitted). "HEAD^" is the archive
# bundle's post-commit re-run: HEAD is then the R2 install commit, and
# the pre-state pin lives at HEAD^.
BASE = os.environ.get("R2_VERIFY_BASE", "HEAD")
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
FOLLOW_UP = ("t_ab715aa474d5", "t_351fa42d396b")
EXPECT_COUNTS = {"t_ea2a427c7aba": [9, 3],
                 "t_057cc9ea8755": [6],
                 "t_968a2f97c9ff": [10]}
REPAIRED = {
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1143a07"),
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1113a21"),
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1143a12"),
}
ALIAS_KEY = "一不成、二不是"
ALIAS_VALUE = "一不成，二不是"

mani = json.loads(
    (BUILD / "maintenance" / "r2-20260903-generic-manifest.json")
    .read_text(encoding="utf-8"))
product_ids = [p["id"] for p in mani["products"]]
wl_set = set(product_ids)
if set(product_ids) != set(PRODUCTS):
    raise SystemExit(f"manifest products {product_ids} != expected")
live = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
live_by_id = {e["Id"]: e for e in live["Entries"]}
live_idx = json.loads((CLONE / "termbase.index.json")
                      .read_text(encoding="utf-8"))
live_leg = json.loads((CLONE / "termbase.json").read_text(encoding="utf-8"))


def git_show(path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(CLONE), "show", f"{BASE}:{path}"],
        capture_output=True, text=True, encoding="utf-8").stdout


head_by_id = {e["Id"]: e for e in json.loads(
    git_show("termbase.v2.json"))["Entries"]}
head_idx = json.loads(git_show("termbase.index.json"))
head_leg = json.loads(git_show("termbase.json"))


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


problems = []

# 1. products byte-bound
for p in mani["products"]:
    eid = p["id"]
    terms_text = (BUILD / "terms" / eid / "entry.v2.json").read_text(
        encoding="utf-8-sig")
    if eid not in live_by_id:
        problems.append(f"{eid}: absent from installed clone")
        continue
    if canon(live_by_id[eid]) != terms_text:
        problems.append(f"{eid}: installed bytes != terms bytes")
    sha = hashlib.sha256(canon(live_by_id[eid])
                         .encode("utf-8")).hexdigest()
    if sha != p["entrySha256"]:
        problems.append(f"{eid}: sha {sha[:8]} != manifest")

# 2. entry count unchanged
if len(live_by_id) != len(head_by_id):
    problems.append(f"entry count {len(head_by_id)} -> {len(live_by_id)} "
                    "(replace-only lane: must be unchanged)")

# 3. registry delta laws
live_terms = {r[0] for r in live_idx["Terms"]}
product_terms = {head_by_id[eid]["SourceTerm"] for eid in wl_set}
missing_rows = sorted(product_terms - live_terms)
if missing_rows:
    problems.append(f"index term rows lost for products: {missing_rows[:5]}")
if len(live_idx["Terms"]) != len(head_idx["Terms"]):
    problems.append(f"index count {len(live_idx['Terms'])} != "
                    f"{len(head_idx['Terms'])}")
if len(live_leg) != len(head_leg):
    problems.append(f"legacy count {len(live_leg)} != {len(head_leg)}")
live_alias = dict(live_idx.get("Aliases") or {})
head_alias = dict(head_idx.get("Aliases") or {})
alias_added = {k for k in live_alias if k not in head_alias}
alias_lost = {k for k in head_alias if k not in live_alias}
alias_changed = {k for k in head_alias if k in live_alias
                 and live_alias[k] != head_alias[k]}
if alias_added != {ALIAS_KEY}:
    problems.append(f"alias delta added {sorted(alias_added)} != "
                    f"[{ALIAS_KEY}]")
if alias_lost or alias_changed:
    problems.append(f"alias rows lost/changed: {sorted(alias_lost)}, "
                    f"{sorted(alias_changed)[:3]}")
if live_alias.get(ALIAS_KEY) != ALIAS_VALUE:
    problems.append(f"alias value {live_alias.get(ALIAS_KEY)!r} != "
                    f"{ALIAS_VALUE!r}")
changed_shards = []
head_shard_ids: dict[str, set[str]] = {}
for pp in sorted((CLONE / "termbase").glob("*.json")):
    head_blob = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"HEAD:termbase/{pp.name}"],
        capture_output=True).stdout
    if pp.read_bytes() != head_blob:
        changed_shards.append(pp.name)
    head_shard_ids[pp.name] = {e.get("Id") for e in json.loads(
        head_blob.decode("utf-8"))["Entries"]}
bad_shards = [s for s in changed_shards
              if not (head_shard_ids.get(s, set()) & wl_set)]
if bad_shards:
    problems.append(f"shards changed without holding any product: "
                    f"{bad_shards}")

# 4. off-footprint protection
drift = [eid for eid, e in sorted(head_by_id.items())
         if eid not in wl_set
         and canon(e) != canon(live_by_id.get(eid))]
if drift:
    problems.append(f"off-footprint entries changed: {drift[:5]} "
                    f"({len(drift)})")

# 5. git footprint
st = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                    capture_output=True, text=True).stdout.splitlines()
changed = [l[3:] for l in st]
allowed_pat = re.compile(
    r"(^termbase(?:\.v2|\.index)?\.json$|^termbase/|termbase-shards/|"
    r"termbase-index|index/|\.idx$|shards?/|^terms/)")
unexpected = [f for f in changed if not allowed_pat.search(f)]
if unexpected:
    problems.append(f"unexpected clone changes: {unexpected[:10]}")
print(f"clone changed files: {len(changed)}")

# 6. staging integrity
for p in mani["products"]:
    src = BUILD / p["sourceDir"]
    for fname, key in (("entry.v2.json", "entrySha256"),
                       ("evidence.draft.json", "worksheetSha256"),
                       ("WORK.md", "workSha256")):
        f = src / fname
        if (not f.is_file()
                or hashlib.sha256(f.read_bytes()).hexdigest() != p[key]):
            problems.append(f"staging drift: {p['id']}/{fname}")

# 7a. global retired scan (occurrences/anchors); SourceTexts informational
leftover = []
st_leftovers = []
for eid, e in sorted(live_by_id.items()):
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") in RETIRED:
                leftover.append(f"{eid} occ {o.get('RelPath')}")
        for a in s.get("ClaimAnchors") or []:
            if a.get("RelPath") in RETIRED:
                leftover.append(f"{eid} anchor {a.get('RelPath')}")
        if eid in wl_set:
            for rel in s.get("SourceTexts") or []:
                if rel in RETIRED:
                    st_leftovers.append(f"{eid} sourceTexts {rel}")
if leftover:
    problems.append(f"retired rels still cited (global): "
                    f"{leftover[:5]} ({len(leftover)})")

# 7b-7e. correction-lane laws
for eid in wl_set:
    senses = live_by_id.get(eid, {}).get("Senses") or []
    counts = [len(s.get("Occurrences") or []) for s in senses]
    if counts != EXPECT_COUNTS[eid]:
        problems.append(f"{eid}: occurrence counts {counts} != "
                        f"{EXPECT_COUNTS[eid]}")
    if canon(live_by_id.get(eid, {})) == canon(head_by_id.get(eid, {})):
        problems.append(f"{eid}: byte-identical to HEAD (correction did "
                        "not land)")
for s in live_by_id.get("t_ea2a427c7aba", {}).get("Senses") or []:
    for o in s.get("Occurrences") or []:
        key = ("t_ea2a427c7aba", o.get("RelPath"), o.get("FromLb"))
        if key not in REPAIRED:
            continue
        from_lb = o.get("FromLb")
        if o.get("MasterName") is not None:
            problems.append(f"repaired window {from_lb}: MasterName not "
                            "null")
        cms = o.get("ContextMasters") or []
        if not any(cm.get("MasterName") == "Dongyang Dehui"
                   and cm.get("Roles") == ["compiler"] for cm in cms):
            problems.append(f"repaired window {from_lb}: Dongyang Dehui "
                            "[compiler] missing from ContextMasters")
        if any("Dehui" == x for x in [o.get("MasterName")]
               + [cm.get("MasterName") for cm in cms]):
            problems.append(f"repaired window {from_lb}: bare 'Dehui' "
                            "survived")

# 7g. follow-up-lane protection
for eid in FOLLOW_UP:
    if canon(live_by_id.get(eid, {})) != canon(head_by_id.get(eid, {})):
        problems.append(f"{eid}: follow-up-lane sibling changed (must be "
                        "byte-identical to HEAD)")

print(json.dumps({
    "products": len(product_ids),
    "entriesHeadToLive": [len(head_by_id), len(live_by_id)],
    "indexRowsHeadToLive": [len(head_idx["Terms"]),
                            len(live_idx["Terms"])],
    "legacyRowsHeadToLive": [len(head_leg), len(live_leg)],
    "aliasDelta": {"added": sorted(alias_added),
                   "value": live_alias.get(ALIAS_KEY)},
    "aliasesOtherwiseUnchanged": not (alias_lost or alias_changed),
    "changedShards": changed_shards,
    "offFootprintDrift": len(drift),
    "retiredCitationsGlobal": len(leftover),
    "retiredSourceTextsGlobal": len(st_leftovers),
    "followUpSiblingsUntouched": [eid for eid in FOLLOW_UP
                                  if canon(live_by_id.get(eid, {}))
                                  == canon(head_by_id.get(eid, {}))],
    "productCounts": {eid: [len(s.get("Occurrences") or [])
                            for s in live_by_id.get(eid, {})
                            .get("Senses") or []]
                      for eid in PRODUCTS},
    "problems": problems, "ok": not problems,
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not problems else 1)
