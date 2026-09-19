from ai.speech.normalizer import normalize_segments, normalize_text


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