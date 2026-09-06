#!/usr/bin/env python3
"""Campaign audit-500 checkpoint (fires after the r9 install).

Standing rule (user, 2026-08-25): every 500 completed installs triggers
a batch audit over the newest installed entries. Counter reached 403 at
campaign start (280 creates + 123 r7-depth replaces since the 515-entry
attribution census); the r9 lane's creates push it to 548.

Scope — newest installed rows (cohort manifests, chronological):
    fresh10k-r7        123 create
    fresh10k-r7-depth  123 replace (same ids as r7 — the depth re-install)
    fresh10k-r8        116 create
    fresh10k-r9        145 create (create lanes; script exits if absent)
= 507 COMPLETED INSTALLS (the unit the 500-rule counts), 384 distinct
entries after dedupe (r7-depth rows supersede their r7 originals; audits
run against the CURRENT public termbase either way). Over-coverage is
free; q3/s1's 41 older creates predate r7 and were covered by the
515-entry attribution census.

Checks per entry against the CURRENT public termbase, CURRENT registry,
and CURRENT corpus (drift detection — the point is catching register
creep, tier-mix regression, and citation drift AT SCALE, row-level
gates having passed at install time):
  A. tier law: no occurrence cites a registry tier>=3 work NOW
     (a post-install registry demotion IS a finding to adjudicate)
  B. family law: >=2 independent tier<3 work families per entry
  C. attribution ladder: every occurrence carries MasterName or
     ActorAttribution(Status+ActorLabel)
  D. claim anchors: every ClaimAnchors[].ClaimText appears
     (whitespace-stripped) inside the reading-text projection of the
     work it cites
  E. kwic: every occurrence Kwic is a contiguous ws-stripped slice of
     its work's reading-text projection (keep-tail law)
  F. public presence: every audited id exists in the clone termbase;
     no duplicate Ids; create-cohort terms not shadowed by dupes
  G. prose evidence (user directive 2026-09-06): every Chinese string
     quoted in Explanation/Note is a substring of that sense's retained
     Kwics/headword (dangling-quote law #10), and every roster master
     named in prose is grounded in the sense's evidence rows, kwics, or
     cited work titles (outside-knowledge ban). Law + whitelist files
     shared with lane_prose_evidence_check.py / the promote gate.

Output: maintenance/audit-campaign-500-20260906.json binding the
public termbase sha. Verdict PASS only with zero findings; drift-class
findings (A) are reported for coordinator adjudication, not auto-pass.
"""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import lane_prose_evidence_check as prose

BUILD = Path(__file__).resolve().parents[1]
M = BUILD / "maintenance"
REPO = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator")
REG = json.loads((REPO / "Assets" / "Data" / "zen-source-authority.json")
                 .read_text(encoding="utf-8-sig"))
REG = {e["RelPath"]: e for e in REG["entries"]}
CORPUS = Path(r"C:\programmieren\CbetaZenTexts\xml-p5")
CLONE_TB = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations"
                r"\termbase.v2.json")

COHORT_MANIFESTS = [
    ("fresh10k-r7", "create"),
    ("fresh10k-r7-depth", "replace"),
    ("fresh10k-r8", "create"),
    ("fresh10k-r9", "create"),
]

# ---- reading-text projection (keep-tail law, lb-aware not needed here)
_SKIP_TAGS = {"note", "app", "rdg", "choice", "corr", "sic", "lem"}
_ws = re.compile(r"\s+")


def _emit(el, out):
    tag = el.tag.split("}")[-1] if isinstance(el.tag, str) else ""
    if tag in _SKIP_TAGS:
        return
    if el.text:
        out.append(el.text)
    for child in el:
        _emit(child, out)
        if child.tail:
            out.append(child.tail)


_doc_cache: dict[str, str] = {}


def work_text(rel: str) -> str:
    if rel not in _doc_cache:
        root = ET.parse(CORPUS / rel).getroot()
        buf: list[str] = []
        _emit(root, buf)
        _doc_cache[rel] = _ws.sub("", "".join(buf))
    return _doc_cache[rel]


# ---- scope
rows = []
for cohort, mode in COHORT_MANIFESTS:
    p = M / f"{cohort}-generic-manifest.json"
    if not p.is_file():
        sys.exit(f"manifest missing: {cohort} — run after its install")
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    for prod in d["products"]:
        rows.append({"cohort": cohort, "id": prod["id"],
                     "mode": prod.get("termsMode", mode)})
install_events = len(rows)
# dedupe by id keeping the NEWEST cohort row (r7-depth supersedes r7;
# later cohorts never share ids with earlier ones — verified below)
by_id: dict[str, dict] = {}
for r in rows:
    if r["id"] in by_id and by_id[r["id"]]["cohort"] != "fresh10k-r7":
        sys.exit(f"unexpected id collision: {r['id']} in "
                 f"{by_id[r['id']]['cohort']} and {r['cohort']}")
    by_id[r["id"]] = r
rows = list(by_id.values())
counts = {c: sum(1 for r in rows if r["cohort"] == c)
          for c, _ in COHORT_MANIFESTS if any(r["cohort"] == c for r in rows)}
print(f"audit scope: {install_events} completed installs, "
      f"{len(rows)} distinct entries "
      f"({', '.join(f'{c}={n}' for c, n in counts.items())})")

# ---- public termbase
tb_bytes = CLONE_TB.read_bytes()
tb_sha = hashlib.sha256(tb_bytes).hexdigest()
public = json.loads(tb_bytes.decode("utf-8-sig"))
by_id = {}
dup_ids = []
for e in public["Entries"]:
    if e.get("Id") in by_id:
        dup_ids.append(e["Id"])
    by_id[e["Id"]] = e

findings = []

# ---- check G state (prose-evidence law; whitelists are per cohort)
PROSE_STATE = prose.load_state()
PROSE_WL: dict[str, set[str]] = {}
for cohort, _ in COHORT_MANIFESTS:
    p = M / f"{cohort}-prose-adjudications.json"
    if p.is_file():
        for wl_eid, wl_rows in (json.loads(p.read_text(encoding="utf-8-sig"))
                                or {}).items():
            PROSE_WL.setdefault(wl_eid, set()).update(
                f["name"] for f in wl_rows if f.get("name"))

# ---- per-entry checks
fam_fail = tier_fail = attr_fail = anchor_fail = kwic_fail = missing = 0
prose_fail = 0
anchor_checked = kwic_checked = 0
for r in rows:
    eid = r["id"]
    e = by_id.get(eid)
    if e is None:
        missing += 1
        findings.append({"id": eid, "cohort": r["cohort"], "check": "F",
                         "detail": "not present in public termbase"})
        continue
    fams = {}
    tier_bad = []
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            rel = o.get("RelPath")
            tier = int(REG.get(rel, {}).get("Tier", 3))
            if tier >= 3:
                tier_bad.append(rel)
            else:
                fams.setdefault(REG[rel]["work_id"], tier)
            # C. attribution ladder
            aa = o.get("ActorAttribution") or {}
            if not o.get("MasterName") and not (aa.get("Status")
                                                and aa.get("ActorLabel")):
                attr_fail += 1
                findings.append({"id": eid, "cohort": r["cohort"],
                                 "check": "C",
                                 "detail": f"occurrence {rel} lacks "
                                           f"MasterName/ActorAttribution"})
            # E. kwic slice
            kw = _ws.sub("", o.get("Kwic") or "")
            if kw:
                try:
                    full = work_text(rel)
                    kwic_checked += 1
                    if kw not in full:
                        kwic_fail += 1
                        findings.append({
                            "id": eid, "cohort": r["cohort"], "check": "E",
                            "detail": f"kwic not contiguous slice of {rel}"})
                except (ET.ParseError, OSError):
                    findings.append({"id": eid, "cohort": r["cohort"],
                                     "check": "E",
                                     "detail": f"cannot read corpus {rel}"})
        # D. claim anchors
        for a in s.get("ClaimAnchors") or []:
            ct = a.get("ClaimText") or ""
            rel = a.get("RelPath") or s.get("RelPath")
            if ct and rel:
                try:
                    full = work_text(rel)
                    anchor_checked += 1
                    if _ws.sub("", ct) not in full:
                        anchor_fail += 1
                        findings.append({
                            "id": eid, "cohort": r["cohort"], "check": "D",
                            "detail": f"ClaimText not found in {rel}: "
                                      f"{ct[:40]}…"})
                except (ET.ParseError, OSError):
                    pass  # already reported under E for the same work
    if tier_bad:
        tier_fail += 1
        findings.append({"id": eid, "cohort": r["cohort"], "check": "A",
                         "detail": f"cites tier>=3 works NOW: "
                                   f"{sorted(set(tier_bad))[:3]} "
                                   f"(registry drift — adjudicate)"})
    if len(fams) < 2:
        fam_fail += 1
        findings.append({"id": eid, "cohort": r["cohort"], "check": "B",
                         "detail": f"only {len(fams)} tier<3 work families"})
    # G. prose evidence (runs only for present entries; skips an entry
    # entirely on any single finding to keep the finding list tight)
    pfs, _, _ = prose.entry_findings(e, e.get("SourceTerm") or "",
                                     PROSE_STATE, PROSE_WL.get(eid))
    if pfs:
        prose_fail += 1
        findings.append({"id": eid, "cohort": r["cohort"], "check": "G",
                         "detail": "; ".join(f"s{f['sense']} {f['field']} "
                                             f"{f['run'][:40]}"
                                             for f in pfs[:3])})
if dup_ids:
    findings.append({"id": dup_ids[:3], "cohort": "*", "check": "F",
                     "detail": f"{len(dup_ids)} duplicate Ids in termbase"})

out = {
    "schema": "campaign-audit-500.v1",
    "rule": "user directive 2026-08-25: batch audit every 500 completed "
            "installs; this is crossing #1 (counter 403 -> 548 via r9)",
    "scope": [{"cohort": c, "entries": sum(1 for r in rows
                                            if r["cohort"] == c)}
              for c, _ in COHORT_MANIFESTS],
    "publicTermbaseSha256": tb_sha,
    "checks": {"A_tierDrift": tier_fail, "B_families": fam_fail,
               "C_attribution": attr_fail, "D_claimAnchors": anchor_fail,
               "E_kwic": kwic_fail, "F_presence": missing,
               "G_proseEvidence": prose_fail},
    "coverage": {"anchorsChecked": anchor_checked,
                 "kwicsChecked": kwic_checked},
    "findings": findings,
    "verdict": "PASS" if not findings else "FINDINGS",
}
out_path = M / "audit-campaign-500-20260906.json"
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
print(json.dumps({k: out[k] for k in ("scope", "checks", "coverage",
                                      "verdict")},
                 ensure_ascii=False, indent=2))
print("wrote", out_path.name)
for f in findings[:20]:
    print(f"  [{f['check']}] {f['cohort']} {f['id']}: {f['detail'][:100]}")
