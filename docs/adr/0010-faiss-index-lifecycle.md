# 0010 - FAISS index lifecycle: keep per-request reload, do not cache yet

## Status
Accepted - revisit if the trigger condition below occurs. Supersedes
the "currently negligible... not yet fixed" language in
[ADR 0008](0008-vector-retrieval-architecture.md) with an actual
measurement instead of an estimate.

## Context
`VectorStore.__init__` reloads the entire FAISS index from disk on
every construction, and `SemanticSearchService`/`get_rag_pipeline`
construct a fresh `VectorStore` on every request - flagged in ADR
0008 as a real but unmeasured scaling risk. Before deciding whether
to add a cache (and the write-invalidation complexity that requires,
since Celery workers write a new index on every embed/reprocess/delete),
this ADR measures the actual cost at several scales and compares it
against the actual cost of the rest of a real RAG request.

## Measurement

`backend/scripts/benchmark_faiss_lifecycle.py` (synthetic 1024-dim
vectors, the real `IndexBuilder`/`faiss.write_index`/`faiss.read_index`
code path, this deployment's real index is currently 7 vectors / ~37KB
so every size below is a synthetic stand-in - see
`docs/benchmarks/performance.md`):

| Vectors | Index size | Load time | Search time | Total FAISS overhead |
|---:|---:|---:|---:|---:|
| 1,000 | 3.91 MB | 1.61 ms | 0.80 ms | 2.41 ms |
| 10,000 | 39.06 MB | 35.36 ms | 6.87 ms | 42.23 ms |
| 50,000 | 195.31 MB | 174.95 ms | 35.66 ms | 210.62 ms |
| 100,000 | 390.63 MB | 410.98 ms | 56.74 ms | 467.72 ms |

Compared against a real, measured end-to-end RAG request on this
deployment (`docs/benchmarks/performance.md`): a single real RAG
query (real retrieval + a real qwen3:8b generation call via Ollama,
running on CPU - `size_vram: 0` confirmed live) took **~210 seconds**.

## Decision
**Keep the current per-request-reload architecture. Do not add
caching yet.**

Even at 100,000 vectors - a scale this deployment's real data (7
vectors) is nowhere close to reaching - the FAISS reload+search
overhead is at most ~468ms, which is **under 0.3% of a single real
request's actual end-to-end latency** (468ms vs ~210,000ms). The
measured bottleneck is overwhelmingly LLM generation (CPU-bound local
inference), not FAISS. Adding an in-process cache with write-
invalidation complexity (ADR 0008's documented concern: Celery writes
a new index on every embed/reprocess/delete, so a cache needs a real
invalidation signal to avoid serving stale search results) would add
real correctness risk to fix a cost that is currently negligible
relative to everything else in the request - this is the premature
optimization this project's own engineering principles explicitly
warn against.

## Alternatives considered
- **Option B (in-process cached index with invalidation)**: rejected
  for now - the measured benefit (saving up to ~468ms at a scale this
  deployment doesn't have) does not justify the added invalidation
  complexity and correctness risk while LLM generation is 3 orders of
  magnitude slower.
- **Option C (dedicated retrieval/index lifecycle abstraction)**:
  rejected for the same reason - there is no current operational
  problem this would solve that isn't already solved more cheaply by
  the fact that FAISS reload is not the bottleneck.

## Consequences
- The real, measured priority for reducing RAG latency on this
  deployment is LLM inference speed (GPU acceleration if available,
  a smaller/faster model, or streaming partial responses to the
  client), not FAISS caching - any future performance work should
  start there, backed by this same kind of measurement, not assumption.
- Revisit this decision if either (a) the real embedded corpus grows
  into the tens of thousands of vectors AND request volume grows
  enough that FAISS's now-small share of total latency starts to
  matter, or (b) LLM generation latency is independently solved (e.g.
  GPU acceleration bringing it from ~210s to under a second), at which
  point FAISS's ~468ms would become a much larger relative share of
  total request time and caching would be worth revisiting with fresh
  numbers.
