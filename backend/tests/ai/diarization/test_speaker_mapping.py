from ai.diarization.speaker_diarization import SpeakerSegment
from ai.diarization.speaker_mapping import SpeakerMapper


def test_map_returns_empty_list_for_empty_input():
    mapper = SpeakerMapper()

    assert mapper.map([]) == []


def test_map_produces_stable_generic_labels_by_first_appearance():
    segments = [
        SpeakerSegment(speaker="SPEAKER_03", start=0.0, end=1.0),
        SpeakerSegment(speaker="SPEAKER_01", start=1.0, end=2.0),
        SpeakerSegment(speaker="SPEAKER_03", start=2.0, end=3.0),
    ]

    mapper = SpeakerMapper()
    mapped = mapper.map(segments)

    # SPEAKER_03 appears first chronologically -> "Speaker 1",
    # regardless of its raw numeric suffix being higher than
    # SPEAKER_01's.
    assert [m.speaker for m in mapped] == [
        "Speaker 1", "Speaker 2", "Speaker 1",
    ]


def test_map_numbers_by_chronological_order_even_if_input_list_is_unordered():
    segments = [
        SpeakerSegment(speaker="SPEAKER_00", start=5.0, end=6.0),
        SpeakerSegment(speaker="SPEAKER_01", start=0.0, end=1.0),
    ]

    mapper = SpeakerMapper()
    mapped = mapper.map(segments)

    by_original_order = {m.start: m.speaker for m in mapped}
    assert by_original_order[0.0] == "Speaker 1"
    assert by_original_order[5.0] == "Speaker 2"


def test_map_preserves_start_and_end_timestamps():
    segments = [SpeakerSegment(speaker="SPEAKER_00", start=1.5, end=3.25)]

    mapper = SpeakerMapper()
    mapped = mapper.map(segments)

    assert mapped[0].start == 1.5
    assert mapped[0].end == 3.25


def test_map_never_produces_hardcoded_identity_labels():
    segments = [SpeakerSegment(speaker="SPEAKER_00", start=0.0, end=1.0)]

    mapper = SpeakerMapper()
    mapped = mapper.map(segments)

    forbidden_terms = {"teacher", "student", "host", "guest", "manager"}
    assert not any(
        term in mapped[0].speaker.lower() for term in forbidden_terms
    )
