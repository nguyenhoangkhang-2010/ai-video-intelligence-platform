import pytest

from ai.retrieval.hybrid_search import HybridRetriever
from ai.retrieval.retriever import RetrievalResult


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def retrieve(self, query, video_id, top_k=5):
        self.calls.append(
            {"query": query, "video_id": video_id, "top_k": top_k},
        )
        return self.results


def _result(id, video_id=10, text=None, score=1.0):
    return RetrievalResult(
        id=id, video_id=video_id, text=text or f"text-{id}", score=score,
    )


def test_hybrid_retriever_requires_at_least_one_retriever():
    with pytest.raises(ValueError):
        HybridRetriever(retrievers=[])


def test_retrieve_forwards_query_and_video_id_to_every_retriever():
    dense = FakeRetriever(results=[])
    sparse = FakeRetriever(results=[])

    hybrid = HybridRetriever(retrievers=[dense, sparse])
    hybrid.retrieve(query="budget", video_id=10, top_k=5)

    assert dense.calls == [{"query": "budget", "video_id": 10, "top_k": 5}]
    assert sparse.calls == [{"query": "budget", "video_id": 10, "top_k": 5}]


def test_retrieve_returns_empty_for_blank_query_without_calling_any_retriever():
    dense = FakeRetriever(results=[_result("a")])
    sparse = FakeRetriever(results=[_result("b")])

    hybrid = HybridRetriever(retrievers=[dense, sparse])
    results = hybrid.retrieve(query="   ", video_id=10, top_k=5)

    assert results == []
    assert dense.calls == []
    assert sparse.calls == []


def test_rrf_fusion_combines_overlapping_results_and_orders_by_fused_score():
    # dense ranks: a (1st), b (2nd)
    dense = FakeRetriever(results=[_result("a", score=0.9), _result("b", score=0.5)])
    # sparse ranks: b (1st), c (2nd) - "b" overlaps with dense
    sparse = FakeRetriever(results=[_result("b", score=5.0), _result("c", score=1.0)])

    fusion_k = 60
    hybrid = HybridRetriever(retrievers=[dense, sparse], fusion_k=fusion_k)

    results = hybrid.retrieve(query="q", video_id=10, top_k=5)

    # "b" appears in both retrievers' outputs - fused, not duplicated.
    assert [r.id for r in results] == ["b", "a", "c"]
    assert len(results) == 3

    expected_b = 1.0 / (fusion_k + 2) + 1.0 / (fusion_k + 1)
    expected_a = 1.0 / (fusion_k + 1)
    expected_c = 1.0 / (fusion_k + 2)

    scores_by_id = {r.id: r.score for r in results}
    assert scores_by_id["b"] == pytest.approx(expected_b)
    assert scores_by_id["a"] == pytest.approx(expected_a)
    assert scores_by_id["c"] == pytest.approx(expected_c)


def test_fused_results_preserve_video_scoping_and_tag_fusion_metadata():
    dense = FakeRetriever(results=[_result("a", video_id=10)])
    sparse = FakeRetriever(results=[])

    hybrid = HybridRetriever(retrievers=[dense, sparse])
    results = hybrid.retrieve(query="q", video_id=10, top_k=5)

    assert all(r.video_id == 10 for r in results)
    assert results[0].metadata["fusion"] == "rrf"


def test_retrieve_truncates_fused_results_to_top_k():
    dense = FakeRetriever(
        results=[_result(f"id-{i}") for i in range(10)],
    )
    sparse = FakeRetriever(results=[])

    hybrid = HybridRetriever(retrievers=[dense, sparse])
    results = hybrid.retrieve(query="q", video_id=10, top_k=3)

    assert len(results) == 3
