from ai.evaluation.review import (
    QUESTION_PROMPT,
    DraftQuestion,
    build_dataset,
    draft_item,
    parse_draft,
    pick_chunks,
)


def _chunk(index, words=20):
    return {
        "video_id": 7,
        "vector_id": f"7_{index}",
        "chunk_index": index,
        "chunk_text": " ".join(["từ"] * words),
        "start_time": index * 30.0,
    }


# ---- parse_draft ----

def test_parse_draft_reads_fenced_json():
    raw = 'Đây:\n```json\n{"question": "Video nói gì về Python?", "answer": "Dễ học"}\n```'

    assert parse_draft(raw) == DraftQuestion(question="Video nói gì về Python?", answer="Dễ học")


def test_parse_draft_rejects_unusable_output():
    assert parse_draft("không có json") is None
    assert parse_draft('["a", "b"]') is None
    assert parse_draft('{"question": "?", "answer": "x"}') is None


def test_prompt_formats_with_passage():
    assert "đoạn văn mẫu" in QUESTION_PROMPT.format(passage="đoạn văn mẫu")


# ---- pick_chunks ----

def test_pick_chunks_skips_short_and_spreads_evenly():
    chunks = [_chunk(i) for i in range(10)] + [_chunk(99, words=3)]

    picked = pick_chunks(chunks, 5)

    assert [c["chunk_index"] for c in picked] == [0, 2, 4, 6, 8]


def test_pick_chunks_returns_all_when_few():
    chunks = [_chunk(0), _chunk(1)]

    assert pick_chunks(chunks, 8) == chunks
    assert pick_chunks(chunks, 0) == []


# ---- draft_item / build_dataset ----

def test_draft_item_points_at_source_chunk_and_is_pending():
    item = draft_item(_chunk(3), DraftQuestion(question="Hỏi gì?", answer="Đáp"))

    assert item["relevant_vector_ids"] == ["7_3"]
    assert item["start_time"] == 90.0
    assert item["status"] == "pending"


def test_build_dataset_keeps_only_reviewed_items():
    base = draft_item(_chunk(0), DraftQuestion(question="Câu hỏi một?", answer=""))
    drafts = [
        {**base, "status": "approved"},
        {**base, "query": "Câu sửa?", "status": "edited"},
        {**base, "status": "rejected"},
        {**base, "status": "pending"},
    ]
    documents = [{"video_id": 7, "vector_id": "7_0", "chunk_text": "x"}]

    dataset = build_dataset(drafts, documents, comment="c")

    assert dataset["documents"] == documents
    assert [q["query"] for q in dataset["queries"]] == ["Câu hỏi một?", "Câu sửa?"]
    assert [q["review"]["decision"] for q in dataset["queries"]] == ["approved", "edited"]
    assert all(q["review"]["source"] == "llm-draft" for q in dataset["queries"])
    assert all(q["relevant_vector_ids"] == ["7_0"] for q in dataset["queries"])
