from __future__ import annotations

from typing import Any

from config import CASE_PROFILE_PATH


DEFAULT_CASE_PROFILE: dict[str, Any] = {
    "case_name": "Generic Healthcare Roadmap Case",
    "primary_conditions_to_track": [],
    "priority_functional_limits": [],
    "priority_evidence_types": [],
    "priority_outputs": [],
    "bottleneck_priorities": [],
    "capacity_window_keywords": [],
    "trust_threshold_keywords": [],
    "report_style": {
        "tone": "professional, grounded, clinician-friendly",
        "avoid": ["overstatement", "unsupported conclusions"],
        "prefer": ["source-cited evidence", "clear next actions"],
    },
    "guardrails": {
        "require_source_links": True,
        "separate_record_evidence_patient_observation_ai_inference": True,
        "do_not_generate_new_diagnoses": True,
        "label_confidence_levels": True,
        "human_review_required": True,
    },
}


def _load_yaml(path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def merge_profile(default: dict[str, Any], loaded: dict[str, Any]) -> dict[str, Any]:
    merged = dict(default)
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def load_case_profile() -> dict[str, Any]:
    return merge_profile(DEFAULT_CASE_PROFILE, _load_yaml(CASE_PROFILE_PATH))


def profile_terms(profile: dict[str, Any], key: str) -> list[str]:
    value = profile.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item).lower() for item in value]


def text_matches_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)

