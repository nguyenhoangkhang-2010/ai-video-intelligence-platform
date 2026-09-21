import dataclasses

import pytest

from ai.retrieval.retriever import RetrievalResult, Retriever


def test_retrieval_result_holds_the_generic_fields():
    result = RetrievalResult(
        id="v1",
        video_id=10,
        text="chunk text",
        score=0.75,
        metadata={"chunk_index": 0},
    )

    assert result.id == "v1"
    assert result.video_id == 10
    assert result.text == "chunk text"
    assert result.score == 0.75
    assert result.metadata == {"chunk_index": 0}


def test_retrieval_result_metadata_defaults_to_empty_dict():
    result = RetrievalResult(id="v1", video_id=10, text="t", score=0.1)

    assert result.metadata == {}


def test_retrieval_result_is_frozen():
    result = RetrievalResult(id="v1", video_id=10, text="t", score=0.1)

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score = 0.9


def test_object_missing_retrieve_method_does_not_satisfy_retriever_protocol():
    class NotARetriever:
        pass

    assert not isinstance(NotARetriever(), Retriever)


def test_object_with_matching_method_shape_satisfies_retriever_protocol():
    class MinimalRetriever:
        def retrieve(self, query, video_id, top_k=5):
            return []

    assert isinstance(MinimalRetriever(), Retriever)
