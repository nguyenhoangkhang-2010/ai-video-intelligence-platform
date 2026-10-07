# Pre-Upgrade Baseline (feat/cv-enterprise-hardening)

Recorded at the start of the CV-enterprise-hardening pass, before any
of this branch's changes except the ones noted inline. Every number
here was produced by actually running the command shown, not read
from a prior report.

## Git

- Branch created from: `feat/frontend`
- Branch: `feat/cv-enterprise-hardening`
- `HEAD` at branch-creation time: `7571f33` (plus a large uncommitted
  working tree from this same session's earlier Phases C-J work,
  listed by `git status --short` as 24 modified + 14 new files -
  those are pre-existing, untouched by this pass unless explicitly
  noted).

## Backend

- `pytest -q` (inside `ai-video-api`, real Postgres): **646 passed**,
  0 failed, 146 warnings.
- `alembic check`: **No new upgrade operations detected.**

## Frontend

- `npx vitest run`: **11 files, 57 passed**, 0 failed.
- `tsc --noEmit`: clean.
- `next lint`: clean, no warnings/errors.
- `next build`: succeeds; 7 static routes + 1 dynamic (`/videos/[id]`).

## Containers

All 10 containers (dev: `ai-video-api`, `ai-video-celery`,
`ai-video-db`, `ai-video-redis`; prod: `ai-video-intelligence-prod-{api,worker,frontend,db,redis,nginx}-1`)
report `healthy`/`Up`.

## CI

5 workflows in `.github/workflows/`: `tests.yml` (backend pytest,
blocking), `lint.yml` (ruff, `continue-on-error: true` -
non-blocking), `ci.yml` (frontend install/lint/build/test),
`docker.yml` (build-verify only, `push: false`), `release.yml`
(tag-triggered GHCR push, no deploy target).

## RAG / Retrieval

Hybrid dense (FAISS `IndexFlatL2`) + sparse (BM25 via `rank-bm25`)
fused with RRF, optional cross-encoder reranking - both on by default
(`settings.retrieval.hybrid_enabled`/`reranking_enabled`). Confirmed
live: `app/api/deps.py::get_rag_pipeline`.

## FAISS

Single shared on-disk index (`storage/faiss/video.index`), currently
~37KB (dev-scale). `VectorStore.__init__` reloads the full index from
disk on every construction - confirmed in code
(`ai/embedding/vector_store.py`), not yet benchmarked at any larger
synthetic scale before this pass.

## AI Evaluation

Three intended tiers before this pass: deterministic
(`ai/evaluation/rag_eval.py`, `metrics/`), model-based opt-in
(`bertscore.py`, lazily imported), and an external-library tier
(`ragas_eval.py`) that was **broken**: live-reproduced
`ModuleNotFoundError: No module named
'langchain_community.chat_models.vertexai'` when importing `ragas`
inside the running `ai-video-api` container.

## Kubernetes

`deployment/kubernetes/` existed with 4 files (`README.md`,
`deployment.yaml`, `ingress.yaml`, `service.yaml`), **all 4 confirmed
0 bytes** via `ls -la` before removal in this pass.

## Secrets

`.gitignore` correctly ignores `.env` and `.env.*`; `git ls-files`
confirms only `.env.example` is tracked, and it contains only safe
placeholders (`CHANGE_ME_TO_A_LONG_RANDOM_VALUE`, `postgres`, empty
`HF_TOKEN=`) - verified by direct inspection, not assumed. Local
(untracked, never-committed) `.env`/`.env.production` files contain
real-looking credentials (an HF token, a Postgres password with
onward reuse into `SECRET_KEY`) that should be rotated - flagged
directly to the project owner earlier this session; rotation itself
is outside what this pass can verify (it requires action against the
real external services those credentials belong to).

## E2E

No browser automation framework present. Confirmed via `package.json`
(frontend): no `@playwright/test`, no `cypress`.

## Documentation

Confirmed 0-byte: `docs/README.md`, `docs/roadmap.md`,
`docs/system_design.md`, `docs/api/openapi.md`,
`docs/architecture/{README,ai_pipeline,backend,database,frontend}.md`,
`docs/benchmark/{README,latency,rag,summary}.md`.
