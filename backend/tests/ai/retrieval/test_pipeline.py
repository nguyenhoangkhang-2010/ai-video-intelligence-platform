from ai.retrieval.pipeline import RetrievalPipeline
from ai.retrieval.retriever import RetrievalResult, Retriever


class FakeRetriever:
    """
    Minimal stand-in that structurally satisfies the Retriever
    Protocol (no inheritance) - this alone proves RetrievalPipeline
    only depends on the retrieve() shape, not a concrete
    implementation, exactly what the Protocol contract is for.
    """

    def __init__(self, results):
        self.results = results
        self.calls = []

    def retrieve(self, query, video_id, top_k=5):
        self.calls.append(
            {"query": query, "video_id": video_id, "top_k": top_k},
        )
        return self.results


def _result(id, video_id=10, text="chunk text", score=0.1):
    return RetrievalResult(id=id, video_id=video_id, text=text, score=score)


def test_retrieve_forwards_query_video_id_and_top_k_to_retriever():
    retriever = FakeRetriever(results=[])
    pipeline = RetrievalPipeline(retriever=retriever)

    pipeline.retrieve(query="what happened?", video_id=10, top_k=3)

    assert retriever.calls == [
        {"query": "what happened?", "video_id": 10, "top_k": 3},
    ]


def test_retrieve_returns_empty_for_blank_query_without_calling_retriever():
    retriever = FakeRetriever(results=[_result("a")])
    pipeline = RetrievalPipeline(retriever=retriever)

    results = pipeline.retrieve(query="   ", video_id=10, top_k=5)

    assert results == []
    assert retriever.calls == []


def test_retrieve_deduplicates_by_id_keeping_first_occurrence():
    first = _result("a", text="first version", score=0.1)
    duplicate = _result("a", text="second version", score=0.9)
    other = _result("b", text="other chunk", score=0.2)

    retriever = FakeRetriever(results=[first, duplicate, other])
    pipeline = RetrievalPipeline(retriever=retriever)

    results = pipeline.retrieve(query="q", video_id=10, top_k=5)

    assert [r.id for r in results] == ["a", "b"]
    assert results[0].text == "first version"


def test_retrieve_truncates_to_top_k():
    results_in = [_result(f"id-{i}") for i in range(10)]
    retriever = FakeRetriever(results=results_in)
    pipeline = RetrievalPipeline(retriever=retriever)

    results = pipeline.retrieve(query="q", video_id=10, top_k=3)

    assert len(results) == 3
    assert [r.id for r in results] == ["id-0", "id-1", "id-2"]


def test_retrieve_never_mixes_in_results_from_another_video():
    retriever = FakeRetriever(
        results=[_result("a", video_id=10), _result("b", video_id=10)],
    )
    pipeline = RetrievalPipeline(retriever=retriever)

    results = pipeline.retrieve(query="q", video_id=10, top_k=5)

    assert all(result.video_id == 10 for result in results)


def test_fake_retriever_structurally_satisfies_retriever_protocol():
    retriever = FakeRetriever(results=[])

    assert isinstance(retriever, Retriever)


class FakeReranker:
    """
    Minimal stand-in that structurally satisfies the Reranker
    Protocol - reverses candidate order and stamps a marker score,
    just enough to prove RetrievalPipeline actually delegates to it
    rather than only using dedupe/truncate.
    """

    def __init__(self):
        self.calls = []

    def rerank(self, query, candidates):
        self.calls.append({"query": query, "candidates": list(candidates)})
        return list(reversed(candidates))


def test_retrieve_without_reranker_fetches_exactly_top_k_candidates():
    retriever = FakeRetriever(results=[])
    pipeline = RetrievalPipeline(retriever=retriever)

    pipeline.retrieve(query="q", video_id=10, top_k=5)

    # No reranker -> original (pre-reranking) behavior: fetch exactly
    # top_k, nothing more.
    assert retriever.calls == [{"query": "q", "video_id": 10, "top_k": 5}]


def test_retrieve_with_reranker_over_fetches_candidates_using_multiplier():
    retriever = FakeRetriever(results=[])
    reranker = FakeReranker()
    pipeline = RetrievalPipeline(
        retriever=retriever,
        reranker=reranker,
        candidate_multiplier=4,
    )

    pipeline.retrieve(query="q", video_id=10, top_k=5)

    # With a reranker present, more candidates than top_k are fetched
    # so there is real material to rerank.
    assert retriever.calls == [{"query": "q", "video_id": 10, "top_k": 20}]


def test_retrieve_calls_reranker_with_deduplicated_candidates_and_applies_its_order():
    duplicate_a = _result("a", text="first", score=0.1)
    duplicate_a_again = _result("a", text="second", score=0.9)
    other = _result("b", text="other", score=0.2)

    retriever = FakeRetriever(results=[duplicate_a, duplicate_a_again, other])
    reranker = FakeReranker()
    pipeline = RetrievalPipeline(
        retriever=retriever,
        reranker=reranker,
        candidate_multiplier=2,
    )

    results = pipeline.retrieve(query="q", video_id=10, top_k=5)

    # Reranker receives already-deduplicated candidates (exactly one
    # "a", keeping the first occurrence's data).
    reranker_candidates = reranker.calls[0]["candidates"]
    assert [c.id for c in reranker_candidates] == ["a", "b"]
    assert reranker_candidates[0].text == "first"

    # Pipeline's final output reflects the reranker's ordering
    # (FakeReranker reverses), not the original retriever order.
    assert [r.id for r in results] == ["b", "a"]


def test_retrieve_truncates_to_top_k_after_reranking():
    results_in = [_result(f"id-{i}") for i in range(10)]
    retriever = FakeRetriever(results=results_in)
    reranker = FakeReranker()
    pipeline = RetrievalPipeline(
        retriever=retriever,
        reranker=reranker,
        candidate_multiplier=1,
    )

    results = pipeline.retrieve(query="q", video_id=10, top_k=3)

    # FakeReranker reverses the 10 candidates, then the pipeline
    # keeps only the first 3 of the RERANKED order.
    assert [r.id for r in results] == ["id-9", "id-8", "id-7"]
