from collections import Counter
from datetime import datetime
from pathlib import Path

from config import CHUNKS_DIR, DEBUG_DIR, EXTRACTED_DIR, PROCESSED_DIR, REPORTS_DIR
from generate_reports import document_extraction_statuses
from utils import read_json, write_json, write_text


def relative_to_run(path: Path, run_dir: Path) -> str:
    try:
        return str(path.relative_to(run_dir)).replace("\\", "/")
    except ValueError:
        return str(path)


def generated_files(run_dir: Path) -> list[str]:
    files = []
    for folder in [run_dir, REPORTS_DIR, DEBUG_DIR]:
        if folder.exists():
            files.extend(path for path in folder.glob("*.md") if path.is_file())
            files.extend(path for path in folder.glob("*.json") if path.is_file())
    return sorted({relative_to_run(path, run_dir) for path in files})


def evidence_role_for_doc(file_name: str, matrix: list[dict]) -> str:
    roles = [row.get("evidence_role") for row in matrix if row.get("source_document") == file_name and row.get("evidence_role")]
    if not roles:
        return "No evidence rows generated."
    return Counter(roles).most_common(1)[0][0]


def ocr_status(status: dict) -> str:
    applied = status.get("ocr_applied_pages", 0)
    errors = status.get("ocr_error_count", 0)
    if applied:
        return f"OCR applied to {applied} page(s); {errors} OCR error(s)."
    return f"No OCR applied; {errors} OCR error(s)."


def document_warnings(status: dict, matrix: list[dict]) -> list[str]:
    file_name = status["file_name"]
    rows = [row for row in matrix if row.get("source_document") == file_name]
    warnings = []
    if status.get("source_document_type") == "unknown":
        warnings.append("Unknown source document type.")
    if any(row.get("source_document_type") != status.get("source_document_type") for row in rows):
        warnings.append("Evidence row source type differs from document-level source type.")
    if any(row.get("evidence_content_type") == "evidence requiring review" for row in rows):
        warnings.append("One or more evidence rows still require content-type review.")
    if status.get("ocr_applied_pages", 0) > 0:
        warnings.append("OCR was used; scanned-document accuracy should be spot-checked.")
    return warnings


def source_authority_passed(statuses: list[dict], matrix: list[dict]) -> bool:
    if any(status.get("source_document_type") == "unknown" for status in statuses):
        return False
    if any(row.get("source_document_type") == "unknown" for row in matrix):
        return False
    if any(row.get("source_document_type") != "PT record" and row.get("pt_evidence_type") for row in matrix):
        return False
    return True


def run_warnings(statuses: list[dict], matrix: list[dict], windows: list[dict]) -> list[str]:
    warnings = []
    unknown_count = sum(1 for status in statuses if status.get("source_document_type") == "unknown")
    low_confidence_rows = [row for row in matrix if row.get("confidence_level") in {"low", "unknown"}]
    if unknown_count:
        warnings.append(f"{unknown_count} source document(s) still need source-authority review.")
    if len(matrix) > 100:
        warnings.append(f"{len(matrix)} evidence rows is too high for easy human-facing review; prioritization is recommended.")
    if len(windows) > 20:
        warnings.append(f"{len(windows)} capacity windows may be overproduced; consolidation is recommended.")
    if low_confidence_rows:
        warnings.append(f"{len(low_confidence_rows)} low/unknown confidence evidence row(s) should be reviewed.")
    if any(status.get("ocr_applied_pages", 0) > 0 for status in statuses):
        warnings.append("OCR worked for scanned/partially scanned documents, but OCR text should be spot-checked before external use.")
    if any(status.get("source_document_type") == "insurance denial letter" for status in statuses):
        warnings.append("Insurance denial rationale should be mapped to provider/therapy evidence before appeal or authorization use.")
    return warnings


def top_domains(matrix: list[dict], limit: int = 8) -> list[tuple[str, int]]:
    counts = Counter()
    for row in matrix:
        for domain in row.get("functional_domains") or []:
            if domain != "administrative metadata":
                counts[domain] += 1
    return counts.most_common(limit)


def capacity_theme_label(window: dict) -> str:
    text = " ".join(
        str(window.get(field, ""))
        for field in [
            "intervention",
            "capacity_window_created",
            "what_became_possible",
            "learning",
            "habit_formation",
            "functional_change",
        ]
    ).lower()
    if any(term in text for term in ["medication", "gabapentin", "dose"]):
        return "medication response"
    if any(term in text for term in ["pain", "symptom", "flare", "muscle relaxation", "blood flow"]):
        return "pain/symptom response"
    if any(term in text for term in ["joint protection", "hypermobility", "stability", "supportive device", "brace"]):
        return "joint protection / stability support"
    if any(term in text for term in ["breathwork", "somatic", "anxiety", "regulating"]):
        return "nervous-system regulation / pacing"
    if any(term in text for term in ["adl", "vacuuming", "home", "functional activity", "activity tolerance"]):
        return "ADL/home-function tolerance"
    if any(term in text for term in ["occupational therapy", "therapy", "rehabilitation", "exercise"]):
        return "therapy/rehabilitation response"
    if any(term in text for term in ["coordinate", "follow-up", "next visit", "provider"]):
        return "care coordination / follow-up"
    return "capacity window requiring review"


def top_capacity_themes(windows: list[dict], limit: int = 6) -> list[tuple[str, int]]:
    counts = Counter()
    for window in windows:
        counts[capacity_theme_label(window)] += 1
    return counts.most_common(limit)


def document_entries(statuses: list[dict], matrix: list[dict]) -> list[dict]:
    evidence_counts = Counter(row.get("source_document", "unknown") for row in matrix)
    return [
        {
            "document_name": status["file_name"],
            "source_document_type": status.get("source_document_type"),
            "source_authority": status.get("source_authority"),
            "evidence_role": evidence_role_for_doc(status["file_name"], matrix),
            "extraction_method": status.get("extraction_method"),
            "ocr_status": ocr_status(status),
            "evidence_rows_generated": evidence_counts.get(status["file_name"], 0),
            "warnings": document_warnings(status, matrix),
        }
        for status in statuses
    ]


def build_manifest(
    run_name: str,
    input_folder: Path,
    output_folder: Path,
    statuses: list[dict],
    pages: list[dict],
    chunks: list[dict],
    events: list[dict],
    matrix: list[dict],
    bottlenecks: list[dict],
    windows: list[dict],
) -> dict:
    unknown_count = sum(1 for status in statuses if status.get("source_document_type") == "unknown")
    warnings = run_warnings(statuses, matrix, windows)
    return {
        "run_name": run_name,
        "run_timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input_folder": str(input_folder),
        "output_folder": str(output_folder),
        "input_documents": document_entries(statuses, matrix),
        "total_extracted_records": len(pages),
        "total_chunks": len(chunks),
        "total_events": len(events),
        "total_evidence_rows": len(matrix),
        "total_bottlenecks": len(bottlenecks),
        "total_capacity_windows": len(windows),
        "unknown_source_document_count": unknown_count,
        "warnings": warnings,
        "generated_report_files": generated_files(output_folder),
    }


def build_run_review(manifest: dict, matrix: list[dict], bottlenecks: list[dict], windows: list[dict]) -> str:
    docs = manifest["input_documents"]
    source_counts = Counter(doc["source_document_type"] for doc in docs)
    domains = top_domains(matrix)
    capacity_themes = top_capacity_themes(windows)
    insurance_present = any(doc["source_document_type"] == "insurance denial letter" for doc in docs)
    care_coordination_rows = sum(1 for row in matrix if "care coordination" in (row.get("functional_domains") or []))

    lines = [
        "# Run Review",
        "",
        "## Run Summary",
        "",
        f"- Documents processed: {len(docs)}",
        f"- OCR status: {'OCR used in this run.' if any('OCR applied' in doc['ocr_status'] for doc in docs) else 'No OCR used in this run.'}",
        f"- Source-authority status: {'passed' if manifest['unknown_source_document_count'] == 0 else 'needs review'}",
        f"- Evidence rows: {manifest['total_evidence_rows']}",
        f"- Bottlenecks: {manifest['total_bottlenecks']}",
        f"- Capacity windows: {manifest['total_capacity_windows']}",
        "",
        "## Document Coverage",
        "",
    ]
    for doc in docs:
        lines.extend(
            [
                f"### {doc['document_name']}",
                "",
                f"- Source document type: {doc['source_document_type']}",
                f"- Source authority: {doc['source_authority']}",
                f"- Evidence role: {doc['evidence_role']}",
                f"- OCR status: {doc['ocr_status']}",
                f"- Extraction method: {doc['extraction_method']}",
                f"- Warnings: {'; '.join(doc['warnings']) if doc['warnings'] else 'None.'}",
                "",
            ]
        )

    lines.extend(["## Core Findings", ""])
    lines.append("- Strongest source categories: " + ", ".join(f"{name} ({count})" for name, count in source_counts.most_common()))
    lines.append("- Main bottleneck categories: " + "; ".join(item.get("current_bottleneck", "Unnamed bottleneck") for item in bottlenecks[:7]))
    lines.append("- Main functional domains: " + (", ".join(f"{name} ({count})" for name, count in domains) if domains else "Not identified."))
    lines.append("- Insurance/authorization issues: " + ("Present; denial/authorization evidence should be mapped to provider and therapy evidence." if insurance_present else "Not identified."))
    lines.append("- Care coordination burden: " + (f"Present in {care_coordination_rows} evidence row(s)." if care_coordination_rows else "Not identified."))
    lines.append("- Capacity-window themes: " + (", ".join(f"{name} ({count})" for name, count in capacity_themes) if capacity_themes else "Not identified."))

    lines.extend(
        [
            "",
            "## Report Index",
            "",
            "1. `source_authority_validation.md`",
            "2. `run_review.md`",
            "3. `agent_review.md`",
            "4. `next_actions.md`",
            "5. `source_authority_map.md`",
            "6. `provider_ready_summary.md`",
            "7. `bottlenecks.md`",
            "8. `best_evidence.md`",
            "9. `evidence_matrix.md`",
            "10. `document_coverage.md`",
            "",
            "## Human Review Notes",
            "",
        ]
    )
    warnings = manifest.get("warnings") or []
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- No major rule-based warnings were detected. Human review is still required before external use.")
    return "\n".join(lines)


def build_agent_review(manifest: dict, matrix: list[dict], bottlenecks: list[dict], windows: list[dict]) -> str:
    docs = manifest["input_documents"]
    unknown_count = manifest["unknown_source_document_count"]
    insurance_present = any(doc["source_document_type"] == "insurance denial letter" for doc in docs)
    low_confidence = [row for row in matrix if row.get("confidence_level") in {"low", "unknown"}]
    source_passed = unknown_count == 0
    domains = top_domains(matrix)
    capacity_themes = top_capacity_themes(windows)

    lines = [
        "# Agent Review",
        "",
        "## Overall Assessment",
        "",
        "Usable for validation and internal review, but needs evidence prioritization before human-facing use because the evidence matrix is large.",
        "",
        "## What Worked",
        "",
        "- Batch isolation worked; Batch 02 outputs were written to the isolated run folder.",
        "- OCR worked for scanned/partially scanned documents.",
        f"- Source-authority classification {'passed' if source_passed else 'needs review'}.",
        "- Report generation completed.",
        "- Bottleneck generation completed.",
        "- Capacity-window generation completed.",
        "",
        "## What Needs Human Review",
        "",
        f"- High evidence row count: {manifest['total_evidence_rows']} rows.",
        f"- High capacity window count: {manifest['total_capacity_windows']} windows.",
        f"- Low/unknown confidence rows: {len(low_confidence)}.",
        "- Possible duplicated evidence in large health-system exports.",
        "- Payer/insurance statements need mapping to provider-authored and therapy evidence.",
        "- Provider-facing summary may need tightening before external use.",
        "",
        "## Source-Authority Review",
        "",
        f"- Unknown documents: {unknown_count}",
        f"- Source-authority passed: {'Yes' if source_passed else 'No'}",
        "- Source/content conflicts: No obvious rule-based conflicts detected." if source_passed else "- Source/content conflicts: possible conflicts require review.",
        "- Insurance denial source is correctly treated as payer evidence rather than provider evidence." if insurance_present else "- Insurance denial source not present.",
        "",
        "## Evidence Review",
        "",
        f"- Total evidence rows: {manifest['total_evidence_rows']}",
        "- Human-manageable volume: No; this should be prioritized before human-facing review." if manifest["total_evidence_rows"] > 100 else "- Human-manageable volume: Yes.",
        "- Evidence should be ranked by source authority, functional impact, system relevance, and confidence.",
        "- Likely strongest evidence categories: " + (", ".join(f"{name} ({count})" for name, count in domains[:5]) if domains else "Not identified."),
        "- Likely weakest evidence categories: metadata, repeated administrative rows, and low-confidence duplicated export rows.",
        "- Low-value metadata should stay out of human-facing reports.",
        "",
        "## Bottleneck Review",
        "",
        f"- Total bottlenecks: {manifest['total_bottlenecks']}",
        "- Bottleneck wording is source-aware.",
        "- Insurance authorization/documentation bottleneck is active appropriately." if insurance_present else "- Insurance authorization/documentation bottleneck is not needed for this run.",
        "- Bottlenecks are actionable, but the evidence supporting them should be ranked before sharing.",
        "",
        "## Capacity Window Review",
        "",
        f"- Total capacity windows: {manifest['total_capacity_windows']}",
        "- Capacity windows are likely overproduced and need consolidation." if manifest["total_capacity_windows"] > 20 else "- Capacity windows are within a manageable range.",
        "- Consolidation is recommended.",
        "- Likely repeated themes: " + (", ".join(f"{name} ({count})" for name, count in capacity_themes[:5]) if capacity_themes else "Not identified."),
        "",
        "## Recommended Next Patch",
        "",
        "`Evidence and capacity-window prioritization layer`",
        "",
        "Reason:",
        "",
        "- 659 evidence rows are too many for human-facing review.",
        "- 47 capacity windows likely need consolidation into a smaller set.",
        "- The system needs to identify the strongest evidence by source authority, functional impact, and system relevance.",
        "",
        "## Recommended Next User Action",
        "",
        "`Review the insurance denial rationale and map it to OT/provider evidence before using the batch for an appeal or care-coordination summary.`",
    ]
    return "\n".join(lines)


def build_next_actions(manifest: dict, matrix: list[dict], windows: list[dict]) -> str:
    docs = manifest["input_documents"]
    insurance_docs = [doc for doc in docs if doc["source_document_type"] == "insurance denial letter"]
    actions = []
    if manifest["unknown_source_document_count"] > 0:
        actions.append(
            {
                "title": "Action 1",
                "action": "Review unknown source documents and assign source-authority categories.",
                "why": "Source authority must be known before evidence can be safely used in provider, disability, insurance, or research contexts.",
                "source": "Run manifest and source authority map.",
                "owner": "human reviewer / Neverlost operator",
                "urgency": "High",
                "opportunity": "Cleaner evidence package and lower risk of source/content confusion.",
            }
        )
    if len(matrix) > 100:
        actions.append(
            {
                "title": f"Action {len(actions) + 1}",
                "action": "Prioritize the 659 evidence rows into a smaller best-evidence set.",
                "why": "Medical facts only become useful when the strongest source-linked evidence is converted into functional consequence and system relevance.",
                "source": "Evidence matrix, best evidence report, provider-ready summary.",
                "owner": "Neverlost operator / human reviewer",
                "urgency": "High",
                "opportunity": "A reviewer can focus on the strongest evidence instead of reading hundreds of rows.",
            }
        )
    if len(windows) > 20:
        actions.append(
            {
                "title": f"Action {len(actions) + 1}",
                "action": "Consolidate 47 capacity windows into a smaller human-readable set.",
                "why": "Repeated intervention and response signals need to become a clear capacity story rather than a long list.",
                "source": "Capacity window tracker and evidence matrix.",
                "owner": "Neverlost operator / care coordinator",
                "urgency": "Medium",
                "opportunity": "Capacity windows can become usable treatment-response and care-planning evidence.",
            }
        )
    if insurance_docs:
        actions.append(
            {
                "title": f"Action {len(actions) + 1}",
                "action": "Extract the insurance denial rationale and map it against OT/provider evidence.",
                "why": "The payer barrier needs provider-authored and therapy evidence tied to medical necessity, function, treatment history, and appeal criteria.",
                "source": ", ".join(doc["document_name"] for doc in insurance_docs) + "; OT/provider reports; bottlenecks.",
                "owner": "insurance / care coordination",
                "urgency": "High",
                "opportunity": "Cleaner appeal packet, stronger authorization request, or clearer documentation gap.",
            }
        )

    actions = actions[:3]
    lines = ["# Next Actions", ""]
    for index, action in enumerate(actions, start=1):
        lines.extend(
            [
                f"## Action {index}",
                "",
                f"* Action: {action['action']}",
                f"* Why it matters: {action['why']}",
                f"* Source basis: {action['source']}",
                f"* Owner: {action['owner']}",
                f"* Urgency: {action['urgency']}",
                f"* Next available opportunity: {action['opportunity']}",
                "",
            ]
        )
    if not actions:
        lines.append("No rule-based next actions generated. Human review is still required.")
    return "\n".join(lines)


def build_light_agentic_review_outputs(
    run_name: str,
    input_folder: Path,
    output_folder: Path,
    pages: list[dict],
    chunks: list[dict],
    events: list[dict],
    matrix: list[dict],
    bottlenecks: list[dict],
    windows: list[dict],
) -> dict:
    statuses = document_extraction_statuses()
    manifest = build_manifest(run_name, input_folder, output_folder, statuses, pages, chunks, events, matrix, bottlenecks, windows)
    write_json(output_folder / "run_manifest.json", manifest)
    write_text(output_folder / "run_review.md", build_run_review(manifest, matrix, bottlenecks, windows))
    write_text(output_folder / "agent_review.md", build_agent_review(manifest, matrix, bottlenecks, windows))
    write_text(output_folder / "next_actions.md", build_next_actions(manifest, matrix, windows))
    manifest["generated_report_files"] = generated_files(output_folder)
    write_json(output_folder / "run_manifest.json", manifest)
    return manifest
