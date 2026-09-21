# AI Video Intelligence Platform

<p align="center">

**An end-to-end AI platform for transforming long-form video into searchable, structured, and interactive knowledge.**

</p>

<p align="center">

Speech Recognition • NLP • RAG • Semantic Search • LLM • Knowledge Graph • AI Processing Pipeline • Async Workers • Vector Search • Docker

</p>

---

## Overview

**AI Video Intelligence Platform** is an end-to-end AI system designed to process long-form video content and transform it into structured, searchable, and interactive knowledge.

The platform combines:

* Speech Recognition
* Voice Activity Detection
* Speaker Diarization
* Transcript Processing
* Topic / Chapter Detection
* Text Chunking
* Embedding Generation
* Vector Search
* Hybrid Retrieval
* Cross-Encoder Reranking
* Retrieval-Augmented Generation (RAG)
* Large Language Models
* Summarization
* Quiz Generation
* Flashcard Generation
* Subtitle Processing
* Translation
* Knowledge Graph Extraction
* Meeting Intelligence
* Asynchronous AI Processing

The system is designed around a pipeline architecture where expensive AI operations can be executed asynchronously through **Celery + Redis**, while the FastAPI backend provides the application API.

---

# Problem Statement

Long-form video contains a large amount of valuable information but is difficult to search and consume efficiently.

Typical examples include:

* University lectures
* Technical presentations
* Business meetings
* Podcasts
* Webinars
* Tutorials
* Interviews
* Educational content

Traditional video platforms primarily provide playback and subtitles.

They do not provide a complete knowledge layer that allows users to:

* Find specific concepts
* Search semantically
* Ask questions about a video
* Generate summaries
* Extract chapters
* Generate learning materials
* Identify speakers
* Extract meeting decisions and action items
* Build relationships between concepts

This project addresses that problem by converting video into a structured knowledge representation.

---

# Core Workflow

```text
Video
  │
  ▼
Audio Extraction
  │
  ▼
Voice Activity Detection
  │
  ▼
Speech Recognition
  │
  ▼
Transcript Normalization
  │
  ├──────────────► Language Detection
  │
  ├──────────────► Speaker Diarization
  │
  ▼
Transcript / Segment Processing
  │
  ├──────────────► Chapter Detection
  │
  ├──────────────► Topic Segmentation
  │
  └──────────────► Key Moment Detection
  │
  ▼
Text Chunking
  │
  ▼
Embedding Generation
  │
  ▼
Vector Storage
  │
  ▼
Hybrid Retrieval
  │
  ▼
Reranking
  │
  ▼
RAG
  │
  ▼
LLM
  │
  ├──► Question Answering
  ├──► Summarization
  ├──► Quiz Generation
  ├──► Flashcards
  ├──► Translation
  └──► Knowledge Extraction
```

---

# Features

## 1. Video Processing

The backend provides a video processing pipeline for handling uploaded video content.

Current processing components include:

* Video metadata extraction
* Audio extraction
* Video utilities
* FFmpeg / FFprobe integration
* Processing job tracking
* Asynchronous processing

The project separates raw, processed, transcript, embedding, and exported data.

---

## 2. Speech Recognition

The platform uses **Faster-Whisper** for speech-to-text processing.

Implemented components include:

* Audio extraction
* Faster-Whisper transcription
* Language detection
* Voice Activity Detection
* Transcript normalization
* Transcript post-processing
* Timestamp handling

The resulting transcript becomes the foundation for downstream AI processing.

---

## 3. Speaker Diarization

The platform includes speaker diarization for identifying different speakers within a video or meeting.

```text
Audio
  │
  ▼
Speaker Diarization
  │
  ├── Speaker 1
  ├── Speaker 2
  └── Speaker 3
```

The diarization module also provides speaker mapping functionality so speaker segments can be associated with processed transcript data.

---

## 4. Transcript Processing

Transcripts are processed before being passed to downstream AI components.

Processing includes:

* Normalization
* Timestamp alignment
* Segment processing
* Topic segmentation
* Chapter detection
* Chunk preparation

This creates structured transcript segments that can later be indexed and retrieved.

---

# 5. Chapter Detection

The platform contains a dedicated chapter detection module.

It includes:

* Chapter detection
* Chapter post-processing
* Timestamp alignment
* Topic segmentation

The goal is to transform a long transcript into meaningful sections.

```text
00:00 ───── Introduction

05:32 ───── Topic A

18:41 ───── Topic B

35:12 ───── Demonstration

48:50 ───── Conclusion
```

---

# 6. Summarization

The summarization pipeline supports multiple levels of summaries.

Current components include:

* Executive Summary
* Detailed Summary
* Bullet Summary
* TL;DR
* Prompt templates
* LLM-based summarization

The architecture separates summary generation from API and persistence layers.

---

# 7. Question Answering

The platform provides a RAG-based question answering pipeline.

```text
User Question
      │
      ▼
Query Processing
      │
      ▼
Retrieval
      │
      ▼
Hybrid Search
      │
      ▼
Reranking
      │
      ▼
Relevant Transcript Chunks
      │
      ▼
Prompt Construction
      │
      ▼
LLM
      │
      ▼
Answer + Citation
```

The question answering module contains components for:

* Retrieval-Augmented Generation
* Prompt building
* Answer generation
* Citation generation
* RAG orchestration

---

# 8. Semantic Search

The system supports semantic retrieval over processed video content.

The embedding pipeline includes:

* Text chunking
* Embedding generation
* Embedding model management
* Vector indexing
* Vector storage
* Index metadata

The retrieval layer also supports hybrid search and reranking.

---

# 9. Embedding & Vector Search

The project supports modern embedding and vector retrieval components.

Current architecture includes:

```text
Transcript
   │
   ▼
Chunking
   │
   ▼
Embedding Model
   │
   ▼
Vector
   │
   ▼
Vector Index
   │
   ▼
Vector Database
```

The codebase includes support for:

* Sentence Transformers
* FlagEmbedding / BGE
* FAISS
* Qdrant
* Vector index construction
* Vector metadata management

Additional vector/database technologies are maintained as infrastructure capabilities and experiments rather than being required simultaneously in the core runtime.

---

# 10. Reranking

The retrieval pipeline includes a dedicated reranking layer.

Components include:

* Cross-encoder reranking
* Reranker orchestration

The retrieval flow is therefore:

```text
Query
  │
  ▼
Initial Retrieval
  │
  ▼
Candidate Documents
  │
  ▼
Cross Encoder
  │
  ▼
Reranked Results
```

This improves the quality of the context supplied to the RAG pipeline.

---

# 11. Chat with Video

Users can interact with processed video content through natural-language questions.

Example:

```text
User:
Where does the speaker explain Retrieval-Augmented Generation?

System:
Answer
+
Relevant transcript
+
Timestamp
+
Citation
```

The feature combines:

* Semantic retrieval
* Reranking
* Transcript context
* Prompt construction
* LLM generation
* Citation generation

---

# 12. Quiz Generation

The platform contains a dedicated quiz-generation module.

Supported question types include:

* Multiple Choice Questions
* True / False
* Short Answer

Quiz generation is integrated with the video knowledge pipeline.

Generated quizzes can be persisted through the backend data layer.

---

# 13. Flashcard Generation

The platform can generate learning flashcards from processed video content.

The flashcard module includes:

* Flashcard generation
* Flashcard persistence
* Anki export

The goal is to transform video knowledge into reusable learning material.

---

# 14. Knowledge Graph

The project includes a knowledge graph extraction pipeline.

Current components include:

* Entity extraction
* Relation extraction
* Graph construction

```text
Video
  │
  ▼
Transcript
  │
  ▼
Knowledge Extraction
  │
  ├── Entities
  │
  └── Relations
        │
        ▼
Knowledge Graph
```

This provides a structured representation of concepts and their relationships extracted from video content.

---

# 15. Translation

The translation module supports translation of processed video knowledge.

Current components include:

* Transcript translation
* Subtitle translation
* Translation pipeline

The architecture keeps translation separate from transcription and summarization so that multilingual processing can be extended independently.

---

# 16. Subtitle Processing

The platform supports subtitle-related processing including:

* Subtitle parsing
* SRT processing
* Timestamp-aware transcript data
* Subtitle translation

Subtitle generation and export can be integrated with the processed transcript pipeline.

---

# 17. Meeting Intelligence

The project includes a dedicated meeting-processing pipeline.

The architecture is designed to support extraction of structured meeting information such as:

* Action items
* Decisions
* Deadlines
* Responsibilities
* Important discussion points

Meeting processing combines:

```text
Audio
  │
  ▼
Transcription
  │
  ▼
Speaker Diarization
  │
  ▼
Transcript Segmentation
  │
  ▼
LLM / Knowledge Extraction
  │
  ▼
Meeting Intelligence
```

---

# 18. Asynchronous AI Processing

AI processing can be computationally expensive.

The platform therefore uses **Celery + Redis** for asynchronous processing.

```text
Frontend
   │
   ▼
FastAPI
   │
   ▼
Processing Job
   │
   ▼
Redis Broker
   │
   ▼
Celery Worker
   │
   ├── Transcription
   ├── Video Processing
   ├── Embedding
   ├── Summarization
   ├── Translation
   └── Quiz Generation
```

The backend maintains processing-job state so long-running operations do not need to block API requests.

---

# Backend Architecture

The backend follows a layered architecture.

```text
API
 │
 ▼
Services
 │
 ▼
Repositories
 │
 ▼
Database
```

AI processing is separated into:

```text
backend/
├── app/
│   ├── api/
│   ├── auth/
│   ├── config/
│   ├── core/
│   ├── database/
│   ├── dependencies/
│   ├── middleware/
│   ├── pipelines/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── types/
│   ├── utils/
│   └── workers/
│
└── ai/
    ├── chapter_detection/
    ├── diarization/
    ├── embedding/
    ├── evaluation/
    ├── flashcards/
    ├── knowledge_graph/
    ├── llm/
    ├── question_answering/
    ├── quiz_generation/
    ├── reranking/
    ├── retrieval/
    ├── speech/
    ├── summarization/
    └── translation/
```

This separation allows the AI modules to evolve independently from the API and persistence layers.

---

# Database Architecture

The backend uses PostgreSQL with SQLAlchemy and Alembic.

Current database-related components include:

* SQLAlchemy ORM
* PostgreSQL
* Alembic migrations
* Repository pattern
* Database sessions
* Processing job persistence

The project currently contains migrations for entities including:

* Users
* Videos
* Processing Jobs
* Transcripts
* Chapters
* Embeddings
* Summaries
* Quizzes
* Flashcards
* Translations
* Chat History

Relationships and cascade-delete behavior are managed through database migrations and ORM relationships.

---

# Storage Architecture

The project separates application data into dedicated storage areas.

```text
storage/
├── audio/
├── subtitles/
├── thumbnails/
└── videos/
```

Processed data is organized separately:

```text
data/
├── embeddings/
├── exports/
├── processed/
├── raw/
├── transcripts/
└── vector_db/
```

The architecture also includes MinIO integration for object-storage workflows.

---

# Authentication

The backend contains an authentication layer supporting:

* User authentication
* OAuth2-style authentication flow
* JWT
* Password hashing
* Authentication dependencies
* Role-aware API dependencies

---

# Monitoring & Observability

Implemented:

* Structured/consistent logging (`GET`/task-scoped `request_id`/`task_id` correlation, configurable level and JSON/plain format) - see `backend/app/config/logging.py`.
* Prometheus metrics: `GET /metrics` on the API (`backend/app/core/metrics.py`) and a dedicated exporter in the Celery worker (`backend/app/workers/metrics.py`).
* A minimal local Prometheus + Grafana stack, gated behind the `monitoring` Compose profile (not required for normal local development):

```text
monitoring/
├── grafana/       # datasource + dashboard provisioning, one overview dashboard
└── prometheus/    # scrape config + a few alert rules
```

* `GET /api/v1/health`, `/health/live`, `/health/ready` (liveness/readiness split - see `docs/deployment.md`).

Not implemented (documented as future enhancements, not built merely to fill a checklist): OpenTelemetry distributed tracing, Sentry error tracking.

See `docs/deployment.md` for the full production infrastructure write-up (CPU/GPU workers, retries, storage/vector strategy, backup/recovery, deployment procedure).

---

# Evaluation

The platform includes an AI evaluation layer.

Current evaluation components include:

* ROUGE
* BERTScore
* RAG evaluation
* Latency measurement
* Benchmarking

Evaluation code is located under:

```text
backend/ai/evaluation/
```

Experiments and benchmarks are also maintained through Jupyter notebooks.

```text
notebooks/
├── Benchmark.ipynb
├── EDA.ipynb
├── RAG.ipynb
└── Whisper.ipynb
```

---

# Testing

The project contains both application-level and AI-related tests.

```text
backend/tests/
├── test_api.py
├── test_embedding.py
├── test_rag.py
├── test_summary.py
└── test_upload.py
```

Additional development scripts are available for testing:

```text
backend/scripts/
├── test_audio.py
├── test_db.py
├── test_model.py
├── test_session.py
├── test_whisper.py
└── test_worker.py
```

Testing and quality tooling includes:

* pytest
* pytest-cov
* Ruff
* Black
* isort
* Flake8
* mypy
* Bandit
* pre-commit

---

# Technology Stack

| Layer               | Technology                                 |
| ------------------- | ------------------------------------------ |
| Backend API         | FastAPI                                    |
| API Server          | Uvicorn                                    |
| Database            | PostgreSQL                                 |
| ORM                 | SQLAlchemy                                 |
| Migration           | Alembic                                    |
| Cache               | Redis                                      |
| Task Queue          | Celery                                     |
| Object Storage      | MinIO                                      |
| AI Framework        | PyTorch                                    |
| LLM Framework       | Transformers                               |
| Speech Recognition  | Faster-Whisper                             |
| VAD                 | WebRTC VAD                                 |
| Speaker Diarization | pyannote.audio                             |
| NLP                 | spaCy / NLTK                               |
| Embedding           | Sentence Transformers / FlagEmbedding      |
| Vector Search       | FAISS / Qdrant                             |
| Retrieval           | BM25 / Hybrid Retrieval                    |
| Reranking           | Cross Encoder                              |
| RAG                 | LangChain + custom pipeline                |
| LLM                 | Qwen-family models / local LLM integration |
| Knowledge Graph     | NetworkX / Graph-based pipeline            |
| Visualization       | Matplotlib / Plotly / PyVis                |
| Dashboard           | Streamlit                                  |
| Evaluation          | ROUGE / BERTScore / RAGAS                  |
| Experiment Tracking | MLflow / Weights & Biases                  |
| Containerization    | Docker                                     |
| Orchestration       | Kubernetes                                 |
| Monitoring          | Prometheus / Grafana                       |
| Observability       | OpenTelemetry / Sentry                     |
| CI/CD               | GitHub Actions                             |

---

# Project Structure

```text
AI-Video-Intelligence-Platform/
│
├── .github/
│   └── workflows/
│
├── assets/
│   ├── demo/
│   └── screenshots/
│
├── backend/
│   ├── ai/
│   │   ├── chapter_detection/
│   │   ├── diarization/
│   │   ├── embedding/
│   │   ├── evaluation/
│   │   ├── flashcards/
│   │   ├── knowledge_graph/
│   │   ├── llm/
│   │   ├── question_answering/
│   │   ├── quiz_generation/
│   │   ├── reranking/
│   │   ├── retrieval/
│   │   ├── speech/
│   │   ├── summarization/
│   │   └── translation/
│   │
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── config/
│   │   ├── core/
│   │   ├── database/
│   │   ├── dependencies/
│   │   ├── exceptions/
│   │   ├── middleware/
│   │   ├── pipelines/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── workers/
│   │
│   ├── scripts/
│   └── tests/
│
├── configs/
│
├── data/
│   ├── embeddings/
│   ├── exports/
│   ├── processed/
│   ├── raw/
│   ├── transcripts/
│   └── vector_db/
│
├── deployment/
│   ├── docker/
│   ├── kubernetes/
│   └── nginx/
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── diagrams/
│
├── frontend/
│   └── src/
│
├── monitoring/
│   ├── grafana/
│   └── prometheus/
│
├── notebooks/
│
├── requirements/
│
├── scripts/
│
├── storage/
│   ├── audio/
│   ├── subtitles/
│   ├── thumbnails/
│   └── videos/
│
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

---

# Docker Architecture

The development environment uses Docker Compose.

Current services include:

```text
┌──────────────────────┐
│      Frontend        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       FastAPI        │
│         API          │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
 PostgreSQL     Redis
                   │
                   ▼
             Celery Worker
                   │
                   ▼
              AI Pipeline
```

The current development Compose configuration (`docker-compose.yml`) includes:

* PostgreSQL (`db`)
* Redis
* FastAPI API service
* Celery worker
* Frontend (optional - `docker compose --profile frontend up`)

The Celery worker executes long-running background processing tasks without blocking the API server. `api`/`db`/`redis` have Docker healthchecks, and `api`/`celery` wait for `db`/`redis` to report healthy before starting.

The backend exposes `GET /api/v1/health` (checks database connectivity) for Compose/CI readiness probes.

**Local development quickstart:**

```bash
cp .env.example .env   # or: scripts/setup.sh
docker compose up --build
```

See the [Makefile](Makefile) for common commands (`make up`, `make down`, `make logs`, `make logs-worker`, `make shell`, `make migrate`, `make down-v`).

> The `frontend/` app is currently an empty scaffold (no application code, no lockfile yet), so its Compose service/Dockerfiles cannot actually build until real Next.js code lands - see `deployment/docker/README.md`.

---

# Deployment

Full write-up: **[docs/deployment.md](docs/deployment.md)** (architecture, environment configuration, service roles, CPU/GPU workers, retries, health/readiness, metrics/monitoring, persistent volumes, backup/recovery, migration procedure, deployment/rollback commands, known limitations).

The repository contains deployment configurations for:

### Docker

```text
deployment/docker/
├── backend.Dockerfile        # multi-stage production backend/worker image
├── frontend.Dockerfile       # multi-stage production frontend image
└── docker-compose.prod.yml   # db + redis + api + worker(+ worker-gpu profile) + nginx (+ frontend profile)
```

Production Compose differs from development: built (not bind-mounted) images, no debug mode, no publicly exposed database/Redis ports, `nginx` as the single public entry point (port 80) proxying to the API and, once it exists, the frontend, per-service CPU/memory limits (env-configurable), and an optional GPU worker (`--profile gpu`, requires the NVIDIA Container Toolkit). See `deployment/docker/README.md` and `docs/deployment.md`.

### CI/CD

```text
.github/workflows/
├── tests.yml     # backend pytest suite
├── lint.yml      # backend ruff check (informational - no lint config adopted yet)
├── ci.yml        # frontend install/lint/build (skips gracefully while frontend/ is empty)
├── docker.yml    # validates backend (dev + prod) and frontend Docker images build
└── release.yml   # on a "v*" tag: publishes backend/frontend images to GHCR
```

None of these call Ollama, Hugging Face inference, or any other external AI service - the backend test suite mocks all of that. `release.yml` only publishes images (using the built-in `GITHUB_TOKEN` - no registry credentials to configure); it does not deploy anywhere, since no staging/production host is established yet.

### Kubernetes

```text
deployment/kubernetes/
├── deployment.yaml
├── ingress.yaml
└── service.yaml
```

Not implemented yet - planned for a later phase (container orchestration/scaling).

### Nginx

```text
deployment/nginx/
└── nginx.conf
```

Reverse proxy used by the production Compose stack - see `deployment/nginx/README.md`.

The deployment architecture is designed to support a transition from local Docker Compose development to container orchestration.

---

# Requirements

The project maintains versioned requirement files during development:

```text
requirements/
├── requirements-v1.txt
├── requirements-v2.txt
├── requirements-v3.txt
├── requirements-v4.txt
├── requirements-v5.txt
├── requirements-v6.txt
└── requirements-v7.txt
```

These versions represent the progressive expansion of the platform.

The final consolidated dependency file is intended to contain the **union of the dependencies from V1–V7**, with duplicate packages removed.

Heavy packages such as PyTorch, CUDA-related packages, xFormers, and other AI infrastructure dependencies are **not removed merely because they are large**. Dependency selection should be based on actual project requirements rather than package size.

---

# Development Roadmap

## Version 1 — Core AI Video Processing

* Video upload
* Audio extraction
* Faster-Whisper transcription
* Transcript processing
* Basic summarization
* Chapter detection
* Initial FastAPI architecture

---

## Version 2 — RAG & Search

* PostgreSQL integration
* SQLAlchemy
* Alembic
* Embedding pipeline
* FAISS
* Qdrant
* LangChain
* BM25 retrieval
* OCR
* Subtitle processing
* PDF processing
* RAG evaluation

---

## Version 3 — Learning & Knowledge Extraction

* Quiz generation
* Flashcard generation
* Anki export
* Mind-map / graph visualization
* Translation
* Language detection
* Markdown / HTML processing
* PDF / DOCX / PPT export
* Data visualization

---

## Version 4 — Meeting Intelligence & Application Layer

* Speaker diarization
* Voice activity detection
* Meeting analytics
* Dashboard
* Authentication
* JWT
* Caching
* Scheduling
* WebSocket support
* Admin interface

---

## Version 5 — Distributed & Production Infrastructure

* Celery
* Redis
* RabbitMQ
* Kafka
* MinIO
* AWS integration
* Docker SDK
* Kubernetes
* Prometheus
* Structured logging
* Async processing
* Production server configuration

---

## Version 6 — AI Optimization & Experimentation

* Model optimization
* Quantization
* PEFT
* LoRA / fine-tuning infrastructure
* GPU optimization
* Ray
* ONNX
* RAG evaluation
* ML evaluation
* MLflow
* Weights & Biases
* Hyperparameter optimization

---

## Version 7 — Data Engineering, MLOps & Observability

* Workflow orchestration
* Data versioning
* Configuration management
* Data validation
* Feature management
* Analytical data processing
* Additional vector database experiments
* Graph database integration
* OpenTelemetry
* Sentry
* Code quality
* Static type checking
* Security scanning
* Pre-commit automation

---

# Current Development Status

The project is being developed incrementally.

### Implemented / Integrated

* FastAPI backend
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis
* Celery
* Video processing pipeline
* Speech recognition
* Transcript processing
* Embedding pipeline
* Vector search architecture
* RAG architecture
* Summarization
* Quiz generation
* Flashcards
* Translation
* Speaker diarization architecture
* Knowledge graph modules
* Authentication layer
* Repository / service architecture
* Processing job tracking
* Docker development environment (backend, worker, Redis, PostgreSQL)
* Production Docker architecture (multi-stage backend/frontend images, production Compose, nginx reverse proxy)
* GitHub Actions CI/CD (backend tests, lint, frontend build, Docker image build validation, GHCR image publishing on release)
* Backend health/readiness/liveness endpoints (`GET /api/v1/health`, `/health/live`, `/health/ready`)
* Prometheus metrics (API `/metrics` + dedicated Celery worker exporter) and a local Prometheus/Grafana Compose profile
* Structured/correlated logging (request/task context, configurable level and JSON output)
* Celery production hardening (late ack, bounded/backed-off retry for transient failures, time limits, worker recycling, CPU/GPU queue routing foundation)
* Database connection pool tuning (env-configurable)
* Extensible storage backend interface (local filesystem default, optional S3-compatible backend)
* FAISS index rebuild tooling (`backend/scripts/rebuild_faiss_index.py`)
* Environment-driven CORS configuration
* Automated testing structure

### In Progress

* Complete distributed processing
* Advanced model optimization
* MLOps workflows
* Advanced observability
* Kubernetes deployment
* Frontend feature expansion
* Production-grade AI evaluation

### Planned / Experimental

Some dependencies in the consolidated requirements represent **future infrastructure, experimentation, or optional integrations** rather than services that are simultaneously required by the current application.

Examples include:

* Airflow
* Prefect
* Feast
* DVC
* Milvus
* Weaviate
* LanceDB
* Neo4j
* Great Expectations
* Ray
* ONNX
* Advanced fine-tuning infrastructure

These are maintained as part of the project's broader AI / MLOps / data-engineering roadmap.

---

# API

The backend exposes REST APIs through FastAPI.

Current API domains include:

```text
/v1/auth
/v1/users
/v1/videos
/v1/transcripts
/v1/summaries
/v1/quizzes
/v1/search
/v1/translations
/v1/processing-jobs
```

Additional application endpoints include functionality related to:

* Chat
* Chapters
* Flashcards
* AI processing

Interactive API documentation is provided by FastAPI during development.

---

# Experiments

The project contains dedicated notebooks and evaluation workflows for experimenting with:

### Speech Recognition

* Whisper models
* Transcription quality
* Latency

### Embeddings

* BGE-family embeddings
* Sentence Transformers
* Vector retrieval

### LLMs

* Qwen-family models
* Local LLM integration
* Prompt experiments

### RAG

* Retrieval quality
* Reranking
* Answer relevance
* Faithfulness
* Latency

---

# Benchmarks

The platform evaluates multiple aspects of the AI pipeline.

### Generation Quality

* ROUGE
* BERTScore

### RAG Quality

* Answer relevancy
* Faithfulness
* Retrieval quality

### System Performance

* Latency
* Throughput
* Processing time

---

# Documentation

Architecture documentation is maintained under:

```text
docs/
├── api/
├── architecture/
├── diagrams/
├── deployment.md
├── roadmap.md
└── system_design.md
```

Architecture diagrams include:

* System architecture
* AI pipeline
* Deployment architecture

---

# Future Improvements

Potential future improvements include:

* More robust multimodal video understanding
* Vision-language models
* OCR-based visual understanding
* Better speaker identification
* Advanced temporal retrieval
* Multi-video knowledge bases
* Cross-video question answering
* Advanced knowledge graph reasoning
* GPU distributed inference
* Model quantization
* Automated MLOps pipelines
* Production Kubernetes deployment
* Advanced observability
* Scalable object storage
* Multi-user collaboration
* Real-time video intelligence

---

# Contributing

Contributions are welcome.

Please open an Issue before submitting a Pull Request.

For development guidelines, see:

```text
CONTRIBUTING.md
```

---

# License

MIT License

---

# Author

**Nguyen Hoang Khang**

Data / AI Engineer

Ho Chi Minh City University of Industry and Trade

---

If you find this project useful, consider giving it a star on GitHub.