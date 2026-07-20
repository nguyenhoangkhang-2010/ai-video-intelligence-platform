from faster_whisper import WhisperModel

from ai.speech.transcriber import BaseTranscriber


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
    ):
        pass