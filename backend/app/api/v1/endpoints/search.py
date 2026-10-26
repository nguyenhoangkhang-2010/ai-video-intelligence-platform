import json
import logging
from collections.abc import Iterator

from fastapi import Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from fastapi import APIRouter

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.config.settings import settings
from app.core.rate_limit import rate_limit
from app.database.session import SessionLocal, get_db
from app.repositories.embedding import EmbeddingRepository

from app.api.deps import get_chat_history_service
from app.api.deps import get_rag_pipeline
from app.api.deps import get_video_service

from ai.llm.errors import LLMError

from app.pipelines.rag_pipeline import RAGPipeline
from app.repositories.chat_history import ChatHistoryRepository
from app.schemas.search import SearchResult
from app.services.chat_history import ChatHistoryService
from app.services.video import VideoService

from app.schemas.rag import RAGResult
from app.schemas.search import SearchRequest
from app.schemas.search import SemanticSearchResponse
from app.services.semantic_search import SemanticSearchService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "/videos/{video_id}",
    response_model=SemanticSearchResponse,
    dependencies=[Depends(rate_limit("search", settings.rate_limit.search_limit, 60))],
)
def search_video(
    video_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    db: Session = Depends(get_db),
):
    """
    Semantic search inside video content.

    Ownership-checked exactly like the RAG endpoint below - this
    previously had no authentication/ownership check at all, letting
    any caller search any video's content by guessing an id.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    logger.info(
        "Searching video %s with query: %s",
        video_id,
        request.query,
    )

    embedding_repository = EmbeddingRepository(
        db=db,
    )

    service = SemanticSearchService(
        embedding_repository=embedding_repository,
    )

    results = service.search(
        video_id=video_id,
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "video_id": video_id,
        "query": request.query,
        "results": results,
    }


@router.post(
    "/videos/{video_id}/rag",
    response_model=RAGResult,
    dependencies=[Depends(rate_limit("rag", settings.rate_limit.search_limit, 60))],
)
def ask_video(
    video_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
):
    """
    Ask a question grounded in a video's transcript content, using
    retrieval-augmented generation scoped to that video only.

    Retrieval/generation stays stateless (no prior turns are fed back
    into this call) - only the *record* of a genuinely answered turn is
    persisted afterward, via ChatHistoryService, so the AI Chat panel
    can restore a user's own conversation after a refresh or when
    reopening the video (see docs/api/rest_api.md, Search & RAG).
    Never recorded for empty_query/no_embeddings/no_relevant_chunks -
    there is no real answer to remember for those. The write is
    best-effort: a failure here is logged, never turned into an error
    response, since the person asking still got their real answer.
    """

    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    logger.info(
        "RAG query for video %s: %s",
        video_id,
        request.query,
    )

    result = rag_pipeline.ask(
        video_id=video_id,
        query=request.query,
        top_k=request.top_k,
    )

    if result.status == "answered" and result.answer:
        try:
            chat_history_service.record(
                user_id=current_user.id,
                video_id=video_id,
                question=request.query,
                answer=result.answer,
                sources=result.sources,
            )
        except Exception:
            logger.exception(
                "Failed to record chat history for video %s (answer still returned).",
                video_id,
            )

    return result


def _sse(event: str, payload: dict) -> str:
    """One Server-Sent Events frame: an event name plus a JSON data line."""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _record_chat_history(
    user_id: int,
    video_id: int,
    question: str,
    answer: str,
    sources: list[SearchResult],
) -> None:
    """
    Persist an answered streamed turn, on a session of its own: the
    request-scoped session can't be relied on while a streaming
    response is still being written. Best-effort, like the
    non-streaming endpoint - a failure is logged, never surfaced.
    """
    db = SessionLocal()
    try:
        ChatHistoryService(ChatHistoryRepository(db)).record(
            user_id=user_id,
            video_id=video_id,
            question=question,
            answer=answer,
            sources=sources,
        )
    except Exception:
        logger.exception(
            "Failed to record chat history for video %s (answer still returned).",
            video_id,
        )
    finally:
        db.close()


@router.post(
    "/videos/{video_id}/rag/stream",
    response_class=StreamingResponse,
    dependencies=[Depends(rate_limit("rag", settings.rate_limit.search_limit, 60))],
)
def ask_video_stream(
    video_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """
    Streaming variant of POST /search/videos/{video_id}/rag: the same
    grounded answer, sent as Server-Sent Events while the model is
    still writing it, so the first words appear in seconds instead of
    after the whole generation (which takes minutes on CPU).

    Ownership, retrieval and context construction all run before the
    response starts, so a missing video is still a normal 404 and a
    question with nothing to ground it in never reaches the LLM.
    Events, in order:

    - `sources` - `{"sources": [...]}`: the chunks the answer is
      grounded in (only when there is an answer to generate).
    - `token` - `{"text": "..."}`: the next piece of the answer, any
      number of times.
    - `done` - the final RAGResult (`video_id`, `query`, `status`,
      `answer`, `sources`), exactly what the non-streaming endpoint
      returns. Always the last event. `status` is `generation_failed`
      if the model failed mid-way; already-sent tokens should then be
      discarded by the client.

    An answered turn is recorded to chat history after the stream
    completes, like the non-streaming endpoint.
    """

    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    logger.info(
        "Streaming RAG query for video %s: %s",
        video_id,
        request.query,
    )

    prepared = rag_pipeline.prepare(
        video_id=video_id,
        query=request.query,
        top_k=request.top_k,
    )

    user_id = current_user.id

    def events() -> Iterator[str]:
        if isinstance(prepared, RAGResult):
            yield _sse("done", prepared.model_dump(mode="json"))
            return

        sources = [source.model_dump(mode="json") for source in prepared.sources]
        yield _sse("sources", {"sources": sources})

        pieces: list[str] = []
        try:
            for piece in prepared.stream():
                pieces.append(piece)
                yield _sse("token", {"text": piece})
        except LLMError:
            logger.exception(
                "Streaming LLM generation failed for video %s after a "
                "successful retrieval of %s chunk(s).",
                video_id,
                len(prepared.sources),
            )
            yield _sse(
                "done",
                RAGResult(
                    video_id=video_id,
                    query=request.query,
                    status="generation_failed",
                    sources=[],
                ).model_dump(mode="json"),
            )
            return

        answer = "".join(pieces).strip()
        if not answer:
            yield _sse(
                "done",
                RAGResult(
                    video_id=video_id,
                    query=request.query,
                    status="generation_failed",
                    sources=[],
                ).model_dump(mode="json"),
            )
            return

        result = RAGResult(
            video_id=video_id,
            query=request.query,
            status="answered",
            answer=answer,
            sources=prepared.sources,
        )
        _record_chat_history(
            user_id=user_id,
            video_id=video_id,
            question=request.query,
            answer=answer,
            sources=prepared.sources,
        )
        yield _sse("done", result.model_dump(mode="json"))

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            # Don't let proxies (nginx in the prod stack) buffer the
            # stream - that would hold every token until the end.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
