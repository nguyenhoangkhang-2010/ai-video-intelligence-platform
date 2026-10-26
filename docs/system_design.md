# System Design Overview

This is the entry point for understanding ReelSense's architecture -
a short overview with links to the real diagrams/decisions, not a
restatement of them. Everything linked here reflects the actual
implementation, verified against the running system, not aspirational
design.

## The shape of the system

```text
Browser --[JWT / media token]--> nginx* --> FastAPI --> PostgreSQL
                                               |
                                               +--> Redis --> Celery --> AI pipeline (8 stages)
                                               |
                                               +--> FAISS + BM25 (query-time RAG retrieval)
```

\* nginx only exists in the production Docker Compose stack; the dev
stack's browser talks to FastAPI directly. See the full diagram below.

- **[System diagram](diagrams/system.md)** - every component, every
  real connection, with the authorization/media-token boundary called
  out explicitly.
- **[Async processing diagram](diagrams/async_processing.md)** - the
  Celery job/stage lifecycle (claim, resume, retry).
- **[AI pipeline diagram](diagrams/ai_pipeline.md)** - the 8-stage
  per-video pipeline and which AI module backs each stage.
- **[RAG pipeline diagram](diagrams/rag_pipeline.md)** - the hybrid
  retrieval + reranking + generation flow behind chat/search.

## Why it's built this way

Every non-obvious decision has a real ADR - context, the alternative
considered, and the actual tradeoff, not just the conclusion:

- [0001 - Celery, not a workflow engine](adr/0001-celery-single-task-pipeline.md)
- [0002 - No Kafka/Kubernetes/OpenTelemetry at this scale](adr/0002-no-kafka-k8s-otel.md)
- [0003 - Per-stage resumability](adr/0003-processing-stage-resumability.md)
- [0004 - AI provider abstraction](adr/0004-ai-provider-abstraction.md)
- [0005 - Local-first AI](adr/0005-local-first-ai.md)
- [0006 - Media token scoping](adr/0006-media-token-scoping.md)
- [0007 - AI evaluation strategy](adr/0007-ai-evaluation-strategy.md)
- [0008 - Vector retrieval architecture](adr/0008-vector-retrieval-architecture.md)
- [0009 - Knowledge graph kept standalone](adr/0009-knowledge-graph-standalone.md)
- [0010 - FAISS index lifecycle (measured, not assumed)](adr/0010-faiss-index-lifecycle.md)

## What's measured, not assumed

- **[RAG retrieval evaluation](benchmarks/rag-evaluation.md)** - real
  retrieval stack, real (small) dataset, real results, explicit
  limitations.
- **[Performance benchmark](benchmarks/performance.md)** - real
  concurrent-load numbers for three representative endpoints,
  measured in this environment, not claimed in the abstract.

## What this is not

Not microservices (one FastAPI process + one Celery worker type,
sharing a codebase). Not Kubernetes (Docker Compose is the only
deployment target - see ADR 0002). Not evaluated against real
production traffic (none exists - every number in this repo's
benchmarks is a controlled local/containerized measurement, stated as
such).
