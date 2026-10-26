# 0001 - Celery + a single resumable task, not a workflow engine

## Status
Accepted (implemented: `app/pipelines/video_pipeline.py`, `ProcessingJob`/`ProcessingStage` models).

## Context
A video goes through 8 processing stages (metadata, transcription,
summary, embedding, translation, quiz, chapter, flashcard) with a
real dependency graph (6 of the 8 stages depend only on
transcription, never on each other). Two things must hold: a stage
that already completed must never redo its work when the job retries
(cost: real ffmpeg/Whisper/LLM calls), and only one active run per
video may exist at a time.

Workflow engines (Temporal, Airflow, Dagster, Prefect) solve exactly
this class of problem - durable step state, retries, DAG-aware
scheduling - as a dedicated product.

## Decision
Keep a single Celery task (`process_video`) as the entry point, and
implement resumability ourselves with two tables:
`ProcessingJob` (one row per run, PENDING/RUNNING/COMPLETED/FAILED,
with a partial unique index enforcing "one active job per video") and
`ProcessingStage` (one row per `(processing_job_id, stage_name)`,
independently claimable/resumable, mirroring the job-level
claim-with-staleness-reclaim pattern). The dependency graph is walked
in-process by `VideoPipelineService.process()`, not by a scheduler.

## Consequences
- No new infrastructure component (no workflow-engine server, no
  second message broker, nothing beyond the Redis+Celery this project
  already runs).
- Resumability logic (staleness thresholds, atomic claims) is ours to
  maintain - a mature workflow engine would give us this for free, at
  the cost of operating it.
- This scales to "one service, one pipeline shape, 8 stages." It would
  stop being the right call if the number of independent pipelines
  grew, if cross-pipeline orchestration (fan-out/fan-in across many
  jobs) became a real requirement, or if the team needed a UI for
  non-engineers to inspect/retry runs - none of which is true today.
