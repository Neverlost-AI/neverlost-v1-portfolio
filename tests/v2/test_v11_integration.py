"""New V2 acceptance tests. Artificial cap inputs are not historical records."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from engine.runtime import adapter
from engine.runtime.v11_stage import ranking_trace

sys.path[:0] = [str(adapter.ROOT / "engine/historical/v1_1/src"), str(adapter.HISTORICAL / "src")]
import prioritization_consolidation as rules
import light_agentic_review as review
import detect_bottlenecks as bottlenecks


class LiveIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = adapter.execute("case_004")

    def test_frozen_v1_and_m1_mode(self):
        expected = ["2fe0a970dad56556b17c013c58636e14fc4731a1f4aae864da6a05c303bec27f",
                    "367773e04b8f76d8057a9a9b983147371b0e1d7255bc9ff388033dde02f0cd9a",
                    "b9ad3137bd3ca42298a3f57603b3c43b33f6413de93d5466e965a86b7f70c838"]
        for index, digest in enumerate(expected, 1):
            case = f"case_{index:03d}"
            with self.subTest(case=case):
                live, m1 = adapter.execute(case), adapter.execute(case, include_v11=False)
                self.assertEqual(live["result_sha256"], digest)
                self.assertEqual(m1["result_sha256"], digest)
                for name in ("artifacts", "reports", "sources"):
                    self.assertEqual(live[name], m1[name])
                self.assertEqual(live["v1_1"]["upstream_v1_sha256"], digest)

    def test_custody(self):
        custody = json.loads((adapter.ROOT / "engine/v11-custody.json").read_text())
        self.assertEqual(len(custody["files"]), 5)
        for entry in custody["files"]:
            data = (adapter.ROOT / "engine/historical/v1_1" / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["adapted_sha256"])
            self.assertEqual(len(entry["original_sha256"]), 64)
        self.assertEqual(len(adapter.verify_historical()), 64)

    def test_case004_preaccepted_classifications_and_events(self):
        result = self.output["v1_1"]
        expected = {"ambiguous note.txt": "unknown", "function report.txt": "function report",
                    "health record.txt": "health-system/provider record", "insurance denial.txt": "insurance denial letter",
                    "occupational therapy.txt": "OT record", "physical therapy.txt": "PT record"}
        self.assertEqual({r["source_document"]: r["source_document_type"] for r in result["evidence_matrix"]}, expected)
        self.assertEqual({r["file_name"]: r["source_document_type"] for r in result["document_statuses"]}, expected)
        self.assertEqual([e["event_type"] for e in self.output["artifacts"]["events"]],
                         ["administrative barrier", "functional limitation", "functional limitation", "insurance event", "intervention", "intervention"])
        self.assertEqual(self.output["counts"]["capacity_windows"], 2)
        self.assertEqual([w["source"]["document"] for w in self.output["artifacts"]["capacity_windows"]],
                         ["occupational therapy.txt", "physical therapy.txt"])

    def test_case004_scores_selection_and_provenance(self):
        result = self.output["v1_1"]
        self.assertEqual([r["evidence_strength_score"] for r in result["evidence_matrix"]], [118, 106, 51, 22, 1, -54])
        self.assertEqual([(r["source_document"], r["score"]) for r in result["prioritized_evidence"]],
                         [("health record.txt", 193), ("function report.txt", 158), ("insurance denial.txt", 140),
                          ("occupational therapy.txt", 137), ("physical therapy.txt", 115), ("ambiguous note.txt", 38)])
        chunks = {r["chunk_id"]: r for r in self.output["artifacts"]["chunks"]}
        for row in result["evidence_matrix"] + result["prioritized_evidence"]:
            self.assertEqual(chunks[row["source_page_or_chunk"]]["document"], row["source_document"])
        for trace in result["instrumentation"]["ranking_trace"]:
            self.assertEqual(sum(trace["components"].values()), trace["score"])
            self.assertEqual(trace["selection_reason"], "selected")

    def test_themes_and_historical_review_are_distinct(self):
        result = self.output["v1_1"]
        self.assertEqual(result["instrumentation"]["initial_review_theme_groups"], [["pain/symptom response", 2]])
        self.assertEqual([(r["theme_name"], r["window_count"]) for r in result["capacity_themes"]],
            [("treatment response/carryover capacity", 2), ("pacing/energy conservation capacity", 2),
             ("insurance/authorization capacity", 1), ("IADL/home-management capacity", 1)])
        self.assertNotEqual(result["initial_review"]["next_actions.md"], result["reports"]["next_actions.md"])
        self.assertIn("659", result["reports"]["run_review.md"])
        self.assertFalse(result["instrumentation"]["source_authority_strict_helper"])

    def test_denial_gates_and_missing_rationale(self):
        result = self.output["v1_1"]
        self.assertTrue(result["actual_denial_source_present"])
        mapping = result["raw_denial_mapping"]
        self.assertEqual(mapping["denial_source"]["payer_name"], "Not identified.")
        self.assertEqual(mapping["denial_rationale"]["requested_or_denied_service"], "OT visits / occupational therapy")
        self.assertEqual(mapping["denial_rationale"]["medical_necessity_language"], "Not clearly detected in V1 rule-based extraction.")
        raw = result["bottlenecks_raw"]
        insurance = [r for r in raw if r["category"] == "insurance_authorization_documentation_barrier"]
        self.assertEqual({r["source_document"] for r in insurance}, {"insurance denial.txt"})
        self.assertFalse(any(r["category"] == "appeal_dds_evidence_organization_gap" for r in raw))

    def test_no_denial_preserves_truthy_mapping_and_negation(self):
        run = adapter.execute("case_003")
        self.assertFalse(run["v1_1"]["actual_denial_source_present"])
        self.assertTrue(run["v1_1"]["raw_denial_mapping"])
        self.assertIn("Barrier removed", [r["state_change"] for r in run["artifacts"]["hidden_states"]])
        self.assertEqual(run["v1_1"]["raw_denial_mapping"]["denial_rationale"]["requested_or_denied_service"], "Not identified.")

    def test_controlled_source_mutation(self):
        source_bytes = adapter.validate_sources(adapter.case_detail("case_004"))
        changed = []
        for document, data in source_bytes:
            document = copy.deepcopy(document)
            if document["filename"] == "function report.txt":
                self.assertIn(b"standing and walking", data)
                data = data.replace(b"standing and walking", b"bathing and dressing")
                document["sha256"] = adapter.digest(data)
            changed.append((document, data))
        with patch.object(adapter, "validate_sources", return_value=changed):
            other = adapter.execute("case_004")
        original = self.output
        for key in ("events", "evidence_matrix"):
            self.assertNotEqual(original["artifacts"][key], other["artifacts"][key])
        self.assertNotEqual(original["result_sha256"], other["result_sha256"])
        self.assertNotEqual(original["v1_1"]["evidence_matrix"], other["v1_1"]["evidence_matrix"])
        self.assertNotEqual(original["v1_1"]["result_sha256"], other["v1_1"]["result_sha256"])
        self.assertEqual(other["v1_1"]["upstream_v1_sha256"], other["result_sha256"])
        self.assertEqual(original["artifacts"]["capacity_windows"], other["artifacts"]["capacity_windows"])
        self.assertEqual(other["counts"]["events"], 6)
        self.assertTrue(other["v1_1"]["actual_denial_source_present"])
        altered = next(r for r in other["v1_1"]["evidence_matrix"] if r["source_document"] == "function report.txt")
        self.assertIn("ADL", altered["functional_domains"])
        self.assertNotIn("mobility", altered["functional_domains"])

    def test_missing_v1_artifact_fails_before_second_stage(self):
        real = adapter.subprocess.run
        def remove(*args, **kwargs):
            completed = real(*args, **kwargs)
            (Path(kwargs["cwd"]) / "data/processed_json/events.json").unlink()
            return completed
        with patch.object(adapter.subprocess, "run", side_effect=remove):
            with self.assertRaisesRegex(adapter.ExecutionFailed, "required artifacts"):
                adapter.execute("case_004")

    def test_second_stage_timeout_and_failure_cleanup(self):
        real_run, temp = adapter.subprocess.run, tempfile.TemporaryDirectory
        for failure in ("timeout", "failure"):
            with self.subTest(failure=failure), temp() as parent:
                def fail(*args, **kwargs):
                    if Path(kwargs["cwd"]).name == "v11":
                        if failure == "timeout":
                            raise subprocess.TimeoutExpired("synthetic-test", 45)
                        return subprocess.CompletedProcess([], 1)
                    return real_run(*args, **kwargs)
                with patch.object(adapter.tempfile, "TemporaryDirectory", lambda **kw: temp(dir=parent, **kw)):
                    with patch.object(adapter.subprocess, "run", side_effect=fail):
                        with self.assertRaises(adapter.ExecutionFailed):
                            adapter.execute("case_004")
                self.assertEqual(list(Path(parent).iterdir()), [])

    def test_deterministic_digest_and_resource_bounds(self):
        repeated = adapter.execute("case_004")
        self.assertEqual(self.output["v1_1"]["result_sha256"], repeated["v1_1"]["result_sha256"])
        self.assertLess(len(json.dumps(repeated).encode()), adapter.MAX_RESULT_BYTES)
        self.assertLess(repeated["execution_metrics"]["combined_seconds"], 45)
        self.assertNotIn(str(adapter.ROOT), json.dumps(repeated))


class RecoveredRuleBoundaries(unittest.TestCase):
    def rows(self, count, one_doc=False, one_type=False, denial=False):
        return [{"source_document": "same" if one_doc else f"doc{i}", "source_page_or_chunk": f"chunk{i}",
                 "record_fact": f"artificial cap-only row {i}", "evidence_content_type": "same" if one_type else f"type{i}",
                 "source_document_type": "insurance denial letter" if denial else "unknown", "source_authority": "unknown",
                 "evidence_strength_score": 0} for i in range(count)]

    def test_global_document_content_caps_and_denial_exception(self):
        for rows, count, reason in [(self.rows(30), 25, "global cap 25; not visited by historical selector"),
                (self.rows(15, one_doc=True), 12, "document cap 12"),
                (self.rows(8, one_type=True), 5, "content type cap 5"),
                (self.rows(15, one_doc=True, one_type=True, denial=True), 12, "document cap 12")]:
            selected = rules.prioritized_evidence_items(rows, [])
            self.assertEqual(len(selected), count)
            trace = ranking_trace(rows, selected, rules)
            self.assertEqual(trace[-1]["selection_reason"], reason)
            self.assertEqual([x["source_page_or_chunk"] for x in selected], [f"chunk{i}" for i in range(count)])

    def test_empty_unknown_negative_strength_and_near_ties(self):
        self.assertEqual(rules.prioritized_evidence_items([], []), [])
        self.assertEqual(rules.build_capacity_themes([], [], []), [])
        rows = self.rows(3)
        rows[0]["evidence_strength_score"] = -7
        rows[1]["evidence_strength_score"] = -8
        rows[2]["evidence_strength_score"] = 8
        self.assertEqual([r["source_page_or_chunk"] for r in rules.prioritized_evidence_items(rows, [])], ["chunk2", "chunk0", "chunk1"])
        self.assertEqual(rules.source_authority_score(rows[0]), 10)

    def test_ten_guard_artificial_groups_only(self):
        # Deliberately impossible classifier output, not ten historical families.
        with patch.object(rules, "capacity_theme_for_window", return_value=[f"test-only-{i}" for i in range(12)]):
            self.assertEqual(len(rules.build_capacity_themes([{}], [], [])), 10)
        self.assertEqual(len(rules.capacity_theme_for_window({"intervention": "bathing home walking joint protection treatment records insurance pacing"})), 8)

    def test_document_warning_and_volume_confidence_rules(self):
        rows = self.rows(101)
        rows[0]["confidence_level"] = "low"
        statuses = [{"file_name": "doc0", "source_document_type": "unknown"}]
        warnings = review.run_warnings(statuses, rows, [{}] * 21)
        self.assertEqual(len(warnings), 4)
        self.assertFalse(review.source_authority_passed(statuses, rows))

    def test_missing_service_placeholder_is_preserved(self):
        rows = self.rows(1, denial=True)
        with patch.object(rules, "document_extraction_statuses", return_value=[]):
            mapping = rules.insurance_denial_mapping(rows)
        self.assertEqual(mapping["denial_rationale"]["requested_or_denied_service"], "Not identified.")
        self.assertTrue(mapping)


if __name__ == "__main__":
    unittest.main()
