import logging

from ai.llm.rag_answerer import RagAnswerer

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
        -> SemanticSearchService (video-scoped retrieval, reused as-is)
        -> context construction
        -> RagAnswerer (Ollama, reused as-is)
        -> RAGResult
    """

    def __init__(
        self,
        semantic_search_service: SemanticSearchService,
        embedding_service: EmbeddingService,
        answerer: RagAnswerer | None = None,
    ):
        self.semantic_search_service = semantic_search_service
        self.embedding_service = embedding_service
        self.answerer = (
            answerer
            or RagAnswerer()
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

        results = self.semantic_search_service.search(
            video_id=video_id,
            query=query,
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
                SearchResult(**result)
                for result in results
            ],
        )

    @staticmethod
    def _build_context(
        chunks: list[dict],
    ) -> str:
        """
        Assemble retrieved chunks (already ordered most-relevant-first
        by SemanticSearchService) into a bounded, numbered context
        block. Greedily includes chunks until MAX_CONTEXT_CHARS would
        be exceeded, always keeping at least the first one.
        """

        parts = []
        total_chars = 0

        for position, chunk in enumerate(chunks, start=1):
            block = (
                f"[Source {position}] "
                f"(chunk_index: {chunk['chunk_index']})\n"
                f"{chunk['chunk_text']}"
            )

            if parts and total_chars + len(block) > MAX_CONTEXT_CHARS:
                break

            parts.append(block)
            total_chars += len(block)

        return "\n\n".join(parts)
