from ai.speech.language_detector import LanguageDetector


def test_from_whisper_result_uses_whisper_language_when_confident():
    detector = LanguageDetector(fallback_threshold=0.5)

    result = detector.from_whisper_result(
        language="en", probability=0.95, text="Hello there",
    )

    assert result.code == "en"
    assert result.confidence == 0.95
    assert result.source == "whisper"


def test_from_whisper_result_accepts_missing_probability():
    detector = LanguageDetector(fallback_threshold=0.5)

    result = detector.from_whisper_result(
        language="ja", probability=None, text="hello",
    )

    assert result.code == "ja"
    assert result.source == "whisper"


def test_from_whisper_result_falls_back_to_text_when_confidence_low():
    detector = LanguageDetector(fallback_threshold=0.9)

    result = detector.from_whisper_result(
        language="en",
        probability=0.3,
        text="Bonjour tout le monde, comment ca va aujourd hui?",
    )

    assert result.source == "text_fallback"
    assert result.code == "fr"


def test_from_whisper_result_defaults_when_no_text_available_for_fallback():
    detector = LanguageDetector(fallback_threshold=0.9)

    result = detector.from_whisper_result(
        language="en", probability=0.1, text="",
    )

    assert result.source == "default"
    assert result.code == "en"
    assert result.confidence == 0.1


def test_from_text_returns_unknown_for_empty_text():
    detector = LanguageDetector()

    result = detector.from_text("   ")

    assert result.code == "unknown"
    assert result.confidence is None
    assert result.source == "default"


def test_from_text_detects_language_generically_not_hardcoded():
    detector = LanguageDetector()

    result = detector.from_text(
        "Day la mot cau tieng Viet hoan chinh de kiem tra ngon ngu.",
    )

    assert result.code == "vi"
    assert result.source == "text_fallback"
    assert result.confidence > 0
