#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path

from maintenance.source_authority_binding import (
    authority_registry_path,
    authority_registry_sha256,
    require_governed_authority_parity,
)
from compile_evidence_draft import compile_draft


ROOT = Path(__file__).resolve().parent.parent


class SourceAuthorityBindingTest(unittest.TestCase):
    @staticmethod
    def _write_json(path, value):
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def test_path_matches_compiler_contract(self):
        self.assertEqual(
            authority_registry_path(ROOT),
            Path(__file__).resolve().parents[5]
            / "Assets" / "Data" / "zen-source-authority.json",
        )

    def test_r79_payload_passes_real_pipeline_authority_check(self):
        config = json.loads(
            (ROOT / "maintenance/non-iriya-v7-depth-regeneration-r79-constructor-config-b.json")
            .read_text(encoding="utf-8")
        )
        payload = copy.deepcopy(config["entries"][0]["evidenceDraft"])
        payload["EvidenceTransport"]["SourceAuthorityManifestSha256"] = (
            authority_registry_sha256(ROOT)
        )
        with tempfile.TemporaryDirectory() as temporary:
            worksheet = Path(temporary) / "evidence.draft.json"
            worksheet.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _, errors = compile_draft(
                payload, require_pipeline_v2=True, worksheet_path=worksheet
            )
        self.assertFalse(
            [e for e in errors if "SourceAuthorityManifestSha256" in e],
            errors,
        )

    def test_governed_parity_accepts_matching_baseline_and_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "registry.json"
            baseline = root / "corpus-baseline.json"
            state = root / "state.json"
            registry.write_bytes(b'{"entries":[]}\n')
            expected = __import__("hashlib").sha256(registry.read_bytes()).hexdigest()
            self._write_json(baseline, {"sourceAuthoritySha256": expected})
            self._write_json(state, {"sourceAuthoritySha256": expected})
            self.assertEqual(
                require_governed_authority_parity(registry, baseline, state),
                expected,
            )

    def test_governed_parity_fails_stale_hash_without_updating_locks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "registry.json"
            baseline = root / "corpus-baseline.json"
            state = root / "state.json"
            registry.write_bytes(b'{"entries":[]}\n')
            self._write_json(baseline, {"sourceAuthoritySha256": "stale-baseline"})
            self._write_json(state, {"sourceAuthoritySha256": "stale-state"})
            before = (baseline.read_bytes(), state.read_bytes())
            with self.assertRaisesRegex(
                RuntimeError, "preflight failed before adapter"
            ):
                require_governed_authority_parity(registry, baseline, state)
            self.assertEqual(before, (baseline.read_bytes(), state.read_bytes()))


if __name__ == "__main__":
    unittest.main()
