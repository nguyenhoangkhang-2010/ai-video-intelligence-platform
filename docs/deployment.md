# Production Infrastructure & Deployment

Covers what Phase 13 actually implemented: container runtime, Celery
hardening, CPU/GPU worker separation, retries, database/Redis
hardening, storage/vector strategy, health/readiness, observability
(logging/metrics/Prometheus/Grafana), security hardening, backup/
recovery, and deployment/rollback procedure with plain Docker Compose.

Nothing below claims Kubernetes, a specific cloud provider, or
autoscaling - none of that is implemented (see "Known limitations").

## 1. Architecture

```
                 nginx (prod only, port 80)
                   |
         +---------+---------+
         |                   |
      frontend             api  ----/metrics----> Prometheus (monitoring profile)
     (profile,                |
      not yet buildable -    /health, /health/live, /health/ready
      see below)              |
                +------------+------------+
                |            |            |
              Postgres      Redis      storage/ (named volume)
                             |
                     +-------+-------+
                     |               |
              celery (CPU)     celery-gpu (profile "gpu")
                     |               |
                     +-------+-------+
                             |
                    app.workers.video_processor.process_video
                             |
                     ProcessingPipeline
                             |
               VideoPipelineService (unchanged, Phases 1-10)
```

`process_video` is one monolithic Celery task covering the whole
pipeline (transcription -> summary -> embedding -> translation ->
quiz/chapter/flashcard) - see "CPU/GPU workers" below for what that
does and does not allow.

## 2. Environment configuration

See `.env.example` at the repository root - every variable is
documented there next to the `Settings` class/field it maps to (or,
for the handful that don't go through `Settings`, an explicit note
saying so: `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, Compose-only
`POSTGRES_*`/resource-limit/`GRAFANA_ADMIN_PASSWORD` variables, and
build-time-only `NEXT_PUBLIC_API_URL`).

Copy it to `.env` (development) or a separate `.env.production` file
(production - see "Deployment" below) and fill in real values.
`.env`/`.env.production` are git-ignored and must never be committed.

## 3. Service roles

| Service | Role | Compose |
|---|---|---|
| `db` | PostgreSQL - primary datastore | dev + prod |
| `redis` | Celery broker + result backend | dev + prod |
| `api` | FastAPI app (uvicorn) | dev + prod |
| `celery` | Default Celery worker (CPU) | dev + prod |
| `celery-gpu` / `worker-gpu` | Optional GPU-capable Celery worker | profile `gpu` |
| `frontend` | Next.js app | profile `frontend` (not yet buildable - empty scaffold, see Phase 12/13 audits) |
| `nginx` | Reverse proxy, sole public entrypoint | prod only |
| `prometheus` / `grafana` | Local monitoring stack | dev, profile `monitoring` |

## 4. CPU/GPU workers

`app/config/settings.py::CelerySettings` and `app/workers/celery_app.py`
declare two Celery queues, `celery_cpu` and `celery_gpu`, and route
`process_video` to whichever one `CELERY_TASK_QUEUE` names (default
`celery_cpu`). Both the default worker and the optional GPU worker
consume from *both* queues by default, so:

- Out of the box, nothing changes: one worker processes everything,
  exactly as before this phase.
- Enabling `--profile gpu` adds GPU-capable processing capacity
  without any further configuration.
- For **strict** separation (e.g. GPU-only videos, CPU-only videos),
  an operator would additionally: set `CELERY_TASK_QUEUE=celery_gpu`
  on the `api` service, and restrict each worker's `-Q` flag to a
  single queue. This is a deployment-level configuration change, not
  a code change.

**Known limitation:** because `process_video` is one task covering the
entire pipeline, this routes the *whole job* to CPU or GPU - there is
no per-stage routing (e.g. "run Whisper on GPU, everything else on
CPU"). That would require splitting the pipeline into multiple Celery
tasks, which is a business-logic change out of scope for this phase.

GPU device selection for AI inference itself is unrelated to Celery
queues: `WHISPER_DEVICE=cpu|cuda` (`app/config/settings.py::SpeechSettings`,
already implemented pre-Phase-13) controls Faster-Whisper's device,
with automatic fallback to CPU if CUDA is requested but unavailable
(`ai/speech/faster_whisper.py::_load_model`) - the application never
fails at import time due to missing CUDA. The embedding
(`FlagEmbedding`) and reranking (`sentence-transformers`) models
currently rely on their own libraries' automatic device detection
rather than an explicit setting; wiring an equivalent explicit
override for those is a reasonable future enhancement, not implemented
here.

`docker compose --profile gpu up` requires the NVIDIA Container
Toolkit on the host. The default (no `gpu` profile) never requires it.

## 5. Retries & failure recovery

- **`ProcessingJob` state machine is unchanged**: `PENDING -> RUNNING
  -> COMPLETED/FAILED`, still governed by
  `ProcessingJobRepository.claim_for_running()`'s atomic conditional
  UPDATE. This was already idempotent-safe before Phase 13 - a
  redelivered/retried Celery task for an already-claimed job is
  always a no-op (see `ProcessingPipeline.run()`).
- **Celery task-level retry** (`app/workers/video_processor.py`,
  `app/core/retry.py`): `process_video` retries, with exponential
  backoff and jitter, only on `TRANSIENT_EXCEPTIONS` (DB/Redis
  connectivity errors, network-level HTTP failures). This only
  provides real recovery for a failure *before* the job is claimed
  (e.g. a transient DB hiccup opening the session). Once claimed, any
  failure is marked `FAILED` and re-raised before Celery's retry logic
  is reached; a subsequent retry is a safe, deliberate no-op (job stays
  `FAILED`, not resurrected, not duplicated).
- **Ollama HTTP calls** (`ai/llm/ollama_client.py`): bounded retry (3
  attempts, exponential backoff) via `tenacity`, scoped to connection/
  timeout errors only - not to HTTP error statuses or an empty-but-
  well-formed response, which are not connectivity problems.
- **Deterministic/application errors are never retried** - e.g. "no
  speech detected in audio" (`ValueError`), malformed LLM JSON output
  (already handled by `ai/llm/json_utils.py` with a deterministic
  fallback, not a retry).
- **Temp files**: already cleaned safely via
  `tempfile.TemporaryDirectory()` (`ai/speech/pipeline.py`), which
  cleans up on both success and exception paths - unchanged in this
  phase, confirmed correct by audit.

## 6. Database / Redis hardening

`app/database/postgres.py` now passes `pool_size`, `max_overflow`,
`pool_timeout`, `pool_recycle`, `pool_pre_ping`, `echo` - all from
`DatabaseSettings`/env vars (`DB_POOL_SIZE`, etc. - see
`.env.example`) - instead of only `pool_pre_ping=True`. Defaults match
previous behavior closely enough to be a safe, backward-compatible
starting point; tune via env vars once you know your real concurrent
load.

Redis is the Celery broker/result backend only (no application-level
cache today). It is never published on a host port in production
Compose (`deployment/docker/docker-compose.prod.yml`) - only reachable
over the internal Compose network. Development Compose does publish
it (`6379:6379`) for local debugging convenience.

## 7. Storage & vector strategy

**Filesystem storage** (`app/config/settings.py::STORAGE_DIR` and
friends): uploads, generated artifacts, and the FAISS index all live
under one directory tree that both `docker-compose.yml` and
`docker-compose.prod.yml` already mount as a persistent volume
(`./storage` bind mount in dev, a `storage_data` named volume in prod)
for both the `api` and worker services - **this already survives
container restarts/recreation**, confirmed by inspecting both Compose
files.

An extensible `StorageBackend` interface now exists
(`backend/app/storage/`: `base.py`, `local.py`, `s3.py`, `factory.py`)
with a `local` (default, wraps the existing directory unchanged) and
an optional `s3` implementation (boto3, lazily imported - only
touched when `STORAGE_BACKEND=s3`). **Existing upload/pipeline code is
not migrated onto this interface in this phase** - it continues to use
`STORAGE_DIR` paths directly, since local filesystem + a persistent
volume already satisfies the actual requirement, and rewiring every
call site is a larger, separately-reviewable change.

**FAISS vector index** (`storage/faiss/video.index` +
`metadata.json`): already has file-locking for concurrent access
(`ai/embedding/faiss_lock.py`) and atomic, corruption-safe writes
(temp file + `os.replace`) from before this phase. Persists via the
same volume as above.

**Rebuild**: if the FAISS index/metadata is ever lost or corrupted,
run (with the same `DATABASE_URL` as the running deployment):

```bash
cd backend
python scripts/rebuild_faiss_index.py
```

This re-encodes every `chunk_text` already stored in the `embeddings`
Postgres table and re-inserts each one under its existing
deterministic `vector_id` - no other table changes, and no RAG/search
code needs to change afterward. Stop the worker (or pause processing)
first so nothing writes to the index mid-rebuild.

No migration to Qdrant or another vector database was made - none was
already established in this repository (only present as unused
scaffolding), and FAISS + Postgres already satisfies the stated
requirements.

## 8. Health, readiness, liveness

- `GET /api/v1/health` - kept for backward compatibility with
  existing Docker/Compose healthchecks and `nginx.conf`. Checks
  database connectivity.
- `GET /api/v1/health/live` - liveness: is the process able to handle
  a request at all? Checks nothing else - never fails due to a
  dependency outage.
- `GET /api/v1/health/ready` - readiness: same check as `/health`
  (database connectivity). Deliberately does **not** check Ollama or
  any other best-effort external service - losing LLM features
  temporarily should not pull a healthy API instance out of rotation.

All three are fast (a single `SELECT 1` at most) and never call an AI
model.

## 9. Logging

`app/config/logging.py::setup_logging()` (previously defined but never
called anywhere - a real pre-Phase-13 gap, meaning most `logger.info()`
calls across the codebase were silently dropped since the root logger
defaulted to `WARNING`) is now called at FastAPI startup
(`app/main.py`) and Celery worker startup (via the
`celery.signals.setup_logging` signal in `app/workers/celery_app.py`).

- Level: `LOG_LEVEL` (default `INFO`).
- Format: human-readable by default; set `LOG_JSON=True` for one-
  JSON-object-per-line output (log-aggregation-friendly).
- Every log line is tagged with the current HTTP `request_id` (set by
  `app/middleware/request_id.py`, propagated via a `contextvars`
  ContextVar - see `app/config/logging.py::ContextFilter`) or Celery
  `task_name`/`task_id` when applicable, so a request or task's logs
  can be correlated even across deeply nested service/pipeline calls.
- Never logs request/response bodies, headers, tokens, or other
  secrets - only timestamp/level/logger/message/request or task
  context.

## 10. Metrics

Two separate Prometheus exporters, in two separate processes:

- **API** (`app/core/metrics.py`): `GET /metrics` on the FastAPI app
  itself (unversioned, root-level - standard Prometheus convention).
  Exposes `http_requests_total`, `http_request_duration_seconds`
  (both labeled by route *template*, e.g. `/api/v1/videos/{video_id}`,
  never the resolved id - avoids unbounded cardinality), and
  `processing_jobs_active` (computed at scrape time via one indexed
  COUNT query; a DB error here degrades gracefully rather than
  breaking the whole endpoint).
- **Celery workers** (`app/workers/metrics.py`): a dedicated
  `prometheus_client` HTTP server started in-process on
  `METRICS_WORKER_PORT` (default `9100`, `9101` for the optional GPU
  worker). Exposes `celery_task_total{task_name,status}` and
  `celery_task_duration_seconds{task_name}`.

**Multiprocess caveat**: Celery's prefork pool forks one child process
per concurrency slot; `prometheus_client`'s registry is per-process, so
metrics from sibling processes are not visible to whichever process's
exporter happens to bind the port first. This module assumes/
recommends worker `--concurrency=1` (`CELERY_WORKER_CONCURRENCY`/
`CELERY_GPU_WORKER_CONCURRENCY` in `.env.example`, already a reasonable
choice for heavy AI tasks sharing a worker) - documented as a known
limitation rather than solved with `prometheus_client`'s multiprocess
mode, which was judged unnecessary complexity for this project's scale.

`GET /metrics` is never proxied by `deployment/nginx/nginx.conf`
(`location /metrics { return 404; }`) - it is scraped directly over
the internal Compose network by Prometheus, and **must not be
publicly exposed over the internet** in any deployment.

## 11. Prometheus / Grafana

`monitoring/prometheus/` and `monitoring/grafana/` (previously empty
scaffolding) now contain a minimal local monitoring stack, wired into
`docker-compose.yml` under the `monitoring` Compose profile - not
required for normal local development:

```bash
docker compose --profile monitoring up -d
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3001 (admin / admin by default)
```

The provisioned Grafana dashboard covers request rate, p95 request
latency, 5xx error rate, Celery task success/failure rate, p95 Celery
task duration, and active processing jobs. A few alert rules
(`monitoring/prometheus/alerts.yml`) are evaluated by Prometheus
itself; no Alertmanager is configured, so alerts are visible in
Prometheus's UI but not routed/notified anywhere.

This is only wired into the *development* Compose file. A real
production deployment typically runs Prometheus/Grafana as a
centrally-managed service scraping this stack's `/metrics` + worker
port(s) - adapt this profile's pattern into
`deployment/docker/docker-compose.prod.yml` if you want the same
stack there instead.

Distributed tracing (OpenTelemetry) was **not** added - no tracing
infrastructure existed in this repository before this phase, and the
phase spec explicitly says not to introduce it just to fill a box.
Documented here as a future enhancement only.

## 12. Security hardening applied

- `app/middleware/cors.py` now reads `settings.security.cors_origins`
  (`CORS_ORIGINS` env var, JSON array) instead of a hardcoded
  `http://localhost:3000` - **this was a real pre-existing bug**
  (`SecuritySettings.cors_origins` existed but was never read by the
  middleware). Production deployments must set this to their real
  public frontend origin(s).
- `deployment/nginx/nginx.conf`: baseline headers
  (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: strict-origin-when-cross-origin`) and an explicit
  `404` for `/metrics` so it can never be reached through the public
  reverse proxy.
- Database/Redis are never published on a host port in production
  Compose; only `nginx` (port 80) is.
- Both Dockerfiles already ran as a non-root user (Phase 12) -
  unchanged, still true.
- No changes to authentication/JWT logic - out of scope, not touched.

## 13. Backup / recovery

| Data | Persistent? | Backup? | Rebuildable? | Safe to delete? |
|---|---|---|---|---|
| PostgreSQL (`postgres_data` volume) | Yes | **Yes - back this up.** Use `pg_dump`/your platform's managed Postgres backups. | No - source of truth for users, videos, transcripts, quizzes, jobs, etc. | No |
| Uploaded videos / generated artifacts (`storage_data` volume / `./storage`) | Yes | Recommended if storage isn't itself redundant (e.g. plain local disk) | Uploads: no. Some generated artifacts (summaries, quizzes, etc.): only by reprocessing the video. | No (until you're certain nothing needs it) |
| FAISS index (`storage/faiss/`) | Yes (same volume) | Optional | **Yes** - `python scripts/rebuild_faiss_index.py` from the `embeddings` Postgres table | Yes, if Postgres is intact (rebuildable) |
| Redis | Yes (`redis_data` volume) but treated as disposable | No | Yes - Celery broker/result state, safe to lose (in-flight tasks would need to be resubmitted) | Yes |
| Logs (stdout, collected by your platform/Docker) | Depends on your log driver | Per your log retention policy | N/A | Yes |

No cloud backup service is implemented (no provider was already
established in this repository) - the table above is the recovery
strategy; wiring it to an actual backup destination (S3, a managed
Postgres backup feature, etc.) is a deployment-specific decision left
to whoever operates this in a real environment.

## 14. Deployment (generic Docker Compose)

This project has no Kubernetes/cloud-provider deployment - "deployment"
here means Docker Compose against a single host (or a small number of
hosts you manage yourself).

**Startup:**

```bash
cp .env.example .env.production   # fill in real production values
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production up -d --build
```

**Migrations (explicit - never run automatically):**

```bash
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production exec api alembic upgrade head
```

**Health verification:**

```bash
curl -f http://<host>/api/v1/health
```

(via `nginx`, which proxies `/api/` to the `api` service - see
`deployment/nginx/nginx.conf`.)

**Rollback / rebuild:**

```bash
# Roll back to a previous image/commit: check out that commit/tag,
# then rebuild and recreate just the affected service(s):
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production up -d --build api worker

# Full rebuild of everything:
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production up -d --build

# Stop everything (data in named volumes is preserved):
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production down
```

There is no automated blue/green or canary deployment mechanism - a
`down`/`up --build` cycle causes a brief outage. Acceptable for this
project's current scale; a zero-downtime strategy would need a load
balancer in front of multiple `api` replicas, which is not set up
here.

## 15. Known limitations

- **Frontend cannot be built/deployed** - `frontend/` is an empty
  scaffold (no application code, no lockfile); this is a pre-existing
  condition from before this phase, not something Phase 13 fixes.
- **Per-stage GPU/CPU task routing is not possible** - only whole-job
  routing, because `process_video` is one monolithic task (see
  section 4).
- **Embedding/reranking models don't have an explicit device
  override** - they rely on their own libraries' auto-detection;
  only Whisper has an explicit, tested `WHISPER_DEVICE` setting with
  CPU fallback.
- **Worker Prometheus metrics assume `--concurrency=1`** - see section
  10's multiprocess caveat.
- **No Kubernetes, autoscaling, or cloud-provider-specific deployment**
  - not implemented; this repository has no established target
    provider, and the phase spec explicitly excludes inventing one.
- **No distributed tracing** - not implemented; no tracing
  infrastructure existed beforehand.
- **Docker build/run could not be executed in this development
  environment** - the Docker CLI is installed but no daemon is
  running here; `docker compose config` (structural/YAML validation)
  was used instead for every Compose file and profile combination.
  Run `docker compose up --build` yourself to get a real build/run
  validation.
- **No Redis AUTH configured** - Redis is protected by not being
  published/reachable outside the Compose network in production, not
  by a password; adding `requirepass` is a reasonable future
  enhancement if network isolation alone isn't sufficient for your
  environment.
