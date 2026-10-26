from ai.retrieval.retriever import RetrievalResult
from app.pipelines.rag_pipeline import RAGPipeline


def _result(content_source, start_time, chunk_index=0):
    return RetrievalResult(
        id=f"v-{chunk_index}",
        video_id=7,
        text="nội dung",
        score=1.0,
        metadata={"chunk_index": chunk_index, "content_source": content_source, "start_time": start_time},
    )


def test_context_says_whether_each_source_was_said_or_shown():
    context, included = RAGPipeline._build_context([
        _result("speech", 75.4, 0),
        _result("visual", 12.0, 1),
        _result(None, None, 2),
    ])

    blocks = context.split("\n\n")
    assert blocks[0].startswith("[Source 1] (chunk_index: 0; lời nói, lúc 1:15)")
    assert blocks[1].startswith("[Source 2] (chunk_index: 1; hiển thị trên màn hình, lúc 0:12)")
    assert blocks[2].startswith("[Source 3] (chunk_index: 2; lời nói)")
    assert len(included) == 3


def test_search_result_carries_the_content_source():
    result = RAGPipeline._to_search_result(_result("visual", 3.0))

    assert result.source == "visual"
    assert result.start_time == 3.0
