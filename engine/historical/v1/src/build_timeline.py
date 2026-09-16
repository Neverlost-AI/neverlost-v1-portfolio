from config import PROCESSED_DIR, REPORTS_DIR, ensure_directories
from utils import parse_date, read_json, source_label, write_json, write_text


def build_timeline() -> list[dict]:
    ensure_directories()
    events = read_json(PROCESSED_DIR / "events.json", [])
    timeline = sorted(events, key=lambda item: (parse_date(item.get("date")), item["event_id"]))
    write_json(PROCESSED_DIR / "timeline.json", timeline)
    return timeline


def timeline_markdown(timeline: list[dict]) -> str:
    lines = [
        "# Medical Timeline",
        "",
        "> Not medical advice. This timeline is a draft healthcare-operations aid and requires human review.",
        "",
    ]
    if not timeline:
        lines.append("No events extracted yet. Add healthcare documents to `data/raw_documents/` and rerun the pipeline.")
        return "\n".join(lines)

    for event in timeline:
        date = event.get("date") or "Date not found"
        lines.extend(
            [
                f"## {date} — {event.get('event_type', 'general').title()}",
                "",
                event.get("event_summary") or event.get("summary", ""),
                "",
                f"**Source:** {source_label(event)}",
                f"**Confidence:** {event.get('confidence_level', 'unknown')}",
                "",
                "**Evidence / Interpretation Split**",
                "",
                f"- Source evidence: {event.get('source_evidence', '')}",
                f"- Patient Observation: {event.get('patient_observation') or event.get('patient_reported') or 'Not separately identified in this chunk.'}",
                f"- AI inference: {event.get('ai_inference', '')}",
                f"- Functional relevance: {event.get('functional_relevance') or 'Not identified.'}",
                f"- Documentation relevance: {event.get('documentation_relevance') or 'Not identified.'}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    timeline = build_timeline()
    write_text(REPORTS_DIR / "timeline.md", timeline_markdown(timeline))
    print(f"Built timeline with {len(timeline)} events.")
    print(f"Wrote {REPORTS_DIR / 'timeline.md'}")


if __name__ == "__main__":
    main()
