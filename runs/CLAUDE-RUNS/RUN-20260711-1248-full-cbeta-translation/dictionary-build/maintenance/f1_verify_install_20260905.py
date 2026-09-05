#!/usr/bin/env python3
"""Verify the F1 install in the agent clone (post-install).

Every "HEAD" reference below is BASE = F1_VERIFY_BASE env (default
"HEAD" = the install-time run; the archive bundle re-runs post-commit
with "HEAD^", where HEAD is the F1 commit and the pin lives at HEAD^).

Checks (R2 mirror — replace-only, 2 products; F1-specific laws 7f-7g):
  1. every product: clone termbase bytes == terms bytes (canonical
     equality + sha vs manifest entrySha256).
  2. entry count unchanged HEAD -> live (no adds, no withdrawals).
  3. registry delta laws: termbase.index.json Terms row count unchanged
     and every product's SourceTerm keeps its Terms row; termbase.json
     legacy row count unchanged; Aliases delta EMPTY (no alias edit
     this lane); shards that change must all hold at least one product
     id, every other shard byte-identical to BASE.
  4. off-footprint protection: every entry outside the 2
     byte-identical to BASE (git show BASE:termbase.v2.json).
  5. clone git footprint confined to the termbase writer surface.
  6. staging integrity: staged entry/worksheet/WORK.md shas vs manifest.
  7. F1-specific (correction-lane laws):
     a. global: NO entry in the installed clone cites either retired
        rel among occurrences or ClaimAnchors; SourceTexts leftovers
        reported informationally (the known pre-existing class).
     b. the 2 products carry NO retired rel anywhere (occurrences,
        anchors, SourceTexts).
     c. occurrence counts preserved vs BASE (一日不作一日不食 3;
        粥飯 3 + 6).
     d. the 2 repaired T48n2025 windows present with the correction
        landed (MasterName null, Dongyang Dehui [compiler] in
        ContextMasters).
     e. both product entries differ from BASE (the repair landed).
     f. census law (SPEC §7): zero MasterName == "Dehui" occurrence
        rows in the ENTIRE installed clone.
     g. R2-product protection: t_ea2a427c7aba, t_057cc9ea8755,
        t_968a2f97c9ff byte-identical to BASE (their repair is the
        shipped R2 state, untouched by F1).
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
# F1_VERIFY_BASE re-points the git reference for every live-vs-baseline
# comparison below. Default "HEAD" reproduces the install-time run
# (installed working tree vs HEAD = the pinned pre-state commit 8457672,
# true while the install is uncommitted). "HEAD^" is the archive
# bundle's post-commit re-run: HEAD is then the F1 install commit, and
# the pre-state pin lives at HEAD^.
BASE = os.environ.get("F1_VERIFY_BASE", "HEAD")
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
PRODUCTS = ("t_ab715aa474d5", "t_351fa42d396b")
R2_PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
EXPECT_COUNTS = {"t_ab715aa474d5": [3],
                 "t_351fa42d396b": [3, 6]}
REPAIRED = {
    ("t_ab715aa474d5", "T/T48/T48n2025.xml", "1144b03"),
    ("t_351fa42d396b", "T/T48/T48n2025.xml", "1127c04"),
}

mani = json.loads(
    (BUILD / "maintenance" / "f1-20260905-generic-manifest.json")
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
if alias_added:
    problems.append(f"alias delta added {sorted(alias_added)} != [] "
                    "(no alias edit this lane)")
if alias_lost or alias_changed:
    problems.append(f"alias rows lost/changed: {sorted(alias_lost)}, "
                    f"{sorted(alias_changed)[:3]}")
changed_shards = []
head_shard_ids: dict[str, set[str]] = {}
for pp in sorted((CLONE / "termbase").glob("*.json")):
    base_blob = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"{BASE}:termbase/{pp.name}"],
        capture_output=True).stdout
    if pp.read_bytes() != base_blob:
        changed_shards.append(pp.name)
    head_shard_ids[pp.name] = {e.get("Id") for e in json.loads(
        base_blob.decode("utf-8"))["Entries"]}
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
        problems.append(f"{eid}: byte-identical to BASE (correction did "
                        "not land)")
for eid, rel, lb in REPAIRED:
    found = False
    for s in live_by_id.get(eid, {}).get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") != rel or o.get("FromLb") != lb:
                continue
            found = True
            if o.get("MasterName") is not None:
                problems.append(f"repaired window {lb}: MasterName not "
                                "null")
            cms = o.get("ContextMasters") or []
            if not any(cm.get("MasterName") == "Dongyang Dehui"
                       and cm.get("Roles") == ["compiler"] for cm in cms):
                problems.append(f"repaired window {lb}: Dongyang Dehui "
                                "[compiler] missing from ContextMasters")
            if any("Dehui" == x for x in [o.get("MasterName")]
                   + [cm.get("MasterName") for cm in cms]):
                problems.append(f"repaired window {lb}: bare 'Dehui' "
                                "survived")
    if not found:
        problems.append(f"repaired window {eid} {lb}: not found")

# 7f. census law (SPEC §7)
dehui_rows = []
for eid, e in sorted(live_by_id.items()):
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("MasterName") == "Dehui":
                dehui_rows.append(f"{eid} {o.get('FromLb')}")
if dehui_rows:
    problems.append(f"census law violated — MasterName 'Dehui' rows "
                    f"remain: {dehui_rows[:5]} ({len(dehui_rows)})")

# 7g. R2-product protection
for eid in R2_PRODUCTS:
    if canon(live_by_id.get(eid, {})) != canon(head_by_id.get(eid, {})):
        problems.append(f"{eid}: R2 product changed (must be "
                        "byte-identical to BASE)")

print(json.dumps({
    "products": len(product_ids),
    "entriesHeadToLive": [len(head_by_id), len(live_by_id)],
    "indexRowsHeadToLive": [len(head_idx["Terms"]),
                            len(live_idx["Terms"])],
    "legacyRowsHeadToLive": [len(head_leg), len(live_leg)],
    "aliasDelta": {"added": sorted(alias_added)},
    "aliasesOtherwiseUnchanged": not (alias_lost or alias_changed),
    "changedShards": changed_shards,
    "offFootprintDrift": len(drift),
    "retiredCitationsGlobal": len(leftover),
    "retiredSourceTextsGlobal": len(st_leftovers),
    "dehuiCensusRows": len(dehui_rows),
    "r2ProductsUntouched": [eid for eid in R2_PRODUCTS
                            if canon(live_by_id.get(eid, {}))
                            == canon(head_by_id.get(eid, {}))],
    "productCounts": {eid: [len(s.get("Occurrences") or [])
                            for s in live_by_id.get(eid, {})
                            .get("Senses") or []]
                      for eid in PRODUCTS},
    "problems": problems, "ok": not problems,
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not problems else 1)
