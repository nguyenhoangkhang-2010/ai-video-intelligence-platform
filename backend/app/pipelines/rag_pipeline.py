import logging

from ai.llm.rag_answerer import RagAnswerer
from ai.reranking.reranker import Reranker
from ai.retrieval.dense_retriever import DenseRetriever
from ai.retrieval.pipeline import RetrievalPipeline
from ai.retrieval.retriever import RetrievalResult, Retriever

from app.schemas.rag import RAGResult
from app.schemas.search import SearchResult
from app.services.embedding import EmbeddingService
from app.services.semantic_search import SemanticSearchService


logger = logging.getLogger(__name__)

# Single source of truth for the retrieval fan-out size, matching the
# existing SearchRequest.top_k default (app/schemas/search.py) so both
# entry points behave the same unless a caller overrides it.
DEFAULT_TOP_K = 5

# Rough char budget for the assembled context, so a query never sends
# an unbounded amount of transcript to the LLM regardless of how many
# chunks a video has.
MAX_CONTEXT_CHARS = 8000


class RAGPipeline:
    """
    Retrieval-augmented question answering scoped to a single video.

    query + video_id
        -> RetrievalPipeline (dense retrieval, reused from the
           existing SemanticSearchService, + optional reranking)
        -> context construction
        -> RagAnswerer (Ollama, reused as-is)
        -> RAGResult

    Backward compatible by default: unless a `retriever`/`reranker`
    is explicitly supplied, this still only ever retrieves through
    the existing SemanticSearchService (same FAISS/dense results,
    same video_id scoping, same top_k semantics as before this
    retrieval layer existed) with no reranking - the four terminal
    statuses and the RAGResult/API contract are unchanged.
    """

    def __init__(
        self,
        semantic_search_service: SemanticSearchService,
        embedding_service: EmbeddingService,
        answerer: RagAnswerer | None = None,
        retriever: Retriever | None = None,
        reranker: Reranker | None = None,
    ):
        self.embedding_service = embedding_service
        self.answerer = (
            answerer
            or RagAnswerer()
        )

        retriever = (
            retriever
            or DenseRetriever(
                semantic_search_service=semantic_search_service,
            )
        )

        self.retrieval_pipeline = RetrievalPipeline(
            retriever=retriever,
            reranker=reranker,
        )

    def ask(
        self,
        video_id: int,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> RAGResult:
        """
        Answer `query` using only content retrieved from `video_id`.
        No LLM call is made unless there is retrieved context to
        ground the answer in.
        """

        if not query or not query.strip():
            logger.info(
                "Empty RAG query for video %s.",
                video_id,
            )
            return RAGResult(
                video_id=video_id,
                query=query,
                status="empty_query",
                sources=[],
            )

        if not self.embedding_service.get_by_video_id(video_id):
            logger.info(
                "Video %s has no embeddings; skipping retrieval and LLM.",
                video_id,
            )
            return RAGResult(
                video_id=video_id,
                query=query,
                status="no_embeddings",
                sources=[],
            )

        results = self.retrieval_pipeline.retrieve(
            query=query,
            video_id=video_id,
            top_k=top_k,
        )

        if not results:
            logger.info(
                "No relevant chunks found for video %s; skipping LLM call.",
                video_id,
            )
            return RAGResult(
                video_id=video_id,
                query=query,
                status="no_relevant_chunks",
                sources=[],
            )

        context = self._build_context(
            results,
        )

        logger.info(
            "Calling LLM for video %s grounded in %s source chunk(s).",
            video_id,
            len(results),
        )

        answer = self.answerer.answer(
            query=query,
            context=context,
        )

        return RAGResult(
            video_id=video_id,
            query=query,
            status="answered",
            answer=answer,
            sources=[
                self._to_search_result(result)
                for result in results
            ],
        )

    @staticmethod
    def _to_search_result(result: RetrievalResult) -> SearchResult:
        """
        Reconstruct the existing SearchResult API contract from a
        generic RetrievalResult. DenseRetriever always populates
        `chunk_index`/`distance` in metadata, and neither
        RetrievalPipeline's dedup step nor any Reranker is allowed to
        drop/rename metadata keys (only add to them) or change
        id/video_id/text, so this reconstruction is exact for the
        default (dense, unreranked) path and stays accurate if a
        reranker is layered in.
        """
        return SearchResult(
            vector_id=result.id,
            video_id=result.video_id,
            chunk_index=result.metadata.get("chunk_index", 0),
            chunk_text=result.text,
            distance=result.metadata.get("distance", 0.0),
        )

    @staticmethod
    def _build_context(
        results: list[RetrievalResult],
    ) -> str:
        """
        Assemble retrieved chunks (already ordered most-relevant-first
        by RetrievalPipeline) into a bounded, numbered context block.
        Greedily includes chunks until MAX_CONTEXT_CHARS would be
        exceeded, always keeping at least the first one.
        """

        parts = []
        total_chars = 0

        for position, result in enumerate(results, start=1):
            chunk_index = result.metadata.get(
                "chunk_index", position - 1,
            )

            block = (
                f"[Source {position}] "
                f"(chunk_index: {chunk_index})\n"
                f"{result.text}"
            )

            if parts and total_chars + len(block) > MAX_CONTEXT_CHARS:
                break

            parts.append(block)
            total_chars += len(block)

        return "\n\n".join(parts)
