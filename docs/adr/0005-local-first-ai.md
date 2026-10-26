# 0005 - Local-first AI (Ollama, faster-whisper) over hosted APIs

## Status
Accepted.

## Context
Every AI capability in this product (transcription, summaries,
translation, quiz/flashcard/chapter generation, embeddings, RAG
answers) could instead call a hosted API (OpenAI, Anthropic, a hosted
Whisper endpoint).

## Decision
Default to local inference: `faster-whisper` for transcription,
Ollama for LLM calls and embeddings (`settings.llm.provider`
defaults to `"ollama"` - see ADR 0004). No API key is required to run
the full pipeline end to end.

## Consequences
- No per-request external cost, no outbound dependency on a third-
  party API's uptime/rate limits for the core pipeline, and no video
  content or transcript ever leaves the deployment by default -
  relevant given this product's content can be sensitive.
- The tradeoff is real: local models (via Ollama) are generally weaker
  than the largest hosted models, and local inference needs real
  compute on the host running it. The `LLMProvider`/`EmbeddingProvider`
  abstraction (ADR 0004) exists specifically so a hosted provider can
  be added later as a configuration choice, not a rewrite - but none
  is implemented today, so that tradeoff is accepted as-is until a
  concrete need (e.g. quality below what local models can deliver for
  a specific task) justifies adding one.
