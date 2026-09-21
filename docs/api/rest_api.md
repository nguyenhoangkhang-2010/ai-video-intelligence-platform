# REST API Reference

Base path: `/api/v1` (except `/`, `/metrics`, `/docs`, `/redoc`, `/openapi.json`, which are unversioned). Interactive, always-current docs are served at `/docs`.

Authentication is a JWT Bearer token (`Authorization: Bearer <token>`), obtained from `POST /auth/login`. Every video-scoped resource below is **ownership-checked**: the resource's video must belong to the authenticated user, or the endpoint returns `404 Not Found` (never `403` - existence of another user's resource is never revealed).

This document reflects the actual, current API surface after the backend-completion phase. It replaces nothing else - `docs/deployment.md` covers infrastructure/production topics (health, metrics, storage backends, retries) and is not duplicated here except where an endpoint's contract depends on it.

## Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Create a user. Body: `{username, email, password}`. Returns `201` + `UserRead`. |
| POST | `/auth/login` | No | Body: `{email, password}`. Returns `{access_token, token_type: "bearer"}`. |
| GET | `/users/me` | Yes | Current user's `{id, username, email}`. |

No refresh token, logout, or password-reset endpoint exists - the client discards the token to "log out."

## Videos

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/videos` | Yes | List the current user's videos. |
| GET | `/videos/{video_id}` | Yes | Single video. |
| GET | `/videos/{video_id}/status` | Yes | Lightweight `{id, status}` for polling. |
| POST | `/videos/upload` | Yes | Multipart upload (`file`). Creates the `Video` (status `uploaded`) and a `ProcessingJob` (status `PENDING`), dispatches async processing, and returns immediately. |
| PUT | `/videos/{video_id}` | Yes | Update `title`/`language`/`status`. |
| DELETE | `/videos/{video_id}` | Yes | Deletes the video and everything derived from it (transcript, summaries, chapters, quizzes, flashcards, translations, embeddings, processing jobs - `ON DELETE CASCADE`). |
| GET | `/videos/{video_id}/stream` | Yes\* | **Video delivery/playback.** See below. |
| GET | `/videos/{video_id}/processing-jobs` | Yes | All processing jobs for this video. |

`Video.status`: `uploaded` -> `processing` -> `processed` \| `failed`.

### Video delivery (`GET /videos/{video_id}/stream`)

\* Accepts the token via the standard `Authorization` header **or** a `?token=` query parameter - a browser `<video>` element cannot attach custom headers, so the query-parameter form exists specifically for that case. Never accepted on any other endpoint.

Goes through the storage abstraction (`app/storage/`, local filesystem by default, optional S3/MinIO - see `docs/deployment.md`), not a hardcoded path:

- **Local backend**: streams the file directly (`FileResponse`, native HTTP Range/seek support, no full-file memory load).
- **S3/MinIO backend**: `307` redirect to a presigned URL; the client fetches the bytes directly from the object store.
- `404` if the video/file doesn't exist (or isn't owned by the caller).

Known constraint: today, uploaded files are always written to local disk (the AI pipeline - ffprobe, Whisper - needs a real local path, which S3 objects aren't). Setting `STORAGE_BACKEND=s3` makes this endpoint S3-*capable*, but does not by itself move uploaded video bytes into S3 - that would require also migrating the upload write path, a separate, larger change.

## Processing Jobs

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/processing-jobs` | Yes | All processing jobs belonging to the current user's own videos. |
| GET | `/processing-jobs/{job_id}` | Yes | Single job, only if it belongs to one of the current user's videos. |
| PATCH | `/processing-jobs/{job_id}` | Yes | Update `status`/`error_message`. Ownership-checked first. |

**Security fix (this phase):** all three were previously unauthenticated and unscoped - `GET /processing-jobs` returned every job for every user, and the other two accepted any job id regardless of owner. `ProcessingJob` has no direct owner column; ownership is now resolved via a join through its `Video.owner_id`.

Status values: `PENDING` -> `RUNNING` -> `COMPLETED` \| `FAILED`, with `progress` (0-100) and `current_step`. The `PENDING -> RUNNING` transition is an atomic, race-safe claim (`ProcessingJobRepository.claim_for_running`) - unchanged by this phase, and Celery retry behavior (Phase 13) still relies on it.

Note: `PATCH` lets an authenticated owner set their own job's status directly. This is a pre-existing capability, now correctly ownership-scoped rather than open to anyone; whether a regular user should be able to mutate job status at all (versus this being admin/internal-only) is a product decision left to a future phase - see the backend-completion report's "Known limitations."

## Transcript

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/transcripts/{video_id}` | Yes | Full transcript text + detected `language` + `word_count`. `404` if not generated yet or video not found/owned. |

**Security fix (this phase):** previously unauthenticated and unscoped - any caller could read any video's transcript by id.

## Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/summaries/video/{video_id}` | Yes | List of summaries (currently always 0 or 1 item; `type` is always `"default"` - only one summarization strategy is implemented today). |

## Translation

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/translations/video/{video_id}` | Yes | List of translations (currently always 0 or 1 item; target language is fixed to `en` in the processing pipeline - not request-configurable). |

## Chapters

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/videos/{video_id}/chapters` | Yes | Chapters detected for the video, ordered by `start_time`. `[]` is a valid response (best-effort detection). |

**New in this phase.** Chapter detection/persistence already existed (a prior phase); this is its first public API. Fields: `id`, `video_id`, `title`, `start_time`, `end_time`, `summary` (nullable).

## Quizzes

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/videos/{video_id}/quizzes` | Yes | Quiz questions for the video, in creation order. |

Fields: `id`, `video_id`, `type` (`multiple_choice` \| `true_false` \| `short_answer`), `question`, `answer`, `options` (nullable, comma-separated for multiple-choice). Read-only - no submit/score/attempt-tracking endpoint exists.

## Flashcards

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/videos/{video_id}/flashcards` | Yes | Flashcards for the video, in creation order. |
| GET | `/videos/{video_id}/flashcards/export` | Yes | Anki-importable **UTF-8 TSV** download (`front\tback` per line - Anki's native "Import File" format). No `.apkg`/`genanki` dependency. |

**New in this phase.** Fields: `id`, `video_id`, `question`, `answer`, `difficulty`.

## Search & RAG

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/search/videos/{video_id}` | Yes | Semantic (dense/FAISS) search within one video. Body: `{query, top_k}`. |
| POST | `/search/videos/{video_id}/rag` | Yes | Ask a question grounded in the video's transcript (retrieval-augmented generation). |

**Security fix (this phase):** the semantic search endpoint was previously unauthenticated and unscoped.

`POST .../rag` response (`RAGResult`): `{video_id, query, status, answer, sources}`.

`status` is one of exactly four values (no others exist):

- `answered` - `answer` + `sources` (retrieved chunks used as citations) populated.
- `empty_query` - the query was blank.
- `no_embeddings` - the video hasn't finished embedding generation yet.
- `no_relevant_chunks` - embeddings exist, but nothing matched well enough.

Stateless by design: no conversation history is persisted or fed back into later calls. A `ChatHistory` model/repository already exist but are intentionally unwired (no service, no write path) - this phase confirmed RAG should stay stateless rather than build conversational memory, since nothing currently needs it (see the backend-completion report).

Retrieval today is plain dense (FAISS) retrieval - hybrid/sparse retrieval and cross-encoder reranking exist in `ai/retrieval`/`ai/reranking` but are not wired into the live RAG dependency (`app/api/deps.py::get_rag_pipeline`); enabling them is a deliberate, separate decision, not made in this phase.

## Meetings (aggregated view)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/meetings/{video_id}` | Yes | One call returning `{video, processing_jobs, transcript, summaries, translations, quizzes}` - composes the endpoints above rather than duplicating their logic. |

Does not include chapters/flashcards (added after this endpoint's schema was last touched) - fetch those separately if needed. There is no separate "Meeting" domain; a meeting recording is a `Video` like any other.

## Knowledge Graph

**Not exposed via API.** Entity/relation extraction and graph building (`ai/knowledge_graph/`) are implemented as reusable domain logic, but there is no persistence (no database table) and no endpoint. See `ai/knowledge_graph/__init__.py` and the backend-completion report for the full rationale - in short: computing the graph live in a GET handler would mean uncached, non-deterministic LLM calls on every request, and building real persistence is a new capability (new tables/migration/pipeline stage), not a hardening of an existing one. Deferred, not abandoned.

## System

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Combined liveness+readiness (kept for existing Docker/Compose healthchecks). |
| GET | `/health/live` | No | Liveness only - never fails due to a dependency outage. |
| GET | `/health/ready` | No | Readiness - checks database connectivity. |
| GET | `/metrics` (root, not under `/api/v1`) | No\*\* | Prometheus scrape endpoint. |

\*\* Not authenticated by design (internal Prometheus scraping) - must never be exposed publicly; see `docs/deployment.md`.

## Error responses

Consistent JSON shape across the whole API: `{"detail": "..."}` (or, for `422` validation errors, FastAPI's structured `{"detail": [...]}` field-error list). `401` for any missing/invalid/expired credential (fixed in this phase - a missing token previously returned `403` from one code path and `401` from another). Unhandled server errors return a generic `{"detail": "Internal server error"}` with status `500` - no stack trace, database error text, or file path is ever included (see `app/exceptions/handlers.py`).
