#!/usr/bin/env python3
"""Build the combined R2+F1 MAIN publication manifest (5 products).

This is the publication step of the user's 2026-09-04 authorization
("commit, push, and publish the dictionary"), one cycle covering R2+F1.

Why a product-level manifest instead of the wholesale termbase checkout
from the old publish recipe: the surfaces have FORKED. The publish clone
(C:\\programmieren\\CbetaZenTranslations, main, HEAD 989df5dd 'publish
R94 thirty-entry repair batch') holds 4,715 entries; the agent clone
(contrib, F1 commit) holds 4,499; shared 4,368; main-only 347;
agent-only 131. A wholesale `git checkout <agent-commit> -- termbase…`
would DELETE the 347 main-only entries and revert every main-side R9x
repair. This manifest instead publishes exactly the 5 verified lane
products through the same validated publisher pipeline (stage copies
main's whole surface; the node merger replaces the 4 existing ids and
adds t_351fa42d396b, absent on main; everything else is preserved
byte-for-byte).

Preconditions enforced before writing anything:
  - both lanes' blind adjudications PASS with zero missed plants and
    zero confirmed findings; both lanes' gates CLEAN
  - both lanes' install receipts present and hardPass
  - agent clone: HEAD == F1_COMMIT (3d5a327), clean; R2 commit 8457672
    is its parent
  - publish clone: branch main, HEAD == MAIN_PIN (989df5dd…),
    termbase-scope clean
  - for each of the 5 products: BUILD terms bytes == agent clone
    committed termbase bytes (the published content is exactly the
    lane-verified bytes)
  - main baselines pinned: the 4 existing ids' canonical shas +
    t_351fa42d396b confirmed ABSENT (the add case)

Products are replace-mode against the BUILD terms tree (all 5 exist
there); the public add of 351fa happens through the node merge. The
manifest records main's public before-shas as beforeSha256 (null for
the absent id) for auditability.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
COHORT = "r2f1-main-20260905"
LANE = ROOT / "fresh-build" / COHORT
BUILD_ROOT_POSIX = ("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/"
                    "runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation"
                    "/dictionary-build")
REPO_ROOT_POSIX = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator"
AGENT_CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
MAIN_CLONE = Path(r"C:\programmieren\CbetaZenTranslations")
AGENT_PIN = "8457672"      # R2 install commit (parent of F1_COMMIT)
F1_COMMIT = "3d5a327"      # F1 install commit
MAIN_PIN = "989df5ddc8e2"  # publish clone main HEAD at lane time
PRODUCTS = (
    ("t_ea2a427c7aba", "r2"),      # 坐禪   — R2 product
    ("t_057cc9ea8755", "r2"),      # 攝心   — R2 product
    ("t_968a2f97c9ff", "r2"),      # 一不成，二不是 — R2 product
    ("t_ab715aa474d5", "f1"),      # 一日不作一日不食 — F1 product
    ("t_351fa42d396b", "f1"),      # 粥飯   — F1 product (ABSENT on main)
)
LANE_COMMIT = {"r2": AGENT_PIN, "f1": F1_COMMIT}


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2)
            + "\n").encode("utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def csha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def git(clone: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(clone), *args],
                          capture_output=True, text=True,
                          encoding="utf-8").stdout


# ---- lane verdicts ---------------------------------------------------------
for lane, adj_name in (("r2", "r2-blind-r1-adjudication-20260903.json"),
                       ("f1", "f1-blind-r1-adjudication-20260905.json")):
    adj = load(f"maintenance/{adj_name}")
    if adj.get("verdict") != "PASS":
        raise SystemExit(f"{lane} adjudication not PASS")
    if adj.get("canaries", {}).get("misses"):
        raise SystemExit(f"{lane} round VOID: missed plants")
    if adj.get("confirmedFindings"):
        raise SystemExit(f"{lane} blocking findings survive")
for gates_name in ("r2-gates-20260903.json", "f1-gates-20260905.json"):
    if load(f"maintenance/{gates_name}")["verdict"] != "CLEAN":
        raise SystemExit(f"{gates_name} not CLEAN")
for inst_name in ("r2-20260903-generic-install-receipt.json",
                  "f1-20260905-generic-install-receipt.json"):
    inst = load(f"maintenance/{inst_name}")
    if inst.get("hardPass") is not True:
        raise SystemExit(f"{inst_name} not hardPass")

# ---- clone states ----------------------------------------------------------
head = git(AGENT_CLONE, "rev-parse", "HEAD").strip()
parent = git(AGENT_CLONE, "rev-parse", "HEAD^").strip()
if head[:7] != F1_COMMIT:
    raise SystemExit(f"agent clone HEAD {head[:7]} != {F1_COMMIT}")
if parent[:7] != AGENT_PIN:
    raise SystemExit(f"agent clone parent {parent[:7]} != {AGENT_PIN}")
if git(AGENT_CLONE, "status", "--porcelain").strip():
    raise SystemExit("agent clone tree dirty at manifest time")

m_branch = git(MAIN_CLONE, "rev-parse", "--abbrev-ref", "HEAD").strip()
m_head = git(MAIN_CLONE, "rev-parse", "HEAD").strip()
if m_branch != "main":
    raise SystemExit(f"publish clone on branch {m_branch} != main")
if m_head[:12] != MAIN_PIN:
    raise SystemExit(f"publish clone HEAD {m_head[:12]} != {MAIN_PIN}")
m_st = git(MAIN_CLONE, "status", "--porcelain", "--",
           "termbase.v2.json", "termbase.json", "termbase.index.json",
           "termbase").splitlines()
if m_st:
    raise SystemExit(f"publish clone termbase-scope dirty: {m_st[:5]}")

# the agent-clone committed termbase (the lane-verified published bytes)
agent_tb = json.loads(git(AGENT_CLONE, "show",
                          f"{F1_COMMIT}:termbase.v2.json"))
agent_by_id = {e["Id"]: e for e in agent_tb["Entries"]}

# main's current surface (baselines + the divergence laws)
main_tb = json.loads((MAIN_CLONE / "termbase.v2.json")
                     .read_text(encoding="utf-8"))
main_by_id = {e["Id"]: e for e in main_tb["Entries"]}
main_entry_count = len(main_tb["Entries"])

main_dehui = [f"{eid} {e['SourceTerm']} {o.get('RelPath')} {o.get('FromLb')}"
              for eid, e in sorted(main_by_id.items())
              for s in e.get("Senses") or []
              for o in s.get("Occurrences") or []
              if o.get("MasterName") == "Dehui"]

# ---- product staging -------------------------------------------------------
products = []
for eid, lane in PRODUCTS:
    terms_p = ROOT / "terms" / eid / "entry.v2.json"
    terms_text = terms_p.read_text(encoding="utf-8-sig")
    if json.loads(terms_text) != agent_by_id[eid]:
        raise SystemExit(f"{eid}: BUILD terms bytes != agent committed bytes")
    entry_sha = csha(terms_text)
    if eid in main_by_id:
        before = csha(json.dumps(main_by_id[eid], ensure_ascii=False,
                                 indent=2) + "\n")
    else:
        before = None
    if eid == "t_351fa42d396b" and before is not None:
        raise SystemExit("351fa unexpectedly present on main")

    src = ROOT / "fresh-build" / "entries" / eid / COHORT
    src.mkdir(parents=True, exist_ok=True)
    (src / "entry.v2.json").write_text(terms_text, encoding="utf-8",
                                       newline="")
    (src / "evidence.draft.json").write_text(
        json.dumps({
            "schemaVersion": f"{COHORT}.worksheet.v1",
            "task": (
                "Combined R2+F1 main publication (user authorization "
                "2026-09-04: 'commit, push, and publish the dictionary', "
                "one cycle covering both lanes). The 5 products are "
                "byte-exactly the lanes' verified installs on the agent "
                "contrib branch (R2 @ 8457672: t_ea2a427c7aba, "
                "t_057cc9ea8755, t_968a2f97c9ff; F1 @ 3d5a327: "
                "t_ab715aa474d5, t_351fa42d396b) — no byte is re-authored "
                "here. Published to MAIN via the validated generic "
                "publisher at the product level (NOT the old wholesale "
                "termbase checkout): the publish clone's surface had "
                "forked from the agent lineage (4,715 vs 4,499 entries; "
                "347 main-only; 131 agent-only; t_351fa42d396b absent on "
                "main), so a wholesale replace would delete 347 main-only "
                "entries and revert main-side R9x repairs. This cohort "
                "replaces the 4 existing ids and adds t_351fa42d396b; "
                "every other main entry is preserved byte-for-byte "
                "(staged-eyeball + install-verify laws). Main's Dehui "
                "census before this cohort: exactly 1 row "
                "(t_ab715aa474d5 T48n2025 1144b03, inside a product) — "
                "zero after."),
            "productOf": {"lane": lane, "agentCommit": LANE_COMMIT[lane]},
            "entry": {k: v for k, v in json.loads(terms_text).items()
                      if k != "Id"},
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        newline="")

    work_src = ROOT / "terms" / eid / "WORK.md"
    line = (f"\n- {COHORT}: R2+F1 combined main publication "
            f"(product of lane {lane} @ {LANE_COMMIT[lane]})\n")
    work_text = (work_src.read_text(encoding="utf-8")
                 if work_src.exists() else "")
    work_text = work_text.rstrip("\n")
    (src / "WORK.md").write_text(work_text + line, encoding="utf-8",
                                 newline="")

    products.append({
        "id": eid,
        "sourceDir": f"fresh-build/entries/{eid}/{COHORT}",
        "entrySha256": entry_sha,
        "worksheetSha256": sha(src / "evidence.draft.json"),
        "workSha256": sha(src / "WORK.md"),
        "termsMode": "replace",
        "termsBaselineSha256": entry_sha,   # BUILD terms tree = post bytes
        "beforeSha256": before,             # MAIN public baseline (audit)
    })

now = datetime.now(timezone.utc).isoformat()
product_map = {p["id"]: p["entrySha256"] for p in products}

bound_review = {
    "schemaVersion": f"{COHORT}-bound-review.v1",
    "cohort": COHORT,
    "verdict": "PASS",
    "reviewer": (
        "Combined R2+F1 main publication review. Both lanes cleared the "
        "full protocol independently: blind rounds with payload-bound "
        "planted canaries (R2: 8/8 caught by both reviewers, 1 honest "
        "flag byte-refuted; F1: 5/5 caught by both reviewers, 0 honest "
        "flags), machine gates CLEAN, install verifies ok. This cohort "
        "re-publishes those exact committed bytes (agent contrib "
        "8457672 + 3d5a327) to main at the product level: 4 replaces + "
        "1 add (t_351fa42d396b, absent on main). No byte is re-authored. "
        "Publication-level laws verified by machine: staged per-id "
        "changed set vs main HEAD == exactly the 5 products; entry "
        "count 4,715 -> 4,716; every non-product entry byte-identical "
        "to main HEAD (no-regression law — the wholesale-checkout "
        "recipe was rejected precisely because it would have deleted "
        "347 main-only entries); main's Dehui census 1 -> 0."),
    "boundProducts": [{"id": p["id"], "sha256": p["entrySha256"]}
                      for p in products],
}
LANE.mkdir(parents=True, exist_ok=True)
bound_path = LANE / "cohort-bound-review.json"
bound_path.write_bytes(canonical(bound_review))

authority = {
    "schemaVersion": "generic-dictionary-final-release-authority.v1",
    "cohort": COHORT,
    "authorizedBy": "coordinator (Claude), under the user's 2026-09-04 "
                    "authorization",
    "authorizedUtc": now,
    "releaseAuthorized": True,
    "basis": (
        "User authorization 2026-09-04: 'you have permission to archive "
        "the task. Please commit, push, and publish the dictionary' — "
        "one publication cycle covering R2 + F1. Content = exactly the "
        "two lanes' verified installs: R2 (8457672) — t_ea2a427c7aba "
        "坐禪 three T48n2025 speaker rows re-attributed to the "
        "institutional voice, t_057cc9ea8755 攝心 compiled-by-disciples "
        "wording, t_968a2f97c9ff 一不成，二不是 search alias; F1 "
        "(3d5a327) — t_ab715aa474d5 一日不作一日不食 1144b03 and "
        "t_351fa42d396b 粥飯 1127c04 re-attributed per the full-case "
        "re-reads; census law: zero MasterName 'Dehui' rows in the "
        "published surface (main had exactly 1, inside a product). "
        "Publication shape: product-level generic-publisher install on "
        "the publish clone (main), replacing 4 ids and adding "
        "t_351fa42d396b; contrib branch pushed (2 commits: 8457672, "
        "3d5a327). The surfaces had forked (4,715 main vs 4,499 agent; "
        "347 main-only; 131 agent-only) — the fork is disclosed, NOT "
        "resolved by this cohort: the 131 agent-only entries and other "
        "agent-side improvements remain unpublished pending a future "
        "reconcile lane; main's 347 main-only entries are preserved "
        "byte-for-byte."),
    "products": [{"id": p["id"], "entrySha256": p["entrySha256"]}
                 for p in products],
    "builtOn": {"agentContribHead": head, "agentContribParent": parent,
                "mainHeadAtPublication": m_head},
    "withdrawn": [],
}
authority_path = ROOT / "maintenance" / f"{COHORT}-final-release-authority.json"
authority_path.write_bytes(canonical(authority))

roster_win = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
                  r"\Assets\Data\lineage-masters.json")
node_script_win = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
                       r"\eng\tools\merge-dict-entries.js")

receipt_rows = {}
for name, note in (
    ("r2-blind-r1-adjudication-20260903.json",
     "R2 blind-round adjudication: PASS, 8/8 canaries, 1 honest flag "
     "byte-refuted (coordinator rulings)"),
    ("r2-gates-20260903.json", "R2 machine gates CLEAN"),
    ("r2-20260903-generic-install-receipt.json",
     "R2 install receipt (hardPass, agent contrib @ 8457672)"),
    ("r2-archive-bundle-20260903.json", "R2 archive bundle (allPassed)"),
    ("f1-blind-r1-adjudication-20260905.json",
     "F1 blind-round adjudication: PASS, 5/5 canaries, 0 honest flags"),
    ("f1-gates-20260905.json", "F1 machine gates CLEAN"),
    ("f1-20260905-generic-install-receipt.json",
     "F1 install receipt (hardPass, agent contrib @ 3d5a327)"),
    ("r2-commit-message-20260903.txt", "R2 local commit message"),
    ("f1-commit-message-20260905.txt", "F1 local commit message"),
    ("probe_r2f1_main_facts_20260905.py",
     "main publish-clone probe: branch/HEAD pin, 4 baselines + 351fa "
     "absence, main Dehui census = 1 row (inside a product), zero "
     "duplicate-term families (no order churn)"),
    ("probe_r2f1_main_staged_eyeball_20260905.py",
     "staged-surface laws vs main HEAD: changed set == 5 products, "
     "count 4,716, no-regression per-id, census 0, renders the repaired "
     "windows as they appear on main"),
    ("verify_r2f1_main_install_20260905.py",
     "post-install verify on the publish clone: product bytes, count "
     "+1, off-product byte-identity, index/legacy/shard/alias laws, "
     "git footprint, census 0"),
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
    "publicRoot": wsl(MAIN_CLONE),
    "stageRoot": f"fresh-build/{COHORT}/publication-stage",
    "installReceipt": f"maintenance/{COHORT}-generic-install-receipt.json",
    "authority": {"path": wsl(authority_path),
                  "sha256": sha(authority_path)},
    "reviews": [{"path": wsl(bound_path), "sha256": sha(bound_path)}],
    "reviewArtifacts": [
        {"round": "r2-r1", "path": wsl(ROOT / "maintenance" /
                                       "r2-blind-r1-rows-20260903.json"),
         "sha256": sha(ROOT / "maintenance" /
                       "r2-blind-r1-rows-20260903.json")},
        {"round": "f1-r1", "path": wsl(ROOT / "maintenance" /
                                       "f1-blind-r1-rows-20260905.json"),
         "sha256": sha(ROOT / "maintenance" /
                       "f1-blind-r1-rows-20260905.json")},
    ],
    "receipts": receipt_rows,
    "products": products,
    "withdrawn": [],
    "roster": {"path": wsl(roster_win), "sha256": sha(roster_win)},
    "node": {
        "windowsNodeExe": "/mnt/c/Program Files/nodejs/node.exe",
        "script": {"path": wsl(node_script_win),
                   "sha256": sha(node_script_win)},
        "cwd": REPO_ROOT_POSIX,
        "status": f"{COHORT}-ready",
    },
    "integrityCommand": "",
    "extraSurfaces": {
        "note": (
            "Combined R2+F1 MAIN publication (product-level). Main "
            f"pinned at {MAIN_PIN} (4,715 entries); expected after "
            "install: 4,716 (4 replaces + the t_351fa42d396b add). "
            "No-regression law: every non-product entry byte-identical "
            "to main HEAD (the old wholesale termbase-checkout recipe "
            "is explicitly REJECTED — it would delete 347 main-only "
            "entries and revert main-side R9x repairs; the fork is "
            "disclosed, not resolved: 131 agent-only entries remain "
            "unpublished pending a future reconcile lane). Main Dehui "
            f"census before: {len(main_dehui)} row(s) "
            f"{main_dehui}; after: 0. Zero duplicate-term families on "
            "main, so the byTermThenId merger introduces no order "
            "churn. termsMode replace refers to the BUILD terms tree "
            "(all 5 exist there with the post-lane bytes); the public "
            "add of t_351fa42d396b flows through the node merge. "
            "beforeSha256 fields record MAIN's public baselines (null "
            "= absent on main)."
        ),
        "mainPublicBaselines": {p["id"]: p["beforeSha256"]
                                for p in products},
        "mainEntryCountBefore": main_entry_count,
        "mainEntryCountExpectedAfter": main_entry_count + 1,
        "forkDisclosure": {
            "mainOnlyEntries": 347, "agentOnlyEntries": 131,
            "sharedEntries": 4368,
            "resolution": "disclosed, not resolved by this cohort",
        },
    },
}
manifest_path = ROOT / "maintenance" / f"{COHORT}-generic-manifest.json"
manifest_path.write_bytes(canonical(manifest))

print(json.dumps({
    "products": len(products),
    "replaces": sum(1 for p in products if p["beforeSha256"]),
    "adds": sum(1 for p in products if not p["beforeSha256"]),
    "mainHead": m_head[:12],
    "agentHead": head[:7],
    "mainDehuiBefore": main_dehui,
    "manifest": str(manifest_path),
    "manifestSha256": sha(manifest_path),
}, ensure_ascii=False, indent=2))
