from unittest.mock import MagicMock, patch

import pytest

from ai.speech.faster_whisper import FasterWhisperTranscriber
from app.config.settings import settings


def _fake_segment(start, end, text, no_speech_prob=0.01):
    segment = MagicMock()
    segment.start = start
    segment.end = end
    segment.text = text
    segment.no_speech_prob = no_speech_prob
    return segment


def _fake_info(language="en", language_probability=0.98, duration=12.5):
    info = MagicMock()
    info.language = language
    info.language_probability = language_probability
    info.duration = duration
    return info


def test_transcribe_maps_segments_and_info_into_result_dict():
    mock_model = MagicMock()
    mock_model.transcribe.return_value = (
        [
            _fake_segment(0.0, 1.5, "Hello"),
            _fake_segment(1.5, 3.0, "world"),
        ],
        _fake_info(),
    )

    with patch(
        "ai.speech.faster_whisper.WhisperModel", return_value=mock_model,
    ):
        transcriber = FasterWhisperTranscriber(
            model_size="base", device="cpu", compute_type="int8",
        )
        result = transcriber.transcribe("audio.wav")

    assert result["language"] == "en"
    assert result["language_probability"] == 0.98
    assert result["duration"] == 12.5
    assert result["text"] == "Hello world"
    assert result["segments"] == [
        {"start": 0.0, "end": 1.5, "text": "Hello", "no_speech_prob": 0.01},
        {"start": 1.5, "end": 3.0, "text": "world", "no_speech_prob": 0.01},
    ]


def test_transcribe_passes_configured_beam_size():
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([], _fake_info())

    with patch(
        "ai.speech.faster_whisper.WhisperModel", return_value=mock_model,
    ):
        transcriber = FasterWhisperTranscriber(beam_size=8)
        transcriber.transcribe("audio.wav")

    mock_model.transcribe.assert_called_once_with(
        "audio.wav", beam_size=8,
    )


def test_constructor_falls_back_to_cpu_when_cuda_device_fails():
    cpu_model = MagicMock(name="cpu_model")

    def fake_whisper_model(model_size, device, compute_type):
        if device == "cuda":
            raise RuntimeError("no CUDA runtime available")
        return cpu_model

    with patch(
        "ai.speech.faster_whisper.WhisperModel",
        side_effect=fake_whisper_model,
    ):
        transcriber = FasterWhisperTranscriber(device="cuda")

    assert transcriber.device == "cpu"
    assert transcriber.model is cpu_model


def test_constructor_reraises_when_cpu_device_itself_fails():
    with patch(
        "ai.speech.faster_whisper.WhisperModel",
        side_effect=RuntimeError("model files corrupted"),
    ):
        with pytest.raises(RuntimeError, match="model files corrupted"):
            FasterWhisperTranscriber(device="cpu")


def test_constructor_uses_settings_defaults_when_not_explicitly_given():
    # Read the real resolved settings rather than hardcoding "base"/
    # "cpu"/"int8": this environment's own .env may override the
    # pydantic class defaults, and the point of centralizing config
    # is that FasterWhisperTranscriber picks up whatever settings
    # actually resolves to.
    with patch(
        "ai.speech.faster_whisper.WhisperModel",
    ) as mock_whisper_model_class:
        FasterWhisperTranscriber()

    mock_whisper_model_class.assert_called_once_with(
        settings.speech.whisper_model,
        device=settings.speech.device,
        compute_type=settings.speech.compute_type,
    )
