from collections import defaultdict

from config import PROCESSED_DIR, ensure_directories
from utils import read_json, write_json


BOTTLENECK_CATEGORIES = [
    {
        "key": "disability_functional_evidence_formatting_gap",
        "title": "Disability functional evidence formatting gap",
        "owner": "disability",
        "domains": {"ADL", "IADL", "mobility", "endurance", "cognition", "disability process"},
        "goal": "Make functional limitations usable for disability and provider review.",
        "bottleneck": "Functional evidence exists, but it is not yet organized into concise disability/provider-ready functional language.",
        "why": "Source documents may describe limitations across different formats; the system needs a coherent source-cited bridge from symptoms to functional limits.",
        "needed": "ADL/IADL limits, walking/standing/sitting tolerance, recovery time, flare pattern, PT/OT observations, and provider documentation.",
        "action": "Convert the strongest functional evidence into a one-page provider/disability-ready summary.",
        "opportunity": "Stronger disability evidence, clearer provider communication, and better documentation alignment.",
    },
    {
        "key": "care_coordination_admin_capacity_bottleneck",
        "title": "Care coordination / administrative capacity bottleneck",
        "owner": "care coordination",
        "domains": {"care coordination", "IADL"},
        "goal": "Reduce administrative burden and organize the next steps.",
        "bottleneck": "Care coordination tasks appear scattered across documents and may exceed available patient capacity.",
        "why": "Complex care requires records, forms, appointments, summaries, and follow-up tasks that are not yet held in one operational roadmap.",
        "needed": "Current task list, missing records, appointment needs, provider asks, and patient capacity limits.",
        "action": "Create a short care-coordination task list with the next one to three actions.",
        "opportunity": "Reduced administrative burden and a clearer next available opportunity for care navigation.",
    },
    {
        "key": "pt_functional_tracking_gap",
        "title": "Therapy/provider functional limitation and treatment-response tracking gap",
        "owner": "provider",
        "domains": {"PT/rehabilitation", "treatment response"},
        "goal": "Use therapy/provider evidence to clarify functional limits and treatment response.",
        "bottleneck": "Therapy/provider observations and treatment response are not yet translated into concise functional evidence.",
        "why": "Therapy and provider records may contain observable function, tolerance, instability, treatment response, and flare information that can support care planning and disability documentation.",
        "needed": "Therapy/provider observations of walking, standing, instability, tolerance, intervention response, flare pattern, and carryover.",
        "action": "Ask PT/provider to document functional tolerance, observed deficits, treatment response, and carryover.",
        "opportunity": "Better provider summary, stronger functional evidence, and clearer capacity-window tracking.",
    },
    {
        "key": "provider_ready_summary_gap",
        "title": "Provider-ready longitudinal summary gap",
        "owner": "provider",
        "domains": {"provider support", "care coordination", "disability process", "treatment response"},
        "goal": "Help providers understand the case faster.",
        "bottleneck": "The longitudinal story is not yet reduced into a clinician-friendly summary that separates evidence from inference.",
        "why": "Complex records contain many pieces of evidence, but providers need a concise scanable bridge from record facts to functional consequences and next asks.",
        "needed": "Top functional issues, strongest sources, current bottlenecks, and one to three specific provider asks.",
        "action": "Prepare a provider-ready summary focused on functional limits, treatment response, documentation needs, and next smallest actions.",
        "opportunity": "Faster provider understanding, clearer visit preparation, and improved care coordination.",
    },
    {
        "key": "adl_iadl_documentation_gap",
        "title": "ADL/IADL documentation gap",
        "owner": "disability",
        "domains": {"ADL", "IADL"},
        "goal": "Document daily-function limitations in system-usable language.",
        "bottleneck": "Daily living limits may be present but not yet organized into concise functional documentation.",
        "why": "Disability and care coordination systems need concrete examples of bathing, grooming, meal preparation, cleaning, paperwork, scheduling, and recovery limitations.",
        "needed": "Specific ADL/IADL examples, frequency, duration, recovery time, assistance needed, and source citations.",
        "action": "Summarize ADL/IADL limits from the strongest source documents and supporting records.",
        "opportunity": "Stronger disability evidence and more concrete provider communication.",
    },
    {
        "key": "insurance_authorization_documentation_barrier",
        "title": "Insurance authorization/documentation barrier",
        "owner": "insurance",
        "source_types": {"insurance denial letter"},
        "domains": set(),
        "goal": "Resolve payer barrier or prepare appeal/authorization support.",
        "bottleneck": "Insurance denial or utilization review may require clearer medical-necessity, functional-impact, or treatment-history evidence.",
        "why": "Insurance decision documents can describe payer rationale, authorization barriers, medical-necessity criteria, appeal rights, or missing documentation.",
        "needed": "Denial reason, medical necessity criteria, provider documentation, functional impact, treatment history, appeal deadline/rights.",
        "action": "Extract the denial rationale and map it to available provider/therapy/function evidence.",
        "opportunity": "Cleaner appeal packet, stronger authorization request, or clearer documentation gap.",
    },
    {
        "key": "appeal_dds_evidence_organization_gap",
        "title": "Appeal/DDS evidence organization gap",
        "owner": "disability",
        "source_terms": ["appeal", "dds", "disability appeal"],
        "domains": set(),
        "goal": "Strengthen disability evidence and reduce mismatch between claimant appeal narrative and provider records.",
        "bottleneck": "Appeal evidence is now extractable through OCR, but it must be separated from provider-authored medical evidence and reconciled with PT/provider records.",
        "why": "Appeal and DDS materials may reference PT, providers, treatment history, or missing records, but source authority must stay clear before appeal statements are treated as medical evidence.",
        "needed": "Appeal statements, Function Report support, PT/provider support, discrepancies, missing records, and source-authority labels for each claim.",
        "action": "Create an appeal evidence reconciliation section comparing appeal statements to Function Report and PT/provider record evidence.",
        "opportunity": "Cleaner disability evidence package and better source-authority separation.",
    },
    {
        "key": "capacity_window_tracking_gap",
        "title": "Capacity window tracking gap",
        "owner": "patient",
        "domains": {"treatment response"},
        "goal": "Track what becomes possible after treatment or intervention response.",
        "bottleneck": "Treatment response is not yet connected to functional change, habit formation, or retained gains.",
        "why": "Interventions matter not only because symptoms change, but because they may create windows for PT, routines, documentation, and function.",
        "needed": "Intervention date, symptom change, what became possible, learning, habit formation, functional change, and retained gains.",
        "action": "Track response and capacity changes for one to two weeks after the intervention.",
        "opportunity": "Better treatment-response evidence and clearer care planning.",
    },
]


def row_text(row: dict) -> str:
    return " ".join(str(value).lower() for value in row.values())


def source_key(row: dict) -> str:
    return f"{row.get('source_document')} ({row.get('source_page_or_chunk')})"


def matches_category(row: dict, category: dict) -> bool:
    domains = set(row.get("functional_domains") or [])
    text = row_text(row)
    domain_match = bool(domains.intersection(category.get("domains", set())))
    source_type_match = row.get("source_document_type") in category.get("source_types", set())
    if category.get("key") == "appeal_dds_evidence_organization_gap":
        return row.get("source_document_type") == "disability appeal"
    source_match = any(term in text for term in category.get("source_terms", []))
    return domain_match or source_match or source_type_match


def source_type_summary(source_types: set[str]) -> str:
    parts = []
    if "function report" in source_types:
        parts.append("Function Report sources describe claimant-reported ADL/IADL, mobility, endurance, cognitive, administrative-capacity, and daily-function limits")
    if "PT record" in source_types:
        parts.append("PT sources describe functional limitation, rehab goals, response, flare/carryover, and treatment-planning context")
    if "OT record" in source_types:
        parts.append("OT sources describe ADL/IADL limits, self-care limitations, adaptive-equipment needs, pacing, joint protection, or functional rehabilitation observations")
    if "health-system/provider record" in source_types:
        parts.append("Provider-authored medical records describe diagnoses, assessments, treatment plans, referrals, medications, clinical observations, or follow-up needs")
    if "insurance denial letter" in source_types:
        parts.append("Insurance denial evidence describes authorization barriers, payer rationale, medical-necessity criteria, appeal rights, or missing documentation")
    if "disability appeal" in source_types:
        parts.append("Appeal/process evidence describes claimant-submitted disability-process context and should be reconciled with provider-authored records")
    return "; ".join(parts)


def source_summary(rows: list[dict], category: dict) -> str:
    docs = {row.get("source_document", "") for row in rows}
    domains = set()
    pt_types = set()
    source_types = set()
    for row in rows:
        domains.update(row.get("functional_domains") or [])
        if row.get("source_document_type"):
            source_types.add(row.get("source_document_type"))
        if row.get("pt_evidence_type"):
            pt_types.add(row.get("pt_evidence_type"))

    key = category.get("key")
    source_description = source_type_summary(source_types)

    if key == "pt_functional_tracking_gap":
        return (source_description or "Therapy/provider sources describe functional limitation, treatment response, and treatment-planning needs.") + "."
    if key == "capacity_window_tracking_gap":
        return (
            (source_description or "Treatment-response sources document possible capacity windows")
            + "; the reports do not yet show retained gains, "
            "carryover between sessions, or what daily function changed after the intervention."
        )
    if key == "adl_iadl_documentation_gap":
        return (source_description or "Source documents describe ADL/IADL and daily-function limits.") + "."
    if key == "care_coordination_admin_capacity_bottleneck":
        return (source_description or "Source documents describe appointment, paperwork, scheduling, follow-up, or care-coordination burden.") + "."
    if key == "provider_ready_summary_gap":
        return (source_description or "Source documents need a concise clinician-friendly summary that separates evidence from inference.") + "."
    if key == "disability_functional_evidence_formatting_gap":
        return (source_description or "Source documents describe functional evidence that needs source-cited disability/provider-ready formatting.") + "."
    if key == "insurance_authorization_documentation_barrier":
        return (
            "Insurance denial evidence describes authorization barriers, payer rationale, medical-necessity criteria, appeal rights, or missing documentation. "
            "Provider, therapy, and functional evidence should be mapped to the denial rationale before appeal or authorization use."
        )
    if key == "appeal_dds_evidence_organization_gap":
        return (
            (source_description or "Appeal/process evidence is readable and should be reconciled with source-authority labels")
            + "."
        )

    domain_summary = ", ".join(sorted(domains)) or "unclassified evidence"
    pt_summary = ", ".join(sorted(pt_types)) if pt_types else "no PT subtype"
    return f"Grouped evidence includes {domain_summary}; PT subtype coverage: {pt_summary}."


def confidence(rows: list[dict]) -> str:
    meaningful_rows = [row for row in rows if row.get("evidence_strength_score", 0) > 0]
    levels = [row.get("confidence_level", "unknown") for row in meaningful_rows or rows]
    if "high" in levels and len(meaningful_rows or rows) >= 2:
        return "high"
    if "high" in levels or "medium" in levels:
        return "medium"
    return "low" if rows else "unknown"


def raw_candidates_from_matrix(matrix: list[dict]) -> list[dict]:
    candidates = []
    for row in matrix:
        for category in BOTTLENECK_CATEGORIES:
            if matches_category(row, category):
                candidates.append(
                    {
                        "category": category["key"],
                        "source_document": row.get("source_document"),
                        "source_page_or_chunk": row.get("source_page_or_chunk"),
                        "record_fact": row.get("record_fact"),
                        "functional_domains": row.get("functional_domains", []),
                        "source_document_type": row.get("source_document_type"),
                        "evidence_content_type": row.get("evidence_content_type"),
                        "source_authority": row.get("source_authority"),
                    }
                )
    return candidates


def detect_bottlenecks(profile: dict | None = None) -> list[dict]:
    ensure_directories()
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    raw_candidates = raw_candidates_from_matrix(matrix)
    write_json(PROCESSED_DIR / "bottlenecks_raw.json", raw_candidates)

    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in matrix:
        for category in BOTTLENECK_CATEGORIES:
            if matches_category(row, category):
                by_category[category["key"]].append(row)

    bottlenecks = []
    for category in BOTTLENECK_CATEGORIES:
        rows = sorted(
            by_category.get(category["key"], []),
            key=lambda row: row.get("evidence_strength_score", 0),
            reverse=True,
        )
        if not rows:
            continue
        key_sources = []
        for row in rows:
            label = source_key(row)
            if label not in key_sources:
                key_sources.append(label)
        bottlenecks.append(
            {
                "current_goal": category["goal"],
                "current_bottleneck": category["bottleneck"],
                "reality_map_owner": category["owner"],
                "why_it_exists": category["why"],
                "source_evidence_summary": source_summary(rows, category),
                "key_sources": key_sources[:6],
                "evidence_needed": category["needed"],
                "recommended_next_action": category["action"],
                "next_available_opportunity": category["opportunity"],
                "source_evidence": source_summary(rows, category),
                "source": {
                    "document": rows[0].get("source_document"),
                    "page": None,
                    "chunk_id": rows[0].get("source_page_or_chunk"),
                },
                "confidence_level": confidence(rows),
            }
        )

    write_json(PROCESSED_DIR / "bottlenecks.json", bottlenecks[:8])
    return bottlenecks[:8]


def main() -> None:
    bottlenecks = detect_bottlenecks()
    print(f"Detected {len(bottlenecks)} consolidated bottleneck candidates.")
    print(f"Wrote {PROCESSED_DIR / 'bottlenecks.json'}")


if __name__ == "__main__":
    main()
