"""
Optional future LLM extraction interface.

V1 does not call this module. The rule-based pipeline must keep working without
LLM access, API keys, cloud storage, or external services.
"""

from typing import Any


class LLMExtractionDisabled(RuntimeError):
    pass


def extract_structured_json_from_chunk(chunk: dict[str, Any], schema_name: str) -> dict[str, Any]:
    """Future extension point for LLM-backed extraction.

    Expected behavior in a later version:
    - Receive one source-linked chunk.
    - Return JSON matching the requested schema.
    - Preserve source document and chunk references.
    - Clearly label AI inference.
    - Never replace the local rule-based pipeline.
    """
    raise LLMExtractionDisabled(
        "LLM extraction is not enabled in V1. Use the local rule-based pipeline."
    )

