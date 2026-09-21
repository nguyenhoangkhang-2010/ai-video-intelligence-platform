from unittest.mock import MagicMock

import pytest

from ai.evaluation.models import RAGEvaluationCase
from ai.evaluation.ragas_eval import RagasEvaluator, RagasUnavailableError


def test_evaluate_raises_clear_error_when_ragas_unavailable(monkeypatch):
    # Forces the "ragas unavailable" path deterministically, without
    # depending on whether ragas actually imports in this environment
    # - no network call happens on either path since the failure is
    # injected before any real ragas/network usage.
    monkeypatch.setattr(
        RagasEvaluator, "_import_ragas",
        staticmethod(lambda: (_ for _ in ()).throw(ImportError("boom"))),
    )
    evaluator = RagasEvaluator()

    with pytest.raises(RagasUnavailableError):
        evaluator.evaluate([
            RAGEvaluationCase(question="q", answer="a", retrieved_contexts=("c",)),
        ])


def test_evaluate_delegates_to_ragas_when_import_succeeds(monkeypatch):
    fake_dataset_cls = MagicMock()
    fake_ragas_evaluate = MagicMock(return_value={"faithfulness": 0.9})
    fake_faithfulness = object()
    fake_answer_relevancy = object()
    fake_context_relevancy = object()

    monkeypatch.setattr(
        RagasEvaluator, "_import_ragas",
        staticmethod(lambda: (
            fake_dataset_cls, fake_ragas_evaluate,
            {
                "faithfulness": fake_faithfulness,
                "answer_relevancy": fake_answer_relevancy,
                "context_relevancy": fake_context_relevancy,
            },
        )),
    )

    evaluator = RagasEvaluator(metric_names=["faithfulness"])
    cases = [
        RAGEvaluationCase(
            question="what is X?", answer="X is Y",
            retrieved_contexts=("X is Y according to the source",),
        ),
    ]

    result = evaluator.evaluate(cases)

    assert result == {"faithfulness": 0.9}
    fake_dataset_cls.from_dict.assert_called_once_with({
        "question": ["what is X?"],
        "answer": ["X is Y"],
        "contexts": [["X is Y according to the source"]],
    })
    fake_ragas_evaluate.assert_called_once()
    called_metrics = fake_ragas_evaluate.call_args.kwargs["metrics"]
    assert called_metrics == [fake_faithfulness]


def test_default_metric_names_cover_all_three_conceptual_metrics():
    evaluator = RagasEvaluator()

    assert set(evaluator.metric_names) == {
        "faithfulness", "answer_relevancy", "context_relevancy",
    }
