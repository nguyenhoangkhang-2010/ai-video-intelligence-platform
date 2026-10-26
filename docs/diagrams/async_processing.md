# Async Processing / Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: ProcessingJob created<br/>(on POST /videos/upload)
    PENDING --> RUNNING: claim_for_running()<br/>atomic, race-safe claim<br/>(Celery redelivery-safe)
    RUNNING --> COMPLETED: all pipeline stages succeed
    RUNNING --> FAILED: any stage raises<br/>(error_message persisted)
    COMPLETED --> [*]
    FAILED --> [*]

    note right of PENDING
        Client-writable via
        PATCH /processing-jobs/{id},
        but ONLY along these exact
        transitions - enforced by
        ProcessingJobService.
        _VALID_JOB_STATUS_TRANSITIONS.
        No transition out of a
        terminal state is allowed.
    end note
```

## Delivery guarantees

```mermaid
flowchart LR
    Upload["POST /videos/upload"] --> Dispatch["process_video.delay(job_id, video_id, path)"]
    Dispatch --> Broker[("Redis broker")]
    Broker --> Worker["Celery worker<br/>task_acks_late=True<br/>task_reject_on_worker_lost=True"]
    Worker --> Claim{"claim_for_running()<br/>still PENDING?"}
    Claim -->|"yes"| Run["Run pipeline"]
    Claim -->|"no (already claimed/redelivered)"| Skip["No-op: treated as already handled"]

    Worker -.->|"transient failure<br/>(DB/Redis connection, network)"| Retry["autoretry_for=TRANSIENT_EXCEPTIONS<br/>bounded, exponential backoff,<br/>max_retries=3"]
    Retry -.-> Worker
```

- **Idempotent redelivery**: `claim_for_running` is an atomic
  `UPDATE ... WHERE status='PENDING'`. If Celery redelivers a task (worker
  crash, broker requeue), a second attempt finds the job already `RUNNING`
  or terminal and safely no-ops instead of reprocessing.
- **Retry is for transport failures, not business failures**: a real
  pipeline error (bad audio, model failure) marks the job `FAILED` and
  re-raises — it is not silently retried, since retrying the exact same
  input against the exact same failure mode rarely helps.
- **Queue separation**: `celery_cpu` and `celery_gpu` are declared as
  separate queues so a GPU-equipped worker fleet can be added later
  (`docker compose --profile gpu up`) without any code change — the
  default single-worker setup consumes both.
- **Progress reporting is real, not simulated**: `ProcessingJob.progress`/
  `current_step` are updated at fixed points as each real stage starts
  (see `docs/diagrams/ai_pipeline.md`) — the frontend polls
  `GET /videos/{id}/processing-jobs` and renders exactly these values,
  never an animated fake percentage.
