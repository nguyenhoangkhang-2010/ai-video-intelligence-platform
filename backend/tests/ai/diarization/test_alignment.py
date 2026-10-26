from ai.diarization.alignment import align_segments_with_speakers
from ai.diarization.speaker_diarization import SpeakerSegment


def test_full_overlap_assigns_the_containing_speaker():
    asr_segments = [{"start": 1.0, "end": 2.0, "text": "hello"}]
    speaker_segments = [
        SpeakerSegment(speaker="Speaker 1", start=0.0, end=5.0),
    ]

    aligned = align_segments_with_speakers(asr_segments, speaker_segments)

    assert aligned[0].speaker == "Speaker 1"
    # Original ASR timestamps are preserved exactly, not clamped to
    # the (wider) speaker segment's bounds.
    assert aligned[0].start == 1.0
    assert aligned[0].end == 2.0


def test_partial_overlap_picks_the_speaker_with_more_overlap_time():
    asr_segments = [{"start": 0.0, "end": 10.0, "text": "hello"}]
    speaker_segments = [
        SpeakerSegment(speaker="Speaker 1", start=-5.0, end=3.0),  # 3s overlap
        SpeakerSegment(speaker="Speaker 2", start=2.0, end=20.0),  # 8s overlap
    ]

    aligned = align_segments_with_speakers(asr_segments, speaker_segments)

    assert aligned[0].speaker == "Speaker 2"


def test_no_overlap_leaves_speaker_none():
    asr_segments = [{"start": 0.0, "end": 1.0, "text": "hello"}]
    speaker_segments = [
        SpeakerSegment(speaker="Speaker 1", start=10.0, end=11.0),
    ]

    aligned = align_segments_with_speakers(asr_segments, speaker_segments)

    assert aligned[0].speaker is None


def test_adjacent_touching_segments_are_treated_as_no_overlap():
    asr_segments = [{"start": 0.0, "end": 1.0, "text": "hello"}]
    speaker_segments = [
        # Touches exactly at t=1.0 but does not overlap.
        SpeakerSegment(speaker="Speaker 1", start=1.0, end=2.0),
    ]

    aligned = align_segments_with_speakers(asr_segments, speaker_segments)

    assert aligned[0].speaker is None


def test_no_speaker_segments_at_all_leaves_every_segment_unattributed():
    asr_segments = [
        {"start": 0.0, "end": 1.0, "text": "hello"},
        {"start": 1.0, "end": 2.0, "text": "world"},
    ]

    aligned = align_segments_with_speakers(asr_segments, [])

    assert all(segment.speaker is None for segment in aligned)


def test_works_with_more_than_two_speakers():
    asr_segments = [
        {"start": 0.0, "end": 1.0, "text": "a"},
        {"start": 1.0, "end": 2.0, "text": "b"},
        {"start": 2.0, "end": 3.0, "text": "c"},
    ]
    speaker_segments = [
        SpeakerSegment(speaker="Speaker 1", start=0.0, end=1.0),
        SpeakerSegment(speaker="Speaker 2", start=1.0, end=2.0),
        SpeakerSegment(speaker="Speaker 3", start=2.0, end=3.0),
    ]

    aligned = align_segments_with_speakers(asr_segments, speaker_segments)

    assert [s.speaker for s in aligned] == [
        "Speaker 1", "Speaker 2", "Speaker 3",
    ]


def test_original_asr_text_and_extra_metadata_are_preserved():
    asr_segments = [
        {
            "start": 0.0, "end": 1.0, "text": "hello",
            "no_speech_prob": 0.02,
        },
    ]

    aligned = align_segments_with_speakers(asr_segments, [])

    assert aligned[0].text == "hello"
    assert aligned[0].metadata == {"no_speech_prob": 0.02}
