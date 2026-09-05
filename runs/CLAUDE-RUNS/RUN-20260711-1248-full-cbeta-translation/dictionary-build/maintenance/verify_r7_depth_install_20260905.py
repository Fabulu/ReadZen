#!/usr/bin/env python3
"""Post-install verification for the fresh10k-r7-depth REPLACE-mode
publication. Baseline: public termbase 4622 Entries after the r7
create-mode install. Depth replaces 123 existing entries in place, so
post-install must STILL be exactly 4622 Entries — same ids, updated
bytes, and the build terms/ tree must hold the NEW entry shas (the
pre-install baselines were pinned in the manifest as
termsBaselineSha256 and re-verified by the publisher at install time).

Checks (all must pass, zero problems):
  1. install receipt: hardPass, cohort fresh10k-r7-depth, manifest
     sha bound, 123 products
  2. public termbase: 4622 Entries (unchanged count); every depth id
     present with canonical entry sha == manifest entrySha256 (the NEW
     depth sha); no duplicate Ids
  3. legacy/index/shard parity mirrors the publisher's own law
  4. build terms/: the 123 dirs exist with entry sha == NEW
     entrySha256 + WORK sha + STATUS "done"
  5. clone footprint: only the termbase surface files changed (git status)
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1]
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
EXPECTED_ENTRIES = 4622
EXPECTED_REPLACED = 123

manifest = json.loads(
    (BUILD / "maintenance" / "fresh10k-r7-depth-generic-manifest.json")
    .read_text(encoding="utf-8-sig"))
receipt = json.loads(
    (BUILD / "maintenance" / "fresh10k-r7-depth-generic-install-receipt.json")
    .read_text(encoding="utf-8-sig"))
msha = hashlib.sha256(
    (BUILD / "maintenance" / "fresh10k-r7-depth-generic-manifest.json")
    .read_bytes()).hexdigest()
products = {p["id"]: p["entrySha256"] for p in manifest["products"]}
baselines = {p["id"]: p["termsBaselineSha256"] for p in manifest["products"]}
if any(baselines[p] == products[p] for p in products):
    raise SystemExit("a depth product sha equals its own baseline — "
                     "entry not actually changed")

problems: list[str] = []

# 1. receipt
if not receipt.get("hardPass"):
    problems.append("install receipt hardPass is not true")
if receipt.get("cohort") != "fresh10k-r7-depth":
    problems.append(f"receipt cohort {receipt.get('cohort')!r}")
if receipt.get("manifestSha256") != msha:
    problems.append("receipt manifestSha256 != current manifest sha")
if len(receipt.get("products") or {}) != EXPECTED_REPLACED:
    problems.append(f"receipt products {len(receipt.get('products') or {})}")

# 2. public termbase
def canon_sha(v: dict) -> str:
    body = json.dumps(v, ensure_ascii=False, indent=2) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

public = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
entries = public["Entries"]
if len(entries) != EXPECTED_ENTRIES:
    problems.append(f"public Entries {len(entries)} != {EXPECTED_ENTRIES} "
                    f"(replace must not change the count)")
by_id = {e["Id"]: e for e in entries}
if len(by_id) != len(entries):
    problems.append("duplicate Ids in public termbase")
for pid, want in products.items():
    e = by_id.get(pid)
    if e is None:
        problems.append(f"{pid} missing from public termbase")
    elif canon_sha(e) != want:
        problems.append(f"{pid} canonical sha mismatch vs manifest")

# 3. legacy/index/shard parity
legacy = json.loads((CLONE / "termbase.json").read_text(encoding="utf-8"))
index = json.loads((CLONE / "termbase.index.json").read_text(encoding="utf-8"))
shards = []
for p in sorted((CLONE / "termbase").glob("*.json")):
    shards.extend(json.loads(p.read_text(encoding="utf-8"))["Entries"])
shard_by_id = {r["Id"]: r for r in shards if isinstance(r, dict) and r.get("Id")}
expected_index = [
    [r["SourceTerm"],
     next((s.get("PreferredTarget", "") for s in r.get("Senses", [])
           if s.get("SenseKey") is None),
          (r.get("Senses") or [{}])[0].get("PreferredTarget", ""))]
    for r in entries]
expected_legacy = [[r["SourceTerm"], expected_index[i][1]]
                   for i, r in enumerate(entries)]
actual_legacy = [[r.get("SourceTerm"), r.get("PreferredTarget", "")]
                 for r in legacy]
if not (len(entries) == len(legacy) == len(index["Terms"]) == len(shards)):
    problems.append(f"count parity: entries={len(entries)} legacy={len(legacy)} "
                    f"index={len(index['Terms'])} shards={len(shards)}")
if shard_by_id != by_id:
    problems.append("shard/rich entry maps differ")
if index["Terms"] != expected_index:
    problems.append("index rows diverge from rich entries")
if actual_legacy != expected_legacy:
    problems.append("legacy rows diverge from rich entries")

# 4. build terms/ (dirs pre-existed; bytes must now be the NEW products)
terms = BUILD / "terms"
missing = [pid for pid in products if not (terms / pid / "entry.v2.json").is_file()]
if missing:
    problems.append(f"{len(missing)} terms dirs missing entry.v2.json: {missing[:5]}")
for p in manifest["products"]:
    d = terms / p["id"]
    if not d.is_dir():
        continue
    for name, key in (("entry.v2.json", "entrySha256"), ("WORK.md", "workSha256")):
        got = hashlib.sha256((d / name).read_bytes()).hexdigest()
        if got != p[key]:
            problems.append(f"{p['id']}/{name} sha mismatch (post-install "
                            f"terms tree must hold the NEW product bytes)")
    status = (d / "STATUS").read_text(encoding="utf-8-sig").strip()
    if status != "done":
        problems.append(f"{p['id']}/STATUS {status!r}")

# 5. clone footprint
status_out = subprocess.run(
    ["git", "-C", str(CLONE), "status", "--porcelain"],
    capture_output=True, text=True).stdout.splitlines()
status_out = [line for line in status_out if line.strip()]
allowed = re.compile(
    r"^(termbase\.v2\.json|termbase\.json|termbase\.index\.json"
    r"|termbase/[^/]+\.json)$")
unexpected = []
for line in status_out:
    path = line[3:].strip('"').replace("\\", "/")
    if not allowed.match(path):
        unexpected.append(line)
if unexpected:
    problems.append(
        f"clone footprint has non-termbase changes: {unexpected[:5]}")

print(json.dumps({
    "ok": not problems,
    "publicEntries": len(entries),
    "depthReplaced": sum(1 for pid in products if canon_sha(by_id.get(pid, {})) == products[pid]),
    "termsDirs": sum(1 for pid in products if (terms / pid).is_dir()),
    "cloneChangedFiles": len(status_out),
    "problems": problems,
}, ensure_ascii=False, indent=2))
