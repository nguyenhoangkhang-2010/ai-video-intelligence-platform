from ai.speech.normalizer import normalize_text, normalize_segments


def test_normalize_text_whitespace():
    text = "  Xin    chào   bạn  "

    assert normalize_text(text) == "Xin chào bạn"


def test_normalize_text_punctuation_spacing():
    text = "Xin chào ,bạn !Hôm nay thế nào?"

    assert normalize_text(text) == "Xin chào, bạn! Hôm nay thế nào?"


def test_normalize_text_preserves_content():
    text = "Đây là một câu tiếng Việt."

    assert normalize_text(text) == text


def test_normalize_segments_preserves_timestamps():
    segments = [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "  Xin    chào  ",
        }
    ]

    result = normalize_segments(segments)

    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 2.5
    assert result[0]["text"] == "Xin chào"