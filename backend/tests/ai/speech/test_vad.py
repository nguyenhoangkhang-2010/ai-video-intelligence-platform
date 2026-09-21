from unittest.mock import patch

from ai.speech.vad import VoiceActivityDetector


def test_detect_speech_segments_converts_sample_timestamps_to_seconds():
    with (
        patch("ai.speech.vad.decode_audio") as mock_decode,
        patch("ai.speech.vad.get_speech_timestamps") as mock_get_ts,
    ):
        mock_get_ts.return_value = [
            {"start": 16000, "end": 32000},   # 1.0s -> 2.0s
            {"start": 48000, "end": 64000},   # 3.0s -> 4.0s
        ]

        vad = VoiceActivityDetector()
        segments = vad.detect_speech_segments("audio.wav")

    mock_decode.assert_called_once_with(
        "audio.wav", sampling_rate=16000,
    )
    mock_get_ts.assert_called_once()
    assert segments == [(1.0, 2.0), (3.0, 4.0)]


def test_has_speech_true_when_segments_present():
    with (
        patch("ai.speech.vad.decode_audio"),
        patch(
            "ai.speech.vad.get_speech_timestamps",
            return_value=[{"start": 0, "end": 16000}],
        ),
    ):
        vad = VoiceActivityDetector()
        assert vad.has_speech("audio.wav") is True


def test_has_speech_false_when_no_speech_segments():
    with (
        patch("ai.speech.vad.decode_audio"),
        patch("ai.speech.vad.get_speech_timestamps", return_value=[]),
    ):
        vad = VoiceActivityDetector()
        assert vad.has_speech("audio.wav") is False


def test_constructor_uses_explicit_options_over_settings_defaults():
    with patch("ai.speech.vad.VadOptions") as mock_vad_options:
        VoiceActivityDetector(threshold=0.9, min_silence_duration_ms=500)

    mock_vad_options.assert_called_once_with(
        threshold=0.9, min_silence_duration_ms=500,
    )
