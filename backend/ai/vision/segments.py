"""
From described frames to visual segments, and how they relate to speech.

A segment is a span of video showing the same thing: consecutive
frames with the same on-screen text (a slide held for a minute) merge
into one. Each segment ends where the next begins (or at the end of
the video).

Speech and visuals are kept as two labelled tracks, never forced into
one. A video can be a talk whose slides match every word, or a
voice-over over unrelated b-roll, or have no speech at all; the
relation is measured (cosine similarity between what was shown and
what was said around it) instead of assumed.
"""
import re
import unicodedata
from dataclasses import dataclass

from ai.vision.describer import FrameDescription


# Speech this many seconds either side of a segment counts as "said
# while it was on screen" - narration often leads or trails the cut.
SPEECH_WINDOW_PADDING = 5.0

_NON_WORD = re.compile(r"[^\w]+", flags=re.UNICODE)
_VIETNAMESE = re.compile(r"[ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]", re.IGNORECASE)


@dataclass
class VisualSegment:
    start_time: float
    end_time: float
    frame_path: str
    text: str
    description: str
    speech_similarity: float | None = None

    def as_text(self) -> str:
        return segment_text(self.text, self.description)


def segment_text(on_screen_text: str, description: str) -> str:
    """How a visual segment reads to search, RAG and the LLM stages."""
    parts = []
    if on_screen_text:
        parts.append(f"Chữ trên màn hình: {on_screen_text}")
    if description:
        parts.append(f"Hình ảnh: {description}")
    return "\n".join(parts)


def _same_text(a: str, b: str) -> bool:
    normalize = lambda value: _NON_WORD.sub(" ", unicodedata.normalize("NFC", value).lower()).strip()  # noqa: E731
    return bool(a or b) and normalize(a) == normalize(b)


def merge_frames(frames: list[FrameDescription], duration: float) -> list[VisualSegment]:
    """
    Consecutive frames whose on-screen text is the same become one
    segment (the first frame's picture and description are kept).
    Frames with no text never merge - two text-free shots are not
    known to be the same shot.
    """
    ordered = sorted(frames, key=lambda frame: frame.time)
    segments: list[VisualSegment] = []
    for frame in ordered:
        if segments and frame.text and _same_text(segments[-1].text, frame.text):
            continue
        segments.append(VisualSegment(frame.time, frame.time, frame.path, frame.text, frame.description))

    for current, following in zip(segments, segments[1:]):
        current.end_time = following.start_time
    if segments:
        segments[-1].end_time = max(segments[-1].start_time, float(duration))
    return segments


def speech_around(segment: VisualSegment, speech_segments: list[dict]) -> str:
    """Words spoken while `segment` was on screen (with padding)."""
    start = segment.start_time - SPEECH_WINDOW_PADDING
    end = segment.end_time + SPEECH_WINDOW_PADDING
    return " ".join(
        str(item.get("text", "")).strip()
        for item in speech_segments
        if item.get("end", 0) >= start and item.get("start", 0) <= end
    ).strip()


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def relation(similarity: float | None, threshold: float) -> str:
    """'illustrates' the speech, 'unrelated' to it (b-roll), or 'no-speech'."""
    if similarity is None:
        return "no-speech"
    return "illustrates" if similarity >= threshold else "unrelated"


def guess_language(text: str) -> str:
    """'vi' if the text has Vietnamese letters, else 'en' (visual-only transcripts)."""
    return "vi" if _VIETNAMESE.search(text or "") else "en"
