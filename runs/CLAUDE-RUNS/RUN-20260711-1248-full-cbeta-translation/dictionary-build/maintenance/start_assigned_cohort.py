#!/usr/bin/env python3
"""Canonical receipt-zero and viability launcher for assigned cohorts."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CREATE = HERE / "create_cohort_artifact_zero.py"
LAUNCH = HERE / "launch_assigned_cohort.py"

def governed_child_env() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("PYTHONPATH", "")
    parts = [str(ROOT)]
    if current:
        parts.append(current)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def expected_binding(args, entries):
    return {
        "selector": str(args.selector.resolve()),
        "priorUnion": str(args.prior_union.resolve()),
        "entries": [
            {"id": identity, "term": term, "requiredFloor": floor}
            for identity, term, floor in entries
        ],
        "reserveIds": sorted(set(args.reserve_id)),
        "researchCandidateReserve": args.research_candidate_reserve,
    }


def verify_resumable_gate(args, entries):
    gate = json.loads(args.timegate.read_text(encoding="utf-8"))
    expected_continuation = args.continuation_of or None
    actual_continuation = gate.get("continuationOf")
    if gate.get("schemaVersion") not in {
            "bounded-dictionary-timegate.v2",
            "bounded-dictionary-timegate.v3"} or \
       gate.get("artifactZero") is not True or gate.get("cohort") != args.cohort or \
       gate.get("requiredFloors") != [floor for _, _, floor in entries] or \
       gate.get("adjudicatedCaseLoad") != args.case_load or \
       gate.get("researchCandidateReserve") != args.research_candidate_reserve or \
       gate.get("assignedLaunch") != expected_binding(args, entries) or \
       actual_continuation != expected_continuation:
        raise SystemExit("existing artifact zero does not exactly match requested resume")
    return gate


def run(args: argparse.Namespace) -> None:
    entries = [(identity, term, int(floor)) for identity, term, floor in args.entry]
    floors = [floor for _, _, floor in entries]
    child_env = governed_child_env()
    if args.resume_artifact_zero:
        if not args.timegate.is_file():
            raise SystemExit("resume requested but artifact zero is missing")
        gate = verify_resumable_gate(args, entries)
    else:
        if args.timegate.exists():
            raise SystemExit(f"refusing to overwrite artifact zero: {args.timegate.resolve()}")
        create = [
            sys.executable, str(CREATE),
            "--output", str(args.timegate),
            "--cohort", args.cohort,
            "--floors", *map(str, floors),
            "--case-load", str(args.case_load),
            "--research-candidate-reserve", str(args.research_candidate_reserve),
            "--selector", str(args.selector),
            "--prior-union", str(args.prior_union),
        ]
        if args.continuation_of:
            create += ["--continuation-of", args.continuation_of]
        for identity, term, floor in entries:
            create += ["--entry", identity, term, str(floor)]
        for identity in args.reserve_id:
            create += ["--reserve-id", identity]
        subprocess.run(create, cwd=ROOT, check=True, env=child_env)
        gate = json.loads(args.timegate.read_text(encoding="utf-8"))
    if gate.get("schemaVersion") not in {
            "bounded-dictionary-timegate.v2",
            "bounded-dictionary-timegate.v3"}:
        raise RuntimeError("artifact-zero creator emitted an unsupported receipt")
    launch = [
        sys.executable, str(LAUNCH),
        "--cohort", args.cohort,
        "--timegate", str(args.timegate),
        "--prior-union", str(args.prior_union),
        "--selector", str(args.selector),
        "--output-dir", str(args.output_dir),
        "--research-candidate-reserve", str(args.research_candidate_reserve),
    ]
    for identity, term, floor in entries:
        launch += ["--entry", identity, term, str(floor)]
    for identity in args.reserve_id:
        launch += ["--reserve-id", identity]
    subprocess.run(launch, cwd=ROOT, check=True, env=child_env)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--timegate", required=True, type=Path)
    parser.add_argument("--prior-union", required=True, type=Path)
    parser.add_argument("--selector", required=True, type=Path)
    parser.add_argument("--entry", action="append", nargs=3,
                        metavar=("ID", "TERM", "FLOOR"), required=True)
    parser.add_argument("--reserve-id", action="append", default=[])
    parser.add_argument("--case-load", required=True, type=int)
    parser.add_argument("--research-candidate-reserve", type=int, default=3)
    parser.add_argument("--continuation-of")
    parser.add_argument("--resume-artifact-zero", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "maintenance")
    args = parser.parse_args()
    if args.research_candidate_reserve < 0:
        raise SystemExit("research-candidate-reserve must be nonnegative")
    run(args)


if __name__ == "__main__":
    main()
