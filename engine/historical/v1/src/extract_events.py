import hashlib
import re

from config import PROCESSED_DIR, ensure_directories
from case_profile import profile_terms
from utils import find_dates, has_substantive_content, is_admin_noise, normalize_whitespace, select_event_date, write_json
from utils import read_json


EVENT_KEYWORDS = {
    "diagnosis": ["diagnosis", "diagnosed", "dx", "hEDS", "POTS", "ME/CFS", "dysautonomia"],
    "symptom": ["pain", "fatigue", "dizziness", "syncope", "nausea", "weakness", "symptom"],
    "functional limitation": ["limitation", "unable", "difficulty", "standing", "walking", "sitting", "lifting", "ADLs"],
    "test": ["lab", "test", "blood", "tilt", "emg"],
    "imaging": ["mri", "x-ray", "xray", "ct", "imaging", "ultrasound"],
    "medication": ["medication", "prescribed", "dose", "mg", "started", "stopped"],
    "intervention": ["injection", "medication", "procedure", "treatment", "physical therapy", "occupational therapy", "manual therapy", "brace", "assistive"],
    "PT/OT event": ["physical therapy", "occupational therapy", "pt", "ot", "exercise", "rehab"],
    "specialist visit": ["neurology", "pm&r", "specialist", "rheumatology", "cardiology"],
    "primary care visit": ["primary care", "pcp", "family medicine"],
    "referral": ["referral", "referred", "refer"],
    "disability documentation": ["disability", "rfc", "functional capacity", "work", "unable to work"],
    "insurance event": ["insurance", "authorization", "coverage", "denied", "approved", "claim"],
    "care coordination event": ["records", "documentation", "care coordination", "case management", "summary"],
    "patient-reported observation": ["patient reports", "reports", "states", "journal", "i feel", "i noticed"],
    "administrative barrier": ["pending", "waiting", "incomplete", "needs documentation", "barrier"],
    "housing or survival-pressure event": ["housing", "rent", "eviction", "food", "survival", "benefits"],
}


PATIENT_REPORTED_MARKERS = ["i ", "my ", "patient reports", "reports", "states", "complains", "journal"]


def contains_term(text: str, term: str) -> bool:
    term = term.lower()
    if len(term) <= 3 and term.replace("/", "").isalnum():
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None
    return term in text


def classify_event(text: str, profile: dict | None = None) -> str:
    lower = text.lower()
    scores = {
        event_type: sum(1 for keyword in keywords if contains_term(lower, keyword))
        for event_type, keywords in EVENT_KEYWORDS.items()
    }
    if profile:
        if any(contains_term(lower, term) for term in profile_terms(profile, "primary_conditions_to_track")):
            scores["diagnosis"] = scores.get("diagnosis", 0) + 2
            scores["symptom"] = scores.get("symptom", 0) + 1
        if any(contains_term(lower, term) for term in profile_terms(profile, "priority_functional_limits")):
            scores["functional limitation"] = scores.get("functional limitation", 0) + 3
        if any(contains_term(lower, term) for term in profile_terms(profile, "priority_evidence_types")):
            scores["disability documentation"] = scores.get("disability documentation", 0) + 1
    best = max(scores, key=scores.get)
    return best if scores[best] else "general"


def confidence_for_event(text: str, dates: list[str]) -> str:
    if dates and len(text) > 80 and not is_admin_noise(text):
        return "high"
    if dates:
        return "medium"
    return "low"


def summarize(text: str, max_chars: int = 420) -> str:
    text = normalize_whitespace(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def extract_events_from_chunks(profile: dict | None = None) -> list[dict]:
    ensure_directories()
    chunks = read_json(PROCESSED_DIR / "chunks.json", [])
    events = []
    for chunk in chunks:
        text = chunk.get("text", "")
        dates = find_dates(text)
        selected_date = select_event_date(text)
        profile_keywords = []
        if profile:
            for key in [
                "primary_conditions_to_track",
                "priority_functional_limits",
                "priority_evidence_types",
                "bottleneck_priorities",
                "capacity_window_keywords",
                "trust_threshold_keywords",
            ]:
                profile_keywords.extend(profile_terms(profile, key))
        has_keyword = any(
            contains_term(text.lower(), keyword)
            for keywords in EVENT_KEYWORDS.values()
            for keyword in keywords
        ) or any(contains_term(text.lower(), keyword) for keyword in profile_keywords)
        if is_admin_noise(text) and not has_substantive_content(text):
            continue
        if not selected_date and not has_keyword:
            continue

        event_id = hashlib.sha1(chunk["chunk_id"].encode("utf-8")).hexdigest()[:12]
        patient_reported = ""
        if any(marker in f" {text.lower()} " for marker in PATIENT_REPORTED_MARKERS):
            patient_reported = summarize(text, 260)

        events.append(
            {
                "event_id": event_id,
                "date": selected_date,
                "approximate_date": selected_date,
                "source_document": chunk["document"],
                "source_page_or_chunk": chunk["chunk_id"],
                "event_type": classify_event(text, profile),
                "event_summary": summarize(text),
                "summary": summarize(text),
                "source_evidence": summarize(text),
                "patient_observation": patient_reported,
                "patient_reported": patient_reported,
                "ai_inference": "Rule-based extraction identified this chunk as potentially relevant to the healthcare roadmap. Human review required.",
                "related_conditions": [term for term in (profile.get("primary_conditions_to_track", []) if profile else ["hEDS", "POTS", "ME/CFS", "dysautonomia"]) if str(term).lower() in text.lower()],
                "related_providers": [],
                "related_body_systems": [],
                "functional_relevance": "Possible functional relevance; human review required." if "function" in text.lower() or "unable" in text.lower() or "limitation" in text.lower() else "",
                "documentation_relevance": "Possible documentation relevance; human review required." if "documentation" in text.lower() or "record" in text.lower() or "rfc" in text.lower() else "",
                "source": {
                    "document": chunk["document"],
                    "page": chunk.get("page"),
                    "chunk_id": chunk["chunk_id"],
                },
                "confidence_level": confidence_for_event(text, [selected_date] if selected_date else []),
            }
        )

    write_json(PROCESSED_DIR / "events.json", events)
    return events


def main() -> None:
    events = extract_events_from_chunks()
    print(f"Extracted {len(events)} structured event candidates.")
    print(f"Wrote {PROCESSED_DIR / 'events.json'}")


if __name__ == "__main__":
    main()
