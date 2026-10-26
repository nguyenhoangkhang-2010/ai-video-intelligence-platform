# 0004 - `LLMProvider`/`EmbeddingProvider` as Protocols, not a full plugin framework

## Status
Accepted (implemented: `ai/llm/factory.py::get_llm_provider`, `ai/embedding/factory.py::get_embedding_provider`).

## Context
Every LLM/embedding call in this codebase went directly through
`ai/llm/ollama_client.py` (and the equivalent embedding client).
Swapping providers (e.g. to evaluate a hosted model) meant editing
call sites, not configuration.

## Decision
Define `LLMProvider`/`EmbeddingProvider` as `typing.Protocol`s (not
ABCs) - mirroring this project's existing convention for swappable
collaborators (`ai.retrieval.retriever.Retriever`,
`ai.reranking.reranker.Reranker`), so a new implementation only needs
to match the shape, not inherit from anything. `get_llm_provider()`
reads `settings.llm.provider` (currently `Literal["ollama"]` - one
real implementation) and returns the configured instance; call sites
depend on the Protocol, not on `OllamaClient` directly.

## Consequences
- Adding a second provider later is a config value and a new class,
  not a refactor of every call site.
- No plugin registry, no dynamic import-by-string, no provider
  marketplace - deliberately, since there is exactly one real
  implementation today and speculative extensibility beyond "a
  factory function and a Protocol" would be unused abstraction.
- `settings.llm.provider` being a `Literal["ollama"]` (not an open
  `str`) means adding a real second provider requires widening that
  literal, which is an intentional one-line signal that a new
  provider was deliberately added, not silently misconfigured.
