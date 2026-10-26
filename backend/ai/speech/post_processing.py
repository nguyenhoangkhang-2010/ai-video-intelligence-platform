from ai.speech.normalizer import normalize_segments, normalize_text
from ai.speech.speech_result import SpeechResult, SpeechSegment


def post_process_speech_result(result: SpeechResult) -> SpeechResult:
    """
    Normalize a full SpeechResult: per-segment text normalization
    (reusing normalize_text, the same function backing
    post_process_transcription below), dropping empty (blank text) or
    invalid (end <= start) segments, and ordering by start time.
    Speaker labels and per-segment metadata are always preserved
    untouched - only text/ordering/filtering are affected. Does not
    alter segment content beyond the same whitespace/punctuation
    normalization already applied elsewhere - no LLM rewriting, no
    semantic changes.
    """

    normalized_segments = []

    for segment in result.segments:
        normalized_text = normalize_text(segment.text)

        if not normalized_text:
            continue

        if segment.end <= segment.start:
            continue

        normalized_segments.append(
            SpeechSegment(
                start=segment.start,
                end=segment.end,
                text=normalized_text,
                speaker=segment.speaker,
                metadata=segment.metadata,
            )
        )

    normalized_segments.sort(key=lambda segment: segment.start)

    normalized_text = normalize_text(
        " ".join(
            segment.text
            for segment in normalized_segments
        )
    )

    return SpeechResult(
        language=result.language,
        text=normalized_text,
        segments=normalized_segments,
        language_probability=result.language_probability,
        metadata=result.metadata,
    )


def post_process_transcription(result: dict) -> dict:
    
    processed = dict(result)

    segments = result.get("segments", [])

    if segments:
        processed_segments = normalize_segments(segments)
        processed["segments"] = processed_segments

        processed["text"] = normalize_text(
            " ".join(
                segment["text"]
                for segment in processed_segments
                if segment.get("text")
            )
        )
    else:
        processed["text"] = normalize_text(
            result.get("text", "")
        )

    return processed