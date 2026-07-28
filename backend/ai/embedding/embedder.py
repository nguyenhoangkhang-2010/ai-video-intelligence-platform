import logging
import uuid

from FlagEmbedding import BGEM3FlagModel


logger = logging.getLogger(__name__)


class Embedder:
    """Embedding generator using Sentence Transformers."""
    
    def __init__(
        self,
    ):
        self.model = BGEM3FlagModel(
            "BAAI/bge-m3",
            use_fp16=False,
        )

    def embed(
        self,
        text: str,
    ) -> list[dict]:
        """
        Generate embeddings for transcript.
        """
        
        logger.info(
            "Generating embeddings.",
        )
        
        result = self.model.encode(
            [text],
        )
        
        vector = result["dense_vecs"][0]

        return [
            {
                "chunk_index": 0,
                "chunk_text": text,
                "embedding_model": "BAAI/bge-m3",
                "vector": vector.tolist(),
                "vector_id": str(uuid.uuid4()),
            }
        ]