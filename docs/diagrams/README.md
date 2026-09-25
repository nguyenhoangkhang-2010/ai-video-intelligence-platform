# Architecture Diagrams

Source-of-truth diagrams for ReelSense, written as Mermaid so they render
directly on GitHub and stay in a diffable, version-controlled text format
instead of a binary `.drawio`/image file that silently drifts from the code.

Each diagram below is verified against the actual source at the time it was
written — file/module names in the diagrams are real, not illustrative.

- [`system.md`](system.md) — request-level system architecture (browser → frontend → API → data/AI infrastructure)
- [`ai_pipeline.md`](ai_pipeline.md) — the async video-processing pipeline (upload → ASR → understanding → indexing)
- [`rag_pipeline.md`](rag_pipeline.md) — the retrieval/RAG path a single chat/search request takes
- [`async_processing.md`](async_processing.md) — the Celery job lifecycle and state machine

The three `.drawio` files previously in this directory were empty
placeholders (0 bytes) and have been superseded by these.
