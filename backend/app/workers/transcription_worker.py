from pathlib import Path
import tempfile

from backend.ai.speech.faster_whisper import FasterWhisperTranscriber
from app.utils.audio import AudioExtractor

class TranscriptionWorker:
    """Worker for speech-to-text transcription."""

    def __init__(
        self,
    ):
        self.extractor = AudioExtractor()
        self.transcriber = FasterWhisperTranscriber()

    def process(
        self,
        video_path: str,
    ) -> dict:
        """
        Extract audio then transcribe it.
        Returns:
            {
                "language": "...",
                "text": "...",
            }
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = Path(tmp_dir) / "audio.wav"
            self.extractor.extract(
                video_path=video_path,
                output_path=str(wav_path),
            )
            result = self.transcriber.transcribe(
                str(wav_path),
            )
            return {
                "language": result["language"],
                "text": result["text"],
            }