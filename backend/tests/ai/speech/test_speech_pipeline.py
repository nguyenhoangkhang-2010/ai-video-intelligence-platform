from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai.diarization.speaker_diarization import SpeakerSegment
from ai.speech.language_detector import DetectedLanguage
from ai.speech.pipeline import NoSpeechDetectedError, SpeechPipeline


def _make_pipeline(diarization_enabled=False, diarizer_factory=None):
    audio_extractor = MagicMock(name="audio_extractor")
    vad = MagicMock(name="vad")
    vad.detect_speech_segments.return_value = [(0.0, 5.0)]
    transcriber = MagicMock(name="transcriber")
    language_detector = MagicMock(name="language_detector")
    speaker_mapper = MagicMock(name="speaker_mapper")

    pipeline = SpeechPipeline(
        audio_extractor=audio_extractor,
        vad=vad,
        transcriber=transcriber,
        language_detector=language_detector,
        diarizer_factory=(
            diarizer_factory or MagicMock(name="diarizer_factory")
        ),
        speaker_mapper=speaker_mapper,
        diarization_enabled=diarization_enabled,
    )

    return (
        pipeline, audio_extractor, vad, transcriber,
        language_detector, speaker_mapper,
    )


def _default_transcribe_result():
    return {
        "language": "en",
        "language_probability": 0.9,
        "text": "hello world",
        "segments": [{"start": 0.0, "end": 1.0, "text": "hello world"}],
        "duration": 5.0,
    }


def test_process_extracts_audio_transcribes_and_returns_speech_result():
    pipeline, audio_extractor, vad, transcriber, language_detector, _ = (
        _make_pipeline()
    )

    transcriber.transcribe.return_value = _default_transcribe_result()
    language_detector.from_whisper_result.return_value = DetectedLanguage(
        code="en", confidence=0.9, source="whisper",
    )

    result = pipeline.process("video.mp4")

    audio_extractor.extract.assert_called_once()
    call_kwargs = audio_extractor.extract.call_args.kwargs
    assert call_kwargs["video_path"] == "video.mp4"
    assert call_kwargs["output_path"].endswith("audio.wav")

    vad.detect_speech_segments.assert_called_once()
    transcriber.transcribe.assert_called_once()

    assert result.language == "en"
    assert result.text == "hello world"
    assert len(result.segments) == 1
    assert result.segments[0].text == "hello world"
    assert result.metadata["speech_ranges"] == [(0.0, 5.0)]
    assert result.metadata["diarization_enabled"] is False


def test_process_raises_no_speech_detected_when_asr_text_is_empty():
    pipeline, audio_extractor, vad, transcriber, language_detector, _ = (
        _make_pipeline()
    )

    transcriber.transcribe.return_value = {
        "language": None, "language_probability": None,
        "text": "   ", "segments": [], "duration": 2.0,
    }

    with pytest.raises(NoSpeechDetectedError):
        pipeline.process("video.mp4")

    language_detector.from_whisper_result.assert_not_called()


def test_process_skips_diarization_when_disabled():
    diarizer_factory = MagicMock(name="diarizer_factory")
    pipeline, audio_extractor, vad, transcriber, language_detector, speaker_mapper = (
        _make_pipeline(
            diarization_enabled=False, diarizer_factory=diarizer_factory,
        )
    )

    transcriber.transcribe.return_value = _default_transcribe_result()
    language_detector.from_whisper_result.return_value = DetectedLanguage(
        "en", 0.9, "whisper",
    )

    result = pipeline.process("video.mp4")

    diarizer_factory.assert_not_called()
    speaker_mapper.map.assert_not_called()
    assert all(segment.speaker is None for segment in result.segments)


def test_process_runs_diarization_and_mapping_when_enabled():
    fake_diarizer = MagicMock(name="diarizer")
    fake_diarizer.diarize.return_value = [
        SpeakerSegment(speaker="SPEAKER_00", start=0.0, end=1.0),
    ]
    diarizer_factory = MagicMock(return_value=fake_diarizer)

    pipeline, audio_extractor, vad, transcriber, language_detector, speaker_mapper = (
        _make_pipeline(
            diarization_enabled=True, diarizer_factory=diarizer_factory,
        )
    )
    speaker_mapper.map.return_value = [
        SpeakerSegment(speaker="Speaker 1", start=0.0, end=1.0),
    ]

    transcriber.transcribe.return_value = _default_transcribe_result()
    language_detector.from_whisper_result.return_value = DetectedLanguage(
        "en", 0.9, "whisper",
    )

    result = pipeline.process("video.mp4")

    diarizer_factory.assert_called_once()
    fake_diarizer.diarize.assert_called_once()
    speaker_mapper.map.assert_called_once()
    assert result.segments[0].speaker == "Speaker 1"


def test_diarizer_is_constructed_lazily_and_only_once():
    fake_diarizer = MagicMock(name="diarizer")
    fake_diarizer.diarize.return_value = []
    diarizer_factory = MagicMock(return_value=fake_diarizer)

    pipeline, audio_extractor, vad, transcriber, language_detector, speaker_mapper = (
        _make_pipeline(
            diarization_enabled=True, diarizer_factory=diarizer_factory,
        )
    )
    speaker_mapper.map.return_value = []

    transcriber.transcribe.return_value = _default_transcribe_result()
    language_detector.from_whisper_result.return_value = DetectedLanguage(
        "en", 0.9, "whisper",
    )

    pipeline.process("video1.mp4")
    pipeline.process("video2.mp4")

    # Loaded once, reused across both process() calls - not reloaded
    # per request.
    diarizer_factory.assert_called_once()


def test_process_cleans_up_the_temporary_audio_directory():
    pipeline, audio_extractor, vad, transcriber, language_detector, _ = (
        _make_pipeline()
    )

    captured_paths = []

    def fake_extract(video_path, output_path):
        captured_paths.append(output_path)
        return output_path

    audio_extractor.extract.side_effect = fake_extract

    transcriber.transcribe.return_value = _default_transcribe_result()
    language_detector.from_whisper_result.return_value = DetectedLanguage(
        "en", 0.9, "whisper",
    )

    pipeline.process("video.mp4")

    assert len(captured_paths) == 1
    temp_dir = Path(captured_paths[0]).parent
    assert not temp_dir.exists()
