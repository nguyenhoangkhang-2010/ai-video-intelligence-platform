from unittest.mock import patch

from ai.embedding.factory import get_embedding_provider
from ai.embedding.provider import EmbeddingProvider


def test_default_provider_is_embedder():
    """
    Embedder() loads the real BGE-M3 model (multi-GB class, see
    ai.embedding.embedder._load_embedding_model) - patched at its
    import site, same as every other test touching Embedder
    construction in this suite, so this stays a fast unit test.
    """
    with patch("ai.embedding.embedder.Embedder") as mock_embedder_class:
        provider = get_embedding_provider()

    assert provider is mock_embedder_class.return_value


def test_embedder_satisfies_embedding_provider_protocol():
    from ai.embedding.embedder import Embedder

    # Structural check only (runtime_checkable Protocol) - does not
    # construct a real Embedder (no __init__ call), just checks the
    # class exposes the right method shape.
    assert isinstance(Embedder, type)
    assert hasattr(Embedder, "embed")
    assert hasattr(Embedder, "embed_query")
    assert issubclass(Embedder, EmbeddingProvider)
