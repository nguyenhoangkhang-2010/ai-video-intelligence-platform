from faster_whisper import WhisperModel

from ai.speech.transcriber import BaseTranscriber

import logging

logger = logging.getLogger(__name__)


class FasterWhisperTranscriber(BaseTranscriber):
    """Speech-to-text implementation using Faster-Whisper."""

    def __init__(
        self,
        model_size: str = "base",
    ):
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )

    def transcribe(
        self,
        audio_path: str,
    ) -> dict:
        logger.info(
            "Start Whisper transcription: %s",
            audio_path,
        )
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
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
                }
            )
        logger.info(
            "Whisper completed. Language=%s",
            info.language
        )
        return {
            "language": info.language,
            "text": text.strip(),
            "segments": result_segments,
        }