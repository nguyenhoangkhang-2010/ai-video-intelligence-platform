from pathlib import Path
import tempfile
import logging

from ai.speech.faster_whisper import FasterWhisperTranscriber
from ai.speech.post_processing import post_process_transcription
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
                "Whisper transcription completed. Language=%s",
                result["language"],
            )

            processed_result = post_process_transcription(result)

            logger.info(
                "Transcription post-processing completed",
            )

            return {
                "language": processed_result["language"],
                "text": processed_result["text"],
                "segments": processed_result.get("segments", []),
            }