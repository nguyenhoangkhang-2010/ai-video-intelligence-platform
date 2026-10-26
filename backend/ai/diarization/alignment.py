import logging

from ai.diarization.speaker_diarization import SpeakerSegment
from ai.speech.speech_result import SpeechSegment


logger = logging.getLogger(__name__)


def align_segments_with_speakers(
    asr_segments: list[dict],
    speaker_segments: list[SpeakerSegment],
) -> list[SpeechSegment]:
    """
    Attach a speaker label to each ASR segment by maximum time
    overlap with the (already speaker-mapped) diarization segments.

    Deterministic, documented behavior:
    - Full overlap (a diarization segment fully contains the ASR
      segment, or vice versa): the containing/contained speaker wins.
    - Partial overlap: whichever speaker segment shares the most
      overlapping time with the ASR segment wins.
    - No overlap at all: speaker is None - never guessed.
    - Adjacent segments (touching at a single point, zero-duration
      overlap) are treated as no overlap.
    - Ties (two speaker segments with exactly equal overlap): the
      first one encountered in `speaker_segments` order wins (in
      practice, SpeakerDiarizer.diarize() already returns
      chronologically sorted segments, so this is the earlier one).

    The ASR segment's own start/end are always preserved exactly as
    given - never clamped/rewritten to a diarization segment's
    boundaries, so no original timestamp information is lost.
    Any extra ASR segment metadata (e.g. no_speech_prob) is carried
    through into SpeechSegment.metadata.

    Works for any number of speakers (0, 1, or many) - nothing here
    assumes or hardcodes a speaker count.
    """

    aligned_segments = []

    for asr_segment in asr_segments:
        start = asr_segment["start"]
        end = asr_segment["end"]
        text = asr_segment.get("text", "")

        speaker = _best_matching_speaker(
            start,
            end,
            speaker_segments,
        )

        metadata = {
            key: value
            for key, value in asr_segment.items()
            if key not in {"start", "end", "text"}
        }

        aligned_segments.append(
            SpeechSegment(
                start=start,
                end=end,
                text=text,
                speaker=speaker,
                metadata=metadata,
            )
        )

    return aligned_segments


def _best_matching_speaker(
    start: float,
    end: float,
    speaker_segments: list[SpeakerSegment],
) -> str | None:
    best_speaker = None
    best_overlap = 0.0

    for speaker_segment in speaker_segments:
        overlap = (
            min(end, speaker_segment.end)
            - max(start, speaker_segment.start)
        )

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker_segment.speaker

    return best_speaker
