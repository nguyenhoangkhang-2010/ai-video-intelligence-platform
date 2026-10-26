import re
import unicodedata


def normalize_text(text: str) -> str:
    
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    text = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", text)

    return text.strip()


def normalize_segments(segments: list[dict]) -> list[dict]:
    
    normalized_segments = []

    for segment in segments:
        normalized_segment = dict(segment)

        normalized_segment["text"] = normalize_text(
            segment.get("text", "")
        )

        normalized_segments.append(normalized_segment)

    return normalized_segments