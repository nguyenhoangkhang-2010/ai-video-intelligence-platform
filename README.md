# ReelSense — AI Video Intelligence Platform

**Turn unstructured video into searchable, explainable, actionable knowledge.**

Upload a video → the platform transcribes it, chunks and embeds the
transcript, and exposes a hybrid (dense + lexical, RRF-fused, reranked)
retrieval stack that grounds a per-video AI chat and semantic search in
real transcript evidence — every answer comes with the exact source chunks
it was built from.

This README documents what the system **actually does today**, verified
against the source, not a roadmap of what it might do eventually. Where a
capability is backend-only, off by default, or intentionally not exposed,
that is stated explicitly rather than implied.

---

## Contents

- [What this is](#what-this-is)
- [30-second demo path](#30-second-demo-path)
- [System architecture](#system-architecture)
- [AI pipeline](#ai-pipeline)
- [Retrieval & RAG](#retrieval--rag)
- [Feature reference](#feature-reference)
- [Engineering decisions & trade-offs](#engineering-decisions--trade-offs)
- [Evaluation](#evaluation)
- [Testing](#testing)
- [Production hardening](#production-hardening)
- [Running locally](#running-locally)
- [Project structure](#project-structure)
- [Documentation](#documentation)
- [Known limitations](#known-limitations)

---

## What this is

Long-form video (lectures, technical talks, recorded meetings, tutorials)
is easy to record and hard to use afterward — there is no good way to find
"the ten seconds where they explained the deployment strategy" short of
scrubbing the whole timeline. ReelSense processes a video once, offline,
and turns it into several queryable representations of the same content:
a full transcript, a summary, best-effort chapters, quiz/flashcard study
material, and — the core of the project — a hybrid-retrieval index that
powers video-scoped semantic search and grounded AI chat, each answer
carrying the exact transcript chunks it came from.

## 30-second demo path

```text
Upload a recording
        ↓
AI processes it asynchronously (transcript → chunks → embeddings)
        ↓
Search: "where did they discuss the deployment strategy?"
        ↓
A ranked transcript segment comes back, with its source chunk index
        ↓
Ask instead: "what did they decide about the rollout timeline?"
        ↓
Grounded answer + the exact cited chunks it was built from
```

This is the single flow worth trying first — see
[`docs/diagrams/rag_pipeline.md`](docs/diagrams/rag_pipeline.md) for
exactly what happens on that request.

---

## System architecture

```text
Next.js frontend (ReelSense — Copper & Graphite design system)
        ↓  HTTP + JWT Bearer
FastAPI (backend/app) — auth, ownership-scoped CRUD, /api/v1/*
        ↓                                  ↓
   PostgreSQL                    Celery (Redis broker)
   (videos, transcripts,               ↓
    embeddings, jobs, ...)    Async AI pipeline (backend/ai)
        ↓                                  ↓
   FAISS vector index  ←───  faster-whisper → BGE-M3 → Ollama (qwen3:8b)
        ↓
Dense + BM25 → Reciprocal Rank Fusion → Cross-Encoder Reranking
        ↓
Grounded RAG (per-video, stateless) — answer + cited transcript chunks
```

Full diagram, with exact module names: [`docs/diagrams/system.md`](docs/diagrams/system.md).

**Stack**: FastAPI · PostgreSQL/SQLAlchemy/Alembic · Redis · Celery ·
FAISS · `rank_bm25` · `sentence-transformers` (cross-encoder) ·
`faster-whisper` · `FlagEmbedding` (BGE-M3) · Ollama (local LLM) ·
Next.js 14 (App Router) / TypeScript / Tailwind · Docker Compose ·
Prometheus/Grafana.

---

## AI pipeline

One Celery task runs every stage below for each uploaded video, in order,
reporting real progress as it goes (see
[`docs/diagrams/ai_pipeline.md`](docs/diagrams/ai_pipeline.md) for the
full diagram and what is deliberately *not* wired in):

```text
Video
  → Transcription (faster-whisper; optional VAD; optional diarization,
    off by default)
  → Transcript persisted (text, detected language, word count)
  → fan-out:
      Summary (Ollama, single strategy today)
      Embeddings (BGE-M3 → chunk → FAISS, FileLock-guarded)
      Translation (Ollama, target fixed to "en"; real translation —
        skipped only when the source is already English)
      Chapters (embedding-based topic segmentation + LLM titles;
        timestamps derived strictly from real ASR segment boundaries)
      Quiz (MCQ / true-false / short-answer, Ollama)
      Flashcards (Ollama, + TSV Anki export)
  → Video.status = processed
```

Every timestamp shown anywhere in the product (chapters, seek-to-play) is
derived from real ASR segment boundaries — there is no per-sentence
timestamp in the transcript itself (the backend does not produce one), so
the frontend does not invent one either.

## Retrieval & RAG

```text
Query (video-scoped)
  → Dense retrieval  (FAISS, cosine over BGE-M3 embeddings)
  → Sparse retrieval (BM25 over this video's own chunks)
  → Reciprocal Rank Fusion (rank-based, not raw-score blending —
    dense distance and BM25 score live on incomparable scales)
  → Cross-encoder reranking (ms-marco-MiniLM-L-6-v2; loaded once per
    process and cached; if the model can't load, RAG falls back to
    hybrid retrieval with no reranking rather than failing the request)
  → Grounded answer (Ollama), or one of three honest non-answers:
    empty_query / no_embeddings / no_relevant_chunks
  → sources[]: { vector_id, chunk_index, chunk_text, distance } — no
    fabricated similarity percentage, no fabricated timestamp
```

Full diagram: [`docs/diagrams/rag_pipeline.md`](docs/diagrams/rag_pipeline.md).
Retrieval is always scoped to a single video and RAG is stateless by
design — no conversation history is persisted server-side (a
`ChatHistory` model exists in the schema but is never written to; kept
that way deliberately rather than half-built into conversational memory
nothing currently needs).

---

## Feature reference

Legend: ✅ exposed end-to-end (frontend + API + real data) · 🔧 real,
backend-only (no frontend surface) · ⛔ intentionally not a product
feature (code exists, deliberately unexposed).

| Capability | Status | Notes |
|---|---|---|
| Auth (register/login/JWT) | ✅ | No OAuth, no refresh token, no password reset — none implemented. |
| Video upload | ✅ | Extension allowlist, size cap, path-traversal-safe filenames, all server-enforced. |
| Async processing + status polling | ✅ | Real `ProcessingJob.progress`/`current_step`, polled by the frontend. |
| Transcript | ✅ | Full text, language, word count. No per-sentence timestamps (backend doesn't produce them). |
| Summary | ✅ | Single "default" strategy. Schema allows for more; not implemented. |
| Translation | ✅ | Real LLM translation, target fixed to English. No language picker (nothing to pick). |
| Chapters | ✅ | Best-effort; can legitimately be empty. Click-to-seek uses real timestamps. |
| Quiz | ✅ | Read-only questions. No scoring/attempt-history endpoint exists. |
| Flashcards | ✅ | Front/back study cards + real TSV Anki export. "Completed" is local UI state only. |
| Semantic search (video-scoped) | ✅ | Dense-only by design (simpler, separate endpoint from RAG). |
| Hybrid retrieval (dense + BM25 + RRF) | ✅ | Wired into the RAG path specifically (see above), on by default. |
| Cross-encoder reranking | ✅ | Wired into the RAG path, on by default, graceful fallback if unavailable. |
| Grounded AI chat (RAG) | ✅ | Video-scoped, stateless, cited sources, four explicit statuses. |
| Meetings aggregate view | ✅ | One endpoint composing transcript+summary+translation+quiz — not a separate "meeting" domain. |
| FK-indexed, ownership-scoped API | 🔧 | Every video-scoped route 404s (never 403) on a resource you don't own. |
| Prometheus metrics + Grafana | 🔧 | Real instrumentation (`/metrics`, worker exporter), no frontend surface — ops-facing by design. |
| Offline AI evaluation framework | 🔧 | Real metric implementations + runnable CLI (see [Evaluation](#evaluation)) — deliberately never runs in the request path. |
| Speaker diarization | 🔧 | Implemented (`pyannote.audio`), off by default (`SPEECH_DIARIZATION_ENABLED=false`), no frontend surface. |
| Knowledge graph extraction | ⛔ | Entity/relation extraction code exists (`ai/knowledge_graph`) but is never called — no table, no endpoint. Computing it live would mean uncached, non-deterministic LLM calls per request; persisting it is a separate, larger change not made here. |
| Global search / global chat | ⛔ | Every search and chat call is scoped to one video by design. |
| Quiz scoring / attempt persistence | ⛔ | No such table or endpoint. |
| S3/MinIO storage | 🔧 | `StorageBackend` is S3-capable for reads/streaming; uploads still always write to local disk (see [Trade-offs](#engineering-decisions--trade-offs)). |
| Kubernetes | ⛔ | Manifests under `deployment/kubernetes/` are placeholders — not a working deployment target. |

---

## Engineering decisions & trade-offs

**FastAPI + SQLAlchemy/Alembic + PostgreSQL.** Ownership-scoped REST over a
relational schema is a good fit for CRUD-shaped resources (videos,
transcripts, processing jobs) with real relational integrity (FK
`ON DELETE CASCADE` on every child table, so deleting a video actually
removes everything derived from it — including its file and its FAISS
vectors, not just DB rows).

**Redis + Celery, single monolithic task per video.** Video processing is
I/O- and CPU-heavy (minutes, not milliseconds), so it has to be async;
Celery + Redis is the simplest correct choice that doesn't require
standing up a separate message broker. The trade-off taken deliberately:
one task runs the whole pipeline (transcribe → summarize → embed →
translate → chapter → quiz → flashcard) rather than a per-stage task
graph, which is simpler to reason about and debug at this scale, at the
cost of re-running the *entire* pipeline (including the expensive ASR
step) if a late stage fails.

**FAISS over a managed vector DB.** A managed vector database (Pinecone,
Qdrant Cloud, ...) buys multi-tenant scaling and operational simplicity
this project doesn't need yet — the entire corpus for any one deployment
is small (per-video chunk counts, not billions of vectors), a self-hosted
`IndexFlatL2` is exact (not approximate) and free, and the file-locked
add/replace design (`ai/embedding/vector_store.py`) already handles
concurrent Celery workers safely. The trade-off: exact search doesn't
scale past a few million vectors, and horizontal scaling would mean
re-architecting this layer, not just changing a config value.

**Dense + BM25 + RRF, not dense-only.** Dense embeddings miss exact
keyword/identifier matches (a product code, a person's name) that lexical
search catches trivially; BM25 alone misses paraphrase and synonymy. RRF
was chosen over a weighted score blend specifically because FAISS
distance and BM25 score live on incomparable scales — RRF only needs each
retriever's *rank ordering*, never its raw score magnitude, so adding a
third retriever later requires no rescaling logic.

**Cross-encoder reranking, with a real fallback.** A cross-encoder scores
`(query, candidate)` pairs jointly instead of independently, which
consistently improves top-k precision over first-stage retrieval alone —
at the cost of being far more expensive per candidate, which is why it
only reranks a small widened candidate set rather than the whole corpus.
Because it's a real model that can fail to load (no cached weights, no
network), the pipeline is written to degrade to hybrid-without-reranking
rather than fail the request — reliability over completeness.

**Local filesystem storage today, S3-capable, not S3-migrated.**
`StorageBackend` is a real Protocol with both a local and an S3/MinIO
implementation, and the streaming/read path already goes through it. The
upload *write* path still targets local disk directly — the AI pipeline
(ffprobe, faster-whisper) needs a real local file path, which an S3
object isn't, so making uploads S3-backed would mean also solving
"materialize this object to local disk for processing," a real, separate
piece of work not done here rather than quietly assumed.

**Ollama (local LLM) over a hosted API.** Every LLM-backed feature
(summary, quiz, flashcards, chapters, translation, RAG) goes through one
`OllamaClient` — no API keys in the deployment, no per-token cost, fully
offline-capable, at the cost of being bounded by local hardware (a
reasoning model on CPU can take tens of seconds per call, which is why
these are all async background-pipeline steps, never synchronous request
handlers, except RAG, which the user is actively waiting on and gets a
real thinking/loading state for).

---

## Evaluation

`backend/ai/evaluation/` is a real, domain-agnostic evaluation framework
(~1,300 lines, its own test suite) — deliberately never imported by any
production request path, since evaluation must stay reproducible and
offline, not run against live traffic.

**What it measures:**

- **Retrieval / reranking** — Precision@K, Recall@K, Mean Reciprocal
  Rank, NDCG@K (`ai/evaluation/metrics/retrieval.py`), all operating on
  generic ranked-ID lists so the exact same functions score a baseline
  retriever, hybrid retrieval, or a reranked ranking.
- **RAG quality** — deterministic (no-LLM-call, always-available) lexical
  faithfulness/answer-relevance/context-relevance proxies, plus optional
  LLM-judge variants that reuse the same `OllamaClient`
  (`ai/evaluation/rag_eval.py`), plus optional ROUGE/BERTScore/RAGAS
  wrappers (`ai/evaluation/rouge.py`, `bertscore.py`, `ragas_eval.py`).
- **Generation** — candidate-vs-reference metrics for any free-text
  output (summary, translation, chapter titles).
- **System performance** — a latency/throughput harness
  (`ai/evaluation/latency.py`).

**Running it**: `backend/scripts/run_evaluation.py` is the runner that
wires this framework to the real, live retrieval stack and the real
`RAGPipeline` — not a mock:

```bash
cd backend
python scripts/run_evaluation.py list-chunks --video-id 1
python scripts/run_evaluation.py retrieval --video-id 1 \
    --fixture ai/evaluation/fixtures/example_retrieval_queries.json
python scripts/run_evaluation.py rag --video-id 1 \
    --fixture ai/evaluation/fixtures/example_rag_questions.json
```

`retrieval` prints a baseline-vs-treatment table: dense-only retrieval
against whatever this deployment's live config actually is (hybrid +
reranking, if enabled) — the same `BenchmarkRunner.compare()` mechanism
that would compare any two retrieval configurations.

**No benchmark numbers are published here.** Retrieval evaluation needs a
set of `(query, relevant_chunk_ids)` judgments a human who has actually
watched the target video authored by hand
(`ai/evaluation/fixtures/example_retrieval_queries.json` is the schema,
explicitly marked as an example, not a dataset) — fabricating those
judgments would produce a number that looks like evidence and isn't. Run
it yourself against a video and a query set you can actually judge to get
a number that means something.

---

## Testing

**Backend**: 503 tests (pytest), covering auth/ownership (every
video-scoped endpoint has an explicit "not owned → 404" test), upload
validation, deletion cleanup (file + FAISS vectors), processing job
lifecycle/status-transition validation, translation, hybrid retrieval
wiring (with reranker-unavailable fallback), semantic search, and the AI
modules' own unit tests (chapter detection, quiz/flashcard generation,
diarization, evaluation metrics, retrieval, reranking). Run with:

```bash
cd backend
pytest tests/ -q
```

**Frontend**: TypeScript strict mode (`noUncheckedIndexedAccess`), typed
end-to-end against the backend's actual Pydantic response shapes (every
`types/*.ts` file cross-references the schema it mirrors). No automated
frontend test suite exists yet — `npx tsc --noEmit` and `next build` are
the current verification surface (see `frontend/package.json`).

---

## Production hardening

Verified in the source, not aspirational:

- **Upload security**: filename sanitized to a safe basename before it
  ever touches the filesystem (path-traversal-safe), extension allowlist,
  streamed size cap enforced before the file is fully written.
- **Deletion cleanup**: deleting a video removes the physical file (via
  `StorageBackend`) and its FAISS vectors (`VectorStore.replace`), not
  just the DB row — best-effort, logged rather than failing the request
  if storage cleanup itself errors.
- **Auth**: `User.is_active` is enforced on login *and* on every request
  for an already-issued token (a deactivated account stops working
  immediately, not just at next login); 401 for missing/invalid
  credentials never distinguishes "wrong password" from "unknown email."
- **Ownership**: every video-scoped route resolves through
  `owner_id`/ownership-checked repository methods — 404, never 403, so a
  resource's existence for another user is never revealed.
- **Database**: FK indexes on every foreign key that lacked one, an N+1
  query eliminated in semantic search (batched from the single already-
  fetched embedding list instead of one query per FAISS hit), 19
  sequential Alembic migrations with no branching.
- **Migrations run automatically**: `docker compose up --build` on a
  clean database no longer requires anyone to know `alembic upgrade
  head` exists — `backend/scripts/docker-entrypoint.sh` runs it (once,
  idempotently) before the API process starts.
- **Celery**: `task_acks_late` + `task_reject_on_worker_lost` (crash-safe
  redelivery), bounded exponential-backoff retry for transient failures
  only (not business-logic failures), an atomic race-safe job claim
  preventing duplicate processing on redelivery, and a real healthcheck
  (the worker's own Prometheus metrics port — not the API's unrelated
  HTTP port, which this container never listens on).
- **Observability**: `/metrics` (API) and a dedicated worker metrics
  exporter, both real `prometheus_client` instrumentation consumed by a
  provisioned Grafana dashboard (`monitoring/`) and Prometheus alert
  rules (`APIDown`, `HighAPIErrorRate`, `HighCeleryTaskFailureRate`,
  `ProcessingJobBacklogGrowing`).

## Running locally

```bash
cp .env.example .env          # fill in SECRET_KEY etc. — see the file's own comments
docker compose up --build
```

This starts PostgreSQL, Redis, the API, and a Celery worker. Migrations
run automatically on the API container's first boot (see above) — no
manual step required. API docs: `http://localhost:8001/docs`.

Frontend (separate terminal):

```bash
cd frontend
cp .env.example .env.local    # NEXT_PUBLIC_API_URL — defaults to http://localhost:8001
npm install
npm run dev
```

Then open `http://localhost:3000`, register an account, and upload a
video.

---

## Project structure

```text
AI-Video-Intelligence-Platform/
├── backend/
│   ├── ai/                 # Pure AI/ML logic — no FastAPI/DB dependency
│   │   ├── speech/ diarization/ embedding/ retrieval/ reranking/
│   │   ├── summarization/ translation/ chapter_detection/
│   │   ├── quiz_generation/ flashcards/ knowledge_graph/
│   │   ├── llm/             # OllamaClient, shared by every LLM-backed stage
│   │   └── evaluation/      # Offline metrics + fixtures + runner
│   ├── alembic/             # 19 linear migrations
│   ├── app/
│   │   ├── api/v1/endpoints/  auth/  config/  core/
│   │   ├── models/ schemas/ repositories/ services/
│   │   ├── pipelines/       # VideoPipelineService orchestration
│   │   ├── workers/         # Celery task + metrics
│   │   └── storage/         # Local / S3 StorageBackend
│   ├── scripts/             # rebuild_faiss_index.py, run_evaluation.py, docker-entrypoint.sh
│   └── tests/                # 503 tests
├── frontend/src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # workspace panels, ui/ design system
│   ├── hooks/ services/ types/ lib/
├── deployment/               # docker/ (prod compose + hardened images), nginx/, kubernetes/ (placeholder)
├── monitoring/                # Prometheus + Grafana provisioning
└── docs/
    ├── api/rest_api.md        # Full API contract
    ├── deployment.md          # Ops/infra deep-dive
    └── diagrams/               # This README's Mermaid diagrams
```

## Documentation

- [`docs/api/rest_api.md`](docs/api/rest_api.md) — the full, current API
  contract (every endpoint, auth rule, status code, response shape).
- [`docs/deployment.md`](docs/deployment.md) — infrastructure deep-dive:
  health/readiness, storage backends, retry semantics, metrics, backup.
- [`docs/diagrams/`](docs/diagrams/) — the four Mermaid diagrams linked
  above.

## Known limitations

- Single monolithic Celery task per video — a late-pipeline failure
  re-runs the whole pipeline, including re-transcription.
- Exact (not approximate) FAISS search — would need re-architecting to
  scale past roughly a few million vectors.
- No frontend automated test suite yet.
- No published evaluation numbers — the framework and runner are real;
  no labeled dataset ships with the repo (see
  [Evaluation](#evaluation)).
- Kubernetes manifests are placeholders, not a working deployment target.

---

## Contributing

Please open an issue before submitting a pull request. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT — see [`LICENSE`](LICENSE).

## Author

**Nguyen Hoang Khang**
Data / AI Engineer · Ho Chi Minh City University of Industry and Trade
