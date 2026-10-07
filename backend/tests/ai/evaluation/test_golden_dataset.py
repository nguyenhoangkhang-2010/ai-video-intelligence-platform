"""
Regression test for the evaluation framework's own wiring
(EvaluationDataset -> BenchmarkRunner -> real metric classes), run
against a small, fixed, version-controlled dataset
(ai/evaluation/fixtures/golden_dataset.json).

This is deliberately distinct from:
- tests/ai/evaluation/test_*_metrics.py etc., which already unit-test
  each metric FUNCTION in isolation with many edge cases.
- scripts/run_evaluation.py, which scores THIS deployment's real
  retrieval/RAG quality against a real, already-processed video - it
  needs Postgres and (for the RAG command) a real LLM provider, so it
  is intentionally never run in CI.

What this test adds: proof that the full pipeline (dataset loading,
BenchmarkRunner aggregation, and the real metric classes together)
produces the expected numbers for known inputs - a change that breaks
that wiring (not just one metric function) would otherwise only show
up the next time someone ran the manual script. Every expected value
below is hand-computed from the fixture (see comments) rather than
captured from a prior run, so this test would fail if the math were
ever wrong, not just if it ever changed.

Uses only deterministic, dependency-free metrics (no BERTScore, no
LLM judge) - nothing here calls a model, a network, or a database, so
it runs anywhere the rest of the test suite does.
"""
import json
from pathlib import Path

import pytest

from ai.evaluation.benchmark import BenchmarkRunner
from ai.evaluation.metrics.generation import RougeMetric
from ai.evaluation.metrics.retrieval import MeanReciprocalRank, NDCGAtK, PrecisionAtK, RecallAtK
from ai.evaluation.models import EvaluationDataset, GenerationEvaluationCase, RAGEvaluationCase, RetrievalEvaluationCase
from ai.evaluation.rag_eval import (
    DeterministicAnswerRelevance,
    DeterministicContextRelevance,
    DeterministicFaithfulness,
)

FIXTURE_PATH = Path(__file__).parent.parent.parent.parent / "ai" / "evaluation" / "fixtures" / "golden_dataset.json"
TOP_K = 3


@pytest.fixture(scope="module")
def golden_dataset() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_retrieval_metrics_match_hand_computed_values(golden_dataset):
    cases = tuple(
        RetrievalEvaluationCase(
            query=entry["query"],
            retrieved_ids=tuple(entry["retrieved_ids"]),
            relevant_ids=frozenset(entry["relevant_ids"]),
        )
        for entry in golden_dataset["retrieval_cases"]
    )
    dataset = EvaluationDataset(name="golden-retrieval", cases=cases)

    runner = BenchmarkRunner(
        [PrecisionAtK(TOP_K), RecallAtK(TOP_K), MeanReciprocalRank(), NDCGAtK(TOP_K)],
    )
    result = runner.run(dataset)
    scores = {r.metric_name: r.value for r in result.metric_results}

    assert result.case_count == 2
    # q1: top-3 = [c1,c2,c3], relevant={c1,c3} -> hits=2/3; q2: top-3=[d1,d2,d3],
    # relevant={d2} -> hits=1/3. Mean = (2/3 + 1/3) / 2 = 0.5.
    assert scores["precision@3"] == pytest.approx(0.5)
    # q1: both relevant ids (c1,c3) appear in top-3 -> 2/2=1.0; q2: the one
    # relevant id (d2) appears in top-3 -> 1/1=1.0. Mean = 1.0.
    assert scores["recall@3"] == pytest.approx(1.0)
    # q1: first relevant id (c1) is rank 1 -> RR=1.0; q2: first relevant id
    # (d2) is rank 2 -> RR=0.5. Mean = 0.75.
    assert scores["mrr"] == pytest.approx(0.75)
    # q1 relevances [1,0,1]: DCG=1/log2(2)+1/log2(4)=1.5, IDCG=1/log2(2)+1/log2(3)=1.6309
    #   -> NDCG=0.9193. q2 relevances [0,1,0]: DCG=1/log2(3)=0.6309, IDCG=1.0
    #   -> NDCG=0.6309. Mean = 0.7751.
    assert scores["ndcg@3"] == pytest.approx(0.7751, abs=1e-3)


def test_generation_metric_matches_hand_computed_values(golden_dataset):
    cases = tuple(
        GenerationEvaluationCase(candidate=entry["candidate"], reference=entry["reference"])
        for entry in golden_dataset["generation_cases"]
    )
    dataset = EvaluationDataset(name="golden-generation", cases=cases)

    runner = BenchmarkRunner([RougeMetric("rougeL")])
    result = runner.run(dataset)
    scores = {r.metric_name: r.value for r in result.metric_results}

    assert result.case_count == 2
    # Case 1 is a verbatim match -> ROUGE-L F1 = 1.0. Case 2 shares no
    # vocabulary at all -> ROUGE-L F1 = 0.0. Mean = 0.5.
    assert scores["rouge_rougeL"] == pytest.approx(0.5)


def test_rag_deterministic_metrics_match_hand_computed_values(golden_dataset):
    cases = tuple(
        RAGEvaluationCase(
            question=entry["question"],
            answer=entry["answer"],
            retrieved_contexts=tuple(entry["retrieved_contexts"]),
        )
        for entry in golden_dataset["rag_cases"]
    )
    dataset = EvaluationDataset(name="golden-rag", cases=cases)

    runner = BenchmarkRunner(
        [DeterministicFaithfulness(), DeterministicAnswerRelevance(), DeterministicContextRelevance()],
    )
    result = runner.run(dataset)
    scores = {r.metric_name: r.value for r in result.metric_results}

    assert result.case_count == 2
    # Case 1: answer tokens {the,sky,is,blue} (4), 3 also in context -> 0.75;
    # Case 2: answer tokens {yes,the,grass,is,green} (5), 3 also in context
    # -> 0.6. Mean = 0.675.
    assert scores["faithfulness_lexical"] == pytest.approx(0.675)
    # Case 1: question tokens {what,color,is,the,sky} (5), 3 also in answer
    # -> 0.6; Case 2: question tokens {is,the,grass,green} (4), all 4 also
    # in answer -> 1.0. Mean = 0.8.
    assert scores["answer_relevance_lexical"] == pytest.approx(0.8)
    # Case 1: question tokens (5), 2 also in context -> 0.4; Case 2:
    # question tokens (4), 3 also in context -> 0.75. Mean = 0.575.
    assert scores["context_relevance_lexical"] == pytest.approx(0.575)


def test_golden_dataset_has_no_domain_specific_entities(golden_dataset):
    """
    This dataset must stay generic/synthetic (see module docstring) -
    guards against someone later "improving realism" by swapping in
    real company/product/skill names, which would silently turn this
    regression fixture into untracked domain-specific test data.
    """
    serialized = json.dumps(golden_dataset).lower()
    for forbidden in ("resume", "job", "company", "certification", "linkedin"):
        assert forbidden not in serialized
