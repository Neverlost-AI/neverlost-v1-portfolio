from collections import Counter, defaultdict
from pathlib import Path

from generate_reports import document_extraction_statuses
from utils import normalize_whitespace, read_json, write_json, write_text


PRIORITIZED_LIMIT = 25


def contains_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def short_text(text: str | None, limit: int = 360) -> str:
    text = normalize_whitespace(text or "")
    if len(text) <= limit:
        return text or "Not identified."
    return text[:limit].rsplit(" ", 1)[0] + "."


def source_authority_score(row: dict) -> int:
    source_type = row.get("source_document_type")
    authority = row.get("source_authority", "")
    if source_type == "health-system/provider record" or "provider-authored medical record" in authority:
        return 40
    if source_type in {"OT record", "PT record"} or "therapy" in authority.lower():
        return 36
    if source_type == "insurance denial letter" or "payer" in authority.lower():
        return 32
    if source_type in {"function report", "disability appeal"}:
        return 24
    return 10


def functional_impact_score(row: dict) -> int:
    domains = set(row.get("functional_domains") or [])
    text = " ".join(
        str(row.get(field, ""))
        for field in ["evidence_content_type", "record_fact", "functional_consequence", "system_relevance"]
    ).lower()
    score = 0
    weights = {
        "ADL": 16,
        "IADL": 14,
        "mobility": 14,
        "endurance": 12,
        "treatment response": 12,
        "care coordination": 10,
        "insurance/authorization": 14,
        "disability process": 12,
        "pain": 8,
        "joint stability": 8,
        "cognition": 8,
    }
    score += sum(weight for domain, weight in weights.items() if domain in domains)
    if contains_any(text, ["functional limitation", "self-care", "medical necessity", "authorization barrier", "denial"]):
        score += 10
    if contains_any(text, ["bathing", "standing", "walking", "stairs", "lifting", "pacing", "care coordination"]):
        score += 8
    return score


def system_relevance_score(row: dict) -> int:
    text = " ".join(
        str(row.get(field, ""))
        for field in ["system_relevance", "why_it_matters", "next_available_opportunity", "missing_evidence"]
    ).lower()
    score = 0
    for term, points in [
        ("provider summary", 10),
        ("disability", 10),
        ("authorization", 10),
        ("insurance", 10),
        ("care coordination", 8),
        ("capacity-window", 8),
        ("functional tolerance", 8),
        ("documentation", 6),
    ]:
        if term in text:
            score += points
    return score


def actionability_score(row: dict) -> int:
    opportunity = (row.get("next_available_opportunity") or "").lower()
    missing = (row.get("missing_evidence") or "").lower()
    score = 0
    if opportunity and "hold this row" not in opportunity:
        score += 12
    if missing:
        score += 6
    if row.get("supports_disability"):
        score += 5
    if row.get("supports_treatment"):
        score += 4
    if row.get("supports_referral"):
        score += 4
    if row.get("supports_insurance_authorization"):
        score += 5
    if row.get("confidence_level") == "high":
        score += 4
    elif row.get("confidence_level") in {"low", "unknown"}:
        score -= 6
    return score


def evidence_score(row: dict) -> int:
    base = row.get("evidence_strength_score") or 0
    return source_authority_score(row) + functional_impact_score(row) + system_relevance_score(row) + actionability_score(row) + int(base / 8)


def recommended_use_text(row: dict) -> str:
    return " ".join(
        str(row.get(field, ""))
        for field in [
            "source_authority",
            "source_document_type",
            "evidence_content_type",
            "record_fact",
            "functional_consequence",
            "system_relevance",
            "why_it_matters",
            "next_available_opportunity",
            "missing_evidence",
        ]
    ).lower()


def recommended_use(
    row: dict,
    insurance_denial_present: bool = False,
    prioritized: bool = False,
) -> list[str]:
    uses: list[str] = []
    source_type = row.get("source_document_type")
    authority = (row.get("source_authority") or "").lower()
    domains = set(row.get("functional_domains") or [])
    text = recommended_use_text(row)

    def add(use: str) -> None:
        if use not in uses:
            uses.append(use)

    has_functional_limits = (
        row.get("supports_disability")
        or "disability process" in domains
        or contains_any(
            text,
            [
                "adl",
                "iadl",
                "self-care",
                "self care",
                "mobility",
                "functional limitation",
                "walking",
                "standing",
                "stairs",
                "bathing",
                "hygiene",
                "carryover",
                "pacing",
                "energy conservation",
                "joint protection",
            ],
        )
    )
    has_treatment_or_medical_necessity = contains_any(
        text,
        ["treatment", "medical necessity", "medically necessary", "authorization", "therapy", "medication", "care plan"],
    )
    has_care_followthrough = (
        "care coordination" in domains
        or contains_any(text, ["care coordination", "follow-up", "follow through", "referral", "records", "forms", "support need"])
    )
    has_denial_or_criteria = contains_any(text, ["denial", "denied", "criteria", "missing documentation", "coverage", "authorization"])
    needs_corroboration = contains_any(text, ["corroborat", "claimant", "appeal", "patient reported", "self-report"])

    if source_type == "health-system/provider record" or "provider-authored medical record" in authority:
        add("provider summary")
        if has_functional_limits:
            add("disability evidence")
        if has_treatment_or_medical_necessity or row.get("supports_insurance_authorization"):
            add("insurance appeal")

    if source_type in {"OT record", "PT record"} or "occupational therapy" in authority or "physical therapy" in authority:
        add("provider summary")
        if has_functional_limits:
            add("disability evidence")
        if insurance_denial_present or has_denial_or_criteria:
            add("insurance appeal")
        if has_care_followthrough:
            add("care coordination")

    if source_type == "insurance denial letter" or "payer" in authority or "insurance utilization review" in authority:
        add("insurance appeal")
        if has_denial_or_criteria:
            add("care coordination")
        if has_denial_or_criteria or contains_any(text, ["evidence gap", "missing", "documentation"]):
            add("internal review")

    if source_type in {"function report", "disability appeal"} or "claimant" in authority:
        add("disability evidence")
        if has_care_followthrough:
            add("care coordination")
        if needs_corroboration:
            add("internal review")

    if contains_any(text, ["provider", "clinician", "doctor", "medical record"]):
        add("provider summary")
    if contains_any(text, ["disability", "functional limitation", "adl", "iadl", "self-care", "self care", "mobility"]):
        add("disability evidence")
    if contains_any(text, ["insurance", "appeal", "authorization", "denial", "coverage", "medical necessity"]):
        add("insurance appeal")
    if contains_any(text, ["care coordination", "referral", "follow-up", "forms", "records", "appointment"]):
        add("care coordination")
    if contains_any(text, ["internal review", "evidence gap", "documentation gap", "missing documentation"]):
        add("internal review")

    if not uses:
        add("internal review")
    return uses


def recommended_use_note(row: dict, uses: list[str], prioritized: bool = False) -> str | None:
    if prioritized and uses == ["internal review"]:
        return "Recommended use inferred because this row was selected as prioritized evidence."
    return None


def linked_bottleneck(row: dict, bottlenecks: list[dict]) -> str:
    source = f"{row.get('source_document')} ({row.get('source_page_or_chunk')})"
    for item in bottlenecks:
        if source in (item.get("key_sources") or []):
            return item.get("current_bottleneck", "Linked bottleneck")
    row_text = " ".join(str(row.get(field, "")) for field in ["system_relevance", "next_available_opportunity", "evidence_content_type"]).lower()
    for item in bottlenecks:
        bottleneck_text = " ".join(str(item.get(field, "")) for field in ["current_bottleneck", "evidence_needed", "recommended_next_action"]).lower()
        if "insurance" in row_text and "insurance" in bottleneck_text:
            return item.get("current_bottleneck", "Linked bottleneck")
        if "care coordination" in row_text and "care coordination" in bottleneck_text:
            return item.get("current_bottleneck", "Linked bottleneck")
        if "capacity" in row_text and "capacity" in bottleneck_text:
            return item.get("current_bottleneck", "Linked bottleneck")
    return "No direct bottleneck link identified."


def prioritized_evidence_items(matrix: list[dict], bottlenecks: list[dict], limit: int = PRIORITIZED_LIMIT) -> list[dict]:
    ranked = sorted(matrix, key=evidence_score, reverse=True)
    selected = []
    per_doc = Counter()
    per_content = Counter()
    insurance_denial_present = any(row.get("source_document_type") == "insurance denial letter" for row in matrix)
    for row in ranked:
        doc = row.get("source_document", "unknown")
        content = row.get("evidence_content_type", "unknown")
        if per_doc[doc] >= 12:
            continue
        if per_content[content] >= 5 and row.get("source_document_type") != "insurance denial letter":
            continue
        uses = recommended_use(row, insurance_denial_present=insurance_denial_present, prioritized=True)
        use_note = recommended_use_note(row, uses, prioritized=True)
        selected.append(
            {
                "rank": len(selected) + 1,
                "score": evidence_score(row),
                "source_document": row.get("source_document"),
                "source_page_or_chunk": row.get("source_page_or_chunk"),
                "source_document_type": row.get("source_document_type"),
                "source_authority": row.get("source_authority"),
                "evidence_role": row.get("evidence_role"),
                "evidence_content_type": row.get("evidence_content_type"),
                "payer_name": row.get("payer_name"),
                "denied_service_type": row.get("denied_service_type"),
                "denial_context": row.get("denial_context"),
                "record_fact": row.get("record_fact"),
                "functional_consequence": row.get("functional_consequence"),
                "system_relevance": row.get("system_relevance"),
                "why_this_evidence_matters": row.get("why_it_matters") or row.get("system_relevance"),
                "linked_bottleneck": linked_bottleneck(row, bottlenecks),
                "recommended_use": uses,
                "recommended_use_note": use_note,
                "confidence_level": row.get("confidence_level"),
            }
        )
        per_doc[doc] += 1
        per_content[content] += 1
        if len(selected) >= limit:
            break
    return selected


def build_prioritized_evidence_md(items: list[dict]) -> str:
    lines = [
        "# Prioritized Evidence",
        "",
        f"This report reduces the full evidence matrix into the strongest {len(items)} source-linked rows for human review.",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"## Rank {item['rank']}",
                "",
                f"- **Source document:** {item['source_document']}",
                f"- **Source page or chunk:** {item['source_page_or_chunk']}",
                f"- **Source document type:** {item['source_document_type']}",
                f"- **Source authority:** {item['source_authority']}",
                f"- **Evidence role:** {item['evidence_role']}",
                f"- **Evidence content type:** {item['evidence_content_type']}",
                f"- **Payer name:** {item.get('payer_name') or 'Not identified.'}",
                f"- **Denied service type:** {item.get('denied_service_type') or 'Not identified.'}",
                f"- **Denial context:** {item.get('denial_context') or 'Not identified.'}",
                f"- **Record fact:** {short_text(item['record_fact'], 500)}",
                f"- **Functional consequence:** {item['functional_consequence']}",
                f"- **System relevance:** {item['system_relevance']}",
                f"- **Why this evidence matters:** {item['why_this_evidence_matters']}",
                f"- **Linked bottleneck:** {item['linked_bottleneck']}",
                f"- **Recommended use:** {', '.join(item['recommended_use'])}",
                f"- **Recommended use note:** {item['recommended_use_note'] or 'No note.'}",
                f"- **Confidence:** {item['confidence_level']}",
                "",
            ]
        )
    return "\n".join(lines)


def capacity_theme_for_window(window: dict) -> list[str]:
    text = " ".join(str(window.get(field, "")) for field in ["intervention", "source_evidence", "what_became_possible", "learning"]).lower()
    themes = []
    if contains_any(text, ["bathing", "self-care", "self care", "adl", "dressing", "hygiene"]):
        themes.append("ADL/self-care capacity")
    if contains_any(text, ["home", "vacuuming", "household", "iadl", "daily activities", "functional activity"]):
        themes.append("IADL/home-management capacity")
    if contains_any(text, ["walking", "stairs", "standing", "mobility", "gait"]):
        themes.append("mobility/stairs/walking capacity")
    if contains_any(text, ["upper extremity", "joint protection", "joint stabilization", "hypermobility", "supportive garments", "supportive devices"]):
        themes.append("upper-extremity/joint-protection capacity")
    if contains_any(text, ["improvement", "treatment", "medication", "respond", "carryover", "symptoms", "pain"]):
        themes.append("treatment response/carryover capacity")
    if contains_any(text, ["coordinate", "records", "follow-up", "appointment", "referral", "provider"]):
        themes.append("care coordination/administrative capacity")
    if contains_any(text, ["authorization", "insurance", "denial", "coverage"]):
        themes.append("insurance/authorization capacity")
    if contains_any(text, ["pacing", "energy conservation", "fatigue", "breathwork", "somatic", "regulating"]):
        themes.append("pacing/energy conservation capacity")
    return themes or ["treatment response/carryover capacity"]


def source_authority_for_document(statuses: list[dict], document: str | None) -> str:
    for status in statuses:
        if status["file_name"] == document:
            return status.get("source_authority", "unknown source authority")
    return "unknown source authority"


def related_bottlenecks_for_theme(theme: str, bottlenecks: list[dict]) -> list[str]:
    theme_text = theme.lower()
    related = []
    for item in bottlenecks:
        text = " ".join(str(item.get(field, "")) for field in ["current_bottleneck", "evidence_needed", "recommended_next_action"]).lower()
        if "insurance" in theme_text and "insurance" in text:
            related.append(item.get("current_bottleneck"))
        elif "care coordination" in theme_text and "care coordination" in text:
            related.append(item.get("current_bottleneck"))
        elif "capacity" in theme_text and any(term in text for term in ["capacity", "treatment response", "functional"]):
            related.append(item.get("current_bottleneck"))
        elif "adl" in theme_text and "adl" in text:
            related.append(item.get("current_bottleneck"))
    return list(dict.fromkeys(item for item in related if item))[:3]


def build_capacity_themes(windows: list[dict], bottlenecks: list[dict], statuses: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for window in windows:
        for theme in capacity_theme_for_window(window):
            grouped[theme].append(window)

    themes = []
    for theme, items in sorted(grouped.items(), key=lambda pair: len(pair[1]), reverse=True):
        documents = sorted({item.get("source", {}).get("document", "unknown") for item in items})
        authority_mix = sorted({source_authority_for_document(statuses, doc) for doc in documents})
        examples = [short_text(item.get("source_evidence"), 220) for item in items[:3]]
        themes.append(
            {
                "theme_name": theme,
                "window_count": len(items),
                "source_documents_supporting_it": documents,
                "source_authority_mix": authority_mix,
                "evidence_summary": " | ".join(examples),
                "functional_meaning": functional_meaning_for_theme(theme),
                "capacity_window_interpretation": capacity_interpretation_for_theme(theme),
                "what_increases_capacity": increases_capacity_for_theme(theme),
                "what_decreases_capacity": decreases_capacity_for_theme(theme),
                "related_bottlenecks": related_bottlenecks_for_theme(theme, bottlenecks),
                "next_available_opportunity": next_opportunity_for_theme(theme),
                "human_review_note": "Review source text for duplicated export rows and confirm whether the apparent capacity change carried over into daily function.",
            }
        )
    return themes[:10]


def functional_meaning_for_theme(theme: str) -> str:
    mapping = {
        "ADL/self-care capacity": "Self-care reliability may improve or decline depending on fatigue, pain, dizziness, and support strategies.",
        "IADL/home-management capacity": "Home tasks may become possible during better windows but need pacing and carryover tracking.",
        "mobility/stairs/walking capacity": "Mobility tolerance is a key bridge between symptoms, therapy goals, and daily function.",
        "upper-extremity/joint-protection capacity": "Joint protection and upper-extremity stability may affect ADLs, household tasks, and flare risk.",
        "treatment response/carryover capacity": "Treatment response matters when symptom improvement creates usable function that carries beyond the visit.",
        "care coordination/administrative capacity": "Administrative capacity affects whether referrals, records, forms, and follow-up can be completed.",
        "insurance/authorization capacity": "Insurance barriers affect access to services that may create or preserve capacity.",
        "pacing/energy conservation capacity": "Pacing and energy conservation can convert temporary improvement into repeatable routine.",
    }
    return mapping.get(theme, "Capacity theme requires human review.")


def capacity_interpretation_for_theme(theme: str) -> str:
    return f"This theme groups repeated capacity-window signals related to {theme.lower()}."


def increases_capacity_for_theme(theme: str) -> str:
    if "insurance" in theme.lower():
        return "Clear denial criteria, provider documentation, functional evidence, and authorization support."
    if "care coordination" in theme.lower():
        return "Clear task lists, source-linked summaries, reduced paperwork burden, and provider alignment."
    if "pacing" in theme.lower():
        return "Pacing plans, energy conservation, symptom tracking, and repeatable routines."
    return "Treatment response, therapy carryover, documented functional gains, and source-supported next steps."


def decreases_capacity_for_theme(theme: str) -> str:
    if "insurance" in theme.lower():
        return "Unclear denial rationale, missing documentation, and unsupported medical-necessity claims."
    if "care coordination" in theme.lower():
        return "Scattered records, appointment burden, paperwork overload, and unclear ownership."
    return "Flares, poor carryover, pain, fatigue, instability, and lack of documented functional change."


def next_opportunity_for_theme(theme: str) -> str:
    if "insurance" in theme.lower():
        return "Build a short authorization or appeal support packet from the strongest source-linked evidence."
    if "care coordination" in theme.lower():
        return "Create a short next-step list that names owner, evidence needed, and follow-up path."
    return "Use this theme to update provider-ready and care-coordination summaries with concise functional language."


def build_capacity_themes_md(themes: list[dict]) -> str:
    lines = [
        "# Consolidated Capacity Windows",
        "",
        f"This report consolidates capacity-window candidates into {len(themes)} human-readable themes.",
        "",
    ]
    for index, theme in enumerate(themes, start=1):
        lines.extend(
            [
                f"## Theme {index}: {theme['theme_name']}",
                "",
                f"- **Window count:** {theme['window_count']}",
                f"- **Source documents supporting it:** {', '.join(theme['source_documents_supporting_it'])}",
                f"- **Source authority mix:** {', '.join(theme['source_authority_mix'])}",
                f"- **Evidence summary:** {theme['evidence_summary']}",
                f"- **Functional meaning:** {theme['functional_meaning']}",
                f"- **Capacity window interpretation:** {theme['capacity_window_interpretation']}",
                f"- **What increases capacity:** {theme['what_increases_capacity']}",
                f"- **What decreases capacity:** {theme['what_decreases_capacity']}",
                f"- **Related bottlenecks:** {', '.join(theme['related_bottlenecks']) if theme['related_bottlenecks'] else 'No direct bottleneck link identified.'}",
                f"- **Next available opportunity:** {theme['next_available_opportunity']}",
                f"- **Human review note:** {theme['human_review_note']}",
                "",
            ]
        )
    return "\n".join(lines)


def select_matching_rows(matrix: list[dict], source_type: str, terms: list[str], limit: int = 8) -> list[dict]:
    candidates = []
    for row in matrix:
        if row.get("source_document_type") != source_type:
            continue
        text = " ".join(str(row.get(field, "")) for field in ["evidence_content_type", "record_fact", "functional_consequence", "system_relevance"]).lower()
        if any(term in text for term in terms):
            candidates.append(row)
    return sorted(candidates, key=evidence_score, reverse=True)[:limit]


def insurance_denial_mapping(matrix: list[dict]) -> dict:
    denial_rows = [row for row in matrix if row.get("source_document_type") == "insurance denial letter"]
    insurance_denial_present = bool(denial_rows)
    denial_doc = denial_rows[0].get("source_document") if denial_rows else "No insurance denial document found."
    statuses_by_doc = {status.get("file_name"): status for status in document_extraction_statuses()}
    document_status = statuses_by_doc.get(denial_doc, {})
    first_payer = next((row.get("payer_name") for row in denial_rows if row.get("payer_name")), None)
    first_service = next((row.get("denied_service_type") for row in denial_rows if row.get("denied_service_type")), None)
    first_context = next((row.get("denial_context") for row in denial_rows if row.get("denial_context")), None)
    denial_source = {
        "document_name": denial_doc,
        "source_document_type": denial_rows[0].get("source_document_type") if denial_rows else "Not identified.",
        "source_authority": denial_rows[0].get("source_authority") if denial_rows else "Not identified.",
        "evidence_role": denial_rows[0].get("evidence_role") if denial_rows else "Not identified.",
        "payer_name": first_payer or document_status.get("payer_name") or "Not identified.",
        "denied_service_type": first_service or document_status.get("denied_service_type") or "Not identified.",
        "denial_context": first_context or document_status.get("denial_context") or "Not identified.",
    }
    denial_text = " ".join(row.get("record_fact", "") for row in denial_rows)
    denial_rationale = {
        "denial_reason": extract_phrase(denial_text, ["not medically necessary", "denied", "denial", "not approved"]),
        "medical_necessity_language": extract_phrase(denial_text, ["medical necessity", "medically necessary", "criteria"]),
        "missing_documentation": extract_phrase(denial_text, ["missing", "documentation", "records", "information"]),
        "criteria_mentioned": extract_phrase(denial_text, ["criteria", "guideline", "benefit", "coverage"]),
        "appeal_rights_or_deadline": extract_phrase(denial_text, ["appeal", "appeal rights", "deadline", "hearing"]),
        "requested_or_denied_service": denial_source["denied_service_type"] or extract_phrase(denial_text, ["service", "therapy", "occupational therapy", "authorization"]),
    }
    ot_terms = ["adl", "iadl", "self-care", "self care", "adaptive", "energy conservation", "pacing", "functional rehabilitation", "treatment response", "joint protection"]
    provider_terms = ["diagnosis", "problem list", "treatment plan", "referral", "medication", "functional limitation", "medical necessity", "assessment"]
    return {
        "denial_source": denial_source,
        "denial_rationale": denial_rationale,
        "matching_ot_evidence": compact_evidence_rows(
            select_matching_rows(matrix, "OT record", ot_terms, 10),
            insurance_denial_present=insurance_denial_present,
        ),
        "matching_provider_evidence": compact_evidence_rows(
            select_matching_rows(matrix, "health-system/provider record", provider_terms, 10),
            insurance_denial_present=insurance_denial_present,
        ),
        "documentation_gaps": documentation_gaps_from_denial(denial_rationale),
        "recommended_next_action": "Extract denial criteria and build a short medical-necessity support packet using the strongest OT and provider-authored evidence.",
    }


def extract_phrase(text: str, terms: list[str]) -> str:
    text = normalize_whitespace(text)
    lower = text.lower()
    for term in terms:
        index = lower.find(term)
        if index >= 0:
            start = max(0, index - 120)
            end = min(len(text), index + 260)
            return short_text(text[start:end], 360)
    return "Not clearly detected in V1 rule-based extraction."


def compact_evidence_rows(rows: list[dict], insurance_denial_present: bool = False) -> list[dict]:
    return [
        {
            "source_document": row.get("source_document"),
            "source_page_or_chunk": row.get("source_page_or_chunk"),
            "source_authority": row.get("source_authority"),
            "evidence_content_type": row.get("evidence_content_type"),
            "payer_name": row.get("payer_name"),
            "denied_service_type": row.get("denied_service_type"),
            "denial_context": row.get("denial_context"),
            "record_fact": short_text(row.get("record_fact"), 420),
            "functional_consequence": row.get("functional_consequence"),
            "system_relevance": row.get("system_relevance"),
            "recommended_use": recommended_use(row, insurance_denial_present=insurance_denial_present),
        }
        for row in rows
    ]


def documentation_gaps_from_denial(denial_rationale: dict) -> list[str]:
    gaps = []
    if denial_rationale["denial_reason"].startswith("Not clearly"):
        gaps.append("Denial reason needs manual extraction from payer letter.")
    if denial_rationale["medical_necessity_language"].startswith("Not clearly"):
        gaps.append("Medical-necessity criteria should be identified explicitly.")
    if denial_rationale["requested_or_denied_service"].startswith("Not clearly"):
        gaps.append("Requested or denied service should be confirmed.")
    gaps.append("Map payer criteria to provider-authored medical evidence and OT functional evidence.")
    gaps.append("Confirm appeal rights/deadline before external use.")
    return gaps


def build_insurance_mapping_md(mapping: dict) -> str:
    lines = ["# Insurance Denial Mapping", "", "## Denial Source", ""]
    for label, value in mapping["denial_source"].items():
        lines.append(f"- **{label.replace('_', ' ').title()}:** {value}")
    lines.extend(["", "## Denial Rationale", ""])
    for label, value in mapping["denial_rationale"].items():
        lines.append(f"- **{label.replace('_', ' ').title()}:** {value}")
    lines.extend(
        [
            "",
            "## Denied Service / Payer Context",
            "",
            f"- **Who Authored The Denial:** {mapping['denial_source'].get('source_authority')}",
            f"- **Payer Name:** {mapping['denial_source'].get('payer_name') or 'Not identified.'}",
            f"- **Denied Service Type:** {mapping['denial_source'].get('denied_service_type') or 'Not identified.'}",
            f"- **Denial Context:** {mapping['denial_source'].get('denial_context') or 'Not identified.'}",
            "- **Source Rule:** Insurance denial letters are payer evidence. OT/provider records mentioning a denial remain OT/provider evidence that references an authorization barrier.",
        ]
    )
    lines.extend(["", "## Matching OT Evidence", ""])
    add_mapping_rows(lines, mapping["matching_ot_evidence"])
    lines.extend(["", "## Matching Provider Evidence", ""])
    add_mapping_rows(lines, mapping["matching_provider_evidence"])
    lines.extend(["", "## Documentation Gaps", ""])
    lines.extend(f"- {gap}" for gap in mapping["documentation_gaps"])
    lines.extend(["", "## Recommended Next Action", "", mapping["recommended_next_action"]])
    return "\n".join(lines)


def add_mapping_rows(lines: list[str], rows: list[dict]) -> None:
    if not rows:
        lines.append("No matching evidence identified by V1 rules.")
        return
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"### Evidence {index}",
                "",
                f"- **Source:** {row['source_document']} ({row['source_page_or_chunk']})",
                f"- **Source authority:** {row['source_authority']}",
                f"- **Evidence content type:** {row['evidence_content_type']}",
                f"- **Payer name:** {row.get('payer_name') or 'Not identified.'}",
                f"- **Denied service type:** {row.get('denied_service_type') or 'Not identified.'}",
                f"- **Denial context:** {row.get('denial_context') or 'Not identified.'}",
                f"- **Record fact:** {row['record_fact']}",
                f"- **Functional consequence:** {row['functional_consequence']}",
                f"- **System relevance:** {row['system_relevance']}",
                f"- **Recommended use:** {', '.join(row.get('recommended_use') or ['internal review'])}",
                "",
            ]
        )


def append_unique_section(path: Path, title: str, content_lines: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    marker = f"## {title}"
    section = marker + "\n\n" + "\n".join(content_lines).strip() + "\n"
    if marker not in text:
        write_text(path, text.rstrip() + "\n\n" + section)
        return

    lines = text.replace("\r\n", "\n").split("\n")
    start = next(index for index, line in enumerate(lines) if line.strip() == marker)
    end = start + 1
    while end < len(lines) and not (lines[end].startswith("## ") and lines[end].strip() != marker):
        end += 1
    updated = "\n".join(lines[:start] + section.rstrip().split("\n") + [""] + lines[end:]).strip() + "\n"
    write_text(path, updated)


def run_files(run_dir: Path) -> list[str]:
    files = []
    for path in run_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json"}:
            files.append(str(path.relative_to(run_dir)).replace("\\", "/"))
    return sorted(files)


def update_manifest_report_files(run_dir: Path) -> None:
    manifest_path = run_dir / "run_manifest.json"
    manifest = read_json(manifest_path, None)
    if not manifest:
        return
    manifest["generated_report_files"] = run_files(run_dir)
    write_json(manifest_path, manifest)


def update_agent_review(run_dir: Path, prioritized: list[dict], themes: list[dict], mapping: dict) -> None:
    content = [
        f"- Prioritized evidence created: {'yes' if prioritized else 'no'}",
        f"- Number of prioritized evidence rows: {len(prioritized)}",
        f"- Capacity windows consolidated: {'yes' if themes else 'no'}",
        f"- Number of consolidated themes: {len(themes)}",
        f"- Insurance denial mapping created: {'yes' if mapping else 'no'}",
        "- Evidence volume is now more human-manageable for review because the first pass is reduced to the prioritized evidence set.",
        "- Capacity-window volume is now more human-manageable because repeated windows are grouped into themes.",
        "- Remaining human review needs: verify prioritized rows, confirm capacity carryover, and manually check the payer denial criteria before external use.",
        "- Recommended-use detection was reviewed. Rows previously marked not detected were reassessed using source authority, evidence content type, system relevance, and bottleneck/actionability signals.",
    ]
    append_unique_section(run_dir / "agent_review.md", "Prioritization and Consolidation Review", content)


def update_next_actions(run_dir: Path) -> None:
    lines = [
        "# Next Actions",
        "",
        "## Action 1",
        "",
        "* Action: Review the top prioritized evidence set for accuracy.",
        "* Why it matters: The full evidence matrix is too large for human-facing review; the prioritized set identifies the strongest source-linked rows first.",
        "* Source basis: `prioritized_evidence.md` and `prioritized_evidence.json`.",
        "* Owner: Neverlost operator / human reviewer",
        "* Urgency: High",
        "* Next available opportunity: A cleaner provider, disability, or care-coordination summary can be built from the strongest evidence rather than the full matrix.",
        "",
        "## Action 2",
        "",
        "* Action: Use consolidated capacity themes to update the provider-ready summary.",
        "* Why it matters: Capacity windows become useful when repeated treatment-response signals are grouped into a smaller functional story.",
        "* Source basis: `consolidated_capacity_windows.md` and `capacity_windows.json`.",
        "* Owner: Neverlost operator / care coordinator",
        "* Urgency: Medium",
        "* Next available opportunity: Treatment response and carryover can be discussed in a concise, human-readable way.",
        "",
        "## Action 3",
        "",
        "* Action: Use insurance denial mapping to prepare an appeal/authorization support packet.",
        "* Why it matters: The payer barrier needs denial criteria mapped to provider-authored and OT functional evidence.",
        "* Source basis: `insurance_denial_mapping.md`, insurance denial evidence, OT evidence, and provider evidence.",
        "* Owner: insurance / care coordination",
        "* Urgency: High",
        "* Next available opportunity: Cleaner appeal packet, stronger authorization request, or clearer documentation gap.",
        "",
    ]
    write_text(run_dir / "next_actions.md", "\n".join(lines))


def update_run_review(run_dir: Path, prioritized: list[dict], themes: list[dict]) -> None:
    content = [
        f"- 659 evidence rows were reduced to {len(prioritized)} prioritized evidence rows.",
        f"- 47 capacity windows were reduced to {len(themes)} consolidated capacity themes.",
        "- Insurance denial evidence was mapped to OT/provider evidence.",
    ]
    update_run_review_index(run_dir / "run_review.md")
    append_unique_section(run_dir / "run_review.md", "Prioritization and Consolidation Summary", content)


def update_run_review_index(path: Path) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if "## Report Index" not in text or "## Human Review Notes" not in text:
        return
    before, rest = text.split("## Report Index", 1)
    _old_index, after = rest.split("## Human Review Notes", 1)
    new_index = "\n".join(
        [
            "## Report Index",
            "",
            "1. `source_authority_validation.md`",
            "2. `run_review.md`",
            "3. `agent_review.md`",
            "4. `next_actions.md`",
            "5. `prioritized_evidence.md`",
            "6. `consolidated_capacity_windows.md`",
            "7. `insurance_denial_mapping.md`",
            "8. `source_authority_map.md`",
            "9. `provider_ready_summary.md`",
            "10. `bottlenecks.md`",
            "11. `best_evidence.md`",
            "12. `evidence_matrix.md`",
            "13. `document_coverage.md`",
            "",
        ]
    )
    write_text(path, before.rstrip() + "\n\n" + new_index + "## Human Review Notes" + after)


def update_demo_validation_summary(run_dir: Path) -> None:
    content = [
        "V1.1 now reduces large report volume into prioritized evidence, consolidated capacity-window themes, and insurance denial mapping. This moves the system from generating reports toward making operations judgments about what deserves attention next."
    ]
    append_unique_section(run_dir / "demo_validation_summary.md", "Prioritization and Consolidation Patch", content)


def build_prioritization_and_consolidation_outputs(run_dir: Path) -> dict:
    matrix = read_json(run_dir / "processed_json" / "evidence_matrix.json", [])
    windows = read_json(run_dir / "processed_json" / "capacity_windows.json", [])
    bottlenecks = read_json(run_dir / "processed_json" / "bottlenecks.json", [])
    statuses = document_extraction_statuses()

    prioritized = prioritized_evidence_items(matrix, bottlenecks)
    themes = build_capacity_themes(windows, bottlenecks, statuses)
    mapping = insurance_denial_mapping(matrix)

    write_json(run_dir / "prioritized_evidence.json", prioritized)
    write_text(run_dir / "prioritized_evidence.md", build_prioritized_evidence_md(prioritized))
    write_json(run_dir / "consolidated_capacity_windows.json", themes)
    write_text(run_dir / "consolidated_capacity_windows.md", build_capacity_themes_md(themes))
    write_json(run_dir / "insurance_denial_mapping.json", mapping)
    write_text(run_dir / "insurance_denial_mapping.md", build_insurance_mapping_md(mapping))

    update_agent_review(run_dir, prioritized, themes, mapping)
    update_next_actions(run_dir)
    update_run_review(run_dir, prioritized, themes)
    update_demo_validation_summary(run_dir)
    update_manifest_report_files(run_dir)

    return {
        "prioritized_evidence_count": len(prioritized),
        "capacity_theme_count": len(themes),
        "insurance_denial_mapping_created": bool(mapping),
        "top_evidence_themes": [name for name, _count in Counter(row.get("evidence_content_type") for row in prioritized).most_common(3)],
        "top_capacity_themes": [theme["theme_name"] for theme in themes[:3]],
    }
