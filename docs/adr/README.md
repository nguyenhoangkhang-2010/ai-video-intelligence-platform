# Architecture Decision Records

Lightweight ADRs for decisions where the alternative was genuinely
considered (not just "the obvious default") and the reasoning would
otherwise only live in commit messages or a chat transcript. Each one
is Context / Decision / Consequences; no new tooling, just markdown.

Not every architectural choice in this codebase has (or needs) an
ADR - these cover the ones where someone picking this project back up
later would reasonably ask "why isn't this Kafka/Kubernetes/a vector
DB?" or "why does this module exist standalone instead of wired into
the pipeline?".

| # | Decision |
|---|---|
| [0001](0001-celery-single-task-pipeline.md) | Celery + a single resumable task, not a workflow engine |
| [0002](0002-no-kafka-k8s-otel.md) | No Kafka, Kubernetes, or OpenTelemetry at this scale |
| [0003](0003-processing-stage-resumability.md) | Per-stage resumability via a `ProcessingStage` table |
| [0004](0004-ai-provider-abstraction.md) | `LLMProvider`/`EmbeddingProvider` as Protocols, not a full plugin framework |
| [0005](0005-local-first-ai.md) | Local-first AI (Ollama, faster-whisper) over hosted APIs |
| [0006](0006-media-token-scoping.md) | Short-lived, resource-scoped media tokens instead of the main access token in URLs |
| [0007](0007-ai-evaluation-strategy.md) | Deterministic-first AI evaluation, model-based metrics opt-in, no hardcoded domain data |
| [0008](0008-vector-retrieval-architecture.md) | A single shared FAISS flat index with hybrid search/reranking layered on top, not a dedicated vector DB |
| [0009](0009-knowledge-graph-standalone.md) | Knowledge graph extraction kept standalone, not wired into the mandatory pipeline |
