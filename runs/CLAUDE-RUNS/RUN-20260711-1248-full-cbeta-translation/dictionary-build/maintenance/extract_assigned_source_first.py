#!/usr/bin/env python3
"""Cohort-parametric, higher-tier-first bounded source extraction."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

import zc

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[3]
AUTHORITY = json.loads(
    (REPO / "Assets/Data/zen-source-authority.json").read_text(encoding="utf-8"))
TIERS = {row["RelPath"]: int(row["Tier"]) for row in AUTHORITY["entries"]}

def evidence_floor(hits: int) -> int:
    if hits <= 0:
        return 0
    if hits < 3:
        return hits
    if hits < 20:
        return 3
    if hits < 100:
        return 4
    if hits < 500:
        return 6
    if hits < 2_000:
        return 7
    if hits < 10_000:
        return 8
    return 10


def write(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)

def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def extract_rows(selection, counts, *, tiers, find_fn, work_id_fn, candidate_reserve=3):
    extracted = []
    for row in selection:
        identity = row.get("identityId") or row["id"]
        term = row["term"]
        floor = int(row["requiredFloor"])
        count_row = counts[identity]
        hit_count = count_row.get("hits", count_row.get("corpusHits"))
        if isinstance(hit_count, bool) or not isinstance(hit_count, int):
            hit_count = sum(int(item[1]) for item in count_row["per_file"])
        actual_floor = evidence_floor(hit_count)
        base_target = floor + candidate_reserve
        target = max(base_target, actual_floor + 3)
        ranked = sorted(
            counts[identity]["per_file"],
            key=lambda item: (tiers.get(item[0], 3), item[0]))
        candidates = []
        seen_works = set()
        seen_families = set()
        for rel_path, _ in ranked:
            tier = tiers.get(rel_path, 3)
            # Candidate reserve is for additional strong witnesses, not a
            # license to pad a satisfied Tier-1/2 floor with lamps.
            if tier == 3 and len(candidates) >= floor:
                break
            work_id = work_id_fn(rel_path)
            provisional_key = work_id
            if work_id in seen_works or provisional_key in seen_families:
                continue
            source_hits = find_fn(rel_path, term, ctx=500, limit=1)
            if not source_hits:
                continue
            hit = source_hits[0]
            context = hit["window"]
            candidates.append({
                "relPath": rel_path,
                "fromLb": hit["fromLb"],
                "toLb": hit.get("toLb") or hit["fromLb"],
                "workId": work_id,
                "provisionalWorkKey": provisional_key,
                "familyAdjudicationRequired": True,
                "tier": tier,
                "context": context,
                "spanText": term,
                "matchedTerm": term,
                "contextSha256": hashlib.sha256(context.encode()).hexdigest(),
                "spanSha256": hashlib.sha256(term.encode()).hexdigest(),
            })
            seen_works.add(work_id)
            seen_families.add(provisional_key)
            if len(candidates) == target:
                break
        if len(candidates) < actual_floor:
            raise RuntimeError(
                f"{identity}: only {len(candidates)} independent candidates for "
                f"evidence floor {actual_floor} derived from {hit_count} hits")
        lamp_count = sum(item["tier"] == 3 for item in candidates)
        extracted.append({
            "id": identity,
            "term": term,
            "requiredFloor": floor,
            "actualHitCount": hit_count,
            "evidenceFloor": actual_floor,
            "researchCandidateReserve": candidate_reserve,
            "baseCandidateTarget": base_target,
            "candidateTarget": target,
            "candidateSupplyExhausted": len(candidates) < target,
            "sourceCandidates": candidates,
            "tier3Consulted": lamp_count > 0,
            "lampFallbackCount": lamp_count,
            "lampPolicy": (
                "minimal last-resort fill after Tier 1/2 exhaustion"
                if lamp_count else "not consulted; Tier 1/2 filled the floor"),
        })
    return extracted


def build_documents(cohort, extracted):
    return ({
        "schemaVersion": "assigned-source-first-extraction.v1",
        "cohort": cohort,
        "rows": extracted,
    }, {
        "schemaVersion": "bounded-research-skeleton.v1",
        "cohort": cohort,
        "rows": [{
            "id": row["id"],
            "term": row["term"],
            "candidateHashes": [
                hashlib.sha256(json.dumps(
                    candidate, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                for candidate in row["sourceCandidates"]
            ],
        } for row in extracted],
    })


def assigned_cohort_from_output_name(name: str) -> tuple[str, str]:
    """Parse ordinary and explicitly corrected cohort labels fail-closed."""
    match = re.search(
        r"(non-iriya-v7-depth-regeneration-(r\d+[a-z]*))-extraction-output-b\.json$",
        name,
    )
    if not match:
        raise ValueError("extraction output does not encode an assigned cohort")
    prefix, cohort_lower = match.groups()
    return prefix, cohort_lower.upper()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extraction-output", required=True, type=Path)
    parser.add_argument("--research-skeleton", required=True, type=Path)
    parser.add_argument("--timegate", type=Path)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--count", type=Path)
    parser.add_argument("--viability-receipt", type=Path)
    args = parser.parse_args()
    try:
        prefix, cohort = assigned_cohort_from_output_name(args.extraction_output.name)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    maintenance = args.extraction_output.resolve().parent
    bindings = (args.timegate, args.selection, args.count, args.viability_receipt)
    if not all(bindings):
        raise SystemExit("extractor requires gate/selection/count/viability bindings")
    selection_path = args.selection.resolve()
    count_path = args.count.resolve()
    expected_selection = maintenance / f"{prefix}-selection-b.json"
    expected_count = maintenance / f"{prefix}-count-b.json"
    if selection_path != expected_selection or count_path != expected_count:
        raise SystemExit("selection/count path does not match cohort output scope")
    gate = json.loads(args.timegate.read_text(encoding="utf-8"))
    viability = json.loads(args.viability_receipt.read_text(encoding="utf-8"))
    if gate.get("schemaVersion") not in {
            "bounded-dictionary-timegate.v2",
            "bounded-dictionary-timegate.v3",
            "bounded-dictionary-timegate.v4"}:
        raise SystemExit("extractor requires a governed v2/v3/v4 artifact zero")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))["rows"]
    ids = [row.get("identityId") or row["id"] for row in selection]
    terms = [row["term"] for row in selection]
    identity_by_term = dict(zip(terms, ids))
    count_rows = json.loads(count_path.read_text(encoding="utf-8"))["results"]
    counts = {
        row.get("id") or identity_by_term[row["term"]]: row
        for row in count_rows
    }
    floors = [int(row["requiredFloor"]) for row in selection]
    candidate_reserve = gate.get("researchCandidateReserve")
    if isinstance(candidate_reserve, bool) or not isinstance(candidate_reserve, int) or candidate_reserve < 0:
        raise SystemExit("artifact zero has invalid researchCandidateReserve")
    if floors != gate.get("requiredFloors") or viability.get("ids") != ids or \
       viability.get("terms") != terms or viability.get("requiredFloors") != floors or \
       viability.get("researchCandidateReserve") != candidate_reserve or \
       viability.get("selectionSha256") != file_sha(selection_path) or \
       viability.get("countSha256") != file_sha(count_path) or \
       viability.get("hardPass") is not True:
        raise SystemExit("stale/tampered gate-selection-count-viability binding")
    extracted = extract_rows(
        selection, counts, tiers=TIERS, find_fn=zc.find, work_id_fn=zc.work_id,
        candidate_reserve=candidate_reserve)
    output, skeleton = build_documents(cohort, extracted)
    write(args.extraction_output, output)
    write(args.research_skeleton, skeleton)


if __name__ == "__main__":
    main()
