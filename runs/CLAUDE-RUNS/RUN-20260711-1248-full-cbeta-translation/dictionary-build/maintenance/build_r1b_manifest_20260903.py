#!/usr/bin/env python3
"""Build the lane R1b publication manifest (retired-source removal, 43 products).

Preconditions enforced before writing anything:
  - blind round r1 adjudication PASS with zero missed plants, zero
    confirmed findings
  - gates CLEAN (r1b-gates-20260903.json)
  - engine receipt applied with the frozen class counts (47 records:
    46 occ-remove-retired + 1 note-count-rewrite)
  - clone clean at pinned HEAD 87a6975
  - per-product staging: entry.v2.json == terms bytes AND ==
    canon(engine(clone)) (confinement re-verified at manifest time)
  - blind rows (plants included via payload binding) all carry entry in
    the 43-product worklist

Template: A1/S1-b (multi-product replace mode). No adds, no
withdrawals: 43 replace-mode products; the public surface regenerates
rows for the touched ids only.
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
COHORT = "r1b-20260903"
LANE = ROOT / "fresh-build" / COHORT
BUILD_ROOT_POSIX = ("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/"
                    "runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation"
                    "/dictionary-build")
REPO_ROOT_POSIX = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator"
CLONE_HEAD_PIN = "87a6975"
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")

EXPECTED_COUNTS = {"occ-remove-retired": 46, "note-count-rewrite": 1}


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


adj = load("maintenance/r1b-blind-r1-adjudication-20260903.json")
gates = load("maintenance/r1b-gates-20260903.json")

if adj.get("verdict") != "PASS":
    raise SystemExit(f"r1 adjudication not PASS: {adj.get('verdict')}")
if adj.get("canaries", {}).get("misses"):
    raise SystemExit(f"round VOID: missed plants {adj['canaries']['misses']}")
if adj.get("confirmedFindings"):
    raise SystemExit(f"blocking findings survive: {adj['confirmedFindings'][:3]}")
if gates["verdict"] != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates['problems'][:3]}")

receipt = load("maintenance/r1b-edit-receipt-20260903.json")
if receipt["schemaVersion"] != "r1b-edit-receipt":
    raise SystemExit(f"engine receipt schema {receipt['schemaVersion']}")
if not receipt["applied"]:
    raise SystemExit("engine receipt not applied")
if receipt["editClassCounts"] != EXPECTED_COUNTS:
    raise SystemExit(f"engine class counts {receipt['editClassCounts']}")
if len(receipt.get("editRecords", [])) != 47:
    raise SystemExit(f"engine edit records {len(receipt.get('editRecords', []))}"
                     " != 47")

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
status = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                        capture_output=True, text=True).stdout.splitlines()
if status:
    raise SystemExit(f"clone tree dirty at manifest time: {status[:5]}")
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD moved: {head[:7]} != {CLONE_HEAD_PIN}")

_spec = importlib.util.spec_from_file_location(
    "_r1b", HERE / "r1b_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

by_id = eng.clone_state()
worklist = eng.derive(by_id)[0]
if len(worklist) != 43:
    raise SystemExit(f"derived worklist {len(worklist)} != 43")
if receipt["products"] != worklist:
    raise SystemExit("engine receipt products != derived worklist")
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, _records = eng.transform(snapshot)

rows_doc = load("maintenance/r1b-blind-r1-rows-20260903.json")
plants_doc = load("maintenance/r1b-blind-r1-plants-20260903.json")
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
            "task": ("Verify the R1b retired-source occurrence removals per "
                     "SPEC_R1b_20260903.md + AMENDMENTS 1-2 (USER-APPROVED "
                     "Option A: 46 occurrences citing the retired rels "
                     "T/T48/T48n2023.xml + X/X63/X63n1245.xml removed over 43 "
                     "entries + the one t_50d75aeeeef1 count-sentence rewrite "
                     "to survivor arithmetic — re-derived from the clone bytes "
                     "under the frozen laws: every removed occurrence's "
                     "RelPath is one of the two retired rels, no sense "
                     "empties, every CJK string of every affected sense's "
                     "Explanation/Note stays anchored over surviving kwics "
                     "(2 prose-dangle entries BLOCKED and untouched), the "
                     "count sentence rewritten with find-once law) and that "
                     "nothing else changed (proven by engine(clone pre-state "
                     f"@{CLONE_HEAD_PIN}) == these bytes; gates CLEAN incl. "
                     "depth movement == the frozen 3-kind set (46 kwa + 44 "
                     "source clears, 20 below-floor surfaces, 0 hardPass "
                     "regressions) and fleet 2993->2993 failing pairs with "
                     "zero newly-failing; blind r1 with 7 payload-bound "
                     "canaries)."),
            "repairs": [{"class": c, "count": n}
                        for c, n in sorted(per_class.items(),
                                           key=lambda kv: -kv[1])],
            "entry": payload_no_id,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")

    work_src = ROOT / "terms" / eid / "WORK.md"
    cls_line = ", ".join(f"{c} x{n}" for c, n in
                         sorted(per_class.items(), key=lambda kv: -kv[1]))
    r1b_line = (f"\n- {COHORT}: R1b retired-source removals per "
                f"SPEC_R1b_20260903.md + AMENDMENTS 1-2 ({cls_line})\n")
    work_text = (work_src.read_text(encoding="utf-8")
                 if work_src.exists() else "")
    work_text = re.sub(rf"\n*- {COHORT}: R1b retired-source removals[^\n]*\n?", "",
                       work_text).rstrip("\n")
    (src / "WORK.md").write_text(work_text + r1b_line, encoding="utf-8",
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
        f"{n_honest} real rows (46 retired-source occurrence removals — each "
        f"row carries the removed occurrence's relPath + full Kwic + "
        f"masterName at (si,oi) in the pre materials and the sense's post "
        f"occurrence rel list — plus the 1 note count-sentence rewrite with "
        f"its live survivor arithmetic; all verified against frozen pre/post "
        f"materials with sha-pinned inputs) and {n_plants} planted canaries "
        f"bound by payload identity (rowSha over the full row bytes): "
        f"{n_plants}/{n_plants} caught by EVERY reviewer (coverage law: "
        f"any miss voids the round). Non-plant flags byte-adjudicated "
        f"against the engine+materials oracle. 100% of the 43 products "
        f"are machine-verified: engine state-driven confinement "
        f"(engine(clone@{CLONE_HEAD_PIN}) == these bytes, re-verified at "
        f"manifest time), attribution+depth gates (POST attribution: "
        f"zero rows on 42, exactly the 2 documented pre-existing 坐堂 "
        f"performer residuals; depth movement == the frozen 3-kind set: "
        f"46 invalid-kwic-anchor + 44 source-not-in-corpus-manifest "
        f"cleared, below-frequency-floor surfaced on exactly 20, 0 "
        f"hardPass regressions, 23 improved), removal coverage, "
        f"determinism, path-scope byte-diff confined to "
        f"Senses[i].Occurrences + the one rewritten Senses[0].Note, "
        f"exactly-43 terms-tree change, fleet regression 2993->2993 "
        f"failing pairs with zero newly-failing. Dictionary edits "
        f"local-only (agent clone, contrib branch); no push."),
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
        f"Lane R1b (retired-source occurrence fleet removal — USER-APPROVED "
        f"Option A, SPEC_R1b_20260903.md + AMENDMENTS 1-2): 47 edit records "
        f"over 43 entries — 46 occurrences citing the retired rels "
        f"T/T48/T48n2023.xml / X/X63/X63n1245.xml removed (every removed "
        f"row's RelPath byte-asserted at apply time; no sense emptied; "
        f"prose-anchoring gate BLOCKED the 2 entries whose Explanations rest "
        f"on retired evidence — t_057cc9ea8755, t_ea2a427c7aba — left "
        f"untouched for an authored decision) + the 1 t_50d75aeeeef1 count "
        f"sentence rewritten to survivor arithmetic. Machine gates CLEAN: "
        f"POST attribution zero rows on 42 entries, exactly the 2 documented "
        f"pre-existing 坐堂 performer residuals; depth movement == the frozen "
        f"3-kind set (46+44 clears, 20 below-floor surfaces, 0 hardPass "
        f"regressions, 23 improved); removal coverage; determinism; "
        f"confinement; path-scope byte-diff; exactly the 43 of 4,504 terms "
        f"entries changed; fleet 2,993 -> 2,993 failing pairs, zero "
        f"newly-failing. Blind r1 PASS with {n_plants}/{n_plants} canaries "
        f"caught by every reviewer and zero confirmed findings. Public "
        f"surface: replace-mode for the 43 ids; no adds, no withdrawals; "
        f"entry count unchanged. Dictionary edits local-only (agent clone, "
        f"contrib branch); no push."),
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

rows_file = ROOT / "maintenance" / "r1b-blind-r1-rows-20260903.json"
review_artifacts = [{
    "round": "r1", "path": wsl(rows_file), "sha256": sha(rows_file),
    "canaryKeySha256": sha(ROOT / "maintenance" /
                           "r1b-blind-r1-plants-20260903.json"),
}]
for n in (1, 2):
    v = (ROOT / "maintenance" / "subagents"
         / f"20260903-r1b-blind-r1-reviewer-{n}" / "verdicts.json")
    if not v.exists():
        raise SystemExit(f"missing {v}")
    review_artifacts.append({
        "round": f"r1-reviewer{n}", "path": wsl(v), "sha256": sha(v),
    })

receipt_rows = {}
for name, note in (
    ("r1b-edit-receipt-20260903.json",
     "engine receipt: 43 products, 47 edit records (frozen class counts), "
     "determinism + path-scope asserts, applied"),
    ("r1b-gates-20260903.json",
     "gates CLEAN: attribution zero rows on 42 + exactly the 2 documented "
     "坐堂 residuals; depth movement == frozen 3-kind set (46+44 clears, 20 "
     "below-floor, 0 regressions, 23 improved); removal coverage; "
     "determinism + confinement; path-scope byte-diff; exactly-43 "
     "terms-tree change; fleet 2993->2993 with zero newly-failing"),
    ("r1b_transform_20260903.py",
     "the removal engine: clone-pre-state confinement, mechanical "
     "re-derivation asserted against the frozen census (cohort + counts), "
     "prose-anchoring gate, identity-bytes asserts at apply time, "
     "path-scope escape assert"),
    ("r1b-census-20260903.json",
     "frozen census worksheet (re-derived at 87a6975): 45 entries / 49 "
     "occurrences all-affected; prose gate blocks 2; cohort 43 / 46 "
     "removals; floor + residual-row + overlap facts"),
    ("probe_r1b_census_20260903.py",
     "census probe: retired-rel occurrence census, prose-dangle gate, "
     "floor consequences, shift hazards, SourceTexts, attribution rows"),
    ("probe_r1b_pre_apply_20260903.py",
     "pre-apply snapshot probe: clone pin + clean, full terms-tree sha "
     "snapshot, materialized POST state under the REAL audits "
     "(attribution + depth) before any write"),
    ("r1b-pre-terms-shas-20260903.json",
     "full terms-tree sha snapshot (4,504 entries) the off-worklist "
     "protection gate re-hashes against"),
    ("build_r1b_blind_r1_20260903.py",
     "blind rows builder: 47 honest rows re-derived from clone via the "
     "engine + frozen pre/post materials; 7 payload-bound canaries at "
     "fixed-stride slots"),
    ("r1b_adjudicate_blind_r1_20260903.py",
     "binding machine adjudicator (r1): oracle rebuild, canary coverage "
     "law, honest-flag byte-adjudication (flags-based reviewer schema, "
     "disclosed)"),
    ("r1b-blind-r1-adjudication-20260903.json",
     f"binding machine adjudication (r1): canaries {n_plants}/{n_plants} "
     f"with zero coverage misses across every reviewer, zero confirmed "
     f"findings — PASS"),
    ("r1b-blind-r1-plants-20260903.json",
     f"canary key (adjudicator-only): {n_plants} planted defects "
     "payload-bound (rowSha)"),
    ("SPEC_R1b_20260903.md",
     "lane SPEC + AMENDMENTS 1-2 (user decision authority; prose-gate "
     "blocked pair disclosed; depth law corrected to the real audit)"),
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
        "note": ("replace-only lane: 43 products in replace mode, no adds, "
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
