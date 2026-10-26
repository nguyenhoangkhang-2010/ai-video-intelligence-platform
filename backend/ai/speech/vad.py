import logging

from faster_whisper import decode_audio
from faster_whisper.vad import VadOptions, get_speech_timestamps

from app.config.settings import settings


logger = logging.getLogger(__name__)

_SAMPLING_RATE = 16000


class VoiceActivityDetector:
    """
    Voice activity detection.

    Reuses the Silero VAD model already bundled with faster-whisper
    (ai.speech.faster_whisper's own dependency) via its public
    faster_whisper.vad module, instead of adding a second VAD
    library/model (webrtcvad is listed in requirements but nothing in
    this project actually uses it - faster-whisper's bundled VAD is
    already integrated and sufficient).

    This runs as its own single pass over the raw audio. Its output
    is used both as pipeline metadata and to fast-fail on audio with
    no speech at all before the far more expensive ASR stage ever
    runs. ai.speech.faster_whisper.FasterWhisperTranscriber does not
    additionally enable its own internal vad_filter, so VAD only ever
    computes once per video.
    """

    def __init__(
        self,
        threshold: float | None = None,
        min_silence_duration_ms: int | None = None,
    ):
        self.vad_options = VadOptions(
            threshold=(
                threshold
                if threshold is not None
                else settings.speech.vad_threshold
            ),
            min_silence_duration_ms=(
                min_silence_duration_ms
                if min_silence_duration_ms is not None
                else settings.speech.vad_min_silence_duration_ms
            ),
        )

    def detect_speech_segments(
        self,
        audio_path: str,
    ) -> list[tuple[float, float]]:
        """
        Return (start, end) second ranges containing speech, in
        chronological order. An empty list means no speech was
        detected anywhere in the audio.
        """

        audio = decode_audio(
            audio_path,
            sampling_rate=_SAMPLING_RATE,
        )

        chunks = get_speech_timestamps(
            audio,
            vad_options=self.vad_options,
        )

        segments = [
            (
                chunk["start"] / _SAMPLING_RATE,
                chunk["end"] / _SAMPLING_RATE,
            )
            for chunk in chunks
        ]

        logger.info(
            "VAD detected %s speech segment(s) in %s.",
            len(segments),
            audio_path,
        )

        return segments

    def has_speech(
        self,
        audio_path: str,
    ) -> bool:
        """
        Cheap "is there any speech at all" check, for failing fast
        before running ASR on audio that is entirely silence/noise.
        """
        return bool(
            self.detect_speech_segments(
                audio_path,
            )
        )
