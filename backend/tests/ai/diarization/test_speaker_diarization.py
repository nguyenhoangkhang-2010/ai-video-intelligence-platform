from unittest.mock import MagicMock, patch

import pytest

from ai.diarization.speaker_diarization import (
    DiarizationUnavailableError,
    SpeakerDiarizer,
    SpeakerSegment,
)


def _make_diarizer_with_mock_pipeline(
    pipeline_return_value=None,
    pipeline_side_effect=None,
):
    """
    SpeakerDiarizer.__init__ lazily imports and loads a real,
    heavy, gated (HuggingFace-authenticated) pyannote.audio pretrained
    pipeline - not appropriate to actually load in a unit test.
    Bypass __init__ and inject a mock `.pipeline` directly, mirroring
    the same technique already used for CrossEncoderReranker in this
    codebase's own tests, so diarize()'s own logic (segment
    extraction, ordering, error wrapping) is exercised for real
    without ever downloading a model.
    """
    diarizer = object.__new__(SpeakerDiarizer)
    diarizer.model_name = "mock-model"
    diarizer.pipeline = MagicMock(name="pyannote_pipeline")

    if pipeline_side_effect is not None:
        diarizer.pipeline.side_effect = pipeline_side_effect
    else:
        diarizer.pipeline.return_value = pipeline_return_value

    return diarizer


def _fake_turn(start, end):
    turn = MagicMock()
    turn.start = start
    turn.end = end
    return turn


def _fake_annotation(tracks):
    annotation = MagicMock()
    annotation.itertracks.return_value = iter(tracks)
    return annotation


def test_diarize_returns_speaker_segments_in_chronological_order():
    annotation = _fake_annotation([
        (_fake_turn(5.0, 6.0), "trackB", "SPEAKER_01"),
        (_fake_turn(0.0, 2.0), "trackA", "SPEAKER_00"),
    ])
    diarizer = _make_diarizer_with_mock_pipeline(
        pipeline_return_value=annotation,
    )

    segments = diarizer.diarize("audio.wav")

    assert segments == [
        SpeakerSegment(speaker="SPEAKER_00", start=0.0, end=2.0),
        SpeakerSegment(speaker="SPEAKER_01", start=5.0, end=6.0),
    ]


def test_diarize_supports_an_unknown_number_of_speakers():
    annotation = _fake_annotation([
        (_fake_turn(0.0, 1.0), "t1", "SPEAKER_00"),
        (_fake_turn(1.0, 2.0), "t2", "SPEAKER_01"),
        (_fake_turn(2.0, 3.0), "t3", "SPEAKER_02"),
    ])
    diarizer = _make_diarizer_with_mock_pipeline(
        pipeline_return_value=annotation,
    )

    segments = diarizer.diarize("audio.wav")

    assert {s.speaker for s in segments} == {
        "SPEAKER_00", "SPEAKER_01", "SPEAKER_02",
    }


def test_diarize_returns_empty_list_when_no_speakers_found():
    annotation = _fake_annotation([])
    diarizer = _make_diarizer_with_mock_pipeline(
        pipeline_return_value=annotation,
    )

    segments = diarizer.diarize("audio.wav")

    assert segments == []


def test_diarize_raises_diarization_unavailable_on_pipeline_failure():
    diarizer = _make_diarizer_with_mock_pipeline(
        pipeline_side_effect=RuntimeError("audio decode failed"),
    )

    with pytest.raises(DiarizationUnavailableError):
        diarizer.diarize("audio.wav")


def test_constructor_wraps_pretrained_load_failure():
    with patch(
        "pyannote.audio.Pipeline.from_pretrained",
        side_effect=RuntimeError("HF auth failed"),
    ):
        with pytest.raises(DiarizationUnavailableError):
            SpeakerDiarizer(model_name="some/model")


def test_constructor_wraps_none_pipeline_result():
    with patch(
        "pyannote.audio.Pipeline.from_pretrained",
        return_value=None,
    ):
        with pytest.raises(DiarizationUnavailableError):
            SpeakerDiarizer(model_name="some/model")
