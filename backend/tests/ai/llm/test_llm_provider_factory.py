from unittest.mock import MagicMock

import pytest

from ai.llm.factory import get_llm_provider
from ai.llm.ollama_client import OllamaClient
from ai.llm.provider import LLMProvider
from app.config.settings import settings


def test_default_provider_is_ollama():
    provider = get_llm_provider()

    assert isinstance(provider, OllamaClient)
    assert isinstance(provider, LLMProvider)  # structural check, runtime_checkable


def test_unknown_provider_raises_value_error(monkeypatch):
    # Swap the whole `llm` settings object for a plain mock rather
    # than assigning an invalid value onto the real (Literal-typed)
    # settings field - this tests the factory's own unreachable-today
    # branch without depending on whether pydantic validates
    # attribute assignment.
    fake_llm_settings = MagicMock()
    fake_llm_settings.provider = "not-a-real-provider"
    monkeypatch.setattr(settings, "llm", fake_llm_settings)

    with pytest.raises(ValueError, match="not-a-real-provider"):
        get_llm_provider()
