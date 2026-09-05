#!/usr/bin/env python3
"""Build the lane R2 publication manifest (review-verdict correction, 3 products).

Preconditions enforced before writing anything:
  - blind round r1 adjudication PASS with zero missed plants, zero
    confirmed findings
  - gates CLEAN (r2-gates-20260903.json)
  - engine receipt applied with the frozen class counts (8 records:
    3 occ-attribution + 1 relatedmasters-rename + 1 explanation-rewrite
    + 1 note-rewrite + 1 attributionnote-rewrite + 1 searchaliases-add)
  - clone clean at pinned HEAD 145b090 (the post-R1c publication state)
  - per-product staging: entry.v2.json == terms bytes AND ==
    canon(engine(clone)) (confinement re-verified at manifest time)
  - blind rows (plants included via payload binding) all carry entry in
    the 3-product worklist

Template: R1c (multi-product replace mode). No adds, no withdrawals: 3
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
COHORT = "r2-20260903"
LANE = ROOT / "fresh-build" / COHORT
BUILD_ROOT_POSIX = ("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/"
                    "runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation"
                    "/dictionary-build")
REPO_ROOT_POSIX = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator"
CLONE_HEAD_PIN = "145b090"
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")

EXPECTED_COUNTS = {"occ-attribution": 3, "relatedmasters-rename": 1,
                   "explanation-rewrite": 1, "note-rewrite": 1,
                   "attributionnote-rewrite": 1, "searchaliases-add": 1}


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

adj = load("maintenance/r2-blind-r1-adjudication-20260903.json")
gates = load("maintenance/r2-gates-20260903.json")

if adj.get("verdict") != "PASS":
    raise SystemExit(f"r1 adjudication not PASS: {adj.get('verdict')}")
if adj.get("canaries", {}).get("misses"):
    raise SystemExit(f"round VOID: missed plants {adj['canaries']['misses']}")
if adj.get("confirmedFindings"):
    raise SystemExit(f"blocking findings survive: {adj['confirmedFindings'][:3]}")
if gates["verdict"] != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates['problems'][:3]}")

receipt = load("maintenance/r2-edit-receipt-20260903.json")
if receipt["schemaVersion"] != "r2-edit-receipt":
    raise SystemExit(f"engine receipt schema {receipt['schemaVersion']}")
if not receipt["applied"]:
    raise SystemExit("engine receipt not applied")
if receipt["editClassCounts"] != EXPECTED_COUNTS:
    raise SystemExit(f"engine class counts {receipt['editClassCounts']}")
if len(receipt.get("editRecords", [])) != 8:
    raise SystemExit(f"engine edit records {len(receipt.get('editRecords', []))}"
                     " != 8")

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
status = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                        capture_output=True, text=True).stdout.splitlines()
if status:
    raise SystemExit(f"clone tree dirty at manifest time: {status[:5]}")
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD moved: {head[:7]} != {CLONE_HEAD_PIN}")

_spec = importlib.util.spec_from_file_location(
    "_r2", HERE / "r2_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

by_id = eng.clone_state()
worklist = eng.derive(by_id)
if len(worklist) != 3:
    raise SystemExit(f"derived worklist {len(worklist)} != 3")
if receipt["products"] != worklist:
    raise SystemExit("engine receipt products != derived worklist")
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, _records = eng.transform(snapshot)

rows_doc = load("maintenance/r2-blind-r1-rows-20260903.json")
plants_doc = load("maintenance/r2-blind-r1-plants-20260903.json")
wl_set = set(worklist)
if not {r["entry"] for r in rows_doc["rows"]} <= wl_set:
    raise SystemExit("blind rows escape the worklist")

records_by_entry: dict[str, list[dict]] = {eid: [] for eid in worklist}
for r in receipt["editRecords"]:
    records_by_entry[r["entry"]].append(r)

products = []
for eid in worklist:
    terms_p = ROOT / "terms" / eid / "entry.v2.json"
    terms_text = terms_p.read_text(encoding="utf-8-sig")
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
            "task": (
                "Verify the R2 external-review correction lane per "
                "SPEC_R2_20260903.md (user review verdict 2026-09-03, "
                "conditional pass): t_ea2a427c7aba 坐禪 — the three "
                "T48n2025 occurrences re-attributed from the fabricated "
                "speaker 'Dehui' (the Yuan recompiler 德煇重編, never a "
                "speaking master) to editorial/compiler-voice "
                "representation: MasterName null, ActorAttribution "
                "impersonal / institutional procedure / 'the monastic "
                "code's institutional voice' (label verbatim in the "
                "note), ContextMasters Dongyang Dehui [compiler] (the "
                "roster name), RelatedMasters 'Dehui' renamed to "
                "'Dongyang Dehui', Explanation 'Dehui's monastic code' "
                "-> 'The Baizhang monastic code redacted by Dongyang "
                "Dehui'; t_057cc9ea8755 攝心 — 'his own record' -> 'his "
                "recorded sayings, compiled by his disciples' (Note) "
                "and the s1o3 AttributionNote gains 'compiled by his "
                "disciples (至柔等編)'; t_968a2f97c9ff 一不成，二不是 — "
                "SearchAliases += '一不成、二不是' (search alias of the "
                "withdrawn-ID replacement t_1a6cdc16c248 -> "
                "t_968a2f97c9ff, C1-confirmed at eng/tools/"
                "merge-dict-entries.js:47) — all re-derived from the "
                "clone bytes under the frozen laws: occurrence counts "
                "unchanged (9+3 / 6 / 10), no retired rel survives in "
                "Occurrences/ClaimAnchors, every CJK string of the "
                "affected senses stays anchored over surviving kwics, "
                "carried fields (RelPath/FromLb/ToLb/Kwic/Curated/"
                "HeadwordSpanReview) byte-identical on the 3 repaired "
                "rows, find-once law, no 'Dehui' name-bearing value "
                "survives anywhere in ea2) and that nothing else "
                "changed (proven by engine(clone pre-state "
                f"@{CLONE_HEAD_PIN}) == these bytes; gates CLEAN incl. "
                "attribution zero rows on the products PRE and POST, "
                "depth hardPass 3/3 preserved, off-worklist "
                "byte-identity over 4,501 files, fleet 8,384 rows zero "
                "NEW; blind r1 with 8 payload-bound canaries)."),
            "repairs": [{"class": c, "count": n}
                        for c, n in sorted(per_class.items(),
                                           key=lambda kv: -kv[1])],
            "entry": payload_no_id,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")

    work_src = ROOT / "terms" / eid / "WORK.md"
    cls_line = ", ".join(f"{c} x{n}" for c, n in
                         sorted(per_class.items(), key=lambda kv: -kv[1]))
    r2_line = (f"\n- {COHORT}: R2 external-review correction lane per "
               f"SPEC_R2_20260903.md ({cls_line})\n")
    work_text = (work_src.read_text(encoding="utf-8")
                 if work_src.exists() else "")
    work_text = re.sub(rf"\n*- {COHORT}: R2 external-review correction "
                       rf"lane[^\n]*\n?", "", work_text).rstrip("\n")
    (src / "WORK.md").write_text(work_text + r2_line, encoding="utf-8",
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
        f"{n_honest} real rows (3 occurrence-attribution rows — each row "
        f"carries the old fabricated-speaker identity + the full new "
        f"attribution payload (MasterName null, ContextMasters, "
        f"ActorAttribution, AttributionNote) at (si,oi) with the carried "
        f"relPath/lb-pair/kwic plus the sense's post occurrence rel list; "
        f"3 prose rewrites (Explanation, Note, AttributionNote) with "
        f"find-once before/after pairs; 1 RelatedMasters rename with the "
        f"post list; 1 SearchAliases addition with the post list — all "
        f"verified against frozen pre/post materials with sha-pinned "
        f"inputs) and {n_plants} planted canaries bound by payload "
        f"identity (rowSha over the full row bytes): {n_plants}/{n_plants} "
        f"caught by EVERY reviewer (coverage law: any miss voids the "
        f"round). Non-plant flags byte-adjudicated against the "
        f"engine+materials oracle. 100% of the 3 products are "
        f"machine-verified: engine state-driven confinement "
        f"(engine(clone@{CLONE_HEAD_PIN}) == these bytes, re-verified at "
        f"manifest time), attribution gates (zero rows on the products "
        f"PRE and POST), depth gates (hardPass 3/3 preserved, no "
        f"true->false), corpus gate (count claims live-true: 1,207/265 "
        f"and 141/75), counts-preserved gate (9+3 / 6 / 10), retired-rel "
        f"gate (zero retired citations in Occurrences/ClaimAnchors "
        f"fleet-wide), sibling protection (the 2 follow-up-lane entries "
        f"byte-identical), off-worklist byte-identity over 4,501 files, "
        f"alias-uniqueness gate (exactly one owner fleet-wide, absent "
        f"from the installed index), fleet regression 8,384 rows with "
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
        f"Lane R2 (external-review correction lane answering the user's "
        f"2026-09-03 conditional-pass verdict on the R1a-R1c repair "
        f"arc, SPEC_R2_20260903.md): 8 edit records over 3 entries — "
        f"t_ea2a427c7aba 坐禪: the three T48n2025 occurrences "
        f"(1143a07, 1113a21, 1143a12) re-attributed from the fabricated "
        f"speaker 'Dehui' — the Yuan recompiler 東陽德煇, never a "
        f"speaking master — to editorial/compiler-voice representation "
        f"(MasterName null; ActorAttribution impersonal / institutional "
        f"procedure / 'the monastic code's institutional voice', label "
        f"verbatim in each note with 元 德煇重編 as textual provenance; "
        f"ContextMasters Dongyang Dehui [compiler]; RelatedMasters "
        f"'Dehui' -> roster name 'Dongyang Dehui'; Explanation "
        f"reworded off the compiler's name), carried rel/lb/kwic/"
        f"Curated/HeadwordSpanReview byte-identical; "
        f"t_057cc9ea8755 攝心: 'his own record' -> 'his recorded "
        f"sayings, compiled by his disciples' + the s1o3 "
        f"AttributionNote gains (至柔等編); t_968a2f97c9ff "
        f"一不成，二不是: SearchAliases += '一不成、二不是' (the "
        f"withdrawn-ID replacement's search alias, C1-confirmed). "
        f"Occurrence counts unchanged (9+3 / 6 / 10). Machine gates "
        f"CLEAN: attribution zero rows on the products PRE and POST; "
        f"depth hardPass 3/3 preserved; count claims live-true "
        f"(1,207/265; 141/75); retired-rel zero fleet-wide; sibling "
        f"protection (t_ab715aa474d5, t_351fa42d396b untouched for the "
        f"follow-up lane); off-worklist byte-identity over 4,501 files; "
        f"alias owned by exactly one entry and absent from the "
        f"installed index; fleet 8,384 rows zero NEW. Blind r1 PASS "
        f"with {n_plants}/{n_plants} canaries caught by every reviewer "
        f"and zero confirmed findings. Public surface: replace-mode for "
        f"the 3 ids; no adds, no withdrawals; entry count unchanged. "
        f"Dictionary edits local-only (agent clone, contrib branch); "
        f"no push."),
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

rows_file = ROOT / "maintenance" / "r2-blind-r1-rows-20260903.json"
review_artifacts = [{
    "round": "r1", "path": wsl(rows_file), "sha256": sha(rows_file),
    "canaryKeySha256": sha(ROOT / "maintenance" /
                           "r2-blind-r1-plants-20260903.json"),
}]
for n in (1, 2):
    v = (ROOT / "maintenance" / "subagents"
         / f"20260903-r2-blind-r1-reviewer-{n}" / "verdicts.json")
    if not v.exists():
        raise SystemExit(f"missing {v}")
    review_artifacts.append({
        "round": f"r1-reviewer{n}", "path": wsl(v), "sha256": sha(v),
    })

receipt_rows = {}
for name, note in (
    ("r2-edit-receipt-20260903.json",
     "engine receipt: 3 products, 8 edit records (frozen class counts), "
     "determinism + path-scope asserts, applied"),
    ("r2-gates-20260903.json",
     "gates CLEAN: identity + off-worklist byte-identity over 4,501 "
     "files; counts preserved + retired-rel zero fleet-wide; "
     "attribution convention + roster membership; audit PRE/POST zero "
     "NEW rows; depth hardPass preserved; anchoring + count claims "
     "live-true; sibling protection; alias uniqueness; fleet 8,384 "
     "rows zero NEW"),
    ("r2_transform_20260903.py",
     "the correction engine: clone-pre-state confinement (full-fleet "
     "view law), defect census, expectOld identity asserts at apply "
     "time, post-state laws (no 'Dehui' name survives, counts "
     "unchanged, retired absent, carried-field byte law on the 3 "
     "repaired rows, prose-anchoring gate), path-scope escape assert"),
    ("r2_pre_apply_20260903.py",
     "pre-apply snapshot: 3 pre entries + full terms-tree sha snapshot "
     "(4,504 files) + PRE attribution (0 rows) + PRE depth (3/3 "
     "hardPass) on the products"),
    ("r2-pre-terms-shas-20260903.json",
     "full terms-tree sha snapshot (4,504 entries) the off-worklist "
     "protection gate re-hashes against"),
    ("build_r2_blind_r1_20260903.py",
     "blind rows builder: 8 honest rows re-derived from clone via the "
     "engine + frozen pre/post materials; 8 payload-bound canaries at "
     "fixed-stride slots (masterName swap, contextMaster role "
     "corruption, actorLabel voice mismatch, kwic mutation, lb "
     "off-by-one, alias-target mutation, fabricated CJK quote, "
     "fabricated compiler string)"),
    ("r2_adjudicate_blind_r1_20260903.py",
     "binding machine adjudicator (r1): oracle rebuild, canary coverage "
     "law, honest-flag byte-adjudication (flags-based reviewer schema)"),
    ("r2-blind-r1-adjudication-20260903.json",
     f"binding machine adjudication (r1): canaries {n_plants}/{n_plants} "
     f"with zero coverage misses across every reviewer, zero confirmed "
     f"findings — PASS"),
    ("r2-blind-r1-plants-20260903.json",
     f"canary key (adjudicator-only): {n_plants} planted defects "
     "payload-bound (rowSha)"),
    ("probe_r2_preview_20260903.py",
     "preview probe: unified diffs + changed-path ledger straight from "
     "the engine (SPEC-exact construction evidence)"),
    ("SPEC_R2_20260903.md",
     "lane SPEC: the review-verdict corrections (Dehui speaker fix, "
     "recorded-sayings wording, alias), path-scope law, gates, blind "
     "round, archive bundle checklist, follow-up-lane scope split "
     "(user decision 2026-09-03)"),
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
        "note": ("replace-only lane: 3 products in replace mode, no adds, "
                 "no withdrawals; termbase.v2.json keeps its entry count "
                 "and the touched ids' rows regenerate; index/shard rows "
                 "for the touched ids update as the publisher regenerates "
                 "the surface; git footprint = termbase files + terms/ "
                 f"dirs only. Products are clone-backed at {CLONE_HEAD_PIN} "
                 "(the post-R1c publication state). The two remaining "
                 "[Dehui] rows (t_ab715aa474d5 1144b03, t_351fa42d396b "
                 "1127c04) are user-assigned to a dedicated follow-up "
                 "lane (decision 2026-09-03) and are NOT touched here. "
                 "node.script.sha256 is the working-tree js (carries "
                 "R1a's uncommitted byTermThenId tie-break + C1's "
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
