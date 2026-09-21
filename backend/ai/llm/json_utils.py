"""
Shared helpers for robustly extracting structured JSON from LLM text output.

LLM responses frequently wrap JSON in markdown code fences, add leading/
trailing commentary, or occasionally emit malformed JSON. These helpers
centralize that parsing so every generator/extractor in the codebase
handles it the same way instead of duplicating fragile parsing logic.
"""
import json
import re
from typing import Any

_CODE_FENCE_RE = re.compile(
    r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE,
)


def extract_json(text: str) -> Any | None:
    """
    Attempt to extract and parse a JSON value from raw LLM text.

    Handles markdown code fences and surrounding commentary. Returns
    None (rather than raising) if no valid JSON could be extracted, so
    callers can apply deterministic fallback behavior instead of
    crashing on malformed LLM output.
    """
    if not text or not text.strip():
        return None

    candidates: list[str] = []

    fence_match = _CODE_FENCE_RE.search(text)
    if fence_match:
        candidates.append(fence_match.group(1))

    candidates.append(text.strip())

    stripped = text.strip()
    first_obj = stripped.find("{")
    first_arr = stripped.find("[")
    starts = [i for i in (first_obj, first_arr) if i != -1]
    if starts:
        start = min(starts)
        last_obj = stripped.rfind("}")
        last_arr = stripped.rfind("]")
        end = max(last_obj, last_arr)
        if end > start:
            candidates.append(stripped[start:end + 1])

    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue

    return None
