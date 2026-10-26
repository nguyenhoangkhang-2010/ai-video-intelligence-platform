# CI Strategy

Three deliberately separate tiers - not merged into one workflow, and
not run with the same failure semantics.

## Required CI (blocking, every push/PR)

Deterministic, fast, no external AI service dependency.

- **`.github/workflows/tests.yml`** - full backend `pytest` suite
  (660 tests as of this pass). SQLite, no real Postgres/Redis/Ollama.
- **`.github/workflows/lint.yml`** - `ruff check backend`
  (`backend/ruff.toml`, `select = ["F"]`). Blocking as of this pass -
  see that config file's own comment for why it was informational
  before and what made it safe to flip.
- **`.github/workflows/ci.yml`** - frontend: install -> lint ->
  typecheck (`tsc --noEmit`) -> `vitest run` -> `next build`.
- **`.github/workflows/docker.yml`** - build-verification only
  (`push: false`) for all three images.

A failure in any of these blocks the PR. None of them need Docker,
Ollama, or a real database reachable from the CI runner.

## Optional / manual (never run in CI)

Needs real data, real human judgment, or a real local LLM - would be
either meaningless or dishonest to gate CI on.

- **`backend/scripts/run_evaluation.py`** - scores THIS deployment's
  real retrieval/RAG quality against a real, already-processed video;
  needs hand-authored ground truth a human has to write after
  actually watching the video. Never run automatically.
- **`backend/scripts/benchmark_rag_retrieval.py`** - the real
  dense/sparse/hybrid/reranking comparison behind
  `docs/benchmarks/rag-evaluation.md`. Rerun by hand when the
  retrieval stack changes, not on every commit.

## Benchmark scripts (never run in CI)

Produce measured numbers for `docs/benchmarks/`, intentionally
decoupled from merge-blocking CI - a performance regression is worth
knowing about, but it should never block an unrelated PR, and these
need a real backend + Ollama reachable, which CI's hosted runners
don't provide for this project.

- **`backend/scripts/benchmark_performance.py`** - the real
  concurrent-load numbers in `docs/benchmarks/performance.md`.
- **`backend/scripts/benchmark_faiss_lifecycle.py`** - the synthetic-
  scale FAISS reload/search numbers behind
  `docs/adr/0010-faiss-index-lifecycle.md`.
- **`frontend/e2e/critical-path.spec.ts`** (Playwright) - needs the
  real dev stack AND Docker reachable from the test runner; see
  `docs/testing/e2e.md` for why this isn't CI-gated either.

Re-run any of these by hand (see each doc's "How to reproduce"
section) whenever a change plausibly affects what they measure - not
on a schedule, and never silently assumed still valid indefinitely.
