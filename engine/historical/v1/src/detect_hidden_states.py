from config import PROCESSED_DIR, ensure_directories
from case_profile import profile_terms
from utils import read_json, write_json


HIDDEN_STATE_RULES = [
    {
        "state_change": "Trust established",
        "keywords": ["rfc", "support", "letter", "documented", "provider agrees"],
        "why": "Documentation or support language may indicate a provider trust threshold has been reached.",
        "opportunity": "Disability documentation, referral support, treatment planning, or care coordination may become easier.",
    },
    {
        "state_change": "Barrier removed",
        "keywords": ["approved", "authorization", "scheduled", "completed"],
        "why": "A prior administrative or access barrier may have been resolved.",
        "opportunity": "The next step in the care pathway may become available.",
    },
    {
        "state_change": "Capacity increased",
        "keywords": ["improved", "tolerated", "reduced pain", "less pain", "increased function", "better"],
        "why": "The source suggests a possible increase in tolerance or function.",
        "opportunity": "A capacity window may allow learning, therapy participation, habit formation, or functional gains.",
    },
    {
        "state_change": "Skill acquired",
        "keywords": ["learned", "training", "breathing", "pacing", "posture", "home exercise"],
        "why": "The source suggests a skill or self-management strategy may have been learned.",
        "opportunity": "The skill may transfer into routine formation and functional change.",
    },
    {
        "state_change": "Treatment pathway opened",
        "keywords": ["referral", "injection", "procedure", "treatment plan", "specialist"],
        "why": "The source suggests a pathway toward treatment, referral, or escalation may have opened.",
        "opportunity": "Provider alignment, authorization, or care coordination may unlock the next step.",
    },
    {
        "state_change": "Documentation gap closed",
        "keywords": ["records received", "documentation", "form completed", "summary", "report"],
        "why": "The source suggests missing evidence may have become available.",
        "opportunity": "Disability, insurance, referral, or provider communication may become stronger.",
    },
]


def detect_hidden_states(profile: dict | None = None) -> list[dict]:
    ensure_directories()
    events = read_json(PROCESSED_DIR / "events.json", [])
    hidden_states = []
    for event in events:
        text = " ".join(
            [
                event.get("summary", ""),
                event.get("source_evidence", ""),
                event.get("patient_reported", ""),
            ]
        ).lower()
        if profile and any(term in text for term in profile_terms(profile, "trust_threshold_keywords")):
            hidden_states.append(
                {
                    "state_change": "Trust established",
                    "source_event": event.get("event_id"),
                    "possible_hidden_state_change": "Trust established",
                    "why_it_matters": "Case profile trust-threshold keyword detected. Human review required.",
                    "downstream_opportunity": "Provider alignment, documentation, referral, or treatment pathway may have opened.",
                    "source_evidence": event.get("source_evidence", ""),
                    "source": event.get("source", {}),
                    "confidence_level": "low",
                }
            )
        for rule in HIDDEN_STATE_RULES:
            if any(keyword in text for keyword in rule["keywords"]):
                hidden_states.append(
                    {
                        "state_change": rule["state_change"],
                        "source_event": event.get("event_id"),
                        "possible_hidden_state_change": rule["state_change"],
                        "why_it_matters": rule["why"],
                        "downstream_opportunity": rule["opportunity"],
                        "source_evidence": event.get("source_evidence", ""),
                        "source": event.get("source", {}),
                        "confidence_level": "medium" if event.get("confidence_level") == "high" else "low",
                    }
                )
    write_json(PROCESSED_DIR / "hidden_states.json", hidden_states)
    return hidden_states


def main() -> None:
    hidden_states = detect_hidden_states()
    print(f"Detected {len(hidden_states)} hidden state candidates.")
    print(f"Wrote {PROCESSED_DIR / 'hidden_states.json'}")


if __name__ == "__main__":
    main()
