#!/usr/bin/env python3
"""Machine-write the F1 archive bundle (SPEC_F1_20260905.md §5).

Run AFTER install + LOCAL clone commit. Every verification is re-run
LIVE here (subprocess, exit status + raw stdout/stderr captured) — the
bundle never transcribes in-session claims. Post-commit re-run mode:
the pin-state scripts (gates, adjudicator) run against a detached git
worktree of the pin commit; verify_install runs against the real clone
with F1_VERIFY_BASE=HEAD^ (see postCommitReRun in the output). Records:

  - final HEAD + parent HEAD of the agent clone; git status
    --porcelain; git diff --stat parent..HEAD
  - corpus manifest sha (registry corpusManifestSha256) + corpus path
  - installed dictionary manifest sha + install receipt sha
  - fresh re-runs: f1 gates, f1 verify_install, f1 adjudicator
    (commands + rc + raw output each)
  - staged-eyeball transcript file (produced between stage and install)
  - off-footprint report (entries outside the 2 products that differ
    parent..HEAD — must be none)
  - R2-product protection report: the 3 R2 products byte-identical
    parent..HEAD and their repaired windows still landed
  - census-law report: zero MasterName 'Dehui' rows in the installed
    clone (the class this lane completes)
  - carry-over notes: 水頭 report-only + X63n1250 lead (R2 bundle);
    stale-SourceTexts fleet observation (pre-existing class, disclosed)

Outputs maintenance/f1-archive-bundle-20260905.json. Exit 0 iff every
embedded verification passed.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
CLONE = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations")
REGISTRY = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
                r"\Assets\Data\zen-source-authority.json")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
PRODUCTS = ("t_ab715aa474d5", "t_351fa42d396b")
R2_PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
PIN = "8457672"
ok = True


def run(cmd: list[str], cwd: Path | None = None,
        env: dict | None = None) -> dict:
    p_env = None
    if env:
        p_env = dict(os.environ)
        p_env.update(env)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=p_env)
    return {"command": " ".join(cmd[:2]) + (" …" if len(cmd) > 2 else ""),
            "argv": cmd, "exitStatus": p.returncode, "env": env,
            "stdout": p.stdout, "stderr": p.stderr}


def check(r: dict, want: int = 0, label: str = "") -> dict:
    global ok
    r["expected"] = want
    r["passed"] = r["exitStatus"] == want
    if not r["passed"]:
        ok = False
        print(f"FAIL {label}: rc={r['exitStatus']}")
    return r


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(CLONE), *args],
                          capture_output=True, text=True,
                          encoding="utf-8").stdout


head = git("rev-parse", "HEAD").strip()
parent = git("rev-parse", "HEAD^").strip()
porcelain = git("status", "--porcelain")
diff_stat = git("diff", "--stat", f"{parent}..{head}")

reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
cms = None
corpus_path = None
if isinstance(reg, dict):
    cms = reg.get("corpusManifestSha256")
    corpus_path = reg.get("corpusPath") or reg.get("corpusRoot")
elif isinstance(reg, list):
    for e in reg:
        if isinstance(e, dict) and e.get("corpusManifestSha256"):
            cms = e["corpusManifestSha256"]
            corpus_path = e.get("corpusPath") or e.get("corpusRoot")
            break

mani_path = HERE / "f1-20260905-generic-manifest.json"
mani_sha = hashlib.sha256(mani_path.read_bytes()).hexdigest()
inst_path = HERE / "f1-20260905-generic-install-receipt.json"
inst_sha = hashlib.sha256(inst_path.read_bytes()).hexdigest() \
    if inst_path.exists() else None

# The pin-state scripts (gates, adjudicator) encode the pre-commit
# window: clone HEAD == pin 8457672 with pre-state bytes in the working
# tree. After the LOCAL install commit, clone HEAD is the F1 commit —
# so they are re-run against a DETACHED GIT WORKTREE of the pin commit
# (byte-identical tree; their HEAD-pin and clean-status assertions hold
# there unchanged). The worktree is removed afterwards; the clone's own
# HEAD, branch and working tree are never touched.
# verify_install re-runs against the REAL clone with F1_VERIFY_BASE=HEAD^
# (HEAD = the F1 commit; the pre-state pin lives at HEAD^).
wt_dir = Path(tempfile.mkdtemp(prefix="f1-pin-worktree-"))
wt_add = subprocess.run(
    ["git", "-C", str(CLONE), "worktree", "add", "--detach",
     str(wt_dir), parent], capture_output=True, text=True,
    encoding="utf-8")
worktree_record = {
    "command": f"git worktree add --detach <tmp> {parent[:7]}",
    "exitStatus": wt_add.returncode,
    "stdout": wt_add.stdout, "stderr": wt_add.stderr}
if wt_add.returncode != 0:
    ok = False
    print(f"FAIL worktree add: rc={wt_add.returncode}")

verifications = {}
try:
    verifications["gates"] = check(run(
        [sys.executable, "-X", "utf8", str(HERE / "f1_gates_20260905.py")],
        env={"F1_CLONE_DIR": str(wt_dir)}), label="gates")
    verifications["adjudication"] = check(run(
        [sys.executable, "-X", "utf8",
         str(HERE / "f1_adjudicate_blind_r1_20260905.py")],
        env={"F1_CLONE_DIR": str(wt_dir)}), label="adjudicator")
finally:
    wt_rm = subprocess.run(
        ["git", "-C", str(CLONE), "worktree", "remove", "--force",
         str(wt_dir)], capture_output=True, text=True, encoding="utf-8")
    wt_pr = subprocess.run(
        ["git", "-C", str(CLONE), "worktree", "prune"],
        capture_output=True, text=True, encoding="utf-8")
    worktree_record["removeExitStatus"] = wt_rm.returncode
    worktree_record["pruneExitStatus"] = wt_pr.returncode
    if wt_rm.returncode != 0 or wt_pr.returncode != 0:
        ok = False
        print("FAIL worktree teardown")

verifications["verifyInstall"] = check(run(
    [sys.executable, "-X", "utf8",
     str(HERE / "f1_verify_install_20260905.py")],
    env={"F1_VERIFY_BASE": "HEAD^"}), label="verify_install")

eyeball_path = HERE / "f1-staged-eyeball-20260905.txt"
eyeball = eyeball_path.read_text(encoding="utf-8") \
    if eyeball_path.exists() else None
if eyeball is None:
    ok = False
    print("FAIL staged-eyeball transcript missing")

# off-footprint: entries that differ parent..HEAD outside the products
live = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
live_by_id = {e["Id"]: e for e in live["Entries"]}
head_by_id = {e["Id"]: e for e in json.loads(
    git("show", f"{parent}:termbase.v2.json"))["Entries"]}


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


off_footprint = sorted(
    eid for eid, e in head_by_id.items()
    if eid not in PRODUCTS and canon(e) != canon(live_by_id.get(eid, {})))
if off_footprint:
    ok = False

# R2-product protection report (byte-identical + repair still landed).
# Expected institutional windows per product: only t_ea2a427c7aba's R2
# repair re-attributed Dehui speaker rows (3 T48n2025 windows); 057's
# repair was compiled-by-disciples wording and 968's was a search alias
# — their expected institutional-window set is legitimately EMPTY.
R2_EXPECTED_WINDOWS = {
    "t_ea2a427c7aba": {"1113a21", "1143a07", "1143a12"},
    "t_057cc9ea8755": set(),
    "t_968a2f97c9ff": set(),
}
r2_protection = []
for eid in R2_PRODUCTS:
    e_live = live_by_id.get(eid, {})
    e_base = head_by_id.get(eid, {})
    windows = []
    for s in e_live.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if (o.get("RelPath") == "T/T48/T48n2025.xml"
                    and o.get("MasterName") is None
                    and any(cm.get("MasterName") == "Dongyang Dehui"
                            for cm in o.get("ContextMasters") or [])):
                windows.append(o.get("FromLb"))
    windows_ok = set(windows) == R2_EXPECTED_WINDOWS[eid]
    r2_protection.append({
        "entry": eid,
        "byteIdenticalParentToHead": canon(e_live) == canon(e_base),
        "institutionalWindowsIntact": sorted(windows),
        "institutionalWindowsAsExpected": windows_ok,
    })
    if not (r2_protection[-1]["byteIdenticalParentToHead"] and windows_ok):
        ok = False
        print(f"FAIL r2 protection: {eid}")

# census-law report: the class this lane completes
dehui_rows = []
for eid, e in sorted(live_by_id.items()):
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            if o.get("MasterName") == "Dehui":
                dehui_rows.append(f"{eid} {o.get('FromLb')}")
census = {
    "law": "SPEC §7: zero MasterName == 'Dehui' rows anywhere in the "
           "installed termbase",
    "remainingRows": dehui_rows,
    "holds": not dehui_rows,
}
if dehui_rows:
    ok = False

# carry-over notes
carry_over = {
    "shuitou": ("t_d7725cb0c8c0 水頭 remains report-only (verified in "
                "the R2 bundle: 「水頭水頭五更燒湯」 verbatim in the occ-2 "
                "full kwic); X63n1250 0648c22 future-evidence lead stands"),
    "withdrawal": ("replace-only lane, no withdrawals (the C1 "
                   "ID-replacement record lives in R2's bundle)"),
}

# stale-SourceTexts fleet observation
stale = sorted(eid for eid, e in live_by_id.items()
               for s in e.get("Senses") or []
               if any(rel in RETIRED for rel in s.get("SourceTexts")
                      or []))
stale_report = {
    "class": ("pre-existing: entries whose sense-level SourceTexts "
              "still LIST a retired rel while citing zero retired "
              "occurrences/anchors (discovered by the R2 census; "
              "includes 水頭); out of F1 scope — disclosed for a future "
              "reconcile lane"),
    "count": len(stale), "entries": stale,
}

bundle = {
    "schemaVersion": "f1-archive-bundle",
    "lane": "F1",
    "spec": "SPEC_F1_20260905.md",
    "clone": {
        "finalHead": head, "parentHead": parent,
        "statusPorcelain": porcelain.strip(),
        "diffStatParentToHead": diff_stat.strip(),
        "remote": ("local commit only at bundle time; push + main "
                   "publication follow under the user's 2026-09-04 "
                   "authorization as one cycle covering R2+F1"),
    },
    "corpus": {"registryCorpusManifestSha256": cms,
               "corpusPath": corpus_path},
    "manifest": {"path": str(mani_path), "sha256": mani_sha},
    "installReceipt": {"path": str(inst_path), "sha256": inst_sha},
    "verifications": verifications,
    "postCommitReRun": {
        "mechanism": (
            "gates + adjudicator re-run against a detached git worktree "
            f"of the pin commit {PIN} (byte-identical tree; their "
            "HEAD-pin and clean-status assertions hold there unchanged); "
            "verify_install re-run against the real clone with "
            "F1_VERIFY_BASE=HEAD^ (HEAD = the F1 install commit, "
            "pre-state pin at HEAD^). Env-override support added "
            "2026-09-05 in f1_transform_20260905.py / f1_gates_20260905."
            "py / f1_verify_install_20260905.py, defaults unchanged "
            "(mechanism inherited from R2)."),
        "worktree": worktree_record,
        "verifyInstallBase": "HEAD^",
    },
    "stagedEyeballTranscript": {
        "path": str(eyeball_path) if eyeball_path.exists() else None,
        "text": eyeball},
    "offFootprint": {"changedOutsideProducts": off_footprint,
                     "law": "empty"},
    "r2ProductProtection": r2_protection,
    "dehuiCensus": census,
    "carryOver": carry_over,
    "staleSourceTextsObservation": stale_report,
    "allPassed": ok,
}
out_path = HERE / "f1-archive-bundle-20260905.json"
out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2)
                    + "\n", encoding="utf-8", newline="")
print(json.dumps({"allPassed": ok,
                  "finalHead": head[:7], "parentHead": parent[:7],
                  "offFootprint": len(off_footprint),
                  "dehuiCensusRows": len(dehui_rows),
                  "staleSourceTexts": len(stale),
                  "bundle": str(out_path)}, indent=2))
raise SystemExit(0 if ok else 1)
