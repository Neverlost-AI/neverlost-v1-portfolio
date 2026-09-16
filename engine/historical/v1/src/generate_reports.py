from collections import Counter, defaultdict
from pathlib import Path

from build_evidence_matrix import source_authority, source_document_type
from case_profile import profile_terms
from config import CHUNKS_DIR, DEBUG_DIR, EXTRACTED_DIR, PROCESSED_DIR, RAW_DIR, REPORTS_DIR, ensure_directories
from utils import read_json, source_label, write_text


DISCLAIMER = (
    "> This is a healthcare organization and care-navigation draft. "
    "It is not medical advice, diagnosis, or treatment recommendation. "
    "All outputs are drafts requiring human review."
)

DOMAIN_LABELS = {
    "ADL": "ADL",
    "IADL": "IADL",
    "mobility": "Mobility",
    "endurance": "Endurance",
    "cognition": "Cognition",
    "autonomic symptoms": "Autonomic Symptoms",
    "pain": "Pain",
    "joint stability": "Joint Stability",
    "PT/rehabilitation": "PT/Rehabilitation",
    "treatment response": "Treatment Response",
    "care coordination": "Care Coordination",
    "disability process": "Disability Process",
    "insurance/authorization": "Insurance/Authorization",
    "provider support": "Provider Support",
}

DOMAIN_CONSEQUENCES = {
    "ADL": "ADL evidence describes self-care limits such as bathing, grooming, dressing, or hygiene completion.",
    "IADL": "IADL evidence describes limits in groceries, meal preparation, cleaning, laundry, paperwork, scheduling, phone calls, or pet care.",
    "mobility": "Mobility evidence describes limits in walking, standing, stairs, balance, gait, sitting, bending, lifting, or positional tolerance.",
    "endurance": "Endurance evidence describes reduced sustained activity, appointment tolerance, recovery capacity, or work-like consistency.",
    "cognition": "Cognition evidence describes paperwork, scheduling, memory, attention, or cognitive-stamina limits.",
    "autonomic symptoms": "Autonomic evidence describes dizziness, orthostatic tolerance, symptom stability, and activity-pacing needs.",
    "pain": "Pain evidence describes activity tolerance, recovery, sleep, positioning, guarding, or consistency limits.",
    "joint stability": "Joint-stability evidence describes instability, guarding, movement tolerance, or rehab-planning needs.",
    "PT/rehabilitation": "PT evidence describes observable functional deficits, therapy tolerance, treatment response, goals, or carryover needs.",
    "treatment response": "Treatment-response evidence describes a possible capacity window or change in functional tolerance.",
    "care coordination": "Care-coordination evidence describes record, appointment, paperwork, provider-ask, or next-step burden.",
    "disability process": "Disability evidence links symptoms to source-cited functional limitations and documentation needs.",
}


def section(title: str) -> list[str]:
    return ["", f"## {title}", ""]


def bullet(label: str, value: object | None) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value if item)
    if value is None or value == "":
        value = "Not identified."
    return f"- **{label}:** {value}"


def source_list(items: list[str] | None) -> str:
    if not items:
        return "Not identified."
    return "; ".join(items)


def domain_text(row: dict) -> str:
    domains = [domain for domain in (row.get("functional_domains") or []) if domain != "administrative metadata"]
    if not domains:
        return "Unclassified"
    return ", ".join(DOMAIN_LABELS.get(domain, domain.title()) for domain in domains)


def top_matrix_rows(matrix: list[dict], limit: int = 8) -> list[dict]:
    priority_domains = [
        "ADL",
        "IADL",
        "mobility",
        "endurance",
        "PT/rehabilitation",
        "disability process",
        "treatment response",
        "provider support",
        "care coordination",
    ]

    def score(row: dict) -> int:
        domains = set(row.get("functional_domains") or [])
        points = sum(8 - index for index, domain in enumerate(priority_domains) if domain in domains)
        if row.get("supports_disability"):
            points += 5
        if row.get("supports_treatment"):
            points += 3
        if row.get("confidence_level") == "high":
            points += 2
        return points

    return sorted(
        matrix,
        key=lambda row: (row.get("evidence_strength_score", 0), score(row)),
        reverse=True,
    )[:limit]


def rows_by_domain(matrix: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in matrix:
        for domain in row.get("functional_domains") or ["Unclassified"]:
            grouped[domain].append(row)
    return grouped


def build_one_paragraph_case_summary(profile: dict | None, matrix: list[dict], bottlenecks: list[dict]) -> str:
    return (
        "This source-cited summary organizes Function Report and PT record evidence into functional domains relevant to "
        "disability documentation, care coordination, PT treatment response, and provider visit preparation. Current evidence "
        "describes ADL/IADL limitations, mobility and endurance limits, cognitive/administrative burden, pain/instability, "
        "symptom variability, and PT rehabilitation findings. The next operational need is to convert the strongest evidence "
        "into concise provider/disability-ready language and track treatment response/capacity changes over time."
    )


def domain_summary_line(domain: str, rows: list[dict]) -> str:
    label = DOMAIN_LABELS.get(domain, domain.title())
    consequence = DOMAIN_CONSEQUENCES.get(domain)
    if not consequence:
        strongest = rows[0] if rows else {}
        consequence = strongest.get("functional_consequence", "Functional consequence requires review.")
    sources = []
    for row in rows[:3]:
        label_text = f"{row.get('source_document')} ({row.get('source_page_or_chunk')})"
        if label_text not in sources:
            sources.append(label_text)
    return f"- **{label}:** {consequence} Sources: {source_list(sources)}"


def build_healthcare_reality_map(profile: dict | None = None) -> str:
    events = read_json(PROCESSED_DIR / "timeline.json", [])
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    hidden = read_json(PROCESSED_DIR / "hidden_states.json", [])
    trust = read_json(PROCESSED_DIR / "trust_thresholds.json", [])
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    windows = read_json(PROCESSED_DIR / "capacity_windows.json", [])

    lines = [
        "# Healthcare Reality Map",
        "",
        DISCLAIMER,
        "",
        "This map separates source evidence, patient-reported information, and AI/rule-based inference. It is a working draft for review.",
        "",
        "## Snapshot",
        "",
        bullet("Case Profile", profile.get("case_name") if profile else "Generic Healthcare Roadmap Case"),
        bullet("Events extracted", str(len(events))),
        bullet("Evidence matrix rows", str(len(matrix))),
        bullet("Hidden state candidates", str(len(hidden))),
        bullet("Trust threshold candidates", str(len(trust))),
        bullet("Consolidated bottlenecks", str(len(bottlenecks))),
        bullet("Capacity window candidates", str(len(windows))),
    ]

    lines.extend(section("Neverlost Bridge"))
    bridge_rows = top_matrix_rows(matrix, 6)
    if not bridge_rows:
        lines.append("No bridge rows generated yet.")
    for row in bridge_rows:
        lines.extend(
            [
                f"### {row.get('source_document')} - {row.get('source_page_or_chunk')}",
                "",
                bullet("Medical / Record Fact", row.get("record_fact")),
                bullet("Functional Consequence", row.get("functional_consequence")),
                bullet("System Relevance", row.get("system_relevance")),
                bullet("Next Available Opportunity", row.get("next_available_opportunity")),
                bullet("Domains", domain_text(row)),
                bullet("Confidence", row.get("confidence_level")),
                "",
            ]
        )

    owner_counts = Counter(item.get("reality_map_owner", "unknown") for item in bottlenecks)
    if owner_counts:
        lines.extend(section("Reality Map Layers With Current Bottlenecks"))
        for owner, count in owner_counts.most_common():
            lines.append(f"- {owner.replace('_', ' ').title()}: {count}")

    lines.extend(section("Current Bottlenecks"))
    if not bottlenecks:
        lines.append("No bottlenecks detected yet.")
    for item in bottlenecks:
        lines.extend(
            [
                f"### {item.get('current_bottleneck', 'Bottleneck')}",
                "",
                bullet("Current Goal", item.get("current_goal")),
                bullet("Reality Map Owner", item.get("reality_map_owner")),
                bullet("Why It Exists", item.get("why_it_exists")),
                bullet("Evidence Needed", item.get("evidence_needed")),
                bullet("Recommended Next Action", item.get("recommended_next_action")),
                bullet("Next Available Opportunity", item.get("next_available_opportunity")),
                bullet("Key Sources", item.get("key_sources")),
                bullet("Confidence", item.get("confidence_level")),
                "",
            ]
        )

    lines.extend(section("Hidden State Changes"))
    if not hidden:
        lines.append("No hidden state changes detected yet.")
    for item in hidden[:10]:
        lines.extend(
            [
                f"### {item.get('state_change')}",
                "",
                bullet("Why It Matters", item.get("why_it_matters")),
                bullet("Downstream Opportunity", item.get("downstream_opportunity")),
                bullet("Source", source_label(item)),
                bullet("Confidence", item.get("confidence_level")),
                "",
            ]
        )

    return "\n".join(lines)


def build_evidence_matrix_report() -> str:
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    lines = [
        "# Evidence Matrix",
        "",
        DISCLAIMER,
        "",
        "Each row should preserve the chain: medical fact -> functional consequence -> system relevance -> next available opportunity.",
        "",
    ]
    if not matrix:
        lines.append("No evidence matrix rows generated yet.")
        return "\n".join(lines)
    for index, item in enumerate(matrix, start=1):
        lines.extend(
            [
                f"## Evidence Row {index}",
                "",
                bullet("Record Fact", item.get("record_fact") or item.get("claim_or_functional_issue")),
                bullet("Functional Consequence", item.get("functional_consequence")),
                bullet("System Relevance", item.get("system_relevance")),
                bullet("Next Available Opportunity", item.get("next_available_opportunity")),
                bullet("Functional Domains", domain_text(item)),
                bullet("Source Document", item.get("source_document")),
                bullet("Source Document Type", item.get("source_document_type")),
                bullet("Evidence Content Type", item.get("evidence_content_type")),
                bullet("Evidence Role", item.get("evidence_role")),
                bullet("Source Authority", item.get("source_authority")),
                bullet("Source Authority Note", item.get("source_authority_note")),
                bullet("Source Page or Chunk", item.get("source_page_or_chunk")),
                bullet("Date", item.get("date")),
                bullet("Evidence Type", item.get("evidence_type")),
                bullet("Supports Disability", str(item.get("supports_disability"))),
                bullet("Supports Treatment", str(item.get("supports_treatment"))),
                bullet("Supports Referral", str(item.get("supports_referral"))),
                bullet("Supports Insurance Authorization", str(item.get("supports_insurance_authorization"))),
                bullet("Missing Evidence", item.get("missing_evidence")),
                bullet("First Layer Fact", item.get("first_layer_fact")),
                bullet("Possible Second-Layer Meaning", item.get("possible_second_layer_meaning") or item.get("possible_second_layer_change")),
                bullet("Why It Matters", item.get("why_it_matters")),
                bullet("PT Evidence Type", item.get("pt_evidence_type")),
                bullet("Evidence Strength Score", item.get("evidence_strength_score")),
                bullet("Confidence Level", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_best_evidence_report() -> str:
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    lines = [
        "# Best Evidence Summary",
        "",
        DISCLAIMER,
        "",
        "This report shows the strongest source-linked rows only. It is intended to be the fastest clinician-friendly evidence review before an appointment.",
        "",
    ]
    if not matrix:
        lines.append("No evidence rows generated yet.")
        return "\n".join(lines)
    for index, item in enumerate(top_matrix_rows(matrix, 12), start=1):
        lines.extend(
            [
                f"## Evidence {index}",
                "",
                bullet("Functional Issue", domain_text(item)),
                bullet("Record Fact", item.get("record_fact")),
                bullet("Functional Consequence", item.get("functional_consequence")),
                bullet("System Relevance", item.get("system_relevance")),
                bullet("Source", f"{item.get('source_document')}, {item.get('source_page_or_chunk')}"),
                bullet("Source Document Type", item.get("source_document_type")),
                bullet("Evidence Content Type", item.get("evidence_content_type")),
                bullet("Source Authority", item.get("source_authority")),
                bullet("Confidence Level", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_hidden_states_report() -> str:
    hidden = read_json(PROCESSED_DIR / "hidden_states.json", [])
    lines = ["# Hidden State Change Map", "", DISCLAIMER, ""]
    if not hidden:
        lines.append("No hidden state changes detected yet.")
        return "\n".join(lines)
    for index, item in enumerate(hidden, start=1):
        lines.extend(
            [
                f"## Hidden State {index}: {item.get('state_change')}",
                "",
                bullet("Why It Matters", item.get("why_it_matters")),
                bullet("Downstream Opportunity", item.get("downstream_opportunity")),
                bullet("Record Evidence", item.get("source_evidence")),
                bullet("AI / Rule-Based Inference", "Hidden-state candidate. Human review required."),
                bullet("Source", source_label(item)),
                bullet("Confidence Level", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_trust_thresholds_report() -> str:
    thresholds = read_json(PROCESSED_DIR / "trust_thresholds.json", [])
    lines = ["# Trust Threshold Tracker", "", DISCLAIMER, ""]
    if not thresholds:
        lines.append("No trust thresholds detected yet.")
        return "\n".join(lines)
    for index, item in enumerate(thresholds, start=1):
        lines.extend(
            [
                f"## Trust Threshold {index}",
                "",
                bullet("Provider Involved", item.get("provider_involved")),
                bullet("Source Event", item.get("source_event")),
                bullet("Evidence That Increased Trust", item.get("evidence_that_increased_trust")),
                bullet("Action That Became Possible", item.get("action_that_became_possible")),
                bullet("Documentation Created", item.get("documentation_created")),
                bullet("Downstream Pathway Opened", item.get("downstream_pathway_opened")),
                bullet("Source Evidence", item.get("source_evidence")),
                bullet("Source", source_label(item)),
                bullet("Confidence Level", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_bottlenecks_report() -> str:
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    lines = [
        "# Current Bottleneck Report",
        "",
        DISCLAIMER,
        "",
        "Bottlenecks are consolidated into V1 categories so the report stays usable instead of listing every repeated source mention.",
        "",
    ]
    if not bottlenecks:
        lines.append("No bottlenecks detected yet.")
        return "\n".join(lines)
    for index, item in enumerate(bottlenecks, start=1):
        lines.extend(
            [
                f"## Bottleneck {index}: {item.get('current_bottleneck')}",
                "",
                bullet("Current Goal", item.get("current_goal")),
                bullet("Reality Map Owner", item.get("reality_map_owner")),
                bullet("Why It Exists", item.get("why_it_exists")),
                bullet("Evidence Needed", item.get("evidence_needed")),
                bullet("Recommended Next Action", item.get("recommended_next_action")),
                bullet("Next Available Opportunity", item.get("next_available_opportunity")),
                bullet("Source Evidence Summary", item.get("source_evidence_summary") or item.get("source_evidence")),
                bullet("Key Sources", item.get("key_sources")),
                bullet("Confidence Level", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_capacity_report() -> str:
    windows = read_json(PROCESSED_DIR / "capacity_windows.json", [])
    lines = [
        "# Capacity Window Tracker",
        "",
        DISCLAIMER,
        "",
        "**Model:** Intervention -> Capacity Window -> Learning -> Habit Formation -> Functional Change",
        "",
    ]
    if not windows:
        lines.append("No capacity windows detected yet.")
        return "\n".join(lines)
    for index, item in enumerate(windows, start=1):
        lines.extend(
            [
                f"## Capacity Window {index}",
                "",
                bullet("Intervention", item.get("intervention")),
                bullet("Date", item.get("date")),
                bullet("Capacity Window Created", item.get("capacity_window_created")),
                bullet("What Became Possible", item.get("what_became_possible")),
                bullet("Learning", item.get("learning")),
                bullet("Habit Formation", item.get("habit_formation")),
                bullet("Functional Change", item.get("functional_change")),
                bullet("Gains Retained", item.get("gains_retained")),
                bullet("Source", source_label(item)),
                bullet("Confidence Level", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_disability_summary() -> str:
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    disability_rows = [
        row
        for row in matrix
        if row.get("supports_disability") or "disability process" in (row.get("functional_domains") or [])
    ]
    lines = [
        "# Disability Evidence Summary",
        "",
        DISCLAIMER,
        "",
        "This summary focuses on source-supported functional evidence, not diagnosis generation.",
        "",
    ]
    if not disability_rows:
        lines.append("No disability-focused evidence detected yet.")
        lines.append("")
        lines.append("Potential missing evidence to look for: RFC forms, function reports, PT/OT functional observations, longitudinal provider notes, work tolerance documentation, and treatment history.")
        return "\n".join(lines)
    for item in top_matrix_rows(disability_rows, 12):
        lines.extend(
            [
                f"## {item.get('date') or 'Date not found'} - {item.get('source_document')}",
                "",
                bullet("Record Fact", item.get("record_fact")),
                bullet("Functional Consequence", item.get("functional_consequence")),
                bullet("System Relevance", item.get("system_relevance")),
                bullet("Missing Evidence", item.get("missing_evidence")),
                bullet("Source", f"{item.get('source_document')}, {item.get('source_page_or_chunk')}"),
                bullet("Confidence", item.get("confidence_level")),
                "",
            ]
        )
    return "\n".join(lines)


def build_documentation_gap_report() -> str:
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    lines = ["# Documentation Gap Report", "", DISCLAIMER, ""]
    if not bottlenecks:
        lines.append("No documentation gaps inferred yet.")
        return "\n".join(lines)
    for item in bottlenecks:
        lines.extend(
            [
                f"## {item.get('current_bottleneck', 'Documentation Gap')}",
                "",
                bullet("Reality Map Owner", item.get("reality_map_owner")),
                bullet("Gap / Bottleneck", item.get("current_bottleneck")),
                bullet("Evidence Needed", item.get("evidence_needed")),
                bullet("Next Action", item.get("recommended_next_action")),
                bullet("Key Sources", item.get("key_sources")),
                "",
            ]
        )
    return "\n".join(lines)


def build_care_coordination_summary() -> str:
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    lines = [
        "# Care Coordination Summary",
        "",
        DISCLAIMER,
        "",
        "This draft is intended to help a human reviewer prepare care coordination tasks without turning them into medical advice.",
        "",
        "## Current Coordination Needs",
        "",
    ]
    care_rows = [
        row
        for row in matrix
        if any(domain in (row.get("functional_domains") or []) for domain in ["care coordination", "provider support", "disability process", "IADL"])
    ]
    if not care_rows:
        lines.append("No care-coordination rows detected yet.")
    for row in care_rows[:8]:
        lines.extend(
            [
                bullet("Record Fact", row.get("record_fact")),
                bullet("System Relevance", row.get("system_relevance")),
                bullet("Next Available Opportunity", row.get("next_available_opportunity")),
                bullet("Source", f"{row.get('source_document')}, {row.get('source_page_or_chunk')}"),
                "",
            ]
        )

    lines.extend(["", "## Suggested Next Smallest Actions", ""])
    if not bottlenecks:
        lines.append("- Add source records and rerun the pipeline.")
    else:
        for item in bottlenecks[:5]:
            lines.append(f"- {item.get('recommended_next_action')} Sources: {source_list(item.get('key_sources'))}")

    lines.extend(["", "## Human Review Checklist", ""])
    lines.extend(
        [
            "- Confirm dates and source references.",
            "- Remove inaccurate AI/rule-based inferences.",
            "- Verify whether each bottleneck is real.",
            "- Decide what should be shared with a provider.",
            "- Decide what should remain patient-only context.",
        ]
    )
    return "\n".join(lines)


def build_provider_ready_summary(profile: dict | None = None) -> str:
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    grouped = rows_by_domain(matrix)
    preferred_domains = [
        "mobility",
        "endurance",
        "ADL",
        "IADL",
        "pain",
        "joint stability",
        "autonomic symptoms",
        "PT/rehabilitation",
        "treatment response",
        "care coordination",
        "disability process",
    ]
    lines = [
        "# Provider-Ready Summary",
        "",
        DISCLAIMER,
        "",
        "## One-Paragraph Case Summary",
        "",
        build_one_paragraph_case_summary(profile, matrix, bottlenecks),
        "",
    ]
    needed_ocr = ocr_needed_statuses()
    if needed_ocr:
        lines.extend(["## Source Coverage Warning", ""])
        for status in needed_ocr:
            lines.append(
                f"{status['file_name']} was present but did not produce extractable text. "
                "It likely requires OCR before it can be included in this summary. "
                "Current outputs may underrepresent appeal-specific evidence."
            )
            lines.append("")
    if any(row.get("source_document_type") == "disability appeal" for row in matrix):
        lines.extend(
            [
                "## Source Authority Note",
                "",
                (
                    "Disability Appeal evidence contributes disability-process context and treatment-history references, "
                    "but it should not be treated as provider-authored PT evidence unless supported by the PT record itself."
                ),
                "",
            ]
        )
    lines.extend(["## Key Functional Issues by Domain", ""])
    added_domains = 0
    for domain in preferred_domains:
        rows = grouped.get(domain, [])
        if not rows:
            continue
        lines.append(domain_summary_line(domain, rows))
        added_domains += 1
    if added_domains == 0:
        lines.append("No functional domains detected yet.")

    lines.extend(["", "## Source-Supported Evidence", ""])
    for row in top_matrix_rows(matrix, 10):
        lines.extend(
            [
                bullet("Record Fact", row.get("record_fact")),
                bullet("Functional Consequence", row.get("functional_consequence")),
                bullet("System Relevance", row.get("system_relevance")),
                bullet("Possible Second-Layer Meaning", row.get("possible_second_layer_meaning") or row.get("possible_second_layer_change")),
                bullet("Source", f"{row.get('source_document')}, {row.get('source_page_or_chunk')}"),
                bullet("Source Document Type", row.get("source_document_type")),
                bullet("Evidence Content Type", row.get("evidence_content_type")),
                bullet("Evidence Role", row.get("evidence_role")),
                bullet("Source Authority", row.get("source_authority")),
                "",
            ]
        )
    if not matrix:
        lines.append("No source-supported evidence rows generated yet.")

    lines.extend(["", "## Current Bottlenecks", ""])
    if not bottlenecks:
        lines.append("No bottleneck candidates detected yet.")
    for item in bottlenecks[:5]:
        lines.extend(
            [
                bullet("Bottleneck", item.get("current_bottleneck")),
                bullet("Why It Exists", item.get("why_it_exists")),
                bullet("Evidence Needed", item.get("evidence_needed")),
                bullet("Key Sources", item.get("key_sources")),
                "",
            ]
        )

    lines.extend(["", "## Next Smallest Useful Actions", ""])
    if not bottlenecks:
        lines.append("- Review extracted timeline and evidence matrix for missing source documents.")
    for item in bottlenecks[:3]:
        lines.append(f"- {item.get('recommended_next_action')}")

    lines.extend(["", "## Next Available Opportunity", ""])
    opportunities = []
    for item in bottlenecks[:3]:
        opportunity = item.get("next_available_opportunity")
        if opportunity and opportunity not in opportunities:
            opportunities.append(opportunity)
    if opportunities:
        for opportunity in opportunities:
            lines.append(f"- {opportunity}")
    else:
        lines.append("- Clarify the strongest source-supported functional evidence and decide what belongs in a provider-facing summary.")

    lines.extend(["", "## What This Summary Does Not Claim", ""])
    lines.extend(
        [
            "- It does not diagnose a new condition.",
            "- It does not make treatment recommendations.",
            "- It does not replace clinician judgment.",
            "- It does not claim disability eligibility.",
            "- It separates record evidence from rule-based inference and requires human review.",
        ]
    )
    return "\n".join(lines)


def build_patient_action_roadmap(profile: dict | None = None) -> str:
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    lines = ["# Patient Action Roadmap", "", DISCLAIMER, ""]
    if not bottlenecks:
        lines.append("No action roadmap generated yet. Add records and rerun the pipeline.")
        return "\n".join(lines)
    priority_terms = profile_terms(profile or {}, "bottleneck_priorities")
    if priority_terms:
        bottlenecks = sorted(
            bottlenecks,
            key=lambda item: 0 if any(term in " ".join(str(v).lower() for v in item.values()) for term in priority_terms) else 1,
        )
    for index, item in enumerate(bottlenecks[:7], start=1):
        lines.extend(
            [
                f"## Step {index}",
                "",
                bullet("Next Smallest Action", item.get("recommended_next_action")),
                bullet("Why This Matters", item.get("why_it_exists")),
                bullet("Evidence Needed", item.get("evidence_needed")),
                bullet("Next Available Opportunity", item.get("next_available_opportunity")),
                bullet("Source Evidence Summary", item.get("source_evidence_summary") or item.get("source_evidence")),
                bullet("Key Sources", item.get("key_sources")),
                "",
            ]
        )
    return "\n".join(lines)


def markdown_list(paths: list[Path]) -> list[str]:
    if not paths:
        return ["- None found."]
    return [f"- {path.name}" for path in paths]


def supported_raw_files() -> list[Path]:
    return sorted(
        path
        for path in RAW_DIR.glob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".md"}
    )


def extraction_method_label(status: dict) -> str:
    if status.get("ocr_applied_pages", 0) > 0 and status.get("raw_pdf_text_character_count", 0) > 0:
        return "mixed direct text + OCR"
    if status.get("ocr_applied_pages", 0) > 0:
        return "OCR"
    return "direct text extraction"


def source_authority_guidance(source_type: str) -> tuple[str, str]:
    if source_type == "disability appeal":
        return (
            "Use for disability-process context, claimant appeal rationale, treatment-history references, and missing-record questions.",
            "Do not treat as provider-authored medical/PT evidence unless the same claim is supported by provider or PT records.",
        )
    if source_type == "function report":
        return (
            "Use for claimant-reported functional impact, ADL/IADL limits, daily routine, and disability-context language.",
            "Do not treat as clinician observation or objective testing without a matching provider-authored source.",
        )
    if source_type == "PT record":
        return (
            "Use for provider/rehabilitation observations, PT goals, treatment response, functional tolerance, and carryover questions.",
            "Do not treat billing tables or header metadata as functional evidence unless paired with assessment, limitation, or response text.",
        )
    return (
        "Use as source evidence requiring human review.",
        "Do not rely on this source type without confirming author, purpose, and context.",
    )


def document_extraction_statuses() -> list[dict]:
    raw_files = supported_raw_files()
    extracted_pages = read_json(EXTRACTED_DIR / "extracted_pages.json", [])
    pages_by_doc: dict[str, list[dict]] = defaultdict(list)
    for page in extracted_pages:
        pages_by_doc[page.get("document", "unknown")].append(page)

    statuses = []
    for path in raw_files:
        pages = pages_by_doc.get(path.name, [])
        page_count = len(pages)
        extracted_chars = sum(len(page.get("text") or "") for page in pages)
        raw_pdf_chars = sum(page.get("raw_pdf_text_character_count") or 0 for page in pages)
        ocr_chars = sum(page.get("ocr_text_character_count") or 0 for page in pages)
        blank_page_count = sum(1 for page in pages if not (page.get("text") or "").strip())
        ocr_required_pages = sum(1 for page in pages if page.get("ocr_required"))
        ocr_applied_pages = sum(1 for page in pages if page.get("ocr_applied"))
        ocr_error_count = sum(1 for page in pages if page.get("ocr_error"))
        if page_count == 0:
            status = "empty_or_failed_extraction"
            action = f"{path.name} did not produce extracted page records. Recheck the file or rerun extraction."
        elif extracted_chars == 0 and blank_page_count == page_count:
            status = "likely_scanned_pdf"
            action = f"{path.name} appears to have {page_count} pages but produced blank extracted text. This likely requires OCR before it can be included in the evidence matrix."
        elif raw_pdf_chars < 100 and ocr_chars > 0:
            status = "extracted_text_ok"
            action = f"OCR preprocessing generated text for {ocr_applied_pages} page(s), and the document is included in the evidence pipeline."
        elif extracted_chars < 100 and path.suffix.lower() == ".pdf":
            status = "likely_scanned_pdf"
            action = f"{path.name} produced very little extracted text. OCR may be needed before evidence extraction is reliable."
        else:
            status = "extracted_text_ok"
            action = "No OCR action needed for V1 text extraction."
        source_type = source_document_type(path.name)
        status_row = {
            "file_name": path.name,
            "source_document_type": source_type,
            "source_authority": source_authority(source_type),
            "page_count": page_count,
            "extracted_text_character_count": extracted_chars,
            "raw_pdf_text_character_count": raw_pdf_chars,
            "ocr_text_character_count": ocr_chars,
            "blank_page_count": blank_page_count,
            "ocr_required_pages": ocr_required_pages,
            "ocr_applied_pages": ocr_applied_pages,
            "ocr_error_count": ocr_error_count,
            "extraction_status": status,
            "recommended_action": action,
        }
        status_row["extraction_method"] = extraction_method_label(status_row)
        statuses.append(status_row)
    return statuses


def ocr_needed_statuses() -> list[dict]:
    return [
        status
        for status in document_extraction_statuses()
        if status.get("extraction_status") in {"likely_scanned_pdf", "empty_or_failed_extraction"}
    ]


def build_document_coverage() -> str:
    raw_files = supported_raw_files()
    statuses = document_extraction_statuses()
    extracted_pages = read_json(EXTRACTED_DIR / "extracted_pages.json", [])
    chunk_files = sorted([path for path in CHUNKS_DIR.glob("*.json") if path.is_file()])
    events = read_json(PROCESSED_DIR / "events.json", [])
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    event_docs = Counter(event.get("source_document", "unknown") for event in events)
    matrix_docs = Counter(row.get("source_document", "unknown") for row in matrix)
    page_docs = Counter(page.get("document", "unknown") for page in extracted_pages)
    blank_pages = Counter(
        page.get("document", "unknown")
        for page in extracted_pages
        if not (page.get("text") or "").strip()
    )
    lines = [
        "# Document Coverage Debug Report",
        "",
        "This report helps identify whether the pipeline actually saw the documents, extracted text, created chunks, and produced source-linked rows.",
        "",
        "## Raw Documents",
        "",
        *markdown_list(raw_files),
        "",
        "## Extraction Status by Document",
        "",
    ]
    for status in statuses:
        lines.extend(
            [
                f"### {status['file_name']}",
                "",
                bullet("Source Document Type", status["source_document_type"]),
                bullet("Source Authority", status["source_authority"]),
                bullet("Extraction Method", status["extraction_method"]),
                bullet("Page Count", status["page_count"]),
                bullet("Extracted Text Character Count", status["extracted_text_character_count"]),
                bullet("Raw PDF Text Character Count", status["raw_pdf_text_character_count"]),
                bullet("OCR Text Character Count", status["ocr_text_character_count"]),
                bullet("Blank Page Count", status["blank_page_count"]),
                bullet("OCR Required Pages", status["ocr_required_pages"]),
                bullet("OCR Applied Pages", status["ocr_applied_pages"]),
                bullet("OCR Error Count", status["ocr_error_count"]),
                bullet("Extraction Status", status["extraction_status"]),
                bullet("Recommended Action", status["recommended_action"]),
                "",
            ]
        )
    lines.extend(
        [
        "## Extracted Pages",
        "",
        bullet("Total extracted pages/text records", len(extracted_pages)),
        "",
        "## Chunk Files",
        "",
        *markdown_list(chunk_files),
        "",
        "## Coverage Counts",
        "",
        bullet("Events extracted", len(events)),
        bullet("Evidence matrix rows", len(matrix)),
        bullet("Consolidated bottlenecks", len(bottlenecks)),
        "",
        ]
    )
    if page_docs:
        lines.extend(["## Extracted Pages by Source", ""])
        for doc, count in page_docs.most_common():
            blank = blank_pages.get(doc, 0)
            note = f" ({blank} blank pages)" if blank else ""
            lines.append(f"- {doc}: {count}{note}")
        lines.append("")
    lines.extend(["## Event Rows by Source", ""])
    if event_docs:
        for doc, count in event_docs.most_common():
            lines.append(f"- {doc}: {count}")
    else:
        lines.append("- None found.")
    lines.extend(["", "## Evidence Rows by Source", ""])
    if matrix_docs:
        for doc, count in matrix_docs.most_common():
            lines.append(f"- {doc}: {count}")
    else:
        lines.append("- None found.")
    missing_matrix_docs = [path.name for path in raw_files if path.name not in matrix_docs]
    if missing_matrix_docs:
        lines.extend(["", "## Raw Documents Without Evidence Rows", ""])
        for name in missing_matrix_docs:
            blank = blank_pages.get(name, 0)
            reason = "text extraction returned blank pages; OCR may be needed" if blank else "no event rows matched V1 rules"
            lines.append(f"- {name}: {reason}")
    return "\n".join(lines)


def build_source_authority_map() -> str:
    statuses = document_extraction_statuses()
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    matrix_docs = Counter(row.get("source_document", "unknown") for row in matrix)
    content_types_by_doc: dict[str, set[str]] = defaultdict(set)
    for row in matrix:
        if row.get("evidence_content_type"):
            content_types_by_doc[row.get("source_document", "unknown")].add(row.get("evidence_content_type"))

    lines = [
        "# Source Authority Map",
        "",
        DISCLAIMER,
        "",
        "This report separates source document type from evidence content type so the pipeline does not mistake appeal/process evidence for provider-authored evidence.",
        "",
    ]
    if not statuses:
        lines.append("No source documents found.")
        return "\n".join(lines)

    for status in statuses:
        use_for, do_not_use_for = source_authority_guidance(status["source_document_type"])
        content_types = sorted(content_types_by_doc.get(status["file_name"], set()))
        lines.extend(
            [
                f"## {status['file_name']}",
                "",
                bullet("Source Document Type", status["source_document_type"]),
                bullet("Source Authority", status["source_authority"]),
                bullet("Extraction Method", status["extraction_method"]),
                bullet("Extraction Status", status["extraction_status"]),
                bullet("Evidence Rows Generated", matrix_docs.get(status["file_name"], 0)),
                bullet("Evidence Content Types Found", content_types),
                bullet("Use For", use_for),
                bullet("Do Not Use For", do_not_use_for),
                "",
            ]
        )
    return "\n".join(lines)


def build_ocr_needed_report() -> str:
    needed = ocr_needed_statuses()
    lines = [
        "# OCR Needed",
        "",
        "This debug report lists documents that were present but did not produce enough extractable text for reliable evidence extraction.",
        "",
    ]
    if not needed:
        lines.append("No OCR-needed documents detected.")
        return "\n".join(lines)
    for status in needed:
        lines.extend(
            [
                f"## {status['file_name']}",
                "",
                bullet("Page Count", status["page_count"]),
                bullet("Extracted Text Character Count", status["extracted_text_character_count"]),
                bullet("Raw PDF Text Character Count", status["raw_pdf_text_character_count"]),
                bullet("OCR Text Character Count", status["ocr_text_character_count"]),
                bullet("Blank Page Count", status["blank_page_count"]),
                bullet("OCR Required Pages", status["ocr_required_pages"]),
                bullet("OCR Applied Pages", status["ocr_applied_pages"]),
                bullet("OCR Error Count", status["ocr_error_count"]),
                bullet("Extraction Status", status["extraction_status"]),
                bullet("Recommended Action", status["recommended_action"]),
                "",
            ]
        )
    return "\n".join(lines)


def build_calibration_notes() -> str:
    events = read_json(PROCESSED_DIR / "events.json", [])
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    raw_bottlenecks = read_json(PROCESSED_DIR / "bottlenecks_raw.json", [])
    bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
    dates_missing = [event for event in events if not event.get("date")]
    unclassified = [row for row in matrix if not row.get("functional_domains")]
    low_confidence = [row for row in matrix if row.get("confidence_level") in {"low", "unknown"}]
    lines = [
        "# Calibration Notes",
        "",
        "Use this file after each run to decide whether the next patch should improve extraction, classification, bottlenecks, or report wording.",
        "",
        "## Quick Counts",
        "",
        bullet("Events without selected event dates", len(dates_missing)),
        bullet("Evidence rows without functional domains", len(unclassified)),
        bullet("Low/unknown confidence evidence rows", len(low_confidence)),
        bullet("Raw bottleneck candidates before clustering", len(raw_bottlenecks)),
        bullet("Consolidated bottlenecks after clustering", len(bottlenecks)),
        "",
        "## Review Prompts",
        "",
        "- Did the selected date represent a visit/service/signed/completed date rather than DOB or administrative metadata?",
        "- Did the Evidence Matrix preserve medical fact -> functional consequence -> system relevance -> next available opportunity?",
        "- Did any patient observation get presented as record evidence?",
        "- Did bottlenecks stay consolidated into a small usable set?",
        "- Did the provider summary avoid new diagnoses, treatment recommendations, or overstatement?",
        "",
        "## Rows Needing Human Review",
        "",
    ]
    if not unclassified and not low_confidence:
        lines.append("- No obvious low-confidence or unclassified evidence rows found by the debug pass.")
    for row in (unclassified + low_confidence)[:15]:
        lines.extend(
            [
                f"- {row.get('source_document')} / {row.get('source_page_or_chunk')}: {row.get('record_fact') or row.get('claim_or_functional_issue')}",
            ]
        )
    return "\n".join(lines)


def generate_all_reports(profile: dict | None = None) -> None:
    ensure_directories()
    write_text(REPORTS_DIR / "healthcare_reality_map.md", build_healthcare_reality_map(profile))
    write_text(REPORTS_DIR / "evidence_matrix.md", build_evidence_matrix_report())
    write_text(REPORTS_DIR / "best_evidence.md", build_best_evidence_report())
    write_text(REPORTS_DIR / "source_authority_map.md", build_source_authority_map())
    write_text(REPORTS_DIR / "bottlenecks.md", build_bottlenecks_report())
    write_text(REPORTS_DIR / "capacity_windows.md", build_capacity_report())
    write_text(REPORTS_DIR / "hidden_states.md", build_hidden_states_report())
    write_text(REPORTS_DIR / "trust_thresholds.md", build_trust_thresholds_report())
    write_text(REPORTS_DIR / "disability_evidence_summary.md", build_disability_summary())
    write_text(REPORTS_DIR / "documentation_gap_report.md", build_documentation_gap_report())
    write_text(REPORTS_DIR / "care_coordination_summary.md", build_care_coordination_summary())
    write_text(REPORTS_DIR / "provider_ready_summary.md", build_provider_ready_summary(profile))
    write_text(REPORTS_DIR / "patient_action_roadmap.md", build_patient_action_roadmap(profile))
    write_text(DEBUG_DIR / "document_coverage.md", build_document_coverage())
    write_text(DEBUG_DIR / "calibration_notes.md", build_calibration_notes())
    write_text(DEBUG_DIR / "ocr_needed.md", build_ocr_needed_report())


def main() -> None:
    generate_all_reports()
    print(f"Wrote reports to {REPORTS_DIR}")
    print(f"Wrote debug reports to {DEBUG_DIR}")


if __name__ == "__main__":
    main()
