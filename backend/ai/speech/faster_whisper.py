import logging

from faster_whisper import WhisperModel

from ai.speech.transcriber import BaseTranscriber
from app.config.settings import settings


logger = logging.getLogger(__name__)


class FasterWhisperTranscriber(BaseTranscriber):
    """
    Speech-to-text implementation using Faster-Whisper.

    Model configuration (size, device, compute type, beam size) is
    centralized in settings.speech rather than hardcoded here, so it
    can be tuned per environment without touching business logic.
    Falls back to CPU automatically if a configured "cuda" device is
    unavailable in the current environment, rather than hard-failing
    or silently assuming GPU is always present.
    """

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        beam_size: int | None = None,
    ):
        self.model_size = (
            model_size
            or settings.speech.whisper_model
        )
        self.beam_size = (
            beam_size
            if beam_size is not None
            else settings.speech.beam_size
        )

        requested_device = (
            device
            or settings.speech.device
        )
        requested_compute_type = (
            compute_type
            or settings.speech.compute_type
        )

        self.model, self.device = self._load_model(
            requested_device,
            requested_compute_type,
        )

    def _load_model(
        self,
        device: str,
        compute_type: str,
    ) -> tuple[WhisperModel, str]:
        try:
            return (
                WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=compute_type,
                ),
                device,
            )
        except Exception:
            if device == "cpu":
                raise

            logger.warning(
                "Failed to load Whisper model on device '%s' "
                "(likely no CUDA runtime available); falling back "
                "to CPU.",
                device,
                exc_info=True,
            )

            return (
                WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                ),
                "cpu",
            )

    def transcribe(
        self,
        audio_path: str,
    ) -> dict:
        logger.info(
            "Start Whisper transcription: %s (model=%s, device=%s)",
            audio_path,
            self.model_size,
            self.device,
        )

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=self.beam_size,
        )

        text = ""
        result_segments = []

        for segment in segments:
            text += segment.text + " "
            result_segments.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "no_speech_prob": segment.no_speech_prob,
                }
            )

        logger.info(
            "Whisper completed. Language=%s (probability=%s)",
            info.language,
            info.language_probability,
        )

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "text": text.strip(),
            "segments": result_segments,
            "duration": info.duration,
        }
