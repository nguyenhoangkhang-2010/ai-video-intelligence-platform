from pathlib import Path
import tempfile
import logging

from ai.speech.faster_whisper import FasterWhisperTranscriber
from app.utils.audio import AudioExtractor


logger = logging.getLogger(__name__)


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
                "language": str,
                "text": str,
            }
        """
        logger.info(
            "Start transcription worker: %s",
            video_path,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = Path(tmp_dir) / "audio.wav"
            logger.info(
                "Extract audio: %s",
                wav_path,
            )
            self.extractor.extract(
                video_path=video_path,
                output_path=str(wav_path),
            )
            logger.info(
                "Start Whisper transcription",
            )
            result = self.transcriber.transcribe(
                str(wav_path),
            )
            logger.info(
                "Transcription completed. Language=%s",
                result["language"],
            )
            return {
                "language": result["language"],
                "text": result["text"],
            }