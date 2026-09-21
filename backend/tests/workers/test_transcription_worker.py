from unittest.mock import MagicMock

from app.workers.transcription_worker import TranscriptionWorker
from ai.speech.speech_result import SpeechResult, SpeechSegment


def test_process_delegates_to_speech_pipeline_and_flattens_result():
    speech_pipeline = MagicMock(name="speech_pipeline")
    speech_pipeline.process.return_value = SpeechResult(
        language="en",
        text="hello world",
        segments=[
            SpeechSegment(
                start=0.0, end=1.0, text="hello",
                speaker="Speaker 1",
                metadata={"no_speech_prob": 0.02},
            ),
            SpeechSegment(start=1.0, end=2.0, text="world"),
        ],
        language_probability=0.95,
    )

    worker = TranscriptionWorker(speech_pipeline=speech_pipeline)

    result = worker.process("video.mp4")

    speech_pipeline.process.assert_called_once_with("video.mp4")

    # Backward-compatible contract: app.pipelines.video_pipeline only
    # ever reads result["text"]/result["language"].
    assert result["language"] == "en"
    assert result["text"] == "hello world"

    # Segments now additionally carry speaker/metadata, purely
    # additive - existing "start"/"end"/"text" keys are unchanged.
    assert result["segments"][0] == {
        "start": 0.0, "end": 1.0, "text": "hello",
        "speaker": "Speaker 1", "no_speech_prob": 0.02,
    }
    assert result["segments"][1]["speaker"] is None


def test_process_returns_empty_segments_list_for_empty_speech_result():
    speech_pipeline = MagicMock(name="speech_pipeline")
    speech_pipeline.process.return_value = SpeechResult(
        language="en", text="", segments=[],
    )

    worker = TranscriptionWorker(speech_pipeline=speech_pipeline)

    result = worker.process("video.mp4")

    assert result == {"language": "en", "text": "", "segments": []}


def test_process_propagates_exceptions_from_speech_pipeline():
    speech_pipeline = MagicMock(name="speech_pipeline")
    speech_pipeline.process.side_effect = ValueError(
        "No speech detected in audio.",
    )

    worker = TranscriptionWorker(speech_pipeline=speech_pipeline)

    try:
        worker.process("video.mp4")
        assert False, "expected ValueError to propagate"
    except ValueError as error:
        assert str(error) == "No speech detected in audio."
