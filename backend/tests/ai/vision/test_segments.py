import pytest

from ai.vision.describer import FrameDescription
from ai.vision.segments import (
    VisualSegment,
    cosine,
    guess_language,
    merge_frames,
    relation,
    segment_text,
    speech_around,
)


def _frame(time, text="", description="d"):
    return FrameDescription(time=time, path=f"{time}.jpg", text=text, description=description)


# ---- merge_frames ----

def test_same_slide_held_across_frames_becomes_one_segment():
    segments = merge_frames(
        [_frame(0, "Slide 1"), _frame(10, "slide 1!"), _frame(20, "Slide 2")],
        duration=30,
    )

    assert [(s.start_time, s.end_time, s.text) for s in segments] == [(0, 20, "Slide 1"), (20, 30, "Slide 2")]


def test_frames_without_text_never_merge():
    segments = merge_frames([_frame(0, "", "street"), _frame(10, "", "street")], duration=20)

    assert len(segments) == 2


def test_merge_orders_frames_and_ends_at_video_end():
    segments = merge_frames([_frame(15, "B"), _frame(0, "A")], duration=40)

    assert [(s.text, s.start_time, s.end_time) for s in segments] == [("A", 0, 15), ("B", 15, 40)]


# ---- text and speech relation ----

def test_segment_text_labels_what_is_shown():
    assert segment_text("Doanh thu +20%", "Một biểu đồ cột.") == "Chữ trên màn hình: Doanh thu +20%\nHình ảnh: Một biểu đồ cột."
    assert segment_text("", "Cảnh đường phố.") == "Hình ảnh: Cảnh đường phố."
    assert VisualSegment(0, 1, "f.jpg", "A", "").as_text() == "Chữ trên màn hình: A"


def test_speech_around_includes_padding():
    segment = VisualSegment(start_time=20, end_time=30, frame_path="f.jpg", text="", description="")
    speech = [
        {"start": 0, "end": 10, "text": "too early"},
        {"start": 12, "end": 16, "text": "lead-in"},
        {"start": 22, "end": 28, "text": "during"},
        {"start": 34, "end": 40, "text": "trailing"},
        {"start": 40, "end": 50, "text": "too late"},
    ]

    assert speech_around(segment, speech) == "lead-in during trailing"


def test_cosine_and_relation():
    assert cosine([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine([], []) == 0.0

    assert relation(0.8, 0.45) == "illustrates"
    assert relation(0.2, 0.45) == "unrelated"
    assert relation(None, 0.45) == "no-speech"


def test_guess_language():
    assert guess_language("Lạm phát tăng") == "vi"
    assert guess_language("Revenue grew") == "en"
    assert guess_language("") == "en"
