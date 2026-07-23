from pathlib import Path
import tempfile

from backend.ai.speech.faster_whisper import FasterWhisperTranscriber
from app.utils.audio import AudioExtractor

from app.schemas.transcript import TranscriptCreate
from app.services.transcript import TranscriptService

class TranscriptionWorker:
    """Worker for speech-to-text transcription."""

    def __init__(
        self,
        transcript_service: TranscriptService,
    ):
        self.extractor = AudioExtractor()
        self.transcriber = FasterWhisperTranscriber()
        self.transcript_service = transcript_service

    def process(
        self,
        video_id: int,
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
            transcript = self.transcript_service.create_transcript(
                TranscriptCreate(
                    video_id=video_id,
                    language=result["language"],
                    text=result["text"],
                )
            )
            return transcript