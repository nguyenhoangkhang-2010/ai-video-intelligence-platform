from unittest.mock import MagicMock

import pytest

from ai.llm.errors import LLMConnectionError
from app.workers.summary_worker import SummaryWorker


def _worker(summary_text="a real generated summary", model_name="qwen3:8b"):
    summarizer = MagicMock(name="summarizer")
    summarizer.summarize.return_value = summary_text
    summarizer.llm_client = MagicMock(model=model_name)

    worker = SummaryWorker.__new__(SummaryWorker)
    worker.summarizer = summarizer

    return worker, summarizer


def test_process_returns_the_exact_shape_video_pipeline_persists():
    """
    video_pipeline.py's summary_stage builds a SummaryCreate directly
    from this dict's keys (type/content/model_name) - a missing or
    renamed key here would be a silent persistence bug, not a loud
    one, since SummaryCreate's own fields are plain strings.
    """
    worker, summarizer = _worker("Nội dung chính: vượt qua nỗi sợ.", "qwen3:8b")

    result = worker.process(transcript="transcript text")

    assert result == {
        "type": "default",
        "content": "Nội dung chính: vượt qua nỗi sợ.",
        "model_name": "qwen3:8b",
    }
    summarizer.summarize.assert_called_once_with("transcript text")


def test_process_reports_the_real_configured_model_name_not_a_hardcoded_one():
    worker, _ = _worker(model_name="a-different-model:latest")

    result = worker.process(transcript="transcript text")

    assert result["model_name"] == "a-different-model:latest"


def test_process_propagates_llm_failure_without_persisting_a_fake_summary():
    """
    No summary dict is ever returned on failure - video_pipeline.py's
    summary_stage never reaches save_summary() if process() raises,
    so a failed generation can never be silently recorded as a real,
    successful summary.
    """
    worker, summarizer = _worker()
    summarizer.summarize.side_effect = LLMConnectionError("unreachable")

    with pytest.raises(LLMConnectionError):
        worker.process(transcript="transcript text")
