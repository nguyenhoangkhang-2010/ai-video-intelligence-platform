# System Architecture

```mermaid
flowchart LR
    subgraph Client
        Browser["Browser<br/>(Next.js app, localhost:3000)"]
    end

    subgraph API["FastAPI (backend/app)"]
        Auth["Auth<br/>(JWT, ownership checks)"]
        Routes["/api/v1/* routes"]
        Services["Services / Repositories"]
    end

    subgraph Async["Async Processing"]
        Celery["Celery worker(s)<br/>celery_cpu / celery_gpu queues"]
        Pipeline["VideoPipelineService<br/>(backend/app/pipelines)"]
    end

    subgraph AI["AI Layer (backend/ai)"]
        Whisper["faster-whisper (ASR)"]
        Embed["BGE-M3 embeddings"]
        Retrieval["Dense + BM25 + RRF + CrossEncoder"]
        LLM["Ollama (qwen3:8b)<br/>summary / quiz / flashcards / chapters / translation / RAG"]
    end

    subgraph Data["Data Infrastructure"]
        PG[("PostgreSQL<br/>videos, transcripts, embeddings, ...")]
        Redis[("Redis<br/>Celery broker + result backend")]
        FAISS[("FAISS index<br/>storage/faiss/")]
        FS[("Local filesystem<br/>storage/videos/<br/>(StorageBackend: local default, S3-capable)")]
    end

    Browser -->|"HTTP + JWT Bearer"| Routes
    Routes --> Auth
    Routes --> Services
    Services --> PG
    Services -->|"dispatch process_video"| Redis
    Redis --> Celery
    Celery --> Pipeline
    Pipeline --> Whisper
    Pipeline --> Embed
    Pipeline --> LLM
    Embed --> FAISS
    Pipeline --> PG
    Services -->|"query-time retrieval"| Retrieval
    Retrieval --> FAISS
    Retrieval --> PG
    Routes -->|"POST .../rag"| LLM
    Routes -->|"GET .../stream"| FS
    Routes -->|"POST /upload"| FS

    style Client fill:#1a1a1a,stroke:#c88a4a,color:#eee
    style API fill:#1a1a1a,stroke:#c88a4a,color:#eee
    style Async fill:#1a1a1a,stroke:#c88a4a,color:#eee
    style AI fill:#1a1a1a,stroke:#c88a4a,color:#eee
    style Data fill:#1a1a1a,stroke:#c88a4a,color:#eee
```

## Notes

- **Two-image, one-Dockerfile split**: `api` and `celery` are the same built
  image (`Dockerfile`), started with a different `command:` — see
  `docker-compose.yml`. Both go through `backend/scripts/docker-entrypoint.sh`,
  which runs `alembic upgrade head` before starting (only for `api`; the
  Celery containers set `RUN_MIGRATIONS_ON_START=false` to avoid two
  containers racing to create the same tables on a fresh database).
- **Storage**: uploads are always written to local disk today
  (`StorageBackend` is S3-capable for the *read/stream* path via
  `STORAGE_BACKEND=s3`, but the upload write path still targets local disk
  directly — see `docs/deployment.md`).
- **The browser never talks to `redis`/`db`/Celery directly** — every
  request goes through the FastAPI process on `localhost:8001` (or through
  `nginx` in the production compose file).
