from scripts.report_stage_timings import fmt, render


def _rows():
    return [
        {"video_id": 20, "video_seconds": 100, "stage": "transcription", "seconds": 65.0},
        {"video_id": 20, "video_seconds": 100, "stage": "chapter", "seconds": 334.0},
        {"video_id": 20, "video_seconds": 100, "stage": "metadata", "seconds": 0.4},
        {"video_id": 19, "video_seconds": 187, "stage": "transcription", "seconds": 126.4},
    ]


def test_fmt():
    assert fmt(9.6) == "10s"
    assert fmt(334) == "5m 34s"


def test_render_orders_videos_and_stages_and_totals():
    table = render(_rows()).splitlines()

    assert table[0] == "| Stage | Video 19 (3m 07s long) | Video 20 (1m 40s long) |"
    assert [line.split("|")[1].strip() for line in table[2:5]] == ["metadata", "transcription", "chapter"]
    assert table[2] == "| metadata | - | 0s |"
    assert table[5] == "| **Total** | **2m 06s** | **6m 39s** |"


def test_render_reports_llm_share():
    last = render(_rows()).splitlines()[-1]

    assert last == "| LLM stages share | 0% | 84% |"


def test_render_without_rows():
    assert render([]).startswith("No completed stages")
