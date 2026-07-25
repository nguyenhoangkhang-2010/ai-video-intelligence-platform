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
    ) -> dict:
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
        return {
            "language": info.language,
            "text": text.strip(),
            "segments": result_segments,
        }