# Performance Benchmark

Run on 2026-10-07, measured inside the running `ai-video-api`
container against `http://localhost:8000` (so these numbers are the
FastAPI process's own response time, not Docker's host-port-publishing
overhead). This is a controlled local/containerized measurement, not
a production-traffic measurement - there is no production traffic for
this deployment (see `docs/audits/final-cv-evidence.md`).

## Environment

- Docker Desktop VM: 20 logical CPUs available, ~20GB RAM, no
  explicit per-container CPU/memory limit set on `ai-video-api`
  (`docker inspect`: `NanoCpus: 0`, `Memory: 0` - unlimited, shares
  the host VM's allocation).
- Database: the real dev PostgreSQL container (`ai-video-db`), real
  schema, real rows (not an in-memory/mocked DB).
- LLM: Ollama running on the host (`host.docker.internal:11434`),
  model `qwen3:8b` (8.2B parameters, Q4_K_M quantization). Confirmed
  live via `GET /api/ps`: `"size_vram": 0` - **running entirely on
  CPU**, no GPU acceleration active for this model in this
  environment.
- Real FAISS index: 7 vectors (~37KB) - this deployment's actual
  current data (see `docs/benchmarks/rag-evaluation.md` for why it's
  this small).
- Rate limiting disabled for this run (`RATE_LIMIT_ENABLED=false`) to
  measure raw endpoint performance rather than the rate limiter's own
  behavior - rate limiting itself is real and enabled by default in
  every other context (`app/core/rate_limit.py`).

## Method

`backend/scripts/benchmark_performance.py` - a dependency-free Python
script (stdlib `concurrent.futures.ThreadPoolExecutor` + `requests`,
already a project dependency; no new load-testing framework added for
three endpoints). Real authenticated requests against a real user
(id 2) and a real, already-processed video (id 4, 68s duration, real
transcript/embeddings) owned by that user.

**A real bug found and fixed while producing these numbers**: the
first run reported 100% errors on every endpoint. Root cause: the
benchmark minted its JWT with a `SECRET_KEY` passed as a `docker exec
-e` override, which only applies to that one exec'd process - the
already-running `uvicorn` server process was started earlier with a
different `SECRET_KEY` from its own environment, so every token the
benchmark minted failed signature verification against the live
server (`401 Invalid token`). Fixed by minting the token without
overriding the environment, so it's signed with the same key the live
server actually verifies against. Reported here because this is
exactly the kind of mistake that silently produces fabricated-looking
"it works" numbers if not caught - the first run's 100%-error output
was never used.

## Results

### Media-token issuance (`GET /videos/{id}/media-token`)
100 requests, concurrency 20, **0 errors**.

| Metric | Value |
|---|---:|
| Throughput | 118.77 req/s |
| p50 | 137.4 ms |
| p95 | 318.2 ms |
| p99 | 324.4 ms |
| Mean | 160.3 ms |

### Video metadata (`GET /videos/{id}`)
100 requests, concurrency 20, **0 errors**.

| Metric | Value |
|---|---:|
| Throughput | 139.38 req/s |
| p50 | 126.5 ms |
| p95 | 195.3 ms |
| p99 | 212.6 ms |
| Mean | 134.0 ms |

### RAG query (`POST /search/videos/{id}/rag`) - real retrieval + real LLM generation

The concurrent run (10 requests, concurrency 3, 120s timeout) **failed
100% of requests** - every request exceeded the 120-second timeout.
Two subsequent sequential, single-request measurements (generous
timeout) completed successfully:

| Sample | Status | Latency |
|---|---|---:|
| 1 (query: "Video này nói về điều gì?") | 200, real grounded answer | **210.4 s** |
| 2 (query: "Thông điệp chính của video là gì?") | 200 | **60.9 s** |

**n=2, high variance (60.9s to 210.4s) - this is not enough samples to
report a confident average**, but both numbers independently confirm
the same conclusion: a single real RAG query on this deployment, with
this model, on this hardware, takes on the order of **one to several
minutes**, entirely dominated by CPU-bound LLM generation (confirmed
`size_vram: 0`). The concurrent-load attempt's 100% timeout failure at
only 3-way concurrency is itself a real, honest data point: this
deployment cannot currently serve concurrent RAG requests within a
120-second budget on this hardware.

## Interpretation

- The two pure-backend endpoints (media-token, video metadata) are
  fast and handle real concurrent load cleanly (0 errors, p99 under
  325ms at 20-way concurrency) - the API/DB layer itself is not a
  bottleneck at this scale.
- RAG query latency is not a backend-engineering problem in this
  deployment - it is a **CPU-bound local-LLM-inference** problem. The
  retrieval side (FAISS + BM25 + RRF, see
  `docs/adr/0010-faiss-index-lifecycle.md`) contributes well under a
  second even at synthetic 100K-vector scale; the ~61-210 second
  figure is almost entirely the LLM forward pass.
- **Do not claim "production-scale" or "highly scalable" from these
  numbers.** They show the backend-engineering layer performs well
  under modest concurrent load, and they honestly expose that this
  deployment's current LLM-serving setup (CPU-only Ollama) could not
  serve even 3 concurrent RAG requests within 2 minutes on this
  hardware - a real, documented limitation, not a hidden one.

## How to reproduce

```bash
# inside the ai-video-api container, backend/ as the working directory
python scripts/benchmark_performance.py --user-id <real user id> --video-id <real, already-processed video id owned by that user>
```
