#!/usr/bin/env python3
"""Machine-write the R2 archive bundle (SPEC_R2_20260903.md §5).

Run AFTER install + LOCAL clone commit. Every verification is re-run
LIVE here (subprocess, exit status + raw stdout/stderr captured) — the
bundle never transcribes in-session claims. Post-commit re-run mode:
the pin-state scripts (gates, adjudicator) run against a detached git
worktree of the pin commit; verify_install runs against the real clone
with R2_VERIFY_BASE=HEAD^ (see postCommitReRun in the output). Records:

  - final HEAD + parent HEAD of the agent clone; git status
    --porcelain; git diff --stat parent..HEAD
  - corpus manifest sha (registry corpusManifestSha256) + corpus path
  - installed dictionary manifest sha + install receipt sha
  - fresh re-runs: r2 gates, r2 verify_install, r2 adjudicator
    (commands + rc + raw output each)
  - staged-eyeball transcript file (produced between stage and install)
  - off-footprint report (entries outside the 3 products that differ
    parent..HEAD — must be none)
  - withdrawal/ID-replacement report: merge-dict-entries.js line 47
    (exact bytes read from the working tree) + the survivor's alias
  - 水頭 claim-support report: full kwic of occurrence 2 from the
    INSTALLED entry + the Explanation sentence it supports, with the
    containment assertion
  - sibling-Dehui follow-up flag: the 2 untouched rows (entry, si, oi,
    rel, lb) + user scope decision
  - stale-SourceTexts observation: fleet count of entries whose
    SourceTexts list a retired rel (pre-existing class, disclosed)

Outputs maintenance/r2-archive-bundle-20260903.json. Exit 0 iff every
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
MERGE_JS = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
                r"\eng\tools\merge-dict-entries.js")
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
FOLLOW_UP = (("t_ab715aa474d5", 1, 2, "T/T48/T48n2025.xml", "1144b03"),
             ("t_351fa42d396b", 1, 1, "T/T48/T48n2025.xml", "1127c04"))
ok = True


def run(cmd: list[str], cwd: Path | None = None,
        env: dict | None = None) -> dict:
    global ok
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

mani_path = HERE / "r2-20260903-generic-manifest.json"
mani_sha = hashlib.sha256(mani_path.read_bytes()).hexdigest()
inst_path = HERE / "r2-20260903-generic-install-receipt.json"
inst_sha = hashlib.sha256(inst_path.read_bytes()).hexdigest() \
    if inst_path.exists() else None

# The pin-state scripts (gates, adjudicator) encode the pre-commit
# window: clone HEAD == pin 145b090 with pre-state bytes in the working
# tree. After the LOCAL install commit, clone HEAD is the R2 commit —
# so they are re-run against a DETACHED GIT WORKTREE of the pin commit
# (byte-identical tree; their HEAD-pin and clean-status assertions hold
# there unchanged). The worktree is removed afterwards; the clone's own
# HEAD, branch and working tree are never touched.
# verify_install re-runs against the REAL clone with R2_VERIFY_BASE=HEAD^
# (HEAD = the R2 commit; the pre-state pin lives at HEAD^).
wt_dir = Path(tempfile.mkdtemp(prefix="r2-pin-worktree-"))
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
        [sys.executable, "-X", "utf8", str(HERE / "r2_gates_20260903.py")],
        env={"R2_CLONE_DIR": str(wt_dir)}), label="gates")
    verifications["adjudication"] = check(run(
        [sys.executable, "-X", "utf8",
         str(HERE / "r2_adjudicate_blind_r1_20260903.py")],
        env={"R2_CLONE_DIR": str(wt_dir)}), label="adjudicator")
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
     str(HERE / "r2_verify_install_20260903.py")],
    env={"R2_VERIFY_BASE": "HEAD^"}), label="verify_install")

eyeball_path = HERE / "r2-staged-eyeball-20260903.txt"
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

# withdrawal / ID-replacement report (exact working-tree bytes)
js_lines = MERGE_JS.read_text(encoding="utf-8").splitlines()
line47 = js_lines[46] if len(js_lines) > 46 else "<missing>"
withdrawal_report = {
    "claim": ("t_1a6cdc16c248 (unattested punctuation-normalization "
              "duplicate of 一不成，二不是) was replaced by "
              "t_968a2f97c9ff (the corpus-attested canonical entry); "
              "merge-dict-entries.js:47 carries the mapping; R2 adds "
              "the 顿号 search alias '一不成、二不是' to the survivor so "
              "the withdrawn form stays findable"),
    "mergeScript": str(MERGE_JS),
    "mergeScriptSha256": hashlib.sha256(MERGE_JS.read_bytes()).hexdigest(),
    "line47": line47.strip(),
    "firstInstalledWithdrawal": "local clone only (no push)",
}

# 水頭 claim-support report (installed bytes)
st = live_by_id.get("t_d7725cb0c8c0")
if not st:
    ok = False
    shuitou = {"error": "t_d7725cb0c8c0 absent from installed clone"}
else:
    occ2 = None
    occs = (st.get("Senses") or [{}])[0].get("Occurrences") or []
    for o in occs:
        if o.get("RelPath") == "T/T48/T48n2025.xml" and o.get("FromLb") \
                == "1133a20":
            occ2 = o
            break
    kwic = str((occ2 or {}).get("Kwic") or "")
    duty = "水頭水頭五更燒湯"
    shuitou = {
        "entry": "t_d7725cb0c8c0", "sourceTerm": st.get("SourceTerm"),
        "reportOnly": True,
        "occurrenceCount": len(occs),
        "occurrence2": {"RelPath": (occ2 or {}).get("RelPath"),
                        "FromLb": (occ2 or {}).get("FromLb"),
                        "ToLb": (occ2 or {}).get("ToLb"),
                        "fullKwic": kwic},
        "dutyListInKwic": duty in kwic,
        "supportedExplanationSentence": (
            "one code states its concrete responsibility as heating "
            "washing water and arranging the community's basins and "
            "towels."),
        "explanationContainsSentence": (
            "heating washing water" in str(
                (st.get("Senses") or [{}])[0].get("Explanation") or "")),
        "note": ("the earlier doubt was a 90-character display "
                 "truncation artifact; the full stored kwic carries the "
                 "duty list verbatim. No product edit (SPEC §6). "
                 "X63n1250 0648c22 「水頭之職…」 recorded as a "
                 "future-evidence lead."),
    }
    if not (shuitou["dutyListInKwic"]
            and shuitou["explanationContainsSentence"]):
        ok = False

# sibling-Dehui follow-up flag (untouched rows)
sibling_flag = []
for eid, si, oi, rel, lb in FOLLOW_UP:
    e = live_by_id.get(eid, {})
    o = ((e.get("Senses") or [{}])[si - 1].get("Occurrences")
         or [{}])[oi - 1] if len(
        (e.get("Senses") or [{}])[si - 1].get("Occurrences") or []) \
        >= oi else {}
    sibling_flag.append({
        "entry": eid, "si": si, "oi": oi, "relPath": o.get("RelPath"),
        "fromLb": o.get("FromLb"), "masterName": o.get("MasterName"),
        "disposition": ("user decision 2026-09-03: dedicated follow-up "
                        "lane with full-case re-reads; byte-identical "
                        "to the pre-R2 state (verified by "
                        "r2_verify_install law 7g)"),
        "identityConfirmed": (o.get("RelPath") == rel
                              and o.get("FromLb") == lb),
    })
    if not sibling_flag[-1]["identityConfirmed"]:
        ok = False

# stale-SourceTexts fleet observation
stale = sorted(eid for eid, e in live_by_id.items()
               for s in e.get("Senses") or []
               if any(rel in RETIRED for rel in s.get("SourceTexts")
                      or []))
stale_report = {
    "class": ("pre-existing: entries whose sense-level SourceTexts "
              "still LIST a retired rel while citing zero retired "
              "occurrences/anchors (discovered by the R2 census; "
              "includes 水頭); out of R2 scope — disclosed for a future "
              "reconcile lane"),
    "count": len(stale), "entries": stale,
}

bundle = {
    "schemaVersion": "r2-archive-bundle",
    "lane": "R2",
    "spec": "SPEC_R2_20260903.md (+AMENDMENT 1)",
    "clone": {
        "finalHead": head, "parentHead": parent,
        "statusPorcelain": porcelain.strip(),
        "diffStatParentToHead": diff_stat.strip(),
        "remote": "NOT PUSHED (hard rule: local commit only)",
    },
    "corpus": {"registryCorpusManifestSha256": cms,
               "corpusPath": corpus_path},
    "manifest": {"path": str(mani_path), "sha256": mani_sha},
    "installReceipt": {"path": str(inst_path), "sha256": inst_sha},
    "verifications": verifications,
    "postCommitReRun": {
        "mechanism": (
            "gates + adjudicator re-run against a detached git worktree "
            "of the pin commit 145b090 (byte-identical tree; their "
            "HEAD-pin and clean-status assertions hold there unchanged); "
            "verify_install re-run against the real clone with "
            "R2_VERIFY_BASE=HEAD^ (HEAD = the R2 install commit, "
            "pre-state pin at HEAD^). Env-override support added "
            "2026-09-04 in r2_transform_20260903.py / r2_gates_20260903."
            "py / r2_verify_install_20260903.py, defaults unchanged."),
        "worktree": worktree_record,
        "verifyInstallBase": "HEAD^",
    },
    "stagedEyeballTranscript": {
        "path": str(eyeball_path) if eyeball_path.exists() else None,
        "text": eyeball},
    "offFootprint": {"changedOutsideProducts": off_footprint,
                     "law": "empty"},
    "withdrawalReport": withdrawal_report,
    "shuitouClaimSupport": shuitou,
    "siblingDehuiFollowUp": sibling_flag,
    "staleSourceTextsObservation": stale_report,
    "allPassed": ok,
}
out_path = HERE / "r2-archive-bundle-20260903.json"
out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2)
                    + "\n", encoding="utf-8", newline="")
print(json.dumps({"allPassed": ok,
                  "finalHead": head[:7], "parentHead": parent[:7],
                  "offFootprint": len(off_footprint),
                  "staleSourceTexts": len(stale),
                  "bundle": str(out_path)}, indent=2))
raise SystemExit(0 if ok else 1)
