from ai.chapter_detection.chapter_postprocess import ChapterPostProcessor
from ai.chapter_detection.chapter_result import Chapter


def _chapter(id, title, start, end, indices=None):
    return Chapter(
        id=id,
        title=title,
        topics=(),
        segment_indices=indices if indices is not None else (0,),
        start=start,
        end=end,
    )


def test_process_returns_empty_for_empty_input():
    processor = ChapterPostProcessor()

    assert processor.process([]) == []


def test_process_drops_chapters_with_missing_timestamps():
    chapters = [
        _chapter("c0", "Valid", 0.0, 20.0),
        _chapter("c1", "No timestamps", None, None),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=5.0)
    result = processor.process(chapters)

    assert [c.id for c in result] == ["c0"]


def test_process_drops_chapters_with_invalid_ranges():
    chapters = [
        _chapter("c0", "Valid", 0.0, 20.0),
        _chapter("c1", "Zero duration", 10.0, 10.0),
        _chapter("c2", "End before start", 10.0, 5.0),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=5.0)
    result = processor.process(chapters)

    assert [c.id for c in result] == ["c0"]


def test_process_drops_chapters_with_no_segment_references():
    chapters = [
        _chapter("c0", "Valid", 0.0, 20.0, indices=(0, 1)),
        _chapter("c1", "Empty", 20.0, 30.0, indices=()),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=5.0)
    result = processor.process(chapters)

    assert [c.id for c in result] == ["c0"]


def test_process_orders_chapters_chronologically():
    chapters = [
        _chapter("c1", "Second", 30.0, 50.0),
        _chapter("c0", "First", 0.0, 20.0),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=5.0)
    result = processor.process(chapters)

    assert [c.id for c in result] == ["c0", "c1"]


def test_process_merges_chapters_shorter_than_minimum_duration():
    chapters = [
        _chapter("c0", "First", 0.0, 5.0, indices=(0,)),
        _chapter("c1", "Tiny", 5.0, 7.0, indices=(1,)),  # only 2s long
        _chapter("c2", "Third", 7.0, 30.0, indices=(2,)),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=10.0)
    result = processor.process(chapters)

    # "Tiny" (< 10s) merges forward into the chapter that follows it
    # in the merge pass (source segment references preserved, not
    # dropped).
    assert len(result) < 3
    all_indices = {
        index
        for chapter in result
        for index in chapter.segment_indices
    }
    assert all_indices == {0, 1, 2}


def test_process_merges_consecutive_duplicate_titles():
    chapters = [
        _chapter("c0", "Introduction", 0.0, 20.0, indices=(0,)),
        _chapter("c1", "Introduction", 20.0, 40.0, indices=(1,)),
        _chapter("c2", "Main Topic", 40.0, 60.0, indices=(2,)),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=1.0)
    result = processor.process(chapters)

    assert len(result) == 2
    assert result[0].title == "Introduction"
    assert result[0].segment_indices == (0, 1)


def test_process_normalizes_whitespace_in_titles():
    chapters = [_chapter("c0", "  Weird   Spacing  ", 0.0, 20.0)]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=1.0)
    result = processor.process(chapters)

    assert result[0].title == "Weird Spacing"


def test_process_clamps_scores_into_valid_range():
    chapter = Chapter(
        id="c0", title="T", topics=(), segment_indices=(0,),
        start=0.0, end=20.0, score=1.5,
    )

    processor = ChapterPostProcessor(min_chapter_duration_seconds=1.0)
    result = processor.process([chapter])

    assert result[0].score == 1.0


def test_process_is_deterministic_given_the_same_input():
    chapters = [
        _chapter("c1", "Second", 30.0, 50.0, indices=(1,)),
        _chapter("c0", "First", 0.0, 20.0, indices=(0,)),
    ]

    processor = ChapterPostProcessor(min_chapter_duration_seconds=1.0)

    first_run = [c.id for c in processor.process(list(chapters))]
    second_run = [c.id for c in processor.process(list(chapters))]

    assert first_run == second_run
