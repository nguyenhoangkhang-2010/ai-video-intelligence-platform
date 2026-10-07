# 0003 - Per-stage resumability via a `ProcessingStage` table

## Status
Accepted (implemented: `app/models/processing_stage.py`, `app/pipelines/video_pipeline.py`).

## Context
Before this, `ProcessingJob` tracked only job-level status
(PENDING/RUNNING/COMPLETED/FAILED). If a job failed after 5 of 8
stages had already produced real output (transcription, summary,
etc.), a retry re-ran every stage from scratch - repeating expensive
Whisper/LLM calls for work that had already succeeded.

## Decision
Add `ProcessingStage`: one row per `(processing_job_id, stage_name)`,
independently PENDING/RUNNING/COMPLETED/FAILED/SKIPPED, claimed
atomically (mirroring the job-level claim-with-staleness-reclaim
pattern rather than inventing a second concurrency model). On retry,
`VideoPipelineService.process()` skips any stage already COMPLETED
and only re-runs stages that are PENDING/FAILED, respecting the real
dependency graph (the 6 non-transcription stages depend only on
transcription, never on each other, so they can be retried
independently of one another).

## Consequences
- A failed job's retry only re-does the work that actually failed -
  the main cost this change was made for.
- One more table and one more atomic-claim pattern to maintain,
  parallel to the job-level one. Accepted because the two claims
  genuinely differ in scope (whole job vs. one stage) and collapsing
  them into one mechanism would have made the job-level "one active
  job per video" invariant harder to reason about.
- Stage-level Prometheus metrics (`app/workers/pipeline_metrics.py`,
  added alongside this) depend on this table existing - stage
  identity is what the `stage` metric label is keyed on.
