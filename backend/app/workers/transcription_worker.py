import logging

from ai.speech.pipeline import SpeechPipeline


logger = logging.getLogger(__name__)


class TranscriptionWorker:
    """
    Worker for speech-to-text transcription.

    Delegates entirely to ai.speech.pipeline.SpeechPipeline (audio
    extraction -> VAD -> ASR -> language detection -> optional
    diarization -> alignment -> normalization) - the one canonical
    speech pipeline, not reimplemented here.

    Return contract is unchanged from before this pipeline existed:
    a dict with "language"/"text"/"segments" (list of dicts with at
    least "start"/"end"/"text") - app.pipelines.video_pipeline.
    VideoPipelineService.transcription_stage only ever reads
    result["text"]/result["language"], so this stays fully
    backward-compatible. Each segment dict now also carries "speaker"
    (None unless diarization is enabled) and any extra ASR metadata -
    purely additive, ignored by existing callers.
    """

    def __init__(
        self,
        speech_pipeline: SpeechPipeline | None = None,
    ):
        self.speech_pipeline = (
            speech_pipeline
            or SpeechPipeline()
        )

    def process(
        self,
        video_path: str,
    ) -> dict:

        logger.info(
            "Start transcription worker: %s",
            video_path,
        )

        speech_result = self.speech_pipeline.process(
            video_path,
        )

        logger.info(
            "Transcription completed. Language=%s",
            speech_result.language,
        )

        return {
            "language": speech_result.language,
            "text": speech_result.text,
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "speaker": segment.speaker,
                    **segment.metadata,
                }
                for segment in speech_result.segments
            ],
        }
