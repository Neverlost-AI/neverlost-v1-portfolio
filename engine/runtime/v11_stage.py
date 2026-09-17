"""V2 orchestration/instrumentation; executed only in the disposable V1.1 root.

Not historical source. Analytical functions are imported from recovered Python.
"""
from collections import Counter
import json
from pathlib import Path
import sys


def ranking_trace(matrix, selected, rules):
    """Explain the recovered selector; assert correspondence instead of replacing it."""
    docs, types = Counter(), Counter()
    trace, accepted = [], []
    for rank, (index, row) in enumerate(sorted(enumerate(matrix), key=lambda item: rules.evidence_score(item[1]), reverse=True), 1):
        doc = row.get("source_document", "unknown")
        content = row.get("evidence_content_type", "unknown")
        denial = row.get("source_document_type") == "insurance denial letter"
        reason = ("global cap 25; not visited by historical selector" if len(accepted) >= 25 else
                  "document cap 12" if docs[doc] >= 12 else
                  "content type cap 5" if types[content] >= 5 and not denial else "selected")
        components = {"source_authority": rules.source_authority_score(row),
                      "functional_impact": rules.functional_impact_score(row),
                      "system_relevance": rules.system_relevance_score(row),
                      "actionability": rules.actionability_score(row),
                      "existing_strength": int((row.get("evidence_strength_score") or 0) / 8)}
        trace.append({"instrumentation": "V2 explanation, not historical provenance",
                      "matrix_index": index, "candidate_rank": rank,
                      "score": rules.evidence_score(row), "components": components,
                      "selection_reason": reason, "denial_content_cap_exception": denial,
                      "source_document": row.get("source_document"),
                      "source_page_or_chunk": row.get("source_page_or_chunk")})
        if reason == "selected":
            accepted.append(row)
            docs[doc] += 1
            types[content] += 1
    assert len(accepted) == len(selected), "Selector instrumentation diverged"
    for row, item in zip(accepted, selected):
        assert all(row.get(key) == item.get(key) for key in
                   ("source_document", "source_page_or_chunk", "record_fact", "evidence_content_type"))
        assert rules.evidence_score(row) == item["score"]
    return trace


def main():
    root = Path.cwd()
    sys.path.insert(0, str(root / "src"))
    import config
    # Imported constants must be configured before importing recovered modules.
    config.PROCESSED_DIR = root / "processed_json"
    config.REPORTS_DIR = root / "reports"
    config.DEBUG_DIR = root / "debug"
    config.ensure_directories()
    from build_evidence_matrix import build_evidence_matrix
    from detect_bottlenecks import detect_bottlenecks
    from generate_reports import generate_all_reports, document_extraction_statuses
    import light_agentic_review as review
    import prioritization_consolidation as priority

    def read(path):
        # No recovered read_json default may hide a missing upstream artifact.
        return json.loads(path.read_text(encoding="utf-8"))

    upstream = {name: read(config.PROCESSED_DIR / (name + ".json")) for name in
                ("events", "chunks", "timeline", "hidden_states", "trust_thresholds", "capacity_windows")}
    pages = read(config.EXTRACTED_DIR / "extracted_pages.json")
    matrix = build_evidence_matrix()
    bottlenecks = detect_bottlenecks()
    generate_all_reports()
    statuses = document_extraction_statuses()
    review.build_light_agentic_review_outputs("v2-synthetic-run", config.RAW_DIR, root,
        pages, upstream["chunks"], upstream["events"], matrix, bottlenecks, upstream["capacity_windows"])
    initial = {name: (root / name).read_text(encoding="utf-8") for name in
               ("run_review.md", "agent_review.md", "next_actions.md")}
    summary = priority.build_prioritization_and_consolidation_outputs(root)
    selected = read(root / "prioritized_evidence.json")
    manifest = read(root / "run_manifest.json")
    # Presentation-only projection: runtime locations and timestamp are not analytics.
    timestamp = manifest.pop("run_timestamp")
    manifest["input_folder"] = "approved-inputs"
    manifest["output_folder"] = "isolated-v1.1-run"
    report_names = ("healthcare_reality_map.md", "evidence_matrix.md", "best_evidence.md",
        "source_authority_map.md", "bottlenecks.md", "capacity_windows.md", "hidden_states.md",
        "trust_thresholds.md", "disability_evidence_summary.md", "documentation_gap_report.md",
        "care_coordination_summary.md", "provider_ready_summary.md", "patient_action_roadmap.md")
    reports = {name: (config.REPORTS_DIR / name).read_text(encoding="utf-8") for name in report_names}
    for name in ("run_review.md", "agent_review.md", "next_actions.md", "prioritized_evidence.md",
                 "consolidated_capacity_windows.md", "insurance_denial_mapping.md"):
        reports[name] = (root / name).read_text(encoding="utf-8")
    result = {"document_statuses": statuses, "evidence_matrix": matrix,
        "bottlenecks_raw": read(config.PROCESSED_DIR / "bottlenecks_raw.json"),
        "bottlenecks": bottlenecks, "review_manifest": manifest,
        "initial_review": initial, "prioritized_evidence": selected,
        "capacity_themes": read(root / "consolidated_capacity_windows.json"),
        "raw_denial_mapping": read(root / "insurance_denial_mapping.json"),
        "actual_denial_source_present": any(r.get("source_document_type") == "insurance denial letter" for r in matrix),
        "historical_summary": summary, "reports": reports,
        "instrumentation": {"ranking_trace": ranking_trace(matrix, selected, priority),
            "initial_review_theme_groups": review.top_capacity_themes(upstream["capacity_windows"]),
            "consolidation_window_membership": [
                {"v1_window_index": index, "themes": priority.capacity_theme_for_window(window)}
                for index, window in enumerate(upstream["capacity_windows"])],
            "source_authority_strict_helper": review.source_authority_passed(statuses, matrix)},
        "warnings": [
            "Recovered Python with documented publication adaptations; not authenticated historical Git ancestry.",
            "Raw reports contain fixed historical counts (659/47), OCR claims and suggested actions that may not describe this run.",
            "A truthy raw denial mapping does not establish that a denial source was classified.",
            "Initial review grouping differs from eight-family consolidation. Keyword and negation defects remain.",
            "Missing service may remain 'Not identified.' despite fallback text. No repair is silently applied.",
            "Historical report indexes may name source_authority_validation.md or other batch-only files not generated here.",
            "V2 manifest projection replaces private runtime paths and moves timestamps outside the analytical digest.",
            "No final-synthesis generator was recovered. Reports are ordinary heuristic outputs, not determinations."]}
    encoded = json.dumps(result, ensure_ascii=False)
    if str(root) in encoded or str(root).replace("\\", "/") in encoded:
        raise ValueError("Runtime path escaped presentation projection")
    (root / "v11-result.json").write_text(encoded, encoding="utf-8")
    execution = {"review_timestamp": timestamp, "peak_rss_bytes": None}
    if sys.platform == "linux":
        import resource
        execution["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    (root / "v11-execution.json").write_text(json.dumps(execution), encoding="utf-8")


if __name__ == "__main__":
    main()
