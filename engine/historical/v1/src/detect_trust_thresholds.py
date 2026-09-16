from config import PROCESSED_DIR, ensure_directories
from case_profile import profile_terms
from utils import read_json, write_json


TRUST_TERMS = [
    "provider completed",
    "completed form",
    "support letter",
    "referral placed",
    "diagnosis documented",
    "provider agreed",
    "care plan",
    "rfc",
    "documented",
    "referred",
]


def detect_provider(text: str) -> str:
    lower = text.lower()
    if "pcp" in lower or "primary care" in lower:
        return "Primary care provider"
    if "pt" in lower or "physical therapy" in lower:
        return "Physical therapist"
    if "ot" in lower or "occupational therapy" in lower:
        return "Occupational therapist"
    if "neurology" in lower or "neurologist" in lower:
        return "Neurology"
    if "pm&r" in lower or "physical medicine" in lower:
        return "PM&R"
    return "Provider not clearly identified"


def detect_trust_thresholds(profile: dict | None = None) -> list[dict]:
    ensure_directories()
    events = read_json(PROCESSED_DIR / "events.json", [])
    thresholds = []
    for event in events:
        text = " ".join([event.get("event_summary", ""), event.get("source_evidence", "")])
        lower = text.lower()
        trust_terms = TRUST_TERMS + profile_terms(profile or {}, "trust_threshold_keywords")
        if not any(term.lower() in lower for term in trust_terms):
            continue
        thresholds.append(
            {
                "provider_involved": detect_provider(text),
                "source_event": event.get("event_id"),
                "evidence_that_increased_trust": event.get("source_evidence", ""),
                "action_that_became_possible": "Possible documentation, referral, treatment planning, care coordination, or disability support pathway opened. Human review required.",
                "documentation_created": "Possible documentation event detected." if "document" in lower or "form" in lower or "rfc" in lower else "",
                "downstream_pathway_opened": "Possible downstream care pathway opened after provider alignment or documentation.",
                "source_evidence": event.get("source_evidence", ""),
                "source": event.get("source", {}),
                "confidence_level": "medium" if event.get("confidence_level") == "high" else "low",
            }
        )
    write_json(PROCESSED_DIR / "trust_thresholds.json", thresholds)
    return thresholds


def main() -> None:
    thresholds = detect_trust_thresholds()
    print(f"Detected {len(thresholds)} trust threshold candidates.")
    print(f"Wrote {PROCESSED_DIR / 'trust_thresholds.json'}")


if __name__ == "__main__":
    main()
