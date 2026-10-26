from unittest.mock import MagicMock

from ai.evaluation.models import RAGEvaluationCase
from ai.evaluation.rag_eval import (
    DeterministicAnswerRelevance,
    DeterministicContextRelevance,
    DeterministicFaithfulness,
    LLMJudgeAnswerRelevance,
    LLMJudgeContextRelevance,
    LLMJudgeFaithfulness,
)


# ---- Deterministic metrics ----

def test_deterministic_faithfulness_is_one_when_answer_fully_grounded():
    case = RAGEvaluationCase(
        question="q", answer="the cat sat on the mat",
        retrieved_contexts=("the cat sat on the mat",),
    )

    result = DeterministicFaithfulness().compute(case)

    assert result.value == 1.0
    assert result.details["kind"] == "deterministic"


def test_deterministic_faithfulness_is_zero_when_answer_shares_no_vocabulary():
    case = RAGEvaluationCase(
        question="q", answer="completely unrelated words here",
        retrieved_contexts=("something else entirely different",),
    )

    result = DeterministicFaithfulness().compute(case)

    assert result.value == 0.0


def test_deterministic_faithfulness_handles_empty_contexts():
    case = RAGEvaluationCase(question="q", answer="an answer", retrieved_contexts=())

    result = DeterministicFaithfulness().compute(case)

    assert result.value == 0.0


def test_deterministic_answer_relevance_measures_question_answer_overlap():
    case = RAGEvaluationCase(
        question="what is the capital of France",
        answer="the capital of France is Paris",
    )

    result = DeterministicAnswerRelevance().compute(case)

    assert 0.0 < result.value <= 1.0


def test_deterministic_context_relevance_measures_question_context_overlap():
    case = RAGEvaluationCase(
        question="what is the capital of France",
        answer="Paris",
        retrieved_contexts=("Paris is the capital of France.",),
    )

    result = DeterministicContextRelevance().compute(case)

    assert 0.0 < result.value <= 1.0


def test_deterministic_metrics_handle_empty_question_and_answer():
    case = RAGEvaluationCase(question="", answer="", retrieved_contexts=("x",))

    assert DeterministicFaithfulness().compute(case).value == 0.0
    assert DeterministicAnswerRelevance().compute(case).value == 0.0
    assert DeterministicContextRelevance().compute(case).value == 0.0


# ---- LLM-judge metrics (OllamaClient always mocked - no network) ----

def _case():
    return RAGEvaluationCase(
        question="what is X?", answer="X is Y.",
        retrieved_contexts=("X is Y, according to the source.",),
    )


def test_llm_judge_faithfulness_parses_score_from_json_response():
    llm_client = MagicMock()
    llm_client.generate.return_value = '{"score": 0.8}'
    metric = LLMJudgeFaithfulness(llm_client=llm_client)

    result = metric.compute(_case())

    assert result.value == 0.8
    assert result.details["kind"] == "model_based"
    llm_client.generate.assert_called_once()


def test_llm_judge_answer_relevance_parses_score_wrapped_in_markdown_fence():
    llm_client = MagicMock()
    llm_client.generate.return_value = '```json\n{"score": 0.5}\n```'
    metric = LLMJudgeAnswerRelevance(llm_client=llm_client)

    result = metric.compute(_case())

    assert result.value == 0.5


def test_llm_judge_context_relevance_clamps_out_of_range_scores():
    llm_client = MagicMock()
    llm_client.generate.return_value = '{"score": 5.0}'
    metric = LLMJudgeContextRelevance(llm_client=llm_client)

    result = metric.compute(_case())

    assert result.value == 1.0


def test_llm_judge_metric_returns_zero_when_llm_call_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("ollama unreachable")
    metric = LLMJudgeFaithfulness(llm_client=llm_client)

    result = metric.compute(_case())

    assert result.value == 0.0
    assert result.details["error"] == "llm_call_failed"


def test_llm_judge_metric_returns_zero_for_unparseable_output():
    llm_client = MagicMock()
    llm_client.generate.return_value = "not valid json at all"
    metric = LLMJudgeFaithfulness(llm_client=llm_client)

    result = metric.compute(_case())

    assert result.value == 0.0
    assert result.details["error"] == "unparseable_output"


def test_llm_judge_metric_returns_zero_when_score_field_missing():
    llm_client = MagicMock()
    llm_client.generate.return_value = '{"not_score": 0.5}'
    metric = LLMJudgeFaithfulness(llm_client=llm_client)

    result = metric.compute(_case())

    assert result.value == 0.0


def test_llm_judge_faithfulness_prompt_includes_context_and_answer():
    llm_client = MagicMock()
    llm_client.generate.return_value = '{"score": 1.0}'
    metric = LLMJudgeFaithfulness(llm_client=llm_client)

    case = RAGEvaluationCase(
        question="q", answer="unique-answer-marker",
        retrieved_contexts=("unique-context-marker",),
    )
    metric.compute(case)

    prompt = llm_client.generate.call_args.args[0]
    assert "unique-answer-marker" in prompt
    assert "unique-context-marker" in prompt
