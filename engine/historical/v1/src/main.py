from build_timeline import build_timeline, timeline_markdown
from build_evidence_matrix import build_evidence_matrix
from case_profile import load_case_profile
from chunk_documents import build_chunks
from config import REPORTS_DIR, ensure_directories
from detect_bottlenecks import detect_bottlenecks
from detect_hidden_states import detect_hidden_states
from detect_trust_thresholds import detect_trust_thresholds
from extract_events import extract_events_from_chunks
from extract_text import extract_all
from generate_reports import generate_all_reports
from track_capacity_windows import track_capacity_windows
from utils import write_text


def main() -> None:
    ensure_directories()
    profile = load_case_profile()
    print("Neverlost Healthcare Roadmap V1")
    print(f"Loaded case profile: {profile.get('case_name')}")
    print("Running local rule-based pipeline...")
    pages = extract_all()
    print(f"Extracted text records: {len(pages)}")
    chunks = build_chunks()
    print(f"Source-linked chunks: {len(chunks)}")
    events = extract_events_from_chunks(profile)
    print(f"Event candidates: {len(events)}")
    timeline = build_timeline()
    write_text(REPORTS_DIR / "timeline.md", timeline_markdown(timeline))
    print(f"Timeline events: {len(timeline)}")
    matrix = build_evidence_matrix(profile)
    print(f"Evidence matrix rows: {len(matrix)}")
    hidden = detect_hidden_states(profile)
    print(f"Hidden state candidates: {len(hidden)}")
    thresholds = detect_trust_thresholds(profile)
    print(f"Trust threshold candidates: {len(thresholds)}")
    bottlenecks = detect_bottlenecks(profile)
    print(f"Consolidated bottlenecks: {len(bottlenecks)}")
    windows = track_capacity_windows(profile)
    print(f"Capacity window candidates: {len(windows)}")
    generate_all_reports(profile)
    print("Done.")
    print("Review reports in outputs/reports.")
    print("Review debug notes in outputs/debug.")


if __name__ == "__main__":
    main()
