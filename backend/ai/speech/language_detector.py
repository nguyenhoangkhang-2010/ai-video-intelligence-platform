import logging
from dataclasses import dataclass

from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException

from app.config.settings import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectedLanguage:
    """
    code is a generic ISO-639-1-ish language code (whatever
    Whisper/langdetect produce - "en", "vi", "ja", "ko", ... - never
    hardcoded to a fixed set of languages).
    """

    code: str
    confidence: float | None
    source: str  # "whisper" | "text_fallback" | "default"


class LanguageDetector:
    """
    Generic language detection, not tied to any specific language.

    The primary path reuses whatever language faster-whisper's ASR
    pass already detected (info.language / info.language_probability)
    - no second language-detection model runs for the common case, as
    required by the audit ("reuse Whisper's result instead of running
    a second language detection model"). A text-based fallback
    (langdetect, already a project dependency) only runs when
    Whisper's own detection is missing or below a configurable
    confidence threshold, or when detecting language from plain text
    with no audio/ASR involved at all.
    """

    def __init__(
        self,
        fallback_threshold: float | None = None,
    ):
        self.fallback_threshold = (
            fallback_threshold
            if fallback_threshold is not None
            else settings.speech.language_detection_fallback_threshold
        )

    def from_whisper_result(
        self,
        language: str | None,
        probability: float | None,
        text: str = "",
    ) -> DetectedLanguage:
        """
        Normalize/validate Whisper's own detected language. Falls
        back to text-based detection only if Whisper's confidence is
        below `fallback_threshold` (or language is missing entirely).
        """

        if language and (
            probability is None
            or probability >= self.fallback_threshold
        ):
            return DetectedLanguage(
                code=language,
                confidence=probability,
                source="whisper",
            )

        logger.info(
            "Whisper language detection ('%s', confidence=%s) below "
            "threshold (%s); falling back to text-based detection.",
            language,
            probability,
            self.fallback_threshold,
        )

        if text and text.strip():
            return self.from_text(text)

        return DetectedLanguage(
            code=language or "unknown",
            confidence=probability,
            source="default",
        )

    def from_text(
        self,
        text: str,
    ) -> DetectedLanguage:
        """
        Detect language from plain text alone (no audio/ASR needed).
        Returns "unknown" if detection fails or text is empty -
        callers must not treat "unknown" as a real language code.
        """

        if not text or not text.strip():
            return DetectedLanguage(
                code="unknown",
                confidence=None,
                source="default",
            )

        try:
            candidates = detect_langs(text)
        except LangDetectException:
            logger.warning(
                "Text-based language detection failed; "
                "returning 'unknown'.",
            )
            return DetectedLanguage(
                code="unknown",
                confidence=None,
                source="default",
            )

        if not candidates:
            return DetectedLanguage(
                code="unknown",
                confidence=None,
                source="text_fallback",
            )

        best = candidates[0]

        return DetectedLanguage(
            code=best.lang,
            confidence=best.prob,
            source="text_fallback",
        )
