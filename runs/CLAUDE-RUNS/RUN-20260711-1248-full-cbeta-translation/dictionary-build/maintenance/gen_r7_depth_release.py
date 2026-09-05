#!/usr/bin/env python3
"""Generate the fresh10k-r7-depth final-release authority doc + generic
publication manifest with live-computed SHAs. Run ONLY after the depth
blind review writes fresh10k-r7-depth-release-review.json with verdict
PASS. REPLACE-mode clone of gen_r7_release.py — every create-mode
precondition is INVERTED:
  - termsMode must be "replace" on every row
  - terms/<id> MUST already exist (the r7 install is the baseline)
  - row.termsBaselineSha256 == sha(terms/<id>/entry.v2.json) as it sits
    right now (install() re-checks this — no drift allowed between
    authorize and install)
  - SourceTerm MUST already be public
Runs under WSL python3 (reads /mnt/c paths for the public termbase)."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/runs/CLAUDE-RUNS/RUN-20260711-1248-full-cbeta-translation/dictionary-build"
PUBLIC_ROOT = "/mnt/c/temp/NewTranslationrepos/CbetaZenTranslations"
COHORT = "fresh10k-r7-depth"
EXPECTED_ROWS = 123
BASELINE_COHORT = "fresh10k-r7"


def canonical(v) -> str:
    return json.dumps(v, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    for stale in ("fresh10k-" + "r6", BASELINE_COHORT + "/products"):
        src = Path(__file__).read_text(encoding="utf-8")
        if stale in src.replace(f'"{COHORT}"', ""):
            sys.exit(f"stale template literal {stale!r} survived the clone")
    review_path = ROOT / f"fresh-build/{COHORT}/{COHORT}-release-review.json"
    if not review_path.exists():
        sys.exit("release review not found — run the depth blind adjudication first")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    schema = review.get("schemaVersion", review.get("schema"))
    if schema != f"{COHORT}-release-review.v1":
        sys.exit(f"unexpected review schema: {schema!r}")
    if review.get("verdict") != "PASS":
        sys.exit(f"release review verdict is {review.get('verdict')!r} — NOT authorizing")

    pmap = json.loads((ROOT / f"fresh-build/{COHORT}/products/product-map.json").read_text(encoding="utf-8"))
    rows = pmap["products"] if isinstance(pmap, dict) and "products" in pmap else pmap
    if len(rows) != EXPECTED_ROWS:
        sys.exit(f"expected {EXPECTED_ROWS} product rows, got {len(rows)}")

    public = json.loads(Path(PUBLIC_ROOT + "/termbase.v2.json").read_text(encoding="utf-8"))
    public_terms = {e.get("SourceTerm") for e in public["Entries"]}
    terms_root = ROOT / "terms"
    for r in rows:
        src = ROOT / f"fresh-build/{COHORT}/products" / r["id"]
        for fname, key in (("entry.v2.json", "entrySha256"), ("WORK.md", "workSha256"),
                           ("evidence.draft.json", "worksheetSha256")):
            actual = hashlib.sha256((src / fname).read_bytes()).hexdigest()
            if actual != r[key]:
                sys.exit(f"{r['id']} {fname}: map says {r[key]}, disk has {actual}")
        entry_bytes = (src / "entry.v2.json").read_bytes()
        entry_value = json.loads(entry_bytes)
        if entry_bytes != canonical(entry_value).encode("utf-8"):
            sys.exit(f"{r['id']}: entry.v2.json is not canonical serialization — parity would fail")
        if r.get("termsMode") != "replace":
            sys.exit(f"{r['id']}: termsMode is {r.get('termsMode')!r}, expected replace")
        baseline = terms_root / r["id"] / "entry.v2.json"
        if not baseline.is_file():
            sys.exit(f"{r['id']}: terms/{r['id']} missing — replace mode would fail")
        actual_baseline = hashlib.sha256(baseline.read_bytes()).hexdigest()
        if actual_baseline != r.get("termsBaselineSha256"):
            sys.exit(f"{r['id']}: termsBaselineSha256 says {r.get('termsBaselineSha256')!r}, "
                     f"terms/ has {actual_baseline} — baseline drift")
        if r["term"] not in public_terms:
            sys.exit(f"{r['id']}: SourceTerm {r['term']} NOT public — replace on what?")

    review_sha = hashlib.sha256(review_path.read_bytes()).hexdigest()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    authority = {
        "schemaVersion": "generic-dictionary-final-release-authority.v1",
        "cohort": COHORT,
        "authorizedBy": "coordinator (Claude)",
        "authorizedUtc": now,
        "releaseAuthorized": True,
        "basis": "Depth-repair lane per the 2026-09-05 depth floor rule: "
                 "corpus scan showed all 123 r7 entries under-collected "
                 "relative to their availability-scaled targets (ground-truth "
                 "corpus scan: zero genuinely thin). Targets scale with "
                 "non-lamp availability (>=200:10, >=100:8, >=50:7, >=20:6, "
                 ">=8:5, else min floor 4). Additions curated from lb-anchored "
                 "tier-1/2 packets by 4 agents (lamp excluded — counts only), "
                 "recompiled hardPass by the real compiler, promotion gate "
                 "verified append-only occurrence growth + tier<3 + "
                 "ws-stripped corpus contiguity + lb anchors + proof-clause "
                 "containment per addition; existing occurrences byte-equal; "
                 "replace-mode manifest pins each entry's terms baseline. "
                 "Blind delta review by the resumed independent reviewer with "
                 "fresh canaries; adjudication recorded in the lane.",
        "products": [{"id": r["id"], "entrySha256": r["entrySha256"]} for r in rows],
        "excluded": [],
    }
    authority_path = ROOT / f"maintenance/{COHORT}-final-release-authority.json"
    authority_path.write_text(json.dumps(authority, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    roster_sha = hashlib.sha256(Path("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/Assets/Data/lineage-masters.json").read_bytes()).hexdigest()
    node_sha = hashlib.sha256(Path("/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/eng/tools/merge-dict-entries.js").read_bytes()).hexdigest()

    manifest = {
        "schemaVersion": "generic-dictionary-publication-manifest.v1",
        "cohort": COHORT,
        "buildRoot": BUILD_ROOT,
        "termsRoot": "terms",
        "publicRoot": PUBLIC_ROOT,
        "stageRoot": f"fresh-build/{COHORT}/publication-stage",
        "installReceipt": f"maintenance/{COHORT}-generic-install-receipt.json",
        "authority": {
            "path": f"maintenance/{COHORT}-final-release-authority.json",
            "sha256": hashlib.sha256(authority_path.read_bytes()).hexdigest(),
        },
        "reviews": [
            {
                "path": f"fresh-build/{COHORT}/{COHORT}-release-review.json",
                "sha256": review_sha,
            }
        ],
        "products": [
            {
                "id": r["id"],
                "sourceDir": f"fresh-build/{COHORT}/products/{r['id']}",
                "entrySha256": r["entrySha256"],
                "worksheetSha256": r["worksheetSha256"],
                "workSha256": r["workSha256"],
                "termsMode": "replace",
                "termsBaselineSha256": r["termsBaselineSha256"],
            }
            for r in rows
        ],
        "roster": {
            "path": "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/Assets/Data/lineage-masters.json",
            "sha256": roster_sha,
        },
        "node": {
            "windowsNodeExe": "/mnt/c/Program Files/nodejs/node.exe",
            "script": {
                "path": "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator/eng/tools/merge-dict-entries.js",
                "sha256": node_sha,
            },
            "cwd": "/mnt/c/programmieren/MergeWorkCbeta/CBETA-Translator",
            "status": f"{COHORT}-ready",
        },
    }
    manifest_path = ROOT / f"maintenance/{COHORT}-generic-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("authority written:", authority_path.name)
    print("  review bound:", review_sha)
    print("manifest written:", manifest_path.name)
    print(f"  products: {len(rows)} (all replace-mode, baselines pinned)")
    for r in rows[:3]:
        print(f"  {r['id']} {r['term']}: {r['entrySha256']}")

if __name__ == "__main__":
    main()
