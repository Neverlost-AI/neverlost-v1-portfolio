import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


DATE_PATTERNS = [
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
]

BAD_DATE_LABELS = [
    "dob",
    "date of birth",
    "birthdate",
    "sex",
    "npi",
    "phone",
    "fax",
    "address",
    "cpt",
    "license",
]

DATE_PRIORITY_LABELS = [
    "visit",
    "visit date",
    "dos",
    "date of service",
    "signed",
    "electronically signed",
    "form date",
    "submitted",
    "completed",
]

ADMIN_NOISE_TERMS = [
    "date of birth",
    "dob",
    "sex:",
    "npi",
    "phone",
    "fax",
    "address",
    "license",
    "cpt",
    "treatment minutes",
    "signature",
    "electronically signed",
]

SUBSTANTIVE_TERMS = [
    "assessment",
    "plan",
    "goal",
    "goals",
    "function",
    "functional",
    "limitation",
    "pain",
    "fatigue",
    "dizziness",
    "walking",
    "standing",
    "sitting",
    "lifting",
    "adls",
    "iadls",
    "tolerance",
    "improved",
    "reduced",
    "diagnosis",
    "referral",
    "appeal",
    "disability",
    "rfc",
    "denied",
    "authorization",
]


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_dates(text: str) -> list[str]:
    dates: list[str] = []
    for pattern in DATE_PATTERNS:
        dates.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return dates


def date_candidates_with_context(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            start = max(0, match.start() - 45)
            end = min(len(text), match.end() + 45)
            context = text[start:end]
            before = text[start:match.start()].lower()
            candidates.append(
                {
                    "date": match.group(0),
                    "context": context,
                    "before": before,
                    "start": match.start(),
                }
            )
    return candidates


def is_bad_date_context(candidate: dict[str, Any]) -> bool:
    before = candidate.get("before", "").lower()
    return any(label in before[-35:] for label in BAD_DATE_LABELS)


def priority_score_for_date(candidate: dict[str, Any]) -> int:
    before = candidate.get("before", "").lower()
    for index, label in enumerate(DATE_PRIORITY_LABELS):
        if label in before[-45:]:
            return 100 - index
    if is_bad_date_context(candidate):
        return -100
    return 1


def select_event_date(text: str) -> str | None:
    candidates = date_candidates_with_context(text)
    if not candidates:
        return None
    candidates = sorted(candidates, key=priority_score_for_date, reverse=True)
    best = candidates[0]
    if priority_score_for_date(best) < 0:
        return None
    return best["date"]


def is_admin_noise(text: str) -> bool:
    lower = text.lower()
    admin_hits = sum(1 for term in ADMIN_NOISE_TERMS if term in lower)
    substantive_hits = sum(1 for term in SUBSTANTIVE_TERMS if term in lower)
    return admin_hits >= 2 and substantive_hits == 0


def has_substantive_content(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in SUBSTANTIVE_TERMS)


def parse_date(value: str | None) -> str:
    if not value:
        return "9999-12-31"
    value = value.strip()
    formats = [
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "9999-12-31"


def source_label(item: dict[str, Any]) -> str:
    source = item.get("source", {})
    doc = item.get("source_document") or source.get("document", "unknown document")
    page = source.get("page")
    chunk_id = item.get("source_page_or_chunk") or source.get("chunk_id", "unknown chunk")
    page_label = f"p. {page}" if page else "page unknown"
    return f"{doc}, {page_label}, {chunk_id}"
