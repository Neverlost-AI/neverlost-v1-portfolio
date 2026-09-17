"""New execution tests; not historical tests or clinical validation."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from engine.runtime import adapter


class RuntimeTests(unittest.TestCase):
    def test_child_dependency_path_does_not_inherit_secrets(self):
        real_run = adapter.subprocess.run
        captured = []
        def record(*args, **kwargs):
            captured.append(kwargs["env"])
            return real_run(*args, **kwargs)
        with patch.dict(adapter.os.environ, {"PYTHONPATH": "untrusted-parent-path", "PRIVATE_TOKEN": "test-only-secret"}):
            with patch.object(adapter.subprocess, "run", side_effect=record):
                adapter.execute("case_001")
        self.assertEqual(captured[0]["PYTHONPATH"], adapter.dependency_path())
        self.assertNotIn("untrusted-parent-path", captured[0]["PYTHONPATH"])
        self.assertNotIn("PRIVATE_TOKEN", captured[0])
        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0], captured[1])

    def test_25_frozen_hashes(self):
        manifest = json.loads(adapter.RECOVERY.read_text())
        self.assertEqual(len(manifest["v1_files"]), 25)
        self.assertEqual(len(adapter.verify_historical()), 64)

    def test_real_execution_and_provenance(self):
        result = adapter.execute("case_001")
        self.assertGreater(result["counts"]["events"], 0)
        self.assertIn("healthcare_reality_map.md", result["reports"])
        chunks = {c["chunk_id"]: c for c in result["artifacts"]["chunks"]}
        for event in result["artifacts"]["events"]:
            source = chunks[event["source_page_or_chunk"]]
            self.assertEqual(source["document"], event["source_document"])
        pdf = next(s for s in result["sources"] if s["filename"].endswith(".pdf"))
        self.assertEqual(pdf["pages"][0]["page"], 1)
        self.assertEqual(pdf["pages"][0]["text_extraction_method"], "pypdf")

    def test_changed_document_changes_analytical_output(self):
        first = adapter.execute("case_001")
        second = adapter.execute("case_002")
        self.assertNotEqual(first["artifacts"]["evidence_matrix"], second["artifacts"]["evidence_matrix"])
        self.assertNotEqual(first["reports"], second["reports"])
        self.assertGreater(second["counts"]["capacity_windows"], 0)

    def test_concurrent_isolation_and_repeatability(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = list(pool.map(adapter.execute, ["case_001", "case_003"]))
        repeat = adapter.execute("case_001")
        self.assertNotEqual(first["run_id"], repeat["run_id"])
        self.assertEqual(first["result_sha256"], repeat["result_sha256"])
        self.assertEqual(first["v1_1"]["result_sha256"], repeat["v1_1"]["result_sha256"])
        self.assertFalse(second["v1_1"]["actual_denial_source_present"])
        self.assertNotIn("negation.txt", str(first["v1_1"]["evidence_matrix"]))
        self.assertNotIn("negation.txt", {s["filename"] for s in first["sources"]})
        self.assertEqual(second["counts"]["documents"], 1)

    def test_same_documents_modified_text_changes_results(self):
        first = adapter.execute("case_001")
        edited = copy.deepcopy(adapter.case_detail("case_002"))
        edited["documents"] = edited["documents"][:2]
        with patch.object(adapter, "case_detail", return_value=edited):
            second = adapter.execute("case_002")
        self.assertEqual(first["counts"]["documents"], second["counts"]["documents"])
        self.assertNotEqual(first["artifacts"]["evidence_matrix"], second["artifacts"]["evidence_matrix"])

    def test_reject_unknown_case(self):
        for value in ["../../private", "", "case_005"]:
            with self.assertRaises(adapter.InputRejected):
                adapter.execute(value)

    def test_reject_tampered_manifest(self):
        case = copy.deepcopy(adapter.case_detail("case_001"))
        case["documents"][0]["sha256"] = "0" * 64
        with self.assertRaises(adapter.InputRejected):
            adapter.validate_sources(case)

    def test_ocr_required_pdf_rejected_before_execution(self):
        case = copy.deepcopy(adapter.case_detail("case_001"))
        case["documents"] = [d for d in case["documents"] if d["filename"].endswith(".pdf")]
        reader = Mock(is_encrypted=False, pages=[Mock()])
        reader.pages[0].extract_text.return_value = ""
        with patch("pypdf.PdfReader", return_value=reader):
            with self.assertRaisesRegex(adapter.InputRejected, "OCR-required"):
                adapter.validate_sources(case)

    def test_missing_engine_is_not_reconstructed(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(adapter, "HISTORICAL", Path(folder)):
                with self.assertRaisesRegex(adapter.ExecutionFailed, "integrity"):
                    adapter.verify_historical()

    def test_manifest_path_traversal_rejected(self):
        case = copy.deepcopy(adapter.case_detail("case_001"))
        case["documents"][0]["filename"] = "../other.md"
        with self.assertRaises(adapter.InputRejected):
            adapter.validate_sources(case)

    def test_failure_cleanup(self):
        original = tempfile.TemporaryDirectory
        with original() as parent:
            with patch.object(adapter.tempfile, "TemporaryDirectory", lambda **kw: original(dir=parent, **kw)):
                with patch.object(adapter.subprocess, "run", side_effect=subprocess.TimeoutExpired("private-path", 45)):
                    with self.assertRaisesRegex(adapter.ExecutionFailed, "bounded execution"):
                        adapter.execute("case_001")
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_success_cleanup(self):
        original = tempfile.TemporaryDirectory
        with original() as parent:
            with patch.object(adapter.tempfile, "TemporaryDirectory", lambda **kw: original(dir=parent, **kw)):
                adapter.execute("case_001")
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_preserve_negation_defect_with_warning(self):
        result = adapter.execute("case_003")
        self.assertIn("Barrier removed", [r["state_change"] for r in result["artifacts"]["hidden_states"]])
        self.assertTrue(any("not approved" in warning for warning in result["warnings"]))
        self.assertIn("not approved", result["sources"][0]["pages"][0]["text"])


if __name__ == "__main__":
    unittest.main()
