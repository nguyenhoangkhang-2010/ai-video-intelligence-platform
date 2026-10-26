import sys
import types
from unittest.mock import MagicMock

import pytest

from ai.evaluation.bertscore import BERTScoreEvaluator, BERTScoreUnavailableError


def test_constructing_evaluator_does_not_import_bert_score(monkeypatch):
    # __init__ must never trigger the heavy import/model load - only
    # an actual .score() call may.
    monkeypatch.delitem(sys.modules, "bert_score", raising=False)

    evaluator = BERTScoreEvaluator()

    assert evaluator._score_fn is None


def test_score_returns_empty_lists_for_empty_input_without_importing():
    evaluator = BERTScoreEvaluator()

    result = evaluator.score([], [])

    assert result == {"precision": [], "recall": [], "f1": []}
    assert evaluator._score_fn is None


def test_score_raises_value_error_on_mismatched_lengths():
    evaluator = BERTScoreEvaluator()

    with pytest.raises(ValueError):
        evaluator.score(["a", "b"], ["only one"])


def _install_fake_bert_score_module(monkeypatch, mock_score_fn):
    fake_module = types.ModuleType("bert_score")
    fake_module.score = mock_score_fn
    monkeypatch.setitem(sys.modules, "bert_score", fake_module)


def test_score_delegates_to_bert_score_and_converts_to_plain_floats(monkeypatch):
    mock_score_fn = MagicMock(
        return_value=([0.9], [0.8], [0.85]),
    )
    _install_fake_bert_score_module(monkeypatch, mock_score_fn)

    evaluator = BERTScoreEvaluator(lang="en")
    result = evaluator.score(["a generated sentence"], ["a reference sentence"])

    assert result == {"precision": [0.9], "recall": [0.8], "f1": [0.85]}
    mock_score_fn.assert_called_once_with(
        ["a generated sentence"], ["a reference sentence"], lang="en",
    )


def test_score_reuses_loaded_score_fn_across_calls(monkeypatch):
    mock_score_fn = MagicMock(return_value=([0.1], [0.1], [0.1]))
    _install_fake_bert_score_module(monkeypatch, mock_score_fn)

    evaluator = BERTScoreEvaluator(lang="en")
    evaluator.score(["a"], ["b"])
    evaluator.score(["c"], ["d"])

    assert mock_score_fn.call_count == 2
    assert evaluator._score_fn is mock_score_fn


def test_score_uses_model_name_over_lang_when_configured(monkeypatch):
    mock_score_fn = MagicMock(return_value=([0.5], [0.5], [0.5]))
    _install_fake_bert_score_module(monkeypatch, mock_score_fn)

    evaluator = BERTScoreEvaluator(model_name="roberta-large", lang="en")
    evaluator.score(["a"], ["b"])

    mock_score_fn.assert_called_once_with(["a"], ["b"], model_type="roberta-large")


def test_score_raises_clear_error_when_bert_score_not_importable(monkeypatch):
    monkeypatch.setitem(sys.modules, "bert_score", None)

    evaluator = BERTScoreEvaluator()

    with pytest.raises(BERTScoreUnavailableError):
        evaluator.score(["a"], ["b"])
