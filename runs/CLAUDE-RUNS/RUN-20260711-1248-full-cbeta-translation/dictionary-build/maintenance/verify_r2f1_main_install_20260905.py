#!/usr/bin/env python3
"""Verify the combined R2+F1 install on the MAIN publish clone.

Every live-vs-baseline comparison uses BASE = R2F1_MAIN_VERIFY_BASE env
(default "HEAD": install-time run, where HEAD is still main's pinned
pre-install commit 989df5dd; post-commit re-run uses "HEAD^", where
HEAD is the publication commit and the pre-state pin lives at HEAD^).

Checks:
  1. every product: main termbase bytes == BUILD terms bytes
     (canonical equality + sha vs manifest entrySha256).
  2. entry count BASE -> live: exactly +1 (the t_351fa42d396b add;
     4,715 -> 4,716), and no BASE entry lost.
  3. NO-REGRESSION law (the reason the wholesale checkout recipe was
     rejected): every entry outside the 5 products byte-identical to
     BASE — main's 347 main-only entries and all R9x repairs survive
     untouched.
  4. registry delta laws: index Terms + legacy +1 each; product term
     rows present; shards that change must hold a product id; alias
     delta recorded (losses fail).
  5. git footprint: the publication's writer-surface changes confined
     to termbase files. (The publish clone carries ~5.9k PRE-EXISTING
     uncommitted non-termbase changes — community/, corpus/, LICENSE,
     NOTICE, workflows — present before this install and excluded from
     the publication commit; reported as an observation, not a law.)
  6. staging integrity vs manifest shas.
  7. lane laws on the published surface:
     a. the 5 Dehui-class windows (R2: 1113a21, 1143a07, 1143a12;
        F1: 1144b03, 1127c04) present with the correction landed
        (MasterName null, Dongyang Dehui [compiler] in ContextMasters).
     b. census law: zero MasterName 'Dehui' rows in the ENTIRE
        installed main surface (main pre-state: exactly 1).
     c. t_057cc9ea8755 occ-3 note carries the compiled-by-disciples
        provenance; t_968a2f97c9ff carries the 一不成、二不是 alias.
     d. ab715 1119b01 carries the Baizhang Huaihai attribution (part
        of the lane-verified product bytes).
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
BASE = os.environ.get("R2F1_MAIN_VERIFY_BASE", "HEAD")
CLONE = Path(r"C:\programmieren\CbetaZenTranslations")
PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff",
            "t_ab715aa474d5", "t_351fa42d396b")
REPAIRED = {
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1113a21"),
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1143a07"),
    ("t_ea2a427c7aba", "T/T48/T48n2025.xml", "1143a12"),
    ("t_ab715aa474d5", "T/T48/T48n2025.xml", "1144b03"),
    ("t_351fa42d396b", "T/T48/T48n2025.xml", "1127c04"),
}

mani = json.loads(
    (BUILD / "maintenance" / "r2f1-main-20260905-generic-manifest.json")
    .read_text(encoding="utf-8"))
product_ids = [p["id"] for p in mani["products"]]
wl = set(product_ids)
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
        problems.append(f"{eid}: absent from installed main surface")
        continue
    if canon(live_by_id[eid]) != terms_text:
        problems.append(f"{eid}: installed main bytes != terms bytes")
    if hashlib.sha256(canon(live_by_id[eid]).encode("utf-8")).hexdigest() \
            != p["entrySha256"]:
        problems.append(f"{eid}: sha != manifest")

# 2. count laws
if len(live_by_id) != len(head_by_id) + 1:
    problems.append(f"entry count {len(head_by_id)} -> {len(live_by_id)} "
                    "(must be exactly +1)")
lost = sorted(eid for eid in head_by_id if eid not in live_by_id)
if lost:
    problems.append(f"BASE entries lost: {lost[:5]}")

# 3. no-regression law
drift = [eid for eid, e in sorted(head_by_id.items())
         if eid not in wl and canon(e) != canon(live_by_id.get(eid, {}))]
if drift:
    problems.append(f"NON-PRODUCT REGRESSION: {drift[:5]} ({len(drift)}) — "
                    "the exact damage the rejected wholesale checkout "
                    "would have caused")

# 4. registry delta laws
live_terms = {r[0] for r in live_idx["Terms"]}
product_terms = {live_by_id[eid]["SourceTerm"] for eid in wl
                 if eid in live_by_id}
missing_rows = sorted(product_terms - live_terms)
if missing_rows:
    problems.append(f"index term rows missing for products: {missing_rows}")
if len(live_idx["Terms"]) != len(head_idx["Terms"]) + 1:
    problems.append(f"index count {len(head_idx['Terms'])} -> "
                    f"{len(live_idx['Terms'])} (must be +1)")
if len(live_leg) != len(head_leg) + 1:
    problems.append(f"legacy count {len(head_leg)} -> {len(live_leg)} "
                    "(must be +1)")
live_alias = dict(live_idx.get("Aliases") or {})
head_alias = dict(head_idx.get("Aliases") or {})
alias_added = sorted(set(live_alias) - set(head_alias))
alias_lost = sorted(set(head_alias) - set(live_alias))
alias_changed = sorted(k for k in set(head_alias) & set(live_alias)
                       if live_alias[k] != head_alias[k])
# Adjudicated alias law (probe_r2f1_alias_delta_20260905.py): every
# index-level loss must be explained by the product set — either the
# alias's main-HEAD owners are all products (the replaced entries'
# old alias sets, e.g. ea2's "sitting Zen" family) or the alias is
# newly AMBIGUOUS in the installed tree (a product also claims it, so
# the merger omits it, e.g. "two daily meals" vs the new 粥飯 entry).
# Every addition must come from a product. Anything else is drift.


def sense_alias_owners(by_id, alias):
    return sorted(eid for eid, e in by_id.items()
                  for s in e.get("Senses") or []
                  if alias in (s.get("SearchAliases") or []))


unexplained_alias = list(alias_changed)
for a in alias_lost:
    owners = sense_alias_owners(head_by_id, a)
    staged_owners = sense_alias_owners(live_by_id, a)
    if not (set(owners) <= wl or len(staged_owners) >= 2):
        unexplained_alias.append(a)
for a in alias_added:
    if not set(sense_alias_owners(live_by_id, a)) & wl:
        unexplained_alias.append(a)
if unexplained_alias:
    problems.append(f"UNEXPLAINED alias delta: {unexplained_alias[:5]}")
changed_shards = []
head_shard_ids: dict[str, set[str]] = {}
live_shard_ids: dict[str, set[str]] = {}
for pp in sorted((CLONE / "termbase").glob("*.json")):
    base_blob = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"{BASE}:termbase/{pp.name}"],
        capture_output=True).stdout
    live_ids = {e.get("Id") for e in json.loads(
        pp.read_text(encoding="utf-8"))["Entries"]}
    live_shard_ids[pp.name] = live_ids
    if pp.read_bytes() != base_blob:
        changed_shards.append(pp.name)
    head_shard_ids[pp.name] = {e.get("Id") for e in json.loads(
        base_blob.decode("utf-8"))["Entries"]}
# a changed shard must hold a product in BASE (replace) or LIVE (add —
# t_351fa42d396b's shard held no product before the publication)
bad_shards = [s for s in changed_shards
              if not ((head_shard_ids.get(s, set()) & wl)
                      or (live_shard_ids.get(s, set()) & wl))]
if bad_shards:
    problems.append(f"shards changed without holding any product: "
                    f"{bad_shards}")

# 5. git footprint — scoped to the publication's writer surface. The
# publish clone carries PRE-EXISTING uncommitted changes outside the
# termbase surface (community translations, corpus/masters, LICENSE,
# NOTICE, workflows — ~5.9k files, present before this install; the
# install receipt's writes are all termbase* paths). Those are not
# this publication's footprint and are excluded from its commit; they
# are reported here as an observation.
st = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                    capture_output=True, text=True,
                    encoding="utf-8").stdout.splitlines()
changed = [l[3:] for l in st]
allowed_pat = re.compile(
    r"(^termbase(?:\.v2|\.index)?\.json$|^termbase/|termbase-shards/|"
    r"termbase-index|index/|\.idx$|shards?/|^terms/)")
footprint = [f for f in changed if allowed_pat.search(f)]
unexpected = [f for f in footprint
              if not re.match(r"^termbase", f)]
preexisting_dirt = len(changed) - len(footprint)
if unexpected:
    problems.append(f"unexpected writer-surface changes: {unexpected[:10]}")
print(f"clone changed files: {len(changed)} "
      f"(publication termbase footprint: {len(footprint)}; "
      f"pre-existing non-termbase dirt: {preexisting_dirt})")

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

# 7a. repaired windows
for eid, rel, lb in sorted(REPAIRED):
    found = False
    for s in live_by_id.get(eid, {}).get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("RelPath") != rel or o.get("FromLb") != lb:
                continue
            found = True
            if o.get("MasterName") is not None:
                problems.append(f"repaired window {lb}: MasterName not null")
            cms = o.get("ContextMasters") or []
            if not any(cm.get("MasterName") == "Dongyang Dehui"
                       and cm.get("Roles") == ["compiler"] for cm in cms):
                problems.append(f"repaired window {lb}: Dongyang Dehui "
                                "[compiler] missing")
    if not found:
        problems.append(f"repaired window {eid} {lb}: not found")

# 7b. census law over the whole main surface
dehui_rows = [f"{eid} {o.get('FromLb')}"
              for eid, e in sorted(live_by_id.items())
              for s in e.get("Senses") or []
              for o in s.get("Occurrences") or []
              if o.get("MasterName") == "Dehui"]
if dehui_rows:
    problems.append(f"census law violated on main: {dehui_rows[:5]} "
                    f"({len(dehui_rows)})")

# 7c. R2 secondary corrections
note3 = ""
for o in live_by_id.get("t_057cc9ea8755", {}) \
        .get("Senses", [{}])[0].get("Occurrences") or []:
    if o.get("RelPath") == "X/X70/X70n1399.xml":
        note3 = o.get("AttributionNote") or ""
if "至柔等編" not in note3:
    problems.append("t_057cc9ea8755: compiled-by-disciples provenance "
                    "(至柔等編) missing from the X70n1399 note")
aliases968 = live_by_id.get("t_968a2f97c9ff", {}) \
    .get("Senses", [{}])[0].get("SearchAliases") or []
if "一不成、二不是" not in aliases968:
    problems.append("t_968a2f97c9ff: search alias 一不成、二不是 missing")

# 7d. ab715 1119b01 Baizhang attribution (lane-verified product bytes)
found_bz = False
for o in live_by_id.get("t_ab715aa474d5", {}) \
        .get("Senses", [{}])[0].get("Occurrences") or []:
    if (o.get("RelPath") == "T/T48/T48n2025.xml"
            and o.get("FromLb") == "1119b01"
            and o.get("MasterName") == "Baizhang Huaihai"):
        found_bz = True
if not found_bz:
    problems.append("t_ab715aa474d5: 1119b01 Baizhang Huaihai "
                    "attribution missing")

print(json.dumps({
    "products": len(product_ids),
    "entriesBaseToLive": [len(head_by_id), len(live_by_id)],
    "indexRowsBaseToLive": [len(head_idx["Terms"]),
                            len(live_idx["Terms"])],
    "legacyRowsBaseToLive": [len(head_leg), len(live_leg)],
    "aliasDelta": {"added": alias_added, "lost": alias_lost,
                   "changed": alias_changed},
    "changedShards": changed_shards,
    "nonProductRegression": len(drift),
    "dehuiCensusRows": len(dehui_rows),
    "repairedWindowsChecked": len(REPAIRED),
    "problems": problems, "ok": not problems,
}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not problems else 1)
