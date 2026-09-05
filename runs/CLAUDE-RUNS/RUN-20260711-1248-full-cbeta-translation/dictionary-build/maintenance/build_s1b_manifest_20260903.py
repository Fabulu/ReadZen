#!/usr/bin/env python3
"""Build the lane S1-b/R publication manifest (anchor removal, 53 products).

Preconditions enforced before writing anything:
  - blind round r1 adjudication PASS with zero missed plants, zero
    confirmed findings
  - gates CLEAN (s1b-gates-20260903.json)
  - engine receipt applied with the frozen class counts (112 records)
  - clone clean at pinned HEAD 5f0e127
  - per-product staging: entry.v2.json == terms bytes AND ==
    canon(engine(clone)) (confinement re-verified at manifest time)
  - blind rows (plants included via payload binding) all carry entry in
    the 53-product worklist

Template: A1 (multi-product replace mode). No adds, no withdrawals: 53
replace-mode products; the public surface regenerates rows for the
touched ids only.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
COHORT = "s1b-20260903"
LANE = ROOT / "fresh-build" / COHORT
BUILD_ROOT_POSIX = ("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/"
                    "runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation"
                    "/dictionary-build")
REPO_ROOT_POSIX = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator"
CLONE_HEAD_PIN = "5f0e127"
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")

EXPECTED_COUNTS = {"anchor-remove-dup": 112}


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wsl(p: Path) -> str:
    out = subprocess.run(
        ["wsl.exe", "wslpath", "-a", str(p.resolve()).replace("\\", "/")],
        capture_output=True, text=True).stdout.strip()
    if not out.startswith("/mnt/"):
        raise SystemExit(f"wslpath failed for {p}: {out}")
    if out.startswith("/mnt/c/Programmieren/"):
        out = "/mnt/c/programmieren/" + out[len("/mnt/c/Programmieren/"):]
    return out


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


adj = load("maintenance/s1b-blind-r1-adjudication-20260903.json")
gates = load("maintenance/s1b-gates-20260903.json")

if adj.get("verdict") != "PASS":
    raise SystemExit(f"r1 adjudication not PASS: {adj.get('verdict')}")
if adj.get("canaries", {}).get("misses"):
    raise SystemExit(f"round VOID: missed plants {adj['canaries']['misses']}")
if adj.get("confirmedFindings"):
    raise SystemExit(f"blocking findings survive: {adj['confirmedFindings'][:3]}")
if gates["verdict"] != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates['problems'][:3]}")

receipt = load("maintenance/s1b-edit-receipt-20260903.json")
if receipt["schemaVersion"] != "s1b-edit-receipt":
    raise SystemExit(f"engine receipt schema {receipt['schemaVersion']}")
if not receipt["applied"]:
    raise SystemExit("engine receipt not applied")
if receipt["editClassCounts"] != EXPECTED_COUNTS:
    raise SystemExit(f"engine class counts {receipt['editClassCounts']}")
if len(receipt.get("editRecords", [])) != 112:
    raise SystemExit(f"engine edit records {len(receipt.get('editRecords', []))}"
                     " != 112")

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
status = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                        capture_output=True, text=True).stdout.splitlines()
if status:
    raise SystemExit(f"clone tree dirty at manifest time: {status[:5]}")
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD moved: {head[:7]} != {CLONE_HEAD_PIN}")

_spec = importlib.util.spec_from_file_location(
    "_s1b", HERE / "s1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

by_id = eng.clone_state()
worklist = eng.derive(by_id)[0]
if len(worklist) != 53:
    raise SystemExit(f"derived worklist {len(worklist)} != 53")
if receipt["products"] != worklist:
    raise SystemExit("engine receipt products != derived worklist")
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, _records = eng.transform(snapshot)

rows_doc = load("maintenance/s1b-blind-r1-rows-20260903.json")
plants_doc = load("maintenance/s1b-blind-r1-plants-20260903.json")
wl_set = set(worklist)
if not {r["entry"] for r in rows_doc["rows"]} <= wl_set:
    raise SystemExit("blind rows escape the worklist")

records_by_entry: dict[str, list[dict]] = {eid: [] for eid in worklist}
for r in receipt["editRecords"]:
    records_by_entry[r["entry"]].append(r)

products = []
for eid in worklist:
    terms_p = ROOT / "terms" / eid / "entry.v2.json"
    terms_text = terms_p.read_text(encoding="utf-8")
    if terms_text != out[eid]:
        raise SystemExit(f"manifest-time confinement failed: {eid}")
    entry_sha = hashlib.sha256(terms_text.encode("utf-8")).hexdigest()
    if receipt["entryShas"][eid] != entry_sha:
        raise SystemExit(f"receipt sha drift: {eid}")
    before_sha = hashlib.sha256(eng.canon(by_id[eid]).encode("utf-8")
                                ).hexdigest()

    per_class: dict[str, int] = {}
    for r in records_by_entry[eid]:
        per_class[r["class"]] = per_class.get(r["class"], 0) + 1
    if not per_class:
        raise SystemExit(f"{eid}: product with no engine edits")

    src = ROOT / "fresh-build" / "entries" / eid / COHORT
    src.mkdir(parents=True, exist_ok=True)
    payload_no_id = dict(json.loads(terms_text))
    payload_no_id.pop("Id", None)
    (src / "entry.v2.json").write_text(terms_text, encoding="utf-8", newline="")
    (src / "evidence.draft.json").write_text(
        json.dumps({
            "schemaVersion": f"{COHORT}.worksheet.v1",
            "task": ("Verify the S1-b/R anchor removals per "
                     "SPEC_S1b_20260903.md + AMENDMENTS 1-2 (112 duplicate "
                     "ClaimAnchor removals over 53 entries, re-derived from "
                     "the clone bytes under the frozen census laws: every "
                     "removed anchor failed a structure kind, its Kwic is "
                     "covered by a surviving same-sense occurrence, senses "
                     "whose anchors were all removed carry no ClaimAnchors "
                     "key, and the simulated post state anchors every "
                     "Chinese string the Explanation/Note quotes) and that "
                     "nothing else changed (proven by engine(clone pre-state "
                     f"@{CLONE_HEAD_PIN}) == these bytes; gates CLEAN incl. "
                     "fleet 3057->2993 failing pairs with zero newly-failing; "
                     "blind r1 with 7 payload-bound canaries)."),
            "repairs": [{"class": c, "count": n}
                        for c, n in sorted(per_class.items(),
                                           key=lambda kv: -kv[1])],
            "entry": payload_no_id,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")

    work_src = ROOT / "terms" / eid / "WORK.md"
    cls_line = ", ".join(f"{c} x{n}" for c, n in
                         sorted(per_class.items(), key=lambda kv: -kv[1]))
    s1b_line = (f"\n- {COHORT}: S1-b/R anchor removals per "
                f"SPEC_S1b_20260903.md + AMENDMENTS 1-2 ({cls_line})\n")
    work_text = (work_src.read_text(encoding="utf-8")
                 if work_src.exists() else "")
    work_text = re.sub(rf"\n*- {COHORT}: S1-b/R anchor removals[^\n]*\n?", "",
                       work_text).rstrip("\n")
    (src / "WORK.md").write_text(work_text + s1b_line, encoding="utf-8",
                                 newline="")

    products.append({
        "id": eid,
        "sourceDir": f"fresh-build/entries/{eid}/{COHORT}",
        "entrySha256": entry_sha,
        "worksheetSha256": sha(src / "evidence.draft.json"),
        "workSha256": sha(src / "WORK.md"),
        "termsMode": "replace",
        "termsBaselineSha256": entry_sha,
        "beforeSha256": before_sha,
    })

now = datetime.now(timezone.utc).isoformat()
n_plants = len(plants_doc["registry"])
n_honest = plants_doc["honestRows"]

bound_review = {
    "schemaVersion": f"{COHORT}-bound-review.v1",
    "cohort": COHORT,
    "verdict": "PASS",
    "reviewer": (
        f"Blind independent review with planted canaries. Round r1 (fresh "
        f"reviewers, first product bytes): {len(rows_doc['rows'])} rows — "
        f"{n_honest} real rows (112 duplicate-ClaimAnchor removals: each "
        f"row carries the removed anchor's full ClaimText + Kwic, the post "
        f"occurrences covering that Kwic, and the sense's post anchor "
        f"shape — all verified against frozen pre/post materials with "
        f"sha-pinned inputs) and {n_plants} planted canaries bound by "
        f"payload identity (rowSha over the full row bytes): "
        f"{n_plants}/{n_plants} caught by EVERY reviewer (coverage law: "
        f"any miss voids the round). Non-plant flags byte-adjudicated "
        f"against the engine+materials oracle. 100% of the 53 products "
        f"are machine-verified: engine state-driven confinement "
        f"(engine(clone@{CLONE_HEAD_PIN}) == these bytes, re-verified at "
        f"manifest time), attribution+depth gates, removal coverage, "
        f"determinism, path-scope byte-diff, exactly-53 terms-tree "
        f"change, fleet regression 3057->2993 failing pairs with zero "
        f"newly-failing. Dictionary edits local-only (agent clone, "
        f"contrib branch); no push."),
    "boundProducts": [{"id": eid, "sha256": p["entrySha256"],
                       "coveredBy": "engine-confinement+gates+fleet-"
                                    "regression; blind-r1-full-row-coverage"}
                      for eid, p in zip(worklist, products)],
}
bound_path = LANE / "cohort-bound-review.json"
LANE.mkdir(parents=True, exist_ok=True)
bound_path.write_bytes(canonical(bound_review))

authority = {
    "schemaVersion": "generic-dictionary-final-release-authority.v1",
    "cohort": COHORT,
    "authorizedBy": "coordinator (Claude)",
    "authorizedUtc": now,
    "releaseAuthorized": True,
    "basis": (
        f"Lane S1-b/R (ClaimAnchor defect removal cohort R, "
        f"SPEC_S1b_20260903.md + AMENDMENTS 1-2): 112 edit records over 53 "
        f"entries — every removed anchor failed an anchor-structure kind, "
        f"was a standalone duplicate (Kwic contained in a same-sense "
        f"occurrence's Kwic), and every fleet failure row on the entry sat "
        f"on an anchor the lane removes; senses whose anchors were all "
        f"removed carry no ClaimAnchors key at all. Machine gates CLEAN: "
        f"zero attribution failure rows on the 53; depth stable; removal "
        f"coverage; determinism; confinement; path-scope byte-diff "
        f"confined to Senses[i].ClaimAnchors; exactly the 53 of 4,504 "
        f"terms entries changed; fleet 3,057 -> 2,993 failing pairs, zero "
        f"newly-failing, 64 resolved. Blind r1 PASS with "
        f"{n_plants}/{n_plants} canaries caught by every reviewer and "
        f"zero confirmed findings. Public surface: replace-mode for the "
        f"53 ids; no adds, no withdrawals; entry count unchanged. "
        f"Dictionary edits local-only (agent clone, contrib branch); no "
        f"push."),
    "products": [{"id": eid, "entrySha256": p["entrySha256"]}
                 for eid, p in zip(worklist, products)],
    "builtOn": {},
    "withdrawn": [],
}
authority_path = ROOT / "maintenance" / f"{COHORT}-final-release-authority.json"
authority_path.write_bytes(canonical(authority))

roster_win = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
                  r"\Assets\Data\lineage-masters.json")
node_script_win = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
                       r"\eng\tools\merge-dict-entries.js")

rows_file = ROOT / "maintenance" / "s1b-blind-r1-rows-20260903.json"
review_artifacts = [{
    "round": "r1", "path": wsl(rows_file), "sha256": sha(rows_file),
    "canaryKeySha256": sha(ROOT / "maintenance" /
                           "s1b-blind-r1-plants-20260903.json"),
}]
for n in (1, 2):
    v = (ROOT / "subagents" / f"20260903-s1b-blind-r1-reviewer-{n}"
         / "verdicts.json")
    if not v.exists():
        raise SystemExit(f"missing {v}")
    review_artifacts.append({
        "round": f"r1-reviewer{n}", "path": wsl(v), "sha256": sha(v),
    })

receipt_rows = {}
for name, note in (
    ("s1b-edit-receipt-20260903.json",
     "engine receipt: 53 products, 112 edit records (frozen class counts), "
     "determinism + path-scope asserts, applied"),
    ("s1b-gates-20260903.json",
     "gates CLEAN: zero attribution rows on the 53; depth PRE/POST stable; "
     "removal coverage; determinism + confinement; path-scope byte-diff; "
     "exactly-53 terms-tree change; fleet 3057->2993 with zero "
     "newly-failing"),
    ("s1b_transform_20260903.py",
     "the removal engine: clone-pre-state confinement, mechanical "
     "re-derivation asserted against the frozen census, identity-bytes "
     "asserts at apply time, path-scope escape assert"),
    ("s1b-anchor-census-20260903.json",
     "frozen census worksheet: universe classification (222 entries / 660 "
     "failing anchors -> 391 dup / 83 pointer / 186 rebuild) and the "
     "eligibility law that selects cohort R (53 entries, 112 removals)"),
    ("probe_s1b_census_20260903.py",
     "census probe: merged-index row decoding, per-anchor action "
     "classification, post-state dangling simulation, cohort eligibility"),
    ("probe_s1b_pre_apply_20260903.py",
     "pre-apply snapshot probe: clone pin + clean, full terms-tree sha "
     "snapshot, materialized POST state under the REAL audits "
     "(attribution + depth) before any write"),
    ("s1b-pre-terms-shas-20260903.json",
     "full terms-tree sha snapshot (4,504 entries) the off-worklist "
     "protection gate re-hashes against"),
    ("build_s1b_blind_r1_20260903.py",
     "blind rows builder: 112 honest rows re-derived from clone via the "
     "engine + frozen pre/post materials; 7 payload-bound canaries at "
     "fixed-stride slots"),
    ("s1b_adjudicate_blind_r1_20260903.py",
     "binding machine adjudicator (r1): oracle rebuild, canary coverage "
     "law, honest-flag byte-adjudication"),
    ("s1b-blind-r1-adjudication-20260903.json",
     f"binding machine adjudication (r1): canaries {n_plants}/{n_plants} "
     f"with zero coverage misses across every reviewer, zero confirmed "
     f"findings — PASS"),
    ("s1b-blind-r1-plants-20260903.json",
     f"canary key (adjudicator-only): {n_plants} planted defects "
     f"payload-bound (rowSha)"),
    ("SPEC_S1b_20260903.md",
     "lane SPEC + AMENDMENTS 1-2 (cohort figures corrected; "
     "surviving-anchor eligibility law)"),
):
    p = ROOT / "maintenance" / name
    if not p.exists():
        raise SystemExit(f"missing receipt artifact {name}")
    receipt_rows[name] = {"path": wsl(p), "sha256": sha(p), "note": note}

manifest = {
    "schemaVersion": "generic-dictionary-publication-manifest.v1",
    "cohort": COHORT,
    "buildRoot": BUILD_ROOT_POSIX,
    "termsRoot": "terms",
    "publicRoot": wsl(CLONE),
    "stageRoot": f"fresh-build/{COHORT}/publication-stage",
    "installReceipt": f"maintenance/{COHORT}-generic-install-receipt.json",
    "authority": {"path": wsl(authority_path), "sha256": sha(authority_path)},
    "reviews": [{"path": wsl(bound_path), "sha256": sha(bound_path)}],
    "reviewArtifacts": review_artifacts,
    "receipts": receipt_rows,
    "products": products,
    "withdrawn": [],
    "roster": {"path": wsl(roster_win), "sha256": sha(roster_win)},
    "node": {
        "windowsNodeExe": "/mnt/c/Program Files/nodejs/node.exe",
        "script": {"path": wsl(node_script_win), "sha256": sha(node_script_win)},
        "cwd": REPO_ROOT_POSIX,
        "status": f"{COHORT}-ready",
    },
    "integrityCommand": "",
    "extraSurfaces": {
        "note": ("replace-only lane: 53 products in replace mode, no adds, "
                 "no withdrawals; termbase.v2.json keeps its entry count "
                 "and the touched ids' rows regenerate; index/shard rows "
                 "for the touched ids update as the publisher regenerates "
                 "the surface; git footprint = termbase files + terms/ "
                 f"dirs only. Products are clone-backed at {CLONE_HEAD_PIN}. "
                 "node.script.sha256 is the working-tree js (carries R1a's "
                 "uncommitted byTermThenId tie-break + C1's "
                 "ID_REPLACEMENTS entry, unchanged this lane)."),
    },
}
manifest_path = ROOT / "maintenance" / f"{COHORT}-generic-manifest.json"
manifest_path.write_bytes(canonical(manifest))

print(json.dumps({"products": len(products),
                  "cloneHead": head[:7],
                  "nodeScriptSha256": manifest["node"]["script"]["sha256"][:16],
                  "manifest": str(manifest_path),
                  "manifestSha256": sha(manifest_path)}, indent=2))
