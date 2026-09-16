from config import PROCESSED_DIR, ensure_directories
from case_profile import profile_terms
from utils import read_json, write_json


INTERVENTION_KEYWORDS = [
    "injection",
    "medication",
    "procedure",
    "physical therapy",
    "occupational therapy",
    "manual therapy",
    "exercise",
    "brace",
    "assistive",
]

CAPACITY_KEYWORDS = [
    "improved",
    "improvement",
    "progressing",
    "responded well",
    "reduced pain",
    "less pain",
    "tolerated",
    "increased",
    "able to",
    "capacity",
    "function",
    "routine",
]


def track_capacity_windows(profile: dict | None = None) -> list[dict]:
    ensure_directories()
    events = read_json(PROCESSED_DIR / "events.json", [])
    windows = []
    for event in events:
        text = " ".join([event.get("summary", ""), event.get("source_evidence", "")]).lower()
        profile_capacity_terms = profile_terms(profile or {}, "capacity_window_keywords")
        if any(term in text for term in ["foster care", "dog", "dogs", "pet care"]):
            continue
        intervention_signal = any(keyword in text for keyword in INTERVENTION_KEYWORDS)
        event_type_signal = event.get("event_type") in {"intervention", "PT/OT event", "medication"}
        if not intervention_signal:
            continue
        if not event_type_signal:
            continue
        capacity_signal = any(keyword in text for keyword in CAPACITY_KEYWORDS) or any(keyword in text for keyword in profile_capacity_terms)
        if not capacity_signal:
            continue
        windows.append(
            {
                "intervention": event.get("summary", "")[:180],
                "date": event.get("date"),
                "capacity_window_created": "Possible capacity window detected from intervention and function/tolerance language.",
                "what_became_possible": "Possible therapy participation, care-plan follow-through, symptom tracking, or routine formation. Human review required.",
                "learning": "Look for skills learned during this window, such as pacing, breathing, posture, strengthening, or self-management.",
                "habit_formation": "Track whether a repeated routine was established during or after this intervention.",
                "functional_change": "Track whether function, tolerance, or care-plan participation changed.",
                "gains_retained": "Unknown until follow-up evidence is reviewed.",
                "source_evidence": event.get("source_evidence", ""),
                "evidence_source": event.get("source_evidence", ""),
                "source": event.get("source", {}),
                "confidence_level": "medium",
            }
        )
    write_json(PROCESSED_DIR / "capacity_windows.json", windows)
    return windows


def main() -> None:
    windows = track_capacity_windows()
    print(f"Detected {len(windows)} capacity window candidates.")
    print(f"Wrote {PROCESSED_DIR / 'capacity_windows.json'}")


if __name__ == "__main__":
    main()
