"""
Optional RAGAS adapter for RAG evaluation.

`ragas` is listed as a project dependency, but in this project's
current environment importing it raises a transitive dependency error
(`langchain_community.chat_models.vertexai` is missing) - so it cannot
be safely imported at module level without risking breaking anything
that merely imports this module (or the wider evaluation package). To
keep the evaluation package - and the rest of the application - usable
regardless of ragas's install/health status in any given environment,
the import is deferred entirely into `RagasEvaluator._import_ragas()`,
and any failure raises a clear, typed error instead of silently
returning a fake score.

This module is never imported by production RAG code
(app.pipelines.rag_pipeline) - it is purely an optional, standalone,
evaluation-time adapter. When ragas is unavailable/broken, use
ai.evaluation.rag_eval's deterministic or LLM-judge evaluators
instead - they cover the same three conceptual metrics without this
dependency.
"""
import logging

from ai.evaluation.models import RAGEvaluationCase

logger = logging.getLogger(__name__)

DEFAULT_METRIC_NAMES = ("faithfulness", "answer_relevancy", "context_relevancy")


class RagasUnavailableError(RuntimeError):
    """Raised when the `ragas` package cannot be imported/used."""


class RagasEvaluator:
    """
    Thin adapter around the `ragas` library's RAG metrics, for
    environments where a fully-installed, working ragas stack is
    available.

    Deliberately does not expand ragas's API surface beyond what this
    project's RAGEvaluationCase already exposes - if ragas needs more
    inputs than a case provides, that surfaces as a normal Python
    error from ragas itself rather than being silently guessed at
    here.
    """

    def __init__(self, metric_names: list[str] | None = None):
        self.metric_names = list(metric_names) if metric_names else list(
            DEFAULT_METRIC_NAMES,
        )

    @staticmethod
    def _import_ragas():
        """
        Isolated in its own method (rather than inlined into
        evaluate()) purely so tests can force the "ragas is
        unavailable" path deterministically, without depending on
        whether ragas actually is broken in the environment the tests
        happen to run in.
        """
        from datasets import Dataset
        from ragas import evaluate as ragas_evaluate
        from ragas.metrics import answer_relevancy, context_relevancy, faithfulness

        return Dataset, ragas_evaluate, {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_relevancy": context_relevancy,
        }

    def evaluate(self, cases: list[RAGEvaluationCase]) -> dict:
        """
        Run ragas's own evaluate() over `cases` and return its result
        as a plain dict. Raises RagasUnavailableError (never a fake
        result) if ragas cannot be imported/used in this environment.
        """
        try:
            dataset_cls, ragas_evaluate, available_metrics = self._import_ragas()
        except Exception as exc:
            raise RagasUnavailableError(
                "ragas is not usable in this environment (import "
                f"failed: {exc!r}). Install/repair the 'ragas' "
                "dependency stack to enable this optional evaluator, "
                "or use ai.evaluation.rag_eval's deterministic/"
                "LLM-judge evaluators instead."
            ) from exc

        selected_metrics = [
            available_metrics[name]
            for name in self.metric_names
            if name in available_metrics
        ]

        dataset = dataset_cls.from_dict({
            "question": [case.question for case in cases],
            "answer": [case.answer for case in cases],
            "contexts": [list(case.retrieved_contexts) for case in cases],
        })

        logger.info(
            "Running ragas evaluation over %s case(s) with metric(s): %s",
            len(cases), self.metric_names,
        )

        result = ragas_evaluate(dataset, metrics=selected_metrics)

        return dict(result)
