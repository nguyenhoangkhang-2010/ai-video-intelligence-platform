from ai.speech.post_processing import post_process_transcription


def test_post_process_transcription():
    result = {
        "language": "vi",
        "text": "  Xin    chào  ",
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "  Xin   ",
            },
            {
                "start": 1.0,
                "end": 2.0,
                "text": " chào  ",
            },
        ],
    }

    processed = post_process_transcription(result)

    assert processed["language"] == "vi"
    assert processed["text"] == "Xin chào"

    assert processed["segments"][0]["start"] == 0.0
    assert processed["segments"][0]["end"] == 1.0
    assert processed["segments"][0]["text"] == "Xin"

    assert processed["segments"][1]["text"] == "chào"


def test_post_process_without_segments():
    result = {
        "language": "vi",
        "text": "  Xin    chào  ",
        "segments": [],
    }

    processed = post_process_transcription(result)

    assert processed["text"] == "Xin chào"