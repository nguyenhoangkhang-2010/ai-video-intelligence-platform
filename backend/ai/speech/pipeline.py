import logging
import tempfile
from pathlib import Path

from ai.diarization.speaker_diarization import SpeakerDiarizer
from ai.diarization.speaker_mapping import SpeakerMapper
from ai.diarization.alignment import align_segments_with_speakers
from ai.speech.audio_extractor import AudioExtractor
from ai.speech.faster_whisper import FasterWhisperTranscriber
from ai.speech.language_detector import LanguageDetector
from ai.speech.post_processing import post_process_speech_result
from ai.speech.speech_result import SpeechResult
from ai.speech.transcriber import BaseTranscriber
from ai.speech.vad import VoiceActivityDetector
from app.config.settings import settings


logger = logging.getLogger(__name__)


class NoSpeechDetectedError(ValueError):
    """
    Raised when no speech could be transcribed from the audio. A
    ValueError subclass so it stays compatible with any existing code
    that already catches/raises ValueError for this exact condition
    (see app.pipelines.video_pipeline.transcription_stage).
    """


class SpeechPipeline:
    """
    Advanced speech intelligence pipeline - the ONE canonical
    transcription path:

    video -> AudioExtractor -> VoiceActivityDetector (metadata) ->
    ASR (FasterWhisperTranscriber) -> LanguageDetector (reuses
    Whisper's own result) -> SpeakerDiarizer (optional) ->
    SpeakerMapper -> timestamp alignment -> post-processing ->
    SpeechResult.

    app.workers.transcription_worker.TranscriptionWorker delegates to
    this instead of wiring extraction/ASR/post-processing itself, so
    there is no second, parallel transcription pipeline.

    VAD's speech-range output is exposed as metadata (and available
    to future stages such as diarization) rather than used to hard
    fail-fast before ASR runs: the existing, already-proven-correct
    signal for "no speech" is Whisper's own transcribed text being
    empty, and changing that would risk turning previously-successful
    transcriptions into new failures if VAD is ever more conservative
    than Whisper's own detection.
    """

    def __init__(
        self,
        audio_extractor: AudioExtractor | None = None,
        vad: VoiceActivityDetector | None = None,
        transcriber: BaseTranscriber | None = None,
        language_detector: LanguageDetector | None = None,
        diarizer_factory=None,
        speaker_mapper: SpeakerMapper | None = None,
        diarization_enabled: bool | None = None,
    ):
        self.audio_extractor = (
            audio_extractor
            or AudioExtractor()
        )
        self.vad = (
            vad
            or VoiceActivityDetector()
        )
        self.transcriber = (
            transcriber
            or FasterWhisperTranscriber()
        )
        self.language_detector = (
            language_detector
            or LanguageDetector()
        )
        self.speaker_mapper = (
            speaker_mapper
            or SpeakerMapper()
        )

        # A factory, not an instance: the (heavy, gated) diarization
        # model is only ever loaded lazily on first actual use, and
        # only when diarization is enabled - never eagerly here.
        self._diarizer_factory = diarizer_factory or SpeakerDiarizer
        self._diarizer: SpeakerDiarizer | None = None

        self.diarization_enabled = (
            diarization_enabled
            if diarization_enabled is not None
            else settings.speech.diarization_enabled
        )

    def process(
        self,
        video_path: str,
    ) -> SpeechResult:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = Path(tmp_dir) / "audio.wav"

            logger.info(
                "Extracting audio: %s",
                wav_path,
            )

            self.audio_extractor.extract(
                video_path=video_path,
                output_path=str(wav_path),
            )

            speech_ranges = self.vad.detect_speech_segments(
                str(wav_path),
            )

            logger.info(
                "Start speech recognition: %s",
                wav_path,
            )

            asr_result = self.transcriber.transcribe(
                str(wav_path),
            )

            if not asr_result["text"].strip():
                logger.warning(
                    "No speech detected in video %s",
                    video_path,
                )
                raise NoSpeechDetectedError(
                    "No speech detected in audio."
                )

            detected_language = (
                self.language_detector.from_whisper_result(
                    language=asr_result.get("language"),
                    probability=asr_result.get(
                        "language_probability",
                    ),
                    text=asr_result["text"],
                )
            )

            speaker_segments = []

            if self.diarization_enabled:
                diarizer = self._get_diarizer()

                raw_speaker_segments = diarizer.diarize(
                    str(wav_path),
                )

                speaker_segments = self.speaker_mapper.map(
                    raw_speaker_segments,
                )

            aligned_segments = align_segments_with_speakers(
                asr_segments=asr_result["segments"],
                speaker_segments=speaker_segments,
            )

            speech_result = SpeechResult(
                language=detected_language.code,
                text=asr_result["text"],
                segments=aligned_segments,
                language_probability=detected_language.confidence,
                metadata={
                    "language_source": detected_language.source,
                    "duration": asr_result.get("duration"),
                    "speech_ranges": speech_ranges,
                    "diarization_enabled": self.diarization_enabled,
                },
            )

            return post_process_speech_result(
                speech_result,
            )

    def _get_diarizer(self) -> SpeakerDiarizer:
        if self._diarizer is None:
            self._diarizer = self._diarizer_factory()

        return self._diarizer
