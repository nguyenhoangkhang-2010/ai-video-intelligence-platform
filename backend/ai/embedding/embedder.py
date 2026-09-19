import logging
import os
import uuid

from FlagEmbedding import BGEM3FlagModel

from ai.embedding.chunking import TextChunker
from app.config.settings import settings


logger = logging.getLogger(__name__)


class Embedder:

    def __init__(
        self,
        chunker: TextChunker | None = None,
    ):
        if settings.huggingface.token:
            os.environ["HF_TOKEN"] = settings.huggingface.token

        self.model = BGEM3FlagModel(
            "BAAI/bge-m3",
            use_fp16=False,
        )

        self.chunker = (
            chunker
            or TextChunker(
                chunk_size=500,
                overlap=50,
            )
        )

    def embed(self, text: str) -> list[dict]:
        
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
                    "embedding_model": "BAAI/bge-m3",
                    "vector": vector.tolist(),
                    "vector_id": str(uuid.uuid4()),
                }
            )

        logger.info(
            "Generated %s embeddings.",
            len(embeddings),
        )

        return embeddings
    
    def embed_query(self, query: str) -> list[float]:
        
        if not query or not query.strip():
            return []

        logger.info(
            "Generating query embedding."
        )

        result = self.model.encode([query.strip()])
        vector = result["dense_vecs"][0]

        return vector.tolist()