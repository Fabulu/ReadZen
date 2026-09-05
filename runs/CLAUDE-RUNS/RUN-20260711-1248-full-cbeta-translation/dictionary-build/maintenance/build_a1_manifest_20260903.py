#!/usr/bin/env python3
"""Build the lane A1 publication manifest (attribution repair, 35 products).

Preconditions enforced before writing anything:
  - blind round r1 adjudication PASS with zero missed plants, zero
    confirmed findings
  - gates CLEAN (a1-gates-20260903.json)
  - engine receipt applied with the frozen class counts (116 records)
  - clone clean at pinned HEAD 20c9011
  - per-product staging: entry.v2.json == terms bytes AND ==
    canon(engine(clone)) (confinement re-verified at manifest time)
  - blind rows (plants included via payload binding) all carry entry in
    the 35-product worklist

Template: Q3 (multi-product replace mode) with C1's bound-review/
authority structure. No adds, no withdrawals: 35 replace-mode products;
the public surface regenerates rows for the touched ids only.
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
COHORT = "a1-20260903"
LANE = ROOT / "fresh-build" / COHORT
BUILD_ROOT_POSIX = ("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/"
                    "runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation"
                    "/dictionary-build")
REPO_ROOT_POSIX = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator"
CLONE_HEAD_PIN = "20c9011"
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")

EXPECTED_COUNTS = {
    "muc-utterer": 83, "muc-verse-author": 8, "vague-reword": 17,
    "dangling-anchor": 1, "performer-context-row": 2,
    "performer-grammar-proof": 1, "anon-monk-restructure": 1,
    "grammar-evidence-repeat": 1, "reviewed-fields": 1, "anchor-remove": 1,
}


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


adj = load("maintenance/a1-blind-r1-adjudication-20260903.json")
gates = load("maintenance/a1-gates-20260903.json")

if adj.get("verdict") != "PASS":
    raise SystemExit(f"r1 adjudication not PASS: {adj.get('verdict')}")
if adj.get("canaries", {}).get("misses"):
    raise SystemExit(f"round VOID: missed plants {adj['canaries']['misses']}")
if adj.get("confirmedFindings"):
    raise SystemExit(f"blocking findings survive: {adj['confirmedFindings'][:3]}")
if gates["verdict"] != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates['problems'][:3]}")

receipt = load("maintenance/a1-edit-receipt-20260903.json")
if receipt["schemaVersion"] != "a1-edit-receipt":
    raise SystemExit(f"engine receipt schema {receipt['schemaVersion']}")
if not receipt["applied"]:
    raise SystemExit("engine receipt not applied")
if receipt["editClassCounts"] != EXPECTED_COUNTS:
    raise SystemExit(f"engine class counts {receipt['editClassCounts']}")
if len(receipt.get("editRecords", [])) != 116:
    raise SystemExit(f"engine edit records {len(receipt.get('editRecords', []))}"
                     " != 116")

worklist = load("maintenance/a1-worklist-details-20260902.json")["worklist"]
if receipt["products"] != worklist or len(worklist) != 35:
    raise SystemExit("engine receipt products != 35-entry worklist")

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
status = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                        capture_output=True, text=True).stdout.splitlines()
if status:
    raise SystemExit(f"clone tree dirty at manifest time: {status[:5]}")
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD moved: {head[:7]} != {CLONE_HEAD_PIN}")

_spec = importlib.util.spec_from_file_location(
    "_a1", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

by_id = eng.clone_state()
eng.clone_snapshot.clear()
eng.clone_snapshot.update({eid: copy.deepcopy(by_id[eid]) for eid in worklist})
out, _records = eng.transform(by_id)

rows_doc = load("maintenance/a1-blind-r1-rows-20260903.json")
plants_doc = load("maintenance/a1-blind-r1-plants-20260903.json")
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

    per_class: dict[str, int] = {}
    for r in records_by_entry[eid]:
        c = "muc-context-row" if r["class"].startswith("muc-") else r["class"]
        per_class[c] = per_class.get(c, 0) + 1
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
            "task": ("Verify the A1 attribution repairs per "
                     "SPEC_A1_20260902.md + AMENDMENTS 1-3 (91 mechanical "
                     "missing_utterer_context rows re-derived from the clone "
                     "bytes under the frozen VERSE_RE note law; 17 vague-"
                     "attributor prose rewords with the no-added-claim law; "
                     "the dangling-Chinese anchor for t_057cc9ea8755 with "
                     "headword-free ClaimText; 2 performer rows + 1 grammar-"
                     "proof sentence; the 僧問 anon-monk restructure; the "
                     "survivor GrammarEvidence label repeat + ReviewedBy/"
                     "ReviewedUtc; the duplicate-anchor removal on "
                     "t_2e77bc793d0c) and that nothing else changed (proven "
                     f"by engine(clone pre-state @{CLONE_HEAD_PIN}) == these "
                     "bytes; gates CLEAN incl. fleet 3099->3057 failing "
                     "pairs with zero newly-failing; blind r1 with 7 "
                     "payload-bound canaries)."),
            "repairs": [{"class": c, "count": n}
                        for c, n in sorted(per_class.items(),
                                           key=lambda kv: -kv[1])],
            "entry": payload_no_id,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")

    work_src = ROOT / "terms" / eid / "WORK.md"
    cls_line = ", ".join(f"{c} x{n}" for c, n in
                         sorted(per_class.items(), key=lambda kv: -kv[1]))
    a1_line = (f"\n- {COHORT}: attribution repairs per SPEC_A1_20260902.md + "
               f"AMENDMENTS 1-3 ({cls_line})\n")
    work_text = (work_src.read_text(encoding="utf-8")
                 if work_src.exists() else "")
    work_text = re.sub(rf"\n*- {COHORT}: attribution repairs[^\n]*\n?", "",
                       work_text).rstrip("\n")
    (src / "WORK.md").write_text(work_text + a1_line, encoding="utf-8",
                                 newline="")

    products.append({
        "id": eid,
        "sourceDir": f"fresh-build/entries/{eid}/{COHORT}",
        "entrySha256": entry_sha,
        "worksheetSha256": sha(src / "evidence.draft.json"),
        "workSha256": sha(src / "WORK.md"),
        "termsMode": "replace",
        "termsBaselineSha256": entry_sha,
        "beforeSha256": receipt["preStateShas"][eid],
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
        f"{n_honest} real rows (91 missing_utterer_context ContextMasters "
        f"rows with byte-exact MasterName + note-law roles, 17 prose rewords "
        f"under the find-once/substitution/no-added-claim laws, the new "
        f"claim anchor with fresh zc + headword-free ClaimText + prose "
        f"anchoring, 2 performer rows, 1 Action-performer grammar-proof "
        f"sentence, the anonymous-monk 僧問 restructure, the GrammarEvidence "
        f"label repeat, the ReviewedBy/ReviewedUtc fields, and the "
        f"duplicate-anchor removal with surviving-holder coverage — all "
        f"verified against frozen pre/post materials with sha-pinned "
        f"inputs) and {n_plants} planted canaries bound by payload identity "
        f"(rowSha over the full row bytes): {n_plants}/{n_plants} caught by "
        f"EVERY reviewer (coverage law: any miss voids the round). "
        f"Non-plant flags byte-adjudicated against the engine+materials "
        f"oracle. 100% of the 35 products are machine-verified: engine "
        f"state-driven confinement (engine(clone@{CLONE_HEAD_PIN}) == these "
        f"bytes, re-verified at manifest time), attribution+depth gates, zc "
        f"on the new anchor, determinism, path-scope byte-diff, exactly-35 "
        f"terms-tree change, fleet regression 3099->3057 failing pairs with "
        f"zero newly-failing. Dictionary edits local-only (agent clone, "
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
        f"Lane A1 (attribution repair worklist, SPEC_A1_20260902.md + "
        f"AMENDMENTS 1-3): 116 edit records over 35 STATUS=done entries — "
        f"91 mechanical ContextMasters rows (utterer/verse-author per the "
        f"frozen VERSE_RE note law, MasterName byte-equal to the occurrence "
        f"bytes), 17 vague-attributor prose rewords (each name evidenced in "
        f"the entry's own bytes), 1 new ClaimAnchor anchoring the previously "
        f"dangling Chinese (zc ok/count-1, ClaimText headword-free verbatim "
        f"prefix), 2 performer rows + 1 grammar-proof sentence, 1 anonymous-"
        f"monk 僧問 restructure (MasterName cleared, respondent-only master "
        f"row), 1 GrammarEvidence label repeat, 1 ReviewedBy/ReviewedUtc "
        f"pair, 1 duplicate-anchor removal (strict duplicate of occurrence "
        f"o1). Machine gates CLEAN: zero attribution failure rows on the 35; "
        f"depth stable; determinism; confinement; path-scope byte-diff; "
        f"exactly the 35 of 4,504 terms entries changed; fleet 3,099 -> "
        f"3,057 failing pairs, zero newly-failing, 42 resolved. Blind r1 "
        f"PASS with {n_plants}/{n_plants} canaries caught by every reviewer "
        f"and zero confirmed findings. Public surface: replace-mode for the "
        f"35 ids; no adds, no withdrawals; entry count unchanged. Dictionary "
        f"edits local-only (agent clone, contrib branch); no push."),
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

rows_file = ROOT / "maintenance" / "a1-blind-r1-rows-20260903.json"
review_artifacts = [{
    "round": "r1", "path": wsl(rows_file), "sha256": sha(rows_file),
    "canaryKeySha256": sha(ROOT / "maintenance" /
                           "a1-blind-r1-plants-20260903.json"),
}]
for n in (1, 2):
    v = (ROOT / "subagents" / f"20260903-a1-blind-r1-reviewer-{n}"
         / "verdicts.json")
    if not v.exists():
        raise SystemExit(f"missing {v}")
    review_artifacts.append({
        "round": f"r1-reviewer{n}", "path": wsl(v), "sha256": sha(v),
    })

receipt_rows = {}
for name, note in (
    ("a1-edit-receipt-20260903.json",
     "engine receipt: 35 products, 116 edit records (frozen class counts), "
     "determinism + path-scope asserts, applied"),
    ("a1-gates-20260903.json",
     "gates CLEAN: zero attribution rows on the 35; depth PRE/POST stable; "
     "zc on the new anchor + anchor-removal coverage; determinism + "
     "confinement; path-scope byte-diff; exactly-35 terms-tree change; "
     "fleet 3099->3057 with zero newly-failing"),
    ("a1_transform_20260903.py",
     "the repair engine: clone-pre-state confinement, mechanical "
     "re-derivation asserted against the frozen table, asserted worksheet "
     "edits, path-scope escape assert"),
    ("a1-repairs-20260903.json",
     "authored worksheet (AMENDMENT 3): prose rewords, the new anchor, "
     "performer bindings, the 僧問 restructure, survivor fields, the "
     "duplicate-anchor removal"),
    ("a1-worklist-details-20260902.json",
     "worklist provenance: the 35 entries + their 121 failing audit rows "
     "(116 unique triples) the lane was scoped to clear"),
    ("a1-muc-derivation-20260902.json",
     "frozen mechanical derivation table the engine re-derives and must "
     "match byte-exact"),
    ("probe_a1_pre_apply_20260903.py",
     "pre-apply snapshot probe: clone pin + clean, terms==canon(clone) for "
     "the 35, full terms-tree sha snapshot, fresh fleet audit"),
    ("build_a1_blind_r1_20260903.py",
     "blind rows builder: 116 honest rows re-derived from clone via the "
     "engine + frozen pre/post materials; 7 payload-bound canaries at "
     "fixed-stride slots"),
    ("a1_adjudicate_blind_r1_20260903.py",
     "binding machine adjudicator (r1): oracle rebuild, canary coverage "
     "law, honest-flag byte-adjudication"),
    ("a1-blind-r1-adjudication-20260903.json",
     f"binding machine adjudication (r1): canaries {n_plants}/{n_plants} "
     f"with zero coverage misses across every reviewer, zero confirmed "
     f"findings — PASS"),
    ("a1-blind-r1-plants-20260903.json",
     f"canary key (adjudicator-only): {n_plants} planted defects "
     f"payload-bound (rowSha)"),
    ("SPEC_A1_20260902.md",
     "lane SPEC + AMENDMENTS 1-3 (headword-free ClaimText law, anchor-"
     "remove class, Note reword, corrected counts)"),
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
        "note": ("replace-only lane: 35 products in replace mode, no adds, "
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
