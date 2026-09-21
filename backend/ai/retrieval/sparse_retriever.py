import logging
import re

from rank_bm25 import BM25Okapi

from ai.retrieval.retriever import RetrievalResult
from app.repositories.embedding import EmbeddingRepository


logger = logging.getLogger(__name__)

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


class SparseRetriever:
    """
    Keyword-based (BM25) Retriever implementation.

    No persistent full-text index/database is introduced: no
    sparse/BM25/full-text infrastructure exists anywhere in this
    project (confirmed by audit), so this reuses the SAME chunk
    storage dense retrieval already depends on (the Embedding table,
    via EmbeddingRepository) rather than duplicating storage. A BM25
    index is built fresh, in memory, over a single video's chunks per
    call - videos have on the order of tens of chunks, so this is
    cheap and avoids the complexity of maintaining a persistent
    index. BM25 scores are already higher-is-better, matching
    RetrievalResult's score contract with no conversion needed
    (unlike DenseRetriever's FAISS distance).
    """

    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
    ):
        self.embedding_repository = embedding_repository

    def retrieve(
        self,
        query: str,
        video_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not query or not query.strip():
            return []

        chunks = self.embedding_repository.get_by_video_id(
            video_id,
        )

        if not chunks:
            return []

        tokenized_corpus = [
            _tokenize(chunk.chunk_text)
            for chunk in chunks
        ]

        bm25 = BM25Okapi(tokenized_corpus)

        scores = bm25.get_scores(
            _tokenize(query),
        )

        ranked = sorted(
            zip(chunks, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )

        results = []

        for chunk, score in ranked:
            if score <= 0:
                continue

            results.append(
                RetrievalResult(
                    id=chunk.vector_id,
                    video_id=chunk.video_id,
                    text=chunk.chunk_text,
                    score=float(score),
                    metadata={
                        "chunk_index": chunk.chunk_index,
                        "source": "sparse",
                    },
                )
            )

            if len(results) >= top_k:
                break

        return results
