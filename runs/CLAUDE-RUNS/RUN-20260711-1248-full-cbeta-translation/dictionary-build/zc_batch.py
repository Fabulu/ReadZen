#!/usr/bin/env python3
"""Batch/persistent front end for the apparatus-clean Zen concordance.

The expensive normalized corpus is loaded once per process and shared by every
job.  Input can be ordinary CLI subcommands or JSON Lines on stdin.  This tool
does not change the evidence model: every result is produced by ``zc``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import zc


# Short headwords can occur only as a splice across larger lexical units.  Exact
# substring verification cannot distinguish that from the intended construction.
# Keep this list narrow and evidence-backed: each tuple is (left graph, right
# graph) immediately outside the headword.
HEADWORD_BOUNDARY_TRAPS = {
    "僧舉": (("山", "揚"),),
}


def headword_boundary_collision(term: str | None, kwic: str | None) -> bool:
    """Return true when every exact headword hit is a known boundary splice."""
    traps = HEADWORD_BOUNDARY_TRAPS.get(term or "")
    if not traps or not kwic:
        return False
    starts = []
    offset = 0
    while True:
        index = kwic.find(term, offset)
        if index < 0:
            break
        starts.append(index)
        offset = index + 1
    if not starts:
        return False
    for index in starts:
        left = kwic[index - 1] if index else ""
        right_index = index + len(term)
        right = kwic[right_index] if right_index < len(kwic) else ""
        if not any(left == trap_left and right == trap_right for trap_left, trap_right in traps):
            return False
    return True


def _occurrences(entry: dict):
    for sense_index, sense in enumerate(entry.get("Senses") or [], 1):
        for occurrence_index, occurrence in enumerate(sense.get("Occurrences") or [], 1):
            yield "occurrence", sense_index, occurrence_index, occurrence
        for occurrence_index, occurrence in enumerate(sense.get("ClaimAnchors") or [], 1):
            yield "claim-anchor", sense_index, occurrence_index, occurrence


def run_job(job: dict) -> dict:
    operation = job.get("op")
    if operation == "count":
        result = {"op": operation, "term": job["term"], **zc.count(job["term"], int(job.get("limit", 0)))}
        if not job.get("per_file"):
            result.pop("per_file", None)
        elif int(job.get("top_files", 0)) > 0:
            result["per_file"] = result["per_file"][: int(job["top_files"])]
        return result
    if operation == "verify":
        return {"op": operation, "rel": job["rel"], **zc.verify(job["rel"], job["kwic"])}
    if operation == "find":
        return {
            "op": operation,
            "rel": job["rel"],
            "term": job["term"],
            "matches": zc.find(job["rel"], job["term"], int(job.get("ctx", 48)), int(job.get("limit", 12))),
        }
    if operation == "context":
        return {
            "op": operation,
            "rel": job["rel"],
            **zc.context(job["rel"], job["lb"], int(job.get("chars", 2000)), job.get("kwic")),
        }
    if operation == "heads":
        return {
            "op": operation,
            "rel": job["rel"],
            "title": zc.title(job["rel"]),
            **zc.heads(job["rel"], job["lb"], int(job.get("limit", 12)), job.get("kwic")),
        }
    raise ValueError(f"unknown operation: {operation!r}")


def count_jobs(terms: list[str], *, per_file: bool = False, top_files: int = 0) -> list[dict]:
    """Count a CLI term batch with one corpus traversal, preserving CLI shape."""
    counted = zc.batch_count(terms)
    results = []
    for supplied in terms:
        normalized = zc._WS.sub("", supplied)
        result = {"op": "count", "term": supplied, **counted[normalized]}
        if not per_file:
            result.pop("per_file", None)
        elif top_files > 0:
            result["per_file"] = result["per_file"][:top_files]
        results.append(result)
    return results


def verify_entries(paths: list[Path]) -> dict:
    results = []
    for supplied in paths:
        path = supplied / "entry.v2.json" if supplied.is_dir() else supplied
        entry = json.loads(path.read_text(encoding="utf-8-sig"))
        failures = []
        total = 0
        totals_by_kind = {"occurrence": 0, "claim-anchor": 0}
        source_term = entry.get("SourceTerm")
        for evidence_kind, sense_index, occurrence_index, occurrence in _occurrences(entry):
            total += 1
            totals_by_kind[evidence_kind] += 1
            actual = zc.verify(occurrence["RelPath"], occurrence["Kwic"])
            boundary_collision = headword_boundary_collision(source_term, occurrence.get("Kwic"))
            claim_text = occurrence.get("ClaimText") if evidence_kind == "claim-anchor" else None
            invalid_claim_text = evidence_kind == "claim-anchor" and (
                not isinstance(claim_text, str)
                or not claim_text.strip()
                or claim_text not in occurrence.get("Kwic", "")
                or source_term in claim_text
            )
            if (
                not actual.get("ok")
                or actual.get("fromLb") != occurrence.get("FromLb")
                or actual.get("toLb") != occurrence.get("ToLb")
                or boundary_collision
                or invalid_claim_text
            ):
                failures.append({
                    "kind": (
                        "headword-boundary-collision" if boundary_collision
                        else "claim-anchor-contract" if invalid_claim_text
                        else evidence_kind
                    ),
                    "sense": sense_index,
                    "occurrence": occurrence_index,
                    "expected": {"FromLb": occurrence.get("FromLb"), "ToLb": occurrence.get("ToLb")},
                    "actual": actual,
                    **({"ClaimText": claim_text, "rule": "exact non-headword substring of Kwic"} if invalid_claim_text else {}),
                    **({"term": source_term, "trap": "山僧+舉揚"} if boundary_collision else {}),
                })
        results.append({
            "path": str(path),
            "id": entry.get("Id"),
            "term": entry.get("SourceTerm"),
            "verified": total,
            "occurrenceVerified": totals_by_kind["occurrence"],
            "claimAnchorVerified": totals_by_kind["claim-anchor"],
            "failures": failures,
        })
    return {
        "entries": len(results),
        "verified": sum(row["verified"] for row in results),
        "occurrenceVerified": sum(row["occurrenceVerified"] for row in results),
        "claimAnchorVerified": sum(row["claimAnchorVerified"] for row in results),
        "failureCount": sum(len(row["failures"]) for row in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    count_parser = sub.add_parser("count")
    count_parser.add_argument("terms", nargs="+")
    count_parser.add_argument("--per-file", action="store_true", help="include the per-document histogram")
    count_parser.add_argument("--top-files", type=int, default=0, help="with --per-file, retain only the top N documents")
    verify_parser = sub.add_parser("verify-entries")
    verify_parser.add_argument("paths", nargs="+", type=Path)
    sub.add_parser("serve", help="read JSON jobs from stdin and emit one JSON result per line")
    sub.add_parser("warm", help="normalize/cache all allowlisted documents")
    args = parser.parse_args()
    started = time.perf_counter()
    if args.command == "count":
        payload = {"results": count_jobs(
            args.terms,
            per_file=args.per_file,
            top_files=args.top_files,
        )}
    elif args.command == "verify-entries":
        payload = verify_entries(args.paths)
    elif args.command == "warm":
        payload = {"allowlisted": len(zc._allow()), "results": [zc._load(rel)[0] and rel for rel in zc._allow()]}
        payload["results"] = len(payload["results"])
    else:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                result = run_job(json.loads(line))
            except Exception as error:
                result = {"error": type(error).__name__, "message": str(error)}
            print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    payload["elapsedSeconds"] = round(time.perf_counter() - started, 3)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("failureCount") else 0


if __name__ == "__main__":
    raise SystemExit(main())
