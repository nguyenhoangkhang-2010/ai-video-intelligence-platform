# 0008 - A single shared FAISS flat index with hybrid search/reranking layered on top, not a dedicated vector DB

## Status
Accepted. The reload-per-request lifecycle question flagged below has
since been measured and resolved in
[ADR 0010](0010-faiss-index-lifecycle.md) - keep reading there for the
actual numbers before assuming it still needs fixing.

## Context
Semantic search over video transcripts needs nearest-neighbor lookup
over embeddings. Dedicated vector databases (Pinecone, Weaviate,
Qdrant, pgvector-as-a-service) exist for this; this project uses
plain FAISS (`ai/embedding/vector_store.py`, `IndexFlatL2`) with
metadata in Postgres.

## Decision
One shared FAISS flat (exact, non-approximate) index on disk for all
videos/users, filtered by `video_id` at query time via the stored
metadata - not one index per video, not a managed vector-DB service.
Retrieval itself is layered on top as swappable `Retriever`
implementations (`ai.retrieval.dense_retriever`, `sparse_retriever`,
`hybrid_search` fusing both via RRF) with an optional
`CrossEncoderReranker`, wired together per-request in
`app/api/deps.py::get_rag_pipeline` based on
`settings.retrieval.hybrid_enabled`/`reranking_enabled`.

## Consequences
- No managed vector-DB dependency/cost; FAISS is a library, not a
  service to operate.
- `IndexFlatL2` is exact (no recall loss from approximate search) and
  simple, at the cost of scaling linearly with total embedded content
  across every video, not sub-linearly - acceptable while the corpus
  is small.
- **Known, currently-low-impact structural issue (not yet fixed):**
  `get_rag_pipeline` builds a fresh `SemanticSearchService` ->
  `VectorStore` on every single request (no caching across requests),
  and `VectorStore.__init__` unconditionally reloads the whole index
  from disk (`ai/embedding/vector_store.py:32-33`). At the current
  dev-scale index size (~37 KB) this is sub-millisecond and invisible;
  it is a genuine scaling risk once the corpus grows, because the cost
  is `O(index size)` per chat/search/RAG request, not O(1). Caching
  the loaded index in-process was deliberately **not** done in this
  pass: Celery workers write a new index to disk on every embed/
  reprocess/delete (`vector_store.py`'s locked read-modify-write-save
  cycle), so an API-process-level cache needs an explicit invalidation
  signal or it would silently serve stale search results for newly
  uploaded/reprocessed videos - a correctness regression, not just a
  performance one. This needs a deliberate design (e.g. a cache keyed
  on the index file's mtime, or an explicit invalidation signal from
  the worker) before it's safe to add, not a quick `@lru_cache`.
