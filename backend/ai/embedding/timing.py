"""
Map retrieval chunks back to the time they were spoken.

Chunks are cut by word position over the whitespace-split transcript
(ai.embedding.chunking.TextChunker), and the transcript text is the
joined text of Whisper's timed segments. So a chunk's word range can be
located inside the segments by counting words: the chunk starts when
the segment holding its first word starts, and ends when the segment
holding its last word ends.

If text normalization changed the word count slightly (punctuation
spacing), the segment word counts no longer add up to the transcript's.
Positions are then scaled proportionally onto the segments' word
timeline - still accurate to within a segment or so, which is what a
"jump to this moment" link needs.
"""
from bisect import bisect_right
from collections.abc import Sequence


def chunk_time_range(
    segments: Sequence[dict],
    total_words: int,
    word_start: int | None,
    word_end: int | None,
) -> tuple[float, float] | None:
    """
    (start_seconds, end_seconds) for the chunk covering transcript
    words [word_start, word_end), or None when it can't be determined
    (no segments, no word span, empty range).
    """
    if not segments or word_start is None or word_end is None or word_end <= word_start:
        return None

    counts = [len(str(segment.get("text", "")).split()) for segment in segments]
    segment_words = sum(counts)
    if segment_words == 0 or total_words <= 0:
        return None

    # cumulative[i] = index of the first word of segment i.
    cumulative = []
    running = 0
    for count in counts:
        cumulative.append(running)
        running += count

    def to_segment_word(position: int) -> int:
        if total_words == segment_words:
            return position
        scaled = round(position * segment_words / total_words)
        return min(max(scaled, 0), segment_words - 1)

    first = to_segment_word(word_start)
    last = to_segment_word(word_end - 1)

    first_segment = max(bisect_right(cumulative, first) - 1, 0)
    last_segment = max(bisect_right(cumulative, last) - 1, first_segment)
    last_segment = min(last_segment, len(segments) - 1)

    start = float(segments[first_segment]["start"])
    end = float(segments[last_segment]["end"])
    if end < start:
        end = start
    return start, end
