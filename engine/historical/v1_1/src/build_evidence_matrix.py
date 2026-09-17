import re

from case_profile import profile_terms
from config import PROCESSED_DIR, ensure_directories
from utils import is_admin_noise, normalize_whitespace, read_json, write_json


DOMAIN_RULES = {
    "ADL": ["bathing", "grooming", "dressing", "toilet", "hygiene", "adls", "wash my body", "shower"],
    "IADL": [
        "groceries",
        "grocery",
        "meal",
        "cleaning",
        "laundry",
        "paperwork",
        "scheduling",
        "phone calls",
        "iadls",
        "dog walks",
        "dog walk",
        "take my dog",
        "care for pets",
        "care for both of my dogs",
        "pet care",
    ],
    "mobility": ["walking", "walk", "stairs", "standing", "gait", "balance", "dorsiflexion", "lift", "squat", "bend", "sit", "kneel", "reach"],
    "endurance": ["fatigue", "tolerance", "endurance", "recovery", "post-exertional", "crash", "breaks", "stop activity"],
    "cognition": ["brain fog", "cognitive", "memory", "attention", "concentration", "overload"],
    "autonomic symptoms": ["pots", "dysautonomia", "dizziness", "tachycardia", "syncope", "orthostatic"],
    "pain": ["pain", "ache", "guarding", "flare", "flare-up", "flare ups"],
    "joint stability": ["hypermobility", "heds", "instability", "subluxation", "joint", "stability"],
    "PT/rehabilitation": [
        "physical therapy",
        "manual therapy",
        "therapeutic exercise",
        "home exercise",
        "rehab",
        "nerve glide",
        "97110",
        "97112",
        "97530",
        "97140",
    ],
    "treatment response": ["injection", "medication", "gabapentin", "helped", "improved", "improvement", "reduced pain", "responded well", "response"],
    "care coordination": ["records", "appointment", "appointments", "scheduling", "summary", "care coordination", "provider", "follow-up", "follow up"],
    "disability process": ["disability", "appeal", "function report", "rfc", "unable to work", "work"],
    "insurance/authorization": ["insurance", "authorization", "denial", "denied", "coverage", "appeal"],
    "provider support": ["support letter", "provider noted", "provider observed", "referral placed", "diagnosis documented"],
    "administrative metadata": ["dob", "npi", "fax", "phone", "cpt", "license", "address", "sex:"],
}

DISABILITY_DOMAINS = {"ADL", "IADL", "mobility", "endurance", "cognition", "pain", "joint stability", "disability process", "provider support"}
TREATMENT_DOMAINS = {"autonomic symptoms", "pain", "joint stability", "PT/rehabilitation", "treatment response", "mobility", "endurance"}
REFERRAL_DOMAINS = {"autonomic symptoms", "joint stability", "PT/rehabilitation", "treatment response", "care coordination", "provider support"}

ADMIN_TERMS = [
    "dob",
    "npi",
    "fax",
    "phone",
    "address",
    "license",
    "cpt code",
    "services provided during visit",
    "total timed code treatment minutes",
    "total treatment time",
    "scheduled provider",
    "clinic",
    "electronically signed",
    "signature",
]

BILLING_TERMS = ["cpt code", "units minutes", "total timed code treatment minutes", "total treatment time", "services provided during visit"]
PT_ACTIVITY_TERMS = ["bike", "marching", "body blade", "bird dog", "walkouts", "total gym", "heel raise", "nerve glide", "exercise ball"]
PT_ASSESSMENT_TERMS = ["patient assessment", "assessment", "diagnosis", "demonstrates", "presents", "impact the patient", "continues to struggle"]
PT_RESPONSE_TERMS = ["responded well", "improvement", "improved", "decreased pain", "reduced pain", "progressing well", "tolerated"]
STRONG_PT_RESPONSE_TERMS = ["responded well", "improvement in their function", "reporting improvements", "decreased pain", "reduced pain", "progressing well"]
PT_GOAL_TERMS = ["goals", "goal duration", "short term", "long term", "will tolerate", "will demonstrate", "patient will"]
PT_PLAN_TERMS = ["plan", "monitor patient response", "adjust treatment plan", "home exercise program", "coordinate care", "reassess", "provide 4-5 targeted exercises", "progression as tolerated"]
FUNCTIONAL_LIMIT_TERMS = [
    "unable",
    "difficult",
    "difficulty",
    "limitation",
    "limitations",
    "flare",
    "flare-ups",
    "flare ups",
    "weakness",
    "instability",
    "dizziness",
    "fatigue",
    "pain",
    "tolerance",
    "breaks",
    "stop",
]

PAYER_NAME_RULES = []  # V2 publication adaptation: no entity-specific aliases.

PAYER_SOURCE_TERMS = [
    "insurance denial",
    "denial letter",
    "notice of denial",
    "utilization review",
    "coverage determination",
    "adverse benefit determination",
    "appeal rights",
    "not medically necessary",
    "not approved",
    "we denied",
    "we are denying",
    "health plan",
    "payer",
]

PROVIDER_NOTE_SOURCE_TERMS = [
    "patient assessment",
    "subjective analysis",
    "objective findings",
    "services provided during visit",
    "total treatment time",
    "home exercise program",
    "occupational therapy",
    "physical therapy",
    "treatment plan",
]


def contains_any(text: str, terms: list[str] | set[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def payer_name(source_document: str | None, source_text: str | None = None) -> str | None:
    text = f"{source_document or ''} {source_text or ''}".lower()
    for name, terms in PAYER_NAME_RULES:
        if any(term in text for term in terms):
            return name
    return None


def denied_service_type(source_text: str | None, source_document: str | None = None) -> str | None:
    text = f"{source_document or ''} {source_text or ''}".lower()
    if not contains_any(
        text,
        [
            "insurance",
            "authorization",
            "preauthorization",
            "prior authorization",
            "denial",
            "denied",
            "not approved",
            "not medically necessary",
            "coverage",
            "appeal",
            "utilization review",
        ],
    ):
        return None
    if contains_any(text, ["occupational therapy", " ot ", "ot visits", "ot visit", "97535"]):
        return "OT visits / occupational therapy"
    if contains_any(text, ["physical therapy", " pt ", "pt visits", "pt visit", "97110", "97112", "97530", "97140"]):
        return "PT visits / physical therapy"
    if contains_any(text, ["medication", "prescription", "drug", "pharmacy"]):
        return "medication / pharmacy benefit"
    if contains_any(text, ["injection", "procedure", "surgery"]):
        return "procedure / intervention"
    if contains_any(text, ["mri", "ct scan", "x-ray", "xray", "imaging"]):
        return "imaging / diagnostic test"
    if contains_any(text, ["genetic testing", "genome", "lab", "blood test", "testing"]):
        return "testing / lab service"
    return None


def is_payer_denial_source(source_document: str | None, source_text: str | None = None) -> bool:
    name = (source_document or "").lower()
    content = (source_text or "").lower()
    text = f"{name} {content}"
    if "insurance denial" in name:
        return True
    if contains_any(name, ["denial", "denied", "appeal", "authorization", "coverage"]) and payer_name(name, content):
        return True
    has_payer_marker = bool(payer_name(name, content)) or contains_any(text, ["health plan", "payer", "insurance"])
    has_decision_marker = contains_any(text, PAYER_SOURCE_TERMS)
    provider_context = contains_any(name, ["occupational therapy", "physical therapy", "health record", "mychart"]) or contains_any(content[:1800], PROVIDER_NOTE_SOURCE_TERMS)
    return has_payer_marker and has_decision_marker and not provider_context


def denial_context(
    source_type: str,
    source_text: str | None,
    source_document: str | None = None,
    content_type: str | None = None,
) -> str | None:
    service = denied_service_type(source_text, source_document)
    payer = payer_name(source_document, source_text)
    if source_type == "insurance denial letter":
        parts = []
        if payer:
            parts.append(f"Payer: {payer}")
        if service:
            parts.append(f"Denied service: {service}")
        if content_type:
            parts.append(f"Denial content: {content_type}")
        return "; ".join(parts) if parts else "Payer-authored denial or authorization context requires human review."
    if source_type == "OT record" and contains_any(source_text or "", ["insurance", "authorization", "denial", "denied", "coverage", "appeal"]):
        service_text = f" involving {service}" if service else ""
        return f"OT/provider record references an insurance or authorization barrier{service_text}; source authority remains OT/provider evidence."
    if source_type == "PT record" and contains_any(source_text or "", ["insurance", "authorization", "denial", "denied", "coverage", "appeal"]):
        service_text = f" involving {service}" if service else ""
        return f"PT/provider record references an insurance or authorization barrier{service_text}; source authority remains PT/provider evidence."
    if source_type == "health-system/provider record" and contains_any(source_text or "", ["insurance", "authorization", "denial", "denied", "coverage", "appeal"]):
        service_text = f" involving {service}" if service else ""
        return f"Health-system/provider record references an insurance or authorization barrier{service_text}; source authority remains provider-authored medical evidence."
    return None


def source_document_type(source_document: str | None, source_text: str | None = None) -> str:
    name = (source_document or "").lower()
    content = (source_text or "").lower()
    text = f"{name} {content}"
    if is_payer_denial_source(source_document, source_text):
        return "insurance denial letter"
    if "appeal" in name:
        return "disability appeal"
    if "function report" in name:
        return "function report"
    if "physical therapy" in name or re.search(r"\bpt\b", name):
        return "PT record"
    if contains_any(name, ["occupational therapy", "occupational therapist"]) or re.search(r"\botl?\b", name):
        return "OT record"
    if contains_any(name, ["health record", "mychart"]):
        return "health-system/provider record"
    if contains_any(text, ["not medically necessary", "utilization review", "appeal rights", "medical necessity criteria"]):
        return "insurance denial letter"
    if contains_any(text, ["health record", "mychart"]):
        return "health-system/provider record"
    if contains_any(text, ["occupational therapy", "occupational therapist"]) or re.search(r"\botl?\b", text):
        return "OT record"
    return "unknown"


def source_authority(source_type: str) -> str:
    return {
        "disability appeal": "claimant appeal / disability process document",
        "function report": "claimant functional report",
        "PT record": "provider/physical therapy record",
        "OT record": "provider/occupational therapy functional record",
        "health-system/provider record": "provider-authored medical record",
        "insurance denial letter": "payer / insurance utilization review document",
    }.get(source_type, "unknown source authority")


def extraction_evidence_role(source_type: str, evidence_content_type: str) -> str:
    if source_type == "disability appeal":
        return "claimant-submitted disability evidence"
    if source_type == "function report":
        return "claimant functional evidence"
    if source_type == "PT record":
        return "provider-authored rehabilitation evidence"
    if source_type == "OT record":
        return "provider-authored functional rehabilitation evidence"
    if source_type == "health-system/provider record":
        return "provider-authored medical evidence"
    if source_type == "insurance denial letter":
        return "insurance decision / authorization barrier evidence"
    return f"source evidence requiring review: {evidence_content_type}"


def detect_domains(text: str, profile: dict | None = None) -> list[str]:
    lower = text.lower()
    domains = [
        domain
        for domain, terms in DOMAIN_RULES.items()
        if any(term in lower for term in terms)
    ]
    if profile:
        if any(term in lower for term in profile_terms(profile, "priority_functional_limits")):
            domains.append("disability process")
        if any(term in lower for term in profile_terms(profile, "capacity_window_keywords")):
            domains.append("treatment response")
        if any(term in lower for term in profile_terms(profile, "trust_threshold_keywords")):
            domains.append("provider support")
    return sorted(set(domains), key=domains.index)


def normalize_domains_for_source(domains: list[str], source_type: str) -> list[str]:
    if source_type == "disability appeal":
        # Appeal documents can reference PT/treatment history, but they are not provider-authored PT records.
        return [domain for domain in domains if domain not in {"PT/rehabilitation", "treatment response", "provider support"}]
    if source_type == "function report":
        return [domain for domain in domains if domain not in {"PT/rehabilitation", "provider support"}]
    if source_type == "insurance denial letter":
        return [domain for domain in domains if domain not in {"PT/rehabilitation", "provider support", "treatment response"}]
    return domains


def classify_pt_evidence(text: str, source_document: str | None = None, source_type: str | None = None) -> str | None:
    if source_type != "PT record":
        return None
    lower = text.lower()
    if "PT/rehabilitation" not in detect_domains(text):
        return None
    if contains_any(lower, PT_GOAL_TERMS) and not contains_any(lower, STRONG_PT_RESPONSE_TERMS):
        return "PT goal"
    if contains_any(lower, STRONG_PT_RESPONSE_TERMS):
        return "PT treatment response"
    if contains_any(lower, PT_ASSESSMENT_TERMS) and contains_any(lower, FUNCTIONAL_LIMIT_TERMS):
        return "PT assessment"
    if contains_any(lower, PT_PLAN_TERMS):
        return "PT plan / care coordination"
    if contains_any(lower, BILLING_TERMS):
        return "PT billing / CPT table"
    if contains_any(lower, PT_ACTIVITY_TERMS) or re.search(r"\b(97110|97112|97530|97140|97014|97535)\b", lower):
        return "PT activity or exercise list"
    if contains_any(lower, FUNCTIONAL_LIMIT_TERMS):
        return "PT functional observation"
    if contains_any(lower, ADMIN_TERMS):
        return "PT header / metadata"
    return "PT functional observation"


def evidence_content_type(source_type: str, domains: list[str], source_text: str, pt_type: str | None = None) -> str:
    lower = source_text.lower()
    if source_type == "PT record":
        return pt_type or "PT evidence requiring review"
    if source_type == "function report":
        content = []
        if "ADL" in domains:
            content.append("ADL limitation")
        if "IADL" in domains:
            content.append("IADL limitation")
        if "mobility" in domains:
            content.append("mobility limitation")
        if "cognition" in domains:
            content.append("cognitive/administrative limitation")
        if "care coordination" in domains:
            content.append("care coordination burden")
        if "endurance" in domains or "pain" in domains or "autonomic symptoms" in domains:
            content.append("symptom variability")
        return " / ".join(dict.fromkeys(content)) or "claimant functional statement"
    if source_type == "disability appeal":
        content = []
        if "appeal" in lower or "reconsideration" in lower or "dds" in lower or "social security" in lower:
            content.append("appeal rationale")
            content.append("DDS/SSA process issue")
        if contains_any(lower, ["missing", "incomplete", "records", "documentation"]):
            content.append("missing-record issue")
        if contains_any(lower, ["physical therapy", "pt", "provider", "medical documentation", "treatment"]):
            content.append("treatment history reference")
        if contains_any(lower, ["functional limitation", "reduced activity tolerance", "upright posture", "symptom exacerbation", "medical condition"]):
            content.append("functional limitation statement")
        if "care coordination" in domains or contains_any(lower, ["contact", "appointments", "records"]):
            content.append("care coordination issue")
        if "disability process" in domains or "insurance/authorization" in domains:
            content.append("disability process evidence")
        return " / ".join(dict.fromkeys(content)) or "disability appeal statement"
    if source_type == "OT record":
        content = []
        if contains_any(lower, ["assessment", "eval", "evaluation"]):
            content.append("OT assessment")
        if contains_any(lower, ["observation", "observed", "performance", "functional capacity"]):
            content.append("OT functional observation")
        if "ADL" in domains or contains_any(lower, ["self-care", "self care", "bathing", "grooming", "dressing"]):
            content.append("ADL limitation")
            content.append("self-care limitation")
        if "IADL" in domains:
            content.append("IADL limitation")
        if contains_any(lower, ["adaptive equipment", "assistive device", "brace", "splint"]):
            content.append("adaptive equipment recommendation")
        if contains_any(lower, ["energy conservation", "pacing", "post-exertional", "fatigue management"]):
            content.append("energy conservation / pacing")
        if contains_any(lower, ["joint protection", "hypermobility", "stability"]):
            content.append("joint protection")
        if contains_any(lower, ["home program", "home exercise", "hep", "care plan", "plan of care"]):
            content.append("home program / care plan")
        if contains_any(lower, ["improved", "progress", "responded", "tolerated"]):
            content.append("OT treatment response")
        if "insurance/authorization" in domains:
            content.append("authorization barrier / insurance context")
        if contains_any(lower, ADMIN_TERMS):
            content.append("OT metadata")
        return " / ".join(dict.fromkeys(content)) or "OT functional evidence"
    if source_type == "health-system/provider record":
        content = []
        if contains_any(lower, ["assessment", "assessments", "impression"]):
            content.append("provider assessment")
        if contains_any(lower, ["diagnosis", "diagnoses", "problem list", "problems"]):
            content.append("diagnosis / problem list")
        if contains_any(lower, ["plan", "treatment plan", "care plan"]):
            content.append("treatment plan")
        if contains_any(lower, ["medication", "medications", "prescribed", "gabapentin", "dose"]):
            content.append("medication evidence")
        if contains_any(lower, ["referral", "referred", "orders", "ordered"]):
            content.append("referral evidence")
        if contains_any(lower, ["observed", "exam", "objective", "findings"]):
            content.append("clinical observation")
        if any(domain in domains for domain in ["ADL", "IADL", "mobility", "endurance", "cognition"]):
            content.append("functional limitation statement")
        if "care coordination" in domains:
            content.append("care coordination note")
        if contains_any(lower, ["follow-up", "follow up", "return", "rtc"]):
            content.append("follow-up plan")
        if "insurance/authorization" in domains:
            content.append("authorization barrier / insurance context")
        if contains_any(lower, ADMIN_TERMS):
            content.append("provider metadata")
        return " / ".join(dict.fromkeys(content)) or "provider medical evidence"
    if source_type == "insurance denial letter":
        content = []
        if contains_any(lower, ["denial", "denied", "not approved", "not medically necessary"]):
            content.append("insurance denial")
        if contains_any(lower, ["authorization", "prior authorization", "preauthorization"]):
            content.append("authorization barrier")
        if contains_any(lower, ["medical necessity", "medically necessary", "criteria", "guideline"]):
            content.append("medical necessity criteria")
        if contains_any(lower, ["appeal rights", "appeal", "grievance", "hearing"]):
            content.append("appeal rights")
        if contains_any(lower, ["missing", "documentation", "records", "information needed"]):
            content.append("missing documentation")
        if contains_any(lower, ["coverage", "benefit", "covered"]):
            content.append("coverage limitation")
        if contains_any(lower, ["reason", "rationale", "because"]):
            content.append("payer rationale")
        if "insurance/authorization" in domains:
            content.append("insurance process evidence")
        return " / ".join(dict.fromkeys(content)) or "insurance process evidence"
    return "evidence requiring review"


def split_candidates(text: str) -> list[str]:
    text = normalize_whitespace(text)
    markers = [
        "Patient Assessment / Diagnosis",
        "Subjective Analysis",
        "Objective Findings",
        "Assessment Goals Plan",
        "GOALS",
        "Plan",
        "Services Provided During Visit",
    ]
    for marker in markers:
        text = text.replace(marker, f". {marker}. ")
    pieces = re.split(r"(?<=[.!?])\s+| - ", text)
    candidates = [normalize_whitespace(piece) for piece in pieces if len(normalize_whitespace(piece)) > 30]
    return candidates or [text]


def candidate_score(text: str, pt_type: str | None = None) -> int:
    lower = text.lower()
    score = 0
    score += 10 * sum(1 for term in FUNCTIONAL_LIMIT_TERMS if term in lower)
    score += 12 * sum(1 for term in ["bathing", "hygiene", "paperwork", "scheduling", "phone calls", "walking", "standing", "stairs", "recovery"] if term in lower)
    score += 12 * sum(1 for term in PT_ASSESSMENT_TERMS + PT_RESPONSE_TERMS if term in lower)
    score += 8 * sum(1 for term in PT_GOAL_TERMS if term in lower)
    score -= 12 * sum(1 for term in ADMIN_TERMS if term in lower)
    score -= 16 * sum(1 for term in BILLING_TERMS if term in lower)
    if pt_type == "PT billing / CPT table":
        score -= 20
    if len(text) < 60:
        score -= 10
    return score


def clean_snippet(text: str, pt_type: str | None = None, max_chars: int = 320) -> str:
    text = normalize_whitespace(text).replace("â€¢", "-").replace("â€™", "'")
    if pt_type == "PT billing / CPT table":
        return "PT billing/CPT table lists services, units, and treatment time; the billing table alone is not treated as functional evidence without paired assessment or response text."
    if pt_type == "PT header / metadata":
        return "PT header contains visit/provider metadata; header metadata alone is not treated as functional evidence."

    candidates = split_candidates(text)
    candidates = [
        candidate
        for candidate in candidates
        if not (contains_any(candidate, ADMIN_TERMS) and not contains_any(candidate, FUNCTIONAL_LIMIT_TERMS + PT_ASSESSMENT_TERMS + PT_RESPONSE_TERMS + PT_GOAL_TERMS))
    ] or candidates
    best = max(candidates, key=lambda item: candidate_score(item, pt_type))
    best = re.sub(r"\b(?:CPT|NPI)\s*#?\s*\d+\b", "", best, flags=re.IGNORECASE)
    best = re.sub(r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b", "", best)
    best = normalize_whitespace(best)
    if len(best) > max_chars:
        best = best[:max_chars].rsplit(" ", 1)[0] + "."
    return best


def evidence_type_from_domains(domains: list[str], event_type: str, pt_type: str | None = None, source_type: str = "unknown", content_type: str | None = None) -> str:
    if source_type == "disability appeal":
        return content_type or "disability appeal evidence"
    if source_type == "function report":
        return content_type or "function report evidence"
    if source_type in {"OT record", "health-system/provider record", "insurance denial letter"}:
        return content_type or f"{source_type} evidence"
    if pt_type:
        return pt_type
    if "administrative metadata" in domains and len(domains) == 1:
        return "administrative metadata"
    if "insurance/authorization" in domains:
        return "insurance / authorization evidence"
    if "disability process" in domains:
        return "disability / functional evidence"
    if "treatment response" in domains:
        return "treatment response evidence"
    if any(domain in domains for domain in ["ADL", "IADL", "mobility", "endurance", "cognition"]):
        return "functional evidence"
    if event_type == "imaging":
        return "imaging evidence"
    return "general healthcare evidence"


def record_fact(event: dict, domains: list[str], pt_type: str | None, snippet: str, source_type: str, content_type: str) -> str:
    doc = event.get("source_document", "Source document")
    if source_type == "disability appeal":
        return f"{doc} contains claimant appeal/process evidence ({content_type}): {snippet}"
    if source_type == "function report":
        if "ADL" in domains:
            return f"{doc} documents ADL limitation evidence: {snippet}"
        if "IADL" in domains:
            return f"{doc} documents IADL or administrative-capacity limitation evidence: {snippet}"
        if "mobility" in domains:
            return f"{doc} documents mobility or positional-tolerance evidence: {snippet}"
        return f"{doc} contains claimant functional evidence ({content_type}): {snippet}"
    if source_type == "OT record":
        return f"{doc} contains provider-authored OT functional evidence ({content_type}): {snippet}"
    if source_type == "health-system/provider record":
        return f"{doc} contains provider-authored medical evidence ({content_type}): {snippet}"
    if source_type == "insurance denial letter":
        return f"{doc} contains payer/insurance decision evidence ({content_type}): {snippet}"
    if pt_type == "PT billing / CPT table":
        return snippet
    if pt_type == "PT header / metadata":
        return snippet
    if pt_type:
        return f"{doc} {pt_type.lower()} documents: {snippet}"
    if "disability process" in domains:
        return f"{doc} contains disability-facing functional evidence: {snippet}"
    if "insurance/authorization" in domains:
        return f"{doc} contains insurance, authorization, denial, or appeal-related evidence: {snippet}"
    return f"{doc} contains healthcare evidence requiring review: {snippet}"


def functional_consequence(domains: list[str], source_text: str, pt_type: str | None = None) -> str:
    lower = source_text.lower()
    if pt_type == "PT treatment response":
        return "PT note documents treatment response, but carryover between sessions still needs tracking."
    if pt_type == "PT assessment":
        return "PT assessment connects symptoms or impairments to functional participation and rehab needs."
    if pt_type == "PT goal":
        return "PT goals identify current functional tolerance targets and measurable rehabilitation endpoints."
    if pt_type == "PT activity or exercise list":
        return "Exercise/activity list supports treatment tracking, but does not prove disability limitation unless paired with tolerance, flare, modification, or observed deficit."
    if pt_type == "PT billing / CPT table":
        return "Billing details document services delivered, not functional limitation by themselves."
    if "bathing" in lower or "hygiene" in lower or "wash my body" in lower:
        return "Bathing/hygiene may not be completed consistently in one attempt due to fatigue, pain, dizziness, and limited endurance."
    if contains_any(lower, ["paperwork", "scheduling", "phone calls", "cognitive overload", "brain fog"]):
        return "Cognitive fatigue and overload interfere with paperwork, scheduling, phone calls, and care-coordination tasks."
    if contains_any(lower, ["lift", "squat", "bend", "stand", "walk", "sit", "climb stairs", "kneel", "reach"]):
        return "Symptoms affect mobility, positional tolerance, stairs, reaching, bending, and sustained activity, requiring breaks or stopping activity."
    if contains_any(lower, ["foster care", "care for both of my dogs", "care for pets", "dog"]):
        return "Pet care and daily household responsibilities exceed current available functional capacity without outside support."
    if "ADL" in domains:
        return "ADL performance needs source-specific review for frequency, assistance required, and completion limits."
    if "IADL" in domains:
        return "IADL tasks require pacing, breaks, or outside support and may compete with care-coordination capacity."
    if "mobility" in domains:
        return "Mobility and positional tolerance require breaks, pacing, or limits on sustained activity."
    if "endurance" in domains:
        return "Endurance limits affect appointment tolerance, recovery time, and work-like consistency."
    return "Functional consequence requires human review before use."


def system_relevance(domains: list[str], pt_type: str | None = None) -> str:
    relevance = []
    if pt_type in {"PT assessment", "PT treatment response", "PT functional observation", "PT goal", "PT plan / care coordination"}:
        relevance.append("Supports PT treatment planning and functional tolerance tracking")
    if pt_type in {"PT assessment", "PT treatment response", "PT functional observation"}:
        relevance.append("Supports provider summary because PT findings translate symptoms into functional consequences")
    if "ADL" in domains:
        relevance.append("Supports ADL limitation evidence for disability documentation")
    if "IADL" in domains:
        relevance.append("Supports IADL and administrative-capacity limitation evidence")
    if "mobility" in domains or "endurance" in domains:
        relevance.append("Supports functional tolerance evidence for provider/disability review")
    if "care coordination" in domains:
        relevance.append("Supports care coordination because appointment and paperwork burden affect follow-through")
    if "PT/rehabilitation" in domains:
        relevance.append("Supports PT treatment planning and functional tolerance tracking")
    if "treatment response" in domains:
        relevance.append("Supports capacity-window tracking because treatment response is documented but carryover is not yet measured")
    if "provider support" in domains:
        relevance.append("Supports provider summary because it translates symptoms into functional consequences")
    if "insurance/authorization" in domains:
        relevance.append("Supports authorization/appeal review only when linked to requested-service criteria")
    if pt_type in {"PT header / metadata", "PT billing / CPT table"}:
        relevance = ["Administrative or billing data should not be treated as functional evidence unless paired with assessment, tolerance, limitation, or treatment-response text"]
    if not relevance:
        relevance.append("System relevance requires human review")
    return "; ".join(dict.fromkeys(relevance)) + "."


def source_authority_note(source_type: str, content_type: str) -> str:
    if source_type == "disability appeal":
        return (
            "This is claimant-submitted appeal/process evidence. It may reference PT, providers, or treatment history, "
            "but it should be reconciled with provider records before being treated as provider-authored medical evidence."
        )
    if source_type == "function report":
        return "This is claimant functional-report evidence and should be used for functional impact, ADL/IADL, and disability-context language."
    if source_type == "PT record":
        return "This is provider-authored physical therapy evidence and can support PT findings, goals, treatment response, and functional tolerance when source text is specific."
    if source_type == "OT record":
        return "This is provider-authored occupational therapy evidence and can support ADL/IADL, self-care, pacing, adaptive-equipment, and functional rehabilitation findings when source text is specific."
    if source_type == "health-system/provider record":
        return "This is provider-authored medical-record evidence and can support diagnoses, assessments, treatment plans, referrals, medications, clinical observations, and follow-up needs."
    if source_type == "insurance denial letter":
        return "This is payer/insurance decision evidence and should be used for authorization barriers, payer rationale, medical-necessity criteria, appeal rights, and documentation gaps."
    return f"Source authority requires review for {content_type}."


def next_available_opportunity(domains: list[str], pt_type: str | None = None) -> str:
    if pt_type == "PT billing / CPT table":
        return "Pair billing/activity data with PT assessment or treatment-response language before using it as evidence."
    if pt_type in {"PT assessment", "PT treatment response", "PT functional observation"}:
        return "Ask PT/provider to document functional tolerance, observed deficits, response, flare pattern, and carryover."
    if pt_type == "PT goal":
        return "Track whether PT goals translate into measurable daily-function changes."
    if "ADL" in domains:
        return "Include hygiene/self-care limitation in the provider/disability-ready summary."
    if "IADL" in domains:
        return "Include paperwork, scheduling, household-task, and pet-care limits in the provider/disability-ready summary."
    if "mobility" in domains or "endurance" in domains:
        return "Convert mobility/endurance limits into concise tolerance language for provider/disability review."
    if "insurance/authorization" in domains:
        return "Link functional limitation and treatment history to the authorization or appeal requirement."
    return "Hold this row for human review before including it in a provider-facing summary."


def second_layer_meaning(domains: list[str], source_text: str, pt_type: str | None = None) -> str:
    lower = source_text.lower()
    if pt_type == "PT treatment response":
        return "PT evidence may show both treatment responsiveness and limited carryover between sessions."
    if pt_type == "PT assessment":
        return "Provider-observed rehab evidence may turn patient-reported limitation into clinically usable functional evidence."
    if pt_type == "PT goal":
        return "The care plan has measurable functional targets that can become future progress or limitation evidence."
    if pt_type in {"PT billing / CPT table", "PT header / metadata"}:
        return "The record establishes service context but does not yet establish functional meaning."
    if "bathing" in lower or "hygiene" in lower:
        return "ADL limitation is explicitly documented in a disability-facing source."
    if contains_any(lower, ["paperwork", "scheduling", "phone calls", "cognitive overload", "brain fog"]):
        return "Administrative capacity is documented as part of functional impairment, not merely personal disorganization."
    if contains_any(lower, ["lift", "squat", "bend", "stand", "walk", "sit", "climb stairs", "kneel", "reach"]):
        return "Symptoms are translated into mobility and positional-tolerance limits that systems can evaluate."
    if "IADL" in domains:
        return "Daily-life support needs are becoming visible as system-relevant functional evidence."
    if "care coordination" in domains:
        return "Care navigation itself is a capacity demand that may need support and documentation."
    return "Second-layer meaning requires human review."


def evidence_strength_score(row_text: str, domains: list[str], pt_type: str | None, date: str | None, consequence: str) -> int:
    lower = row_text.lower()
    score = 0
    score += 16 * sum(1 for domain in domains if domain in {"ADL", "IADL", "mobility", "endurance", "cognition"})
    score += 14 * sum(1 for term in ["unable", "difficult", "difficulty", "not always able", "requires breaks", "stop activity"] if term in lower)
    score += 12 * sum(1 for term in ["walking", "standing", "sitting", "stairs", "bathing", "hygiene", "paperwork", "scheduling", "phone calls"] if term in lower)
    score += 12 * sum(1 for term in ["flare", "recovery", "tolerance", "fatigue", "brain fog", "cognitive overload"] if term in lower)
    score += 10 * sum(1 for term in ["responded well", "improved", "improvement", "decreased pain", "observed", "demonstrates"] if term in lower)
    if pt_type in {"PT assessment", "PT treatment response", "PT functional observation"}:
        score += 25
    if pt_type == "PT goal":
        score += 10
    if date:
        score += 6
    if "Functional consequence requires human review" in consequence:
        score -= 25
    if "healthcare evidence requiring review" in lower or "second-layer meaning requires human review" in lower:
        score -= 35
    score -= 10 * sum(1 for term in ADMIN_TERMS if term in lower)
    score -= 20 * sum(1 for term in BILLING_TERMS if term in lower)
    if pt_type in {"PT billing / CPT table", "PT header / metadata"}:
        score -= 35
    if len(row_text) < 60:
        score -= 15
    if "golf" in lower and not contains_any(lower, ["daily", "walking", "standing", "pain", "instability", "tolerance", "flare"]):
        score -= 12
    return score


def supports_disability_from(domains: list[str], pt_type: str | None, source_text: str) -> bool:
    if pt_type in {"PT header / metadata", "PT billing / CPT table"}:
        return False
    if pt_type in {"PT assessment", "PT treatment response", "PT functional observation"}:
        return True
    if pt_type == "PT activity or exercise list":
        return contains_any(source_text, FUNCTIONAL_LIMIT_TERMS)
    if pt_type == "PT goal":
        return contains_any(source_text, ["without dizziness", "without pain", "improve", "limitation", "weakness", "stability", "tolerance"])
    return bool(DISABILITY_DOMAINS.intersection(domains))


def build_evidence_matrix(profile: dict | None = None) -> list[dict]:
    ensure_directories()
    events = read_json(PROCESSED_DIR / "events.json", [])
    matrix = []
    for event in events:
        raw_text = " ".join([event.get("event_summary", ""), event.get("source_evidence", "")])
        source_type = source_document_type(event.get("source_document"), raw_text)
        domains = normalize_domains_for_source(detect_domains(raw_text, profile), source_type)
        pt_type = classify_pt_evidence(raw_text, event.get("source_document"), source_type)
        if pt_type == "PT goal" and not contains_any(raw_text, STRONG_PT_RESPONSE_TERMS):
            domains = [domain for domain in domains if domain != "treatment response"]
        if pt_type in {"PT header / metadata", "PT billing / CPT table"}:
            domains = [domain for domain in domains if domain not in {"ADL", "IADL", "mobility", "endurance", "cognition", "disability process"}]
        if is_admin_noise(raw_text) and not [d for d in domains if d != "administrative metadata"]:
            continue

        snippet = clean_snippet(raw_text, pt_type)
        if pt_type in {"PT header / metadata", "PT billing / CPT table"} and len(snippet) < 40:
            continue

        content_type = evidence_content_type(source_type, domains, snippet, pt_type)
        authority = source_authority(source_type)
        role = extraction_evidence_role(source_type, content_type)
        authority_note = source_authority_note(source_type, content_type)
        payer = payer_name(event.get("source_document"), snippet)
        service_type = denied_service_type(snippet, event.get("source_document"))
        payer_context = denial_context(source_type, snippet, event.get("source_document"), content_type)
        fact = record_fact(event, domains, pt_type, snippet, source_type, content_type)
        consequence = functional_consequence(domains, snippet, pt_type)
        relevance = system_relevance(domains, pt_type)
        opportunity = next_available_opportunity(domains, pt_type)
        second_layer = second_layer_meaning(domains, snippet, pt_type)

        supports_disability = supports_disability_from(domains, pt_type, snippet)
        supports_treatment = (
            source_type in {"PT record", "OT record", "health-system/provider record"}
            and (
                "PT/rehabilitation" in domains
                or "treatment response" in domains
                or event.get("event_type") in {"diagnosis", "symptom", "medication", "intervention", "PT/OT event"}
            )
        )
        if source_type == "disability appeal" and "treatment history reference" in content_type:
            supports_treatment = True
        if pt_type in {"PT header / metadata", "PT billing / CPT table"}:
            supports_treatment = pt_type == "PT billing / CPT table"
        supports_referral = bool(REFERRAL_DOMAINS.intersection(domains)) and (
            "care coordination" in domains or "provider support" in domains or pt_type in {"PT assessment", "PT treatment response"}
        )
        supports_insurance = "insurance/authorization" in domains or source_type == "insurance denial letter"

        missing = []
        if supports_disability and not any(domain in domains for domain in ["ADL", "IADL", "mobility", "endurance"]):
            missing.append("specific functional limitation language")
        if supports_treatment and "treatment response" not in domains and pt_type not in {"PT treatment response"}:
            missing.append("treatment response or capacity change")
        if "insurance/authorization" in domains:
            missing.append("authorization criteria or requested-service link")

        score = evidence_strength_score(f"{fact} {snippet}", domains, pt_type, event.get("date"), consequence)
        row = {
            "claim_or_functional_issue": fact,
            "record_fact": fact,
            "cleaned_source_text": snippet,
            "functional_consequence": consequence,
            "system_relevance": relevance,
            "next_available_opportunity": opportunity,
            "first_layer_fact": fact,
            "possible_second_layer_meaning": second_layer,
            "possible_second_layer_change": second_layer,
            "why_it_matters": relevance,
            "functional_domains": domains,
            "source_document_type": source_type,
            "evidence_content_type": content_type,
            "evidence_role": role,
            "source_authority": authority,
            "source_authority_note": authority_note,
            "payer_name": payer,
            "denied_service_type": service_type,
            "denial_context": payer_context,
            "pt_evidence_type": pt_type,
            "evidence_strength_score": score,
            "source_document": event.get("source_document"),
            "source_page_or_chunk": event.get("source_page_or_chunk"),
            "date": event.get("date"),
            "evidence_type": evidence_type_from_domains(domains, event.get("event_type", ""), pt_type, source_type, content_type),
            "supports_disability": supports_disability,
            "supports_treatment": supports_treatment,
            "supports_referral": supports_referral,
            "supports_insurance_authorization": supports_insurance,
            "missing_evidence": ", ".join(missing),
            "confidence_level": event.get("confidence_level", "unknown"),
        }
        matrix.append(row)

    matrix = sorted(matrix, key=lambda row: row.get("evidence_strength_score", 0), reverse=True)
    write_json(PROCESSED_DIR / "evidence_matrix.json", matrix)
    return matrix


def main() -> None:
    matrix = build_evidence_matrix()
    print(f"Built {len(matrix)} evidence matrix rows.")
    print(f"Wrote {PROCESSED_DIR / 'evidence_matrix.json'}")


if __name__ == "__main__":
    main()
