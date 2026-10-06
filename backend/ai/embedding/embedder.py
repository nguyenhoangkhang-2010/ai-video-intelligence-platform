import logging
import os
import uuid
from functools import lru_cache

from FlagEmbedding import BGEM3FlagModel

from ai.embedding.chunking import TextChunker
from app.config.settings import settings


logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

_VECTOR_ID_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_DNS,
    "ai-video-intelligence-platform.embeddings",
)


@lru_cache(maxsize=1)
def _load_embedding_model() -> BGEM3FlagModel:
    """
    Loads BGE-M3 (a multi-hundred-MB-to-GB-class model) from disk
    exactly once per process and reuses it for every `Embedder`
    instance thereafter - matching this codebase's own established,
    correct pattern for the cross-encoder reranker
    (app/api/deps.py::_get_cross_encoder_reranker). Before this fix,
    every `Embedder()` construction re-loaded the model from scratch -
    real found cost, since `Embedder()` is constructed fresh per HTTP
    request (SemanticSearchService.__init__, called from both
    get_rag_pipeline and search_video) and fresh per Celery task
    (EmbeddingWorker.__init__, chapter_detector.py,
    topic_segmentation.py).
    """
    if settings.huggingface.token:
        os.environ["HF_TOKEN"] = settings.huggingface.token

    logger.info(
        "Loading embedding model %s (first use in this process)...",
        EMBEDDING_MODEL_NAME,
    )

    return BGEM3FlagModel(
        EMBEDDING_MODEL_NAME,
        use_fp16=False,
    )


class Embedder:

    def __init__(
        self,
        chunker: TextChunker | None = None,
    ):
        self.model = _load_embedding_model()

        self.chunker = (
            chunker
            or TextChunker(
                chunk_size=500,
                overlap=50,
            )
        )

    def embed(
        self,
        text: str,
        video_id: int | str | None = None,
    ) -> list[dict]:

        if not text or not text.strip():
            return []

        logger.info(
            "Generating embeddings for text."
        )

        chunks = self.chunker.chunk(text)

        if not chunks:
            return []

        result = self.model.encode(chunks)
        vectors = result["dense_vecs"]

        embeddings = []

        for chunk_index, (
            chunk_text,
            vector,
        ) in enumerate(zip(chunks, vectors)):
            embeddings.append(
                {
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text,
                    "embedding_model": EMBEDDING_MODEL_NAME,
                    "vector": vector.tolist(),
                    "vector_id": self._build_vector_id(
                        video_id=video_id,
                        chunk_index=chunk_index,
                    ),
                }
            )

        logger.info(
            "Generated %s embeddings.",
            len(embeddings),
        )

        return embeddings

    def _build_vector_id(
        self,
        video_id: int | str | None,
        chunk_index: int,
    ) -> str:
        """
        Deterministic vector id so the same video + chunk position
        always resolves to the same identity across retries/reprocessing.
        Falls back to a random id when no owning document identity is
        given, keeping the method usable standalone.
        """
        if video_id is None:
            return str(uuid.uuid4())

        seed = f"{video_id}:{chunk_index}:{EMBEDDING_MODEL_NAME}"

        return str(
            uuid.uuid5(
                _VECTOR_ID_NAMESPACE,
                seed,
            )
        )

    def embed_query(self, query: str) -> list[float]:
        
        if not query or not query.strip():
            return []

        logger.info(
            "Generating query embedding."
        )

        result = self.model.encode([query.strip()])
        vector = result["dense_vecs"][0]

        return vector.tolist()