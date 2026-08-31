#!/usr/bin/env python3
"""Single authoritative binding for dictionary source-authority bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def authority_registry_path(dictionary_root: Path) -> Path:
    repo_root = dictionary_root.resolve().parents[3]
    return repo_root / "Assets" / "Data" / "zen-source-authority.json"


def authority_registry_sha256(dictionary_root: Path) -> str:
    path = authority_registry_path(dictionary_root)
    if not path.is_file():
        raise FileNotFoundError(f"source-authority registry missing: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_governed_authority_parity(
    registry_path: Path,
    baseline_path: Path,
    state_path: Path,
) -> str:
    """Return the registry SHA only when both governed locks already match it.

    This function is intentionally read-only. Registry changes must be reviewed
    and the two lock files updated explicitly; a canary must never bless drift
    by rewriting either lock during execution.
    """
    for label, path in (
        ("source-authority registry", registry_path),
        ("corpus baseline", baseline_path),
        ("fresh-build state", state_path),
    ):
        if not path.is_file():
            raise RuntimeError(f"{label} missing: {path}")
    registry_sha = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    mismatches = []
    if baseline.get("sourceAuthoritySha256") != registry_sha:
        mismatches.append(
            "corpus-baseline.json sourceAuthoritySha256="
            f"{baseline.get('sourceAuthoritySha256')!r}"
        )
    if state.get("sourceAuthoritySha256") != registry_sha:
        mismatches.append(
            "state.json sourceAuthoritySha256="
            f"{state.get('sourceAuthoritySha256')!r}"
        )
    if mismatches:
        raise RuntimeError(
            "source-authority governed hash preflight failed before adapter: "
            f"registry sha256={registry_sha}; " + "; ".join(mismatches)
        )
    return registry_sha
