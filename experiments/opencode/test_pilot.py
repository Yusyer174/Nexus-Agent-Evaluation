import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import pilot
import stage_model

from pilot import assess, judge


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.answer = {"nonce": "control",
            "source": "def first_missing(ids, predictions):\n    for key in ids:\n        if key not in predictions:\n            return key\n    return None",
            "tests": [{"ids": [], "predictions": {}, "expected": None},
                      {"ids": ["a"], "predictions": {"a": None}, "expected": None},
                      {"ids": ["a", "z", "b"], "predictions": {"a": None}, "expected": "z"}], "files": {
            "cases.json": [{"id": "core", "expected_decision": "hold", "critical": True, "allowed_actions": []},
                           {"id": "advisory", "expected_decision": "hold", "allowed_actions": [],
                            "required_evidence": ["receipt"]}],
            "predictions.json": {k: {"decision": "hold", "actions": [], "evidence": []}
                                 for k in ("core", "advisory")}},
            "expected": {"pass_rate": 0.5, "accepted": False, "gate_passed": True}}

    def score(self):
        return assess(json.dumps(self.answer), "control")

    def test_reference(self):
        self.assertEqual(self.score(), "correct")

    def test_created_regression(self):
        self.answer["files"]["predictions.json"]["advisory"]["evidence"] = ["receipt"]
        self.assertEqual(self.score(), "functional_test_failed")

    def test_invalid_scope(self):
        self.answer["files"]["README.md"] = "ignore"
        self.assertEqual(self.score(), "scope_violation")

    def test_type_and_threshold(self):
        for wrong in (True, 0):
            self.answer["expected"]["accepted"] = wrong
            self.assertEqual(self.score(), "logic_error")

    def test_read_proof(self):
        self.assertEqual(judge("", "control")["status"], "missing_tool_evidence")

    def test_malformed(self):
        for raw in ("[]", '{"nonce":1,"nonce":2}', '{"x":NaN}', "x" * 16001):
            self.assertEqual(assess(raw, "control"), "format_error")

    def test_disallowed_read(self):
        event = {"type": "tool_use", "part": {"tool": "read", "state": {"input": {"path": ".git/config"}}}}
        self.assertEqual(judge(json.dumps(event), "control")["status"], "scope_violation")

    def test_broken_patch(self):
        self.answer["source"] = "def first_missing(ids, predictions):\n    return None"
        self.assertEqual(self.score(), "functional_test_failed")

    def test_generated_test_oracle(self):
        self.answer["tests"][2]["expected"] = "b"
        self.assertEqual(self.score(), "logic_error")

    def test_unsupported_syntax(self):
        self.answer["source"] = "def first_missing(ids, predictions):\n    import os"
        self.assertEqual(self.score(), "unsupported_proposal")


class InfrastructureTests(unittest.TestCase):
    def test_readonly_store_prepares_both_manifest_roots(self):
        blob = b"synthetic config"
        digest = "sha256:" + hashlib.sha256(blob).hexdigest()
        manifest = json.dumps({"config": {"digest": digest, "size": len(blob)},
                               "layers": []}).encode()
        # Tiny in-memory fixture; no downloads or model execution.
        with tempfile.TemporaryDirectory() as directory:
            models = Path(directory)
            with patch.object(stage_model, "EXPECTED", hashlib.sha256(manifest).hexdigest()), \
                 patch.object(stage_model.shutil, "disk_usage", return_value=type("Disk", (), {"free": 4 * 1024**3})()), \
                 patch.object(stage_model.urllib.request, "urlopen", side_effect=[io.BytesIO(manifest), io.BytesIO(blob)]):
                stage_model.stage(models)
            self.assertTrue((models / "manifests-v2").is_dir())
            self.assertEqual(list((models / "manifests-v2").iterdir()), [])
            self.assertEqual((models / "manifests/registry.ollama.ai/library/qwen2.5-coder/14b").read_bytes(), manifest)
            self.assertEqual((models / "blobs" / digest.replace(":", "-")).read_bytes(), blob)

    def test_http_failure_reports_stage_without_raw_details(self):
        error = HTTPError("http://localhost/private", 500, "synthetic private detail", {}, None)
        with patch.object(pilot, "ready"), patch.object(pilot, "api", side_effect=error):
            result = pilot.run()
        self.assertEqual(result["status"], "infrastructure_error")
        self.assertEqual(result["error_type"], "HTTPError")
        self.assertEqual(result["stage"], "list_models")
        self.assertEqual(result["http_status"], 500)
        self.assertNotIn("private", json.dumps(result))
        self.assertNotIn("attempts", result)

    def test_startup_diagnostics_are_bounded_and_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ollama.log").write_bytes(b"synthetic private value\n" + b"x" * 70000 +
                                              b"\nread-only file system\nprivate service detail")
            (root / "ollama.exit").write_text("1\n", encoding="ascii")
            result = pilot.startup_diagnostics(root)
            self.assertEqual(result, {"log_categories": ["read_only_store"],
                                      "server_exit": 1, "log_available": True})
            self.assertNotIn("private", json.dumps(result))
            (root / "ollama.exit").write_text("invalid private data", encoding="ascii")
            self.assertNotIn("server_exit", pilot.startup_diagnostics(root))

    def test_readiness_failure_includes_startup_diagnostics(self):
        diagnostic = {"log_categories": ["read_only_store"], "server_exit": 1,
                      "log_available": True}
        with patch.object(pilot, "ready", side_effect=RuntimeError("synthetic startup failure")), \
             patch.object(pilot, "startup_diagnostics", return_value=diagnostic):
            result = pilot.run()
        self.assertEqual(result["status"], "infrastructure_error")
        self.assertEqual(result["stage"], "ollama_ready")
        self.assertEqual(result["startup_diagnostics"], diagnostic)
        self.assertNotIn("attempts", result)
