from ai.speech.post_processing import post_process_speech_result
from ai.speech.speech_result import SpeechResult, SpeechSegment


def test_post_process_speech_result_normalizes_whitespace_in_each_segment():
    result = SpeechResult(
        language="en",
        text="",
        segments=[
            SpeechSegment(start=0.0, end=1.0, text="  Hello    world  "),
        ],
    )

    processed = post_process_speech_result(result)

    assert processed.segments[0].text == "Hello world"
    assert processed.text == "Hello world"


def test_post_process_speech_result_drops_empty_segments():
    result = SpeechResult(
        language="en",
        text="",
        segments=[
            SpeechSegment(start=0.0, end=1.0, text="Hello"),
            SpeechSegment(start=1.0, end=2.0, text="   "),
            SpeechSegment(start=2.0, end=3.0, text="world"),
        ],
    )

    processed = post_process_speech_result(result)

    assert [s.text for s in processed.segments] == ["Hello", "world"]


def test_post_process_speech_result_drops_invalid_timestamp_segments():
    result = SpeechResult(
        language="en",
        text="",
        segments=[
            SpeechSegment(start=0.0, end=1.0, text="valid"),
            SpeechSegment(start=5.0, end=5.0, text="zero duration"),
            SpeechSegment(start=6.0, end=4.0, text="end before start"),
        ],
    )

    processed = post_process_speech_result(result)

    assert [s.text for s in processed.segments] == ["valid"]


def test_post_process_speech_result_orders_segments_by_start_time():
    result = SpeechResult(
        language="en",
        text="",
        segments=[
            SpeechSegment(start=5.0, end=6.0, text="second"),
            SpeechSegment(start=0.0, end=1.0, text="first"),
        ],
    )

    processed = post_process_speech_result(result)

    assert [s.text for s in processed.segments] == ["first", "second"]


def test_post_process_speech_result_preserves_speaker_and_metadata():
    result = SpeechResult(
        language="en",
        text="",
        segments=[
            SpeechSegment(
                start=0.0, end=1.0, text="Hello",
                speaker="Speaker 1",
                metadata={"no_speech_prob": 0.02},
            ),
        ],
    )

    processed = post_process_speech_result(result)

    assert processed.segments[0].speaker == "Speaker 1"
    assert processed.segments[0].metadata == {"no_speech_prob": 0.02}


def test_post_process_speech_result_preserves_language_fields():
    result = SpeechResult(
        language="vi",
        text="",
        segments=[SpeechSegment(start=0.0, end=1.0, text="xin chao")],
        language_probability=0.87,
        metadata={"duration": 10.0},
    )

    processed = post_process_speech_result(result)

    assert processed.language == "vi"
    assert processed.language_probability == 0.87
    assert processed.metadata == {"duration": 10.0}
