# Final CV Evidence Matrix

Produced at the end of the `feat/cv-enterprise-hardening` pass. Every
row was verified live during this pass (not inherited from a prior
report) unless marked otherwise.

| Claim | Evidence | Verification | Metric | CV-safe wording |
|---|---|---|---|---|
| Short-lived, video-scoped media tokens | `backend/app/auth/jwt.py::create_media_token`, `dependencies.py::_resolve_media_token` | VERIFIED (live curl: valid→200, wrong video_id→403, main-token-as-media→401) | 300s expiry | "Implemented short-lived, video-scoped JWT media authorization, live-verified against wrong-resource and wrong-scope attempts." |
| HTTP Range / 206 streaming | `FileResponse` (Starlette) | VERIFIED (live curl: `Range: bytes=0-4` → `206`, correct `Content-Range`) | — | "Supports HTTP Range/206 Partial Content streaming." |
| Consistent ownership enforcement (no IDOR) | `get_by_id_and_owner` pattern across all video-scoped routes | VERIFIED (live curl: cross-user access to video/media-token all 404) | — | "Enforced consistent, information-leak-free ownership authorization (404, never 403)." |
| Zero raw-SQL-injection surface | one literal `.execute(text("SELECT 1"))` | VERIFIED (grep, this pass) | 1 raw query, static literal | "Maintained a zero SQL-injection-surface backend, audited." |
| Real RAG retrieval evaluation | `backend/scripts/benchmark_rag_retrieval.py`, `docs/benchmarks/rag-evaluation.md` | MEASURED (real data, real stack, this pass) | 10 queries / 6 real documents; reranking: MRR 0.900→0.850 | "Ran a real (small, disclosed-limitation) RAG retrieval evaluation against the live stack." Do NOT say "benchmarked RAG quality" without the size caveat. |
| Real performance benchmark | `backend/scripts/benchmark_performance.py`, `docs/benchmarks/performance.md` | MEASURED (this pass) | media-token/metadata: 100 req/20 concurrency, 0 errors, p99 <325ms; RAG query: 60-210s/request on CPU | "Measured real concurrent-load performance for representative endpoints." Do NOT say "production-scale" or "highly scalable." |
| FAISS lifecycle decision backed by data | `backend/scripts/benchmark_faiss_lifecycle.py`, `docs/adr/0010-faiss-index-lifecycle.md` | MEASURED (synthetic scale, this pass) | 100K vectors: ~468ms total overhead, vs. ~210,000ms real LLM call | "Made an evidence-based decision not to cache a vector index after measuring its real cost was <0.3% of request latency." |
| Pipeline failure recovery | `backend/tests/pipelines/test_failure_recovery_integration.py` + pre-existing repository concurrency tests | VERIFIED (new integration test, passes; 2 pre-existing real multi-connection concurrency tests cited) | 1 new integration test + 2 pre-existing concurrency tests | "Verified job+stage-level crash recovery and concurrent-claim safety via integration tests (real multi-connection concurrency, not mocks)." Call this "failure-recovery integration testing," not "chaos engineering" (no fault-injection framework used). |
| Summarization test coverage | `backend/tests/{ai/summarization,workers,pipelines}/*summar*` | VERIFIED (16 new tests, this pass) | 0 → 16 tests | "Added test coverage for the one mandatory pipeline stage that previously had none." |
| Browser E2E coverage | `frontend/e2e/critical-path.spec.ts` | VERIFIED (real browser, real backend, this pass; 1 retry observed under real resource contention, documented) | 1 suite, 2 tests | "Added one real, browser-driven E2E test covering registration through real media-token-gated playback." Do NOT say "comprehensive E2E coverage." |
| Lint gate adopted and blocking | `backend/ruff.toml`, `.github/workflows/lint.yml` | VERIFIED (0 findings, this pass; was 786 under ruff's raw defaults before a real config was adopted) | select=F, 13 real findings fixed (incl. 1 real latent bug) | "Adopted and enforced a real lint gate, finding and fixing a real bug (`__all__` referencing a renamed symbol) in the process." |
| Kubernetes production deployment | `deployment/kubernetes/` | **NOT APPLICABLE** - deleted this pass (confirmed 0 bytes, never implemented) | — | Do NOT claim Kubernetes anywhere. |
| ML model training/fine-tuning | — | **NOT APPLICABLE** | — | Do NOT claim "ML Engineer" work - this project orchestrates pre-trained models. |
| Production traffic / scale | — | **NOT MEASURED, NOT APPLICABLE** - prod DB was empty except this session's throwaway, cleaned-up verification rows | — | Do NOT claim any user/traffic/scale number. |
| Test coverage percentage | `pytest-cov` installed | **NOT MEASURED** - never actually run and recorded this pass | — | Do NOT cite a coverage percentage. |
| 660 backend / 57 frontend tests | live `pytest -q` / `vitest run` output | VERIFIED (this pass, fresh) | 660 + 57 = 717 automated tests, plus 1 E2E suite (2 tests) | "717 automated tests (660 backend, 57 frontend) plus a real browser E2E suite." |

## Explicitly re-verified this pass (not inherited)

- Horizontal privilege escalation (cross-user access to video/media-token): re-tested live, all 404/401/403 as expected.
- Media-token full chain (valid/wrong-video/wrong-scope): re-tested live with fresh tokens.
- `ragas` import failure: reproduced live (`ModuleNotFoundError`), and the proposed fix (pinning to `0.1.21`) was actually attempted and shown to cascade into breaking `pyannote.audio`/numpy/langchain - not assumed, tested.
- Backend/frontend/E2E test suites: all run fresh at the end of this pass (660/57/2 passing), not assumed from an earlier number.
