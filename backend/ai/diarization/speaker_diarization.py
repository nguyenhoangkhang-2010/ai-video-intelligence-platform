import logging
from dataclasses import dataclass

from app.config.settings import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpeakerSegment:
    """
    A single speaker-attributed time range from diarization. `speaker`
    is a raw, model-assigned label (e.g. "SPEAKER_00") - never a
    fabricated person identity. See ai.diarization.speaker_mapping
    for turning these into stable, generic labels.
    """

    speaker: str
    start: float
    end: float


class DiarizationUnavailableError(RuntimeError):
    """
    Raised when diarization cannot run (model failed to load, no
    speech, etc). Callers (ai.speech.pipeline.SpeechPipeline) decide
    whether this is fatal or whether to continue without speaker
    labels - this error type alone must never be swallowed silently.
    """


class SpeakerDiarizer:
    """
    Speaker diarization using pyannote.audio (already a project
    dependency - confirmed by audit, no new dependency added).

    Supports an unknown number of speakers (pyannote's pipelines
    determine speaker count themselves; this class never hardcodes
    one). Model lifecycle: loaded once in __init__, reused for every
    diarize() call on that instance.

    pyannote.audio is imported lazily inside __init__ rather than at
    module level, for the same reason as
    ai.reranking.cross_encoder.CrossEncoderReranker: in the
    environment this was developed in, importing heavy
    torch-dependent packages can trip an unrelated torchcodec/FFmpeg
    native-library loading issue. Deferring the import keeps this
    module - and anything only needing the SpeakerSegment/contract
    shape - importable and testable without the model needing to be
    loadable; the import (and any environment issue with it) only
    surfaces when a SpeakerDiarizer is actually instantiated.

    Diarization is a genuinely heavy, gated (HuggingFace
    authentication required) pretrained pipeline - this class does
    not attempt to download/run a real model as part of this phase's
    own validation; see the test suite, which mocks the pipeline.
    """

    def __init__(
        self,
        model_name: str | None = None,
    ):
        from pyannote.audio import Pipeline

        self.model_name = (
            model_name
            or settings.speech.diarization_model
        )

        try:
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=settings.huggingface.token,
            )
        except Exception as error:
            raise DiarizationUnavailableError(
                f"Could not load diarization model "
                f"'{self.model_name}': {error}"
            ) from error

        if self.pipeline is None:
            raise DiarizationUnavailableError(
                f"Diarization model '{self.model_name}' could not be "
                f"loaded (pyannote returned None - commonly means the "
                f"model's HuggingFace license was not accepted for "
                f"the configured token)."
            )

    def diarize(
        self,
        audio_path: str,
    ) -> list[SpeakerSegment]:
        """
        Run diarization over the full audio file. Returns segments in
        chronological order; an empty list means no speakers were
        identified (e.g. no speech in the audio).
        """

        logger.info(
            "Running speaker diarization: %s",
            audio_path,
        )

        try:
            annotation = self.pipeline(audio_path)
        except Exception as error:
            raise DiarizationUnavailableError(
                f"Diarization failed for {audio_path}: {error}"
            ) from error

        segments = [
            SpeakerSegment(
                speaker=str(speaker),
                start=float(turn.start),
                end=float(turn.end),
            )
            for turn, _, speaker in annotation.itertracks(
                yield_label=True,
            )
        ]

        segments.sort(key=lambda segment: segment.start)

        logger.info(
            "Diarization found %s segment(s) across %s speaker(s).",
            len(segments),
            len({segment.speaker for segment in segments}),
        )

        return segments
