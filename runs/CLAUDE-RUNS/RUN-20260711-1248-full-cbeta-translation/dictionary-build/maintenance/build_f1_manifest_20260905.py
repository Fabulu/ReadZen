#!/usr/bin/env python3
"""Build the lane F1 publication manifest (follow-up correction, 2 products).

Preconditions enforced before writing anything:
  - blind round r1 adjudication PASS with zero missed plants, zero
    confirmed findings
  - gates CLEAN (f1-gates-20260905.json)
  - engine receipt applied with the frozen class counts (5 records:
    2 occ-attribution + 2 relatedmasters-rename + 1 explanation-rewrite)
  - clone clean at pinned HEAD 8457672 (the R2 install state)
  - per-product staging: entry.v2.json == terms bytes AND ==
    canon(engine(clone)) (confinement re-verified at manifest time)
  - blind rows (plants included via payload binding) all carry entry in
    the 2-product worklist

Template: R2 (multi-product replace mode). No adds, no withdrawals: 2
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
COHORT = "f1-20260905"
LANE = ROOT / "fresh-build" / COHORT
BUILD_ROOT_POSIX = ("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/"
                    "runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation"
                    "/dictionary-build")
REPO_ROOT_POSIX = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator"
CLONE_HEAD_PIN = "8457672"
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
R2_PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")

EXPECTED_COUNTS = {"occ-attribution": 2, "relatedmasters-rename": 2,
                   "explanation-rewrite": 1}


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

adj = load("maintenance/f1-blind-r1-adjudication-20260905.json")
gates = load("maintenance/f1-gates-20260905.json")

if adj.get("verdict") != "PASS":
    raise SystemExit(f"r1 adjudication not PASS: {adj.get('verdict')}")
if adj.get("canaries", {}).get("misses"):
    raise SystemExit(f"round VOID: missed plants {adj['canaries']['misses']}")
if adj.get("confirmedFindings"):
    raise SystemExit(f"blocking findings survive: {adj['confirmedFindings'][:3]}")
if gates["verdict"] != "CLEAN":
    raise SystemExit(f"gates not CLEAN: {gates['problems'][:3]}")

receipt = load("maintenance/f1-edit-receipt-20260905.json")
if receipt["schemaVersion"] != "f1-edit-receipt":
    raise SystemExit(f"engine receipt schema {receipt['schemaVersion']}")
if not receipt["applied"]:
    raise SystemExit("engine receipt not applied")
if receipt["editClassCounts"] != EXPECTED_COUNTS:
    raise SystemExit(f"engine class counts {receipt['editClassCounts']}")
if len(receipt.get("editRecords", [])) != 5:
    raise SystemExit(f"engine edit records {len(receipt.get('editRecords', []))}"
                     " != 5")
if receipt.get("r2ProductsProtected") != list(R2_PRODUCTS):
    raise SystemExit("engine receipt r2ProductsProtected drift")

head = subprocess.run(["git", "-C", str(CLONE), "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
status = subprocess.run(["git", "-C", str(CLONE), "status", "--porcelain"],
                        capture_output=True, text=True).stdout.splitlines()
if status:
    raise SystemExit(f"clone tree dirty at manifest time: {status[:5]}")
if head[:7] != CLONE_HEAD_PIN:
    raise SystemExit(f"clone HEAD moved: {head[:7]} != {CLONE_HEAD_PIN}")

_spec = importlib.util.spec_from_file_location(
    "_f1", HERE / "f1_transform_20260905.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

by_id = eng.clone_state()
worklist = eng.derive(by_id)
if len(worklist) != 2:
    raise SystemExit(f"derived worklist {len(worklist)} != 2")
if receipt["products"] != worklist:
    raise SystemExit("engine receipt products != derived worklist")
snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
out, _records = eng.transform(snapshot)

rows_doc = load("maintenance/f1-blind-r1-rows-20260905.json")
plants_doc = load("maintenance/f1-blind-r1-plants-20260905.json")
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
                "Verify the F1 follow-up correction lane per "
                "SPEC_F1_20260905.md (user scope decision 2026-09-03): "
                "the two remaining T48n2025 [Dehui] speaker rows — "
                "t_ab715aa474d5 一日不作一日不食 s1o2 (1144b03, the 普請 "
                "communal-labor directive citing 古人) and t_351fa42d396b "
                "粥飯 s1o1 (1127c04, the 遷化 funeral-observance "
                "scheduling) — re-attributed from the fabricated speaker "
                "'Dehui' (the Yuan recompiler 德煇重編, never a speaking "
                "master) to editorial/compiler-voice representation: "
                "MasterName null, ActorAttribution impersonal / "
                "institutional procedure / 'the monastic code's "
                "institutional voice' (label verbatim in the note, with "
                "元 德煇重編 as textual provenance and the section "
                "identified from the full-case re-read), ContextMasters "
                "Dongyang Dehui [compiler] (the roster name), "
                "RelatedMasters 'Dehui' renamed to 'Dongyang Dehui' in "
                "both entries, Explanation 'redacted by Dehui,' -> "
                "'redacted by Dongyang Dehui,' — all re-derived from the "
                "clone bytes under the frozen laws: occurrence counts "
                "unchanged (3; 3+6), no retired rel survives in "
                "Occurrences/ClaimAnchors, every CJK string of the "
                "edited sense stays anchored over surviving kwics, "
                "carried fields (RelPath/FromLb/ToLb/Kwic/Curated/"
                "HeadwordSpanReview) byte-identical on the 2 repaired "
                "rows, find-once law, no 'Dehui' name-bearing value "
                "survives in either entry) and that nothing else "
                "changed (proven by engine(clone pre-state "
                f"@{CLONE_HEAD_PIN}) == these bytes; gates CLEAN incl. "
                "attribution zero rows on the products PRE and POST, "
                "depth hardPass 2/2 preserved, R2-product protection "
                "(ea2/057/968 byte-identical), off-worklist "
                "byte-identity over 4,502 files, fleet 8,384 rows zero "
                "NEW, census law zero MasterName 'Dehui' rows "
                "fleet-wide; blind r1 with 5 payload-bound canaries)."),
            "repairs": [{"class": c, "count": n}
                        for c, n in sorted(per_class.items(),
                                           key=lambda kv: -kv[1])],
            "entry": payload_no_id,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")

    work_src = ROOT / "terms" / eid / "WORK.md"
    cls_line = ", ".join(f"{c} x{n}" for c, n in
                         sorted(per_class.items(), key=lambda kv: -kv[1]))
    f1_line = (f"\n- {COHORT}: F1 follow-up correction lane per "
               f"SPEC_F1_20260905.md ({cls_line})\n")
    work_text = (work_src.read_text(encoding="utf-8")
                 if work_src.exists() else "")
    work_text = re.sub(rf"\n*- {COHORT}: F1 follow-up correction "
                       rf"lane[^\n]*\n?", "", work_text).rstrip("\n")
    (src / "WORK.md").write_text(work_text + f1_line, encoding="utf-8",
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
        f"{n_honest} real rows (2 occurrence-attribution rows — each row "
        f"carries the old fabricated-speaker identity + the full new "
        f"attribution payload (MasterName null, ContextMasters, "
        f"ActorAttribution, AttributionNote) at (si,oi) with the carried "
        f"relPath/lb-pair/kwic plus the sense's post occurrence rel list; "
        f"1 Explanation rewrite with a find-once before/after pair; 2 "
        f"RelatedMasters renames with the post lists — all verified "
        f"against frozen pre/post materials with sha-pinned inputs) and "
        f"{n_plants} planted canaries bound by payload identity (rowSha "
        f"over the full row bytes): {n_plants}/{n_plants} caught by EVERY "
        f"reviewer (coverage law: any miss voids the round). Non-plant "
        f"flags byte-adjudicated against the engine+materials oracle. "
        f"100% of the 2 products are machine-verified: engine "
        f"state-driven confinement (engine(clone@{CLONE_HEAD_PIN}) == "
        f"these bytes, re-verified at manifest time), attribution gates "
        f"(zero rows on the products PRE and POST), depth gates (hardPass "
        f"2/2 preserved, no true->false), corpus gate (count claims "
        f"preserved byte-exactly), counts-preserved gate (3; 3+6), "
        f"retired-rel gate (zero retired citations in Occurrences/"
        f"ClaimAnchors fleet-wide), R2-product protection (the 3 R2 "
        f"products byte-identical), off-worklist byte-identity over 4,502 "
        f"files, census law (zero MasterName 'Dehui' rows anywhere in the "
        f"written tree), fleet regression 8,384 rows with zero "
        f"newly-failing. Dictionary edits local-only through this "
        f"manifest's install (agent clone, contrib branch); push + main "
        f"publication follow under the user's 2026-09-04 authorization "
        f"as one cycle covering R2+F1."),
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
        f"Lane F1 (the follow-up correction lane for the two sibling "
        f"[Dehui] rows the user routed here by decision 2026-09-03, with "
        f"full-case re-reads; SPEC_F1_20260905.md): 5 edit records over 2 "
        f"entries — t_ab715aa474d5 一日不作一日不食 s1o2 (1144b03): the "
        f"window sits in the code's 普請 communal-labor section, a "
        f"directive citing 古人 ('the ancients') — re-attributed from the "
        f"fabricated speaker 'Dehui' (the Yuan recompiler 東陽德煇, never "
        f"a speaking master) to editorial/compiler-voice representation "
        f"(MasterName null; ActorAttribution impersonal / institutional "
        f"procedure / 'the monastic code's institutional voice', label "
        f"verbatim in the note with 元 德煇重編 as textual provenance; "
        f"ContextMasters Dongyang Dehui [compiler]; RelatedMasters "
        f"'Dehui' -> roster name 'Dongyang Dehui'); t_351fa42d396b 粥飯 "
        f"s1o1 (1127c04): the 遷化 funeral-observance scheduling "
        f"regulation — same representation, plus Explanation 'redacted "
        f"by Dehui,' -> 'redacted by Dongyang Dehui,' and the "
        f"RelatedMasters rename; carried rel/lb/kwic/Curated/"
        f"HeadwordSpanReview byte-identical on both rows. Occurrence "
        f"counts unchanged (3; 3+6). Machine gates CLEAN: attribution "
        f"zero rows on the products PRE and POST; depth hardPass 2/2 "
        f"preserved; retired-rel zero fleet-wide; R2-product protection "
        f"(t_ea2a427c7aba, t_057cc9ea8755, t_968a2f97c9ff untouched); "
        f"off-worklist byte-identity over 4,502 files; fleet 8,384 rows "
        f"zero NEW; census law — zero MasterName 'Dehui' rows anywhere "
        f"in the termbase after this lane. Blind r1 PASS with "
        f"{n_plants}/{n_plants} canaries caught by every reviewer and "
        f"zero confirmed findings. Public surface: replace-mode for the "
        f"2 ids; no adds, no withdrawals; entry count unchanged. "
        f"Dictionary edits local-only through this install (agent clone, "
        f"contrib branch); push + main publication follow under the "
        f"user's 2026-09-04 authorization as one cycle covering R2+F1."),
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

rows_file = ROOT / "maintenance" / "f1-blind-r1-rows-20260905.json"
review_artifacts = [{
    "round": "r1", "path": wsl(rows_file), "sha256": sha(rows_file),
    "canaryKeySha256": sha(ROOT / "maintenance" /
                           "f1-blind-r1-plants-20260905.json"),
}]
for n in (1, 2):
    v = (ROOT / "maintenance" / "subagents"
         / f"20260905-f1-blind-r1-reviewer-{n}" / "verdicts.json")
    if not v.exists():
        raise SystemExit(f"missing {v}")
    review_artifacts.append({
        "round": f"r1-reviewer{n}", "path": wsl(v), "sha256": sha(v),
    })

receipt_rows = {}
for name, note in (
    ("f1-edit-receipt-20260905.json",
     "engine receipt: 2 products, 5 edit records (frozen class counts), "
     "determinism + path-scope asserts, R2 products protected, applied"),
    ("f1-gates-20260905.json",
     "gates CLEAN: identity + off-worklist byte-identity over 4,502 "
     "files (R2 products protected); counts preserved + retired-rel "
     "zero fleet-wide; attribution convention + roster membership; "
     "audit PRE/POST zero NEW rows; depth hardPass preserved; anchoring "
     "+ count-claim preservation; fleet 8,384 rows zero NEW; census "
     "law zero MasterName 'Dehui' rows in the written tree"),
    ("f1_transform_20260905.py",
     "the correction engine: clone-pre-state confinement (full-fleet "
     "view law, R2-repair-intact asserts), defect census, expectOld "
     "identity asserts at apply time, post-state laws (no 'Dehui' "
     "name survives, counts unchanged, retired absent, carried-field "
     "byte law on the 2 repaired rows, prose-anchoring gate), "
     "path-scope escape assert"),
    ("f1_pre_apply_20260905.py",
     "pre-apply snapshot: 2 pre entries + full terms-tree sha snapshot "
     "(4,504 files) + PRE attribution (0 rows) + PRE depth (2/2 "
     "hardPass) on the products"),
    ("f1-pre-terms-shas-20260905.json",
     "full terms-tree sha snapshot (4,504 entries) the off-worklist "
     "protection gate re-hashes against"),
    ("build_f1_blind_r1_20260905.py",
     "blind rows builder: 5 honest rows re-derived from clone via the "
     "engine + frozen pre/post materials; 5 payload-bound canaries at "
     "fixed-stride slots (masterName swap, contextMaster role "
     "corruption, actorLabel voice mismatch, kwic mutation, fabricated "
     "CJK quote)"),
    ("f1_adjudicate_blind_r1_20260905.py",
     "binding machine adjudicator (r1): oracle rebuild, canary coverage "
     "law, honest-flag byte-adjudication (flags-based reviewer schema)"),
    ("f1-blind-r1-adjudication-20260905.json",
     f"binding machine adjudication (r1): canaries {n_plants}/{n_plants} "
     f"with zero coverage misses across every reviewer, zero confirmed "
     f"findings — PASS"),
    ("f1-blind-r1-plants-20260905.json",
     f"canary key (adjudicator-only): {n_plants} planted defects "
     "payload-bound (rowSha)"),
    ("probe_f1_corpus_windows_20260905.py",
     "full-case re-read probe (user-mandated): the T48n2025 XML windows "
     "for 1144b03 (普請 communal-labor directive citing 古人), 1127c04 "
     "(遷化 funeral scheduling), and the 1119b01 常曰 Baizhang contrast "
     "row — plain-text extraction with section headers"),
    ("probe_f1_design_facts_20260905.py",
     "design-facts probe: the installed R2 convention bytes mirrored "
     "for this lane + fleet census of the 2 target rows"),
    ("f1-design-facts-20260905.txt",
     "design-facts transcript: R2 institutional-voice rows, roster "
     "check, target-row pre bytes, fleet census exactly 2"),
    ("SPEC_F1_20260905.md",
     "lane SPEC: the 2 sibling [Dehui] rows with full-case re-reads "
     "(§0), the 5-edit repair (§1), path scope (§2), gates (§3), blind "
     "round (§4), publication + archive (§5), out of scope (§6), "
     "census-law completion language (§7)"),
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
        "note": ("replace-only lane: 2 products in replace mode, no adds, "
                 "no withdrawals; termbase.v2.json keeps its entry count "
                 "and the touched ids' rows regenerate; index/shard rows "
                 "for the touched ids update as the publisher regenerates "
                 "the surface; git footprint = termbase files + terms/ "
                 f"dirs only. Products are clone-backed at {CLONE_HEAD_PIN} "
                 "(the R2 install state; R2's three products are "
                 "protected siblings this lane). This lane completes the "
                 "Dehui speaker class: after install, zero MasterName "
                 "'Dehui' rows remain anywhere in the termbase (census "
                 "law). Push + main publication follow under the user's "
                 "2026-09-04 authorization as one cycle covering R2+F1 "
                 "(surgical termbase-artifact merge to main via the "
                 "clean publish clone; contrib-branch push first). "
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
