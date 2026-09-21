"""
Application settings.

This module centralizes every configuration used across the
AI Video Intelligence Platform.

Environment variables are loaded from `.env`
and validated using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# Paths
# =============================================================================

# backend/app/config/settings.py
#              ↑
# parents[0] = config
# parents[1] = app
# parents[2] = backend
# parents[3] = project root

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"

BACKEND_DIR = PROJECT_ROOT / "backend"

AI_DIR = BACKEND_DIR / "ai"

DATA_DIR = PROJECT_ROOT / "data"

STORAGE_DIR = PROJECT_ROOT / "storage"

UPLOAD_DIR = STORAGE_DIR / "videos"

VIDEO_UPLOAD_DIR = STORAGE_DIR / "videos"

TEMP_DIR = STORAGE_DIR / "temp"

CACHE_DIR = STORAGE_DIR / "cache"

LOG_DIR = PROJECT_ROOT / "logs"

# =============================================================================
# Application
# =============================================================================
class BaseConfig(BaseSettings):
    """Base configuration shared by all settings."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

class AppSettings(BaseConfig):
    """Application metadata."""
    name: str = Field(
        default="AI Video Intelligence Platform",
        alias="APP_NAME",
    )

    version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )
    environment: Literal[
        "development",
        "testing",
        "production",
    ] = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    api_prefix: str = "/api/v1"

    docs_url: str = "/docs"

    redoc_url: str = "/redoc"

    openapi_url: str = "/openapi.json"


# =============================================================================
# Server
# =============================================================================
class ServerSettings(BaseConfig):
    """FastAPI server settings."""
    host: str = Field(
        default="0.0.0.0",
        alias="HOST",
    )

    port: int = Field(
        default=8000,
        alias="PORT",
    )
    workers: int = 1
    reload: bool = True
    timeout: int = 300
    
# =============================================================================
# Security
# =============================================================================
class SecuritySettings(BaseConfig):
    """Security configuration."""
    secret_key: str = Field(
        ...,
        alias="SECRET_KEY",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        alias="CORS_ORIGINS",
    )

# =============================================================================
# Database
# =============================================================================
class DatabaseSettings(BaseConfig):
    """PostgreSQL configuration."""
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
    )
    echo: bool = Field(
        default=False,
        alias="DB_ECHO",
    )
    pool_size: int = Field(
        default=10,
        alias="DB_POOL_SIZE",
    )
    max_overflow: int = Field(
        default=20,
        alias="DB_MAX_OVERFLOW",
    )
    pool_timeout: int = Field(
        default=30,
        alias="DB_POOL_TIMEOUT",
    )
    pool_recycle: int = Field(
        default=1800,
        alias="DB_POOL_RECYCLE",
    )
    pool_pre_ping: bool = Field(
        default=True,
        alias="DB_POOL_PRE_PING",
    )

    @property
    def url(self) -> str:
        """Return database URL."""
        return self.database_url

# =============================================================================
# HuggingFace
# =============================================================================
class HuggingFaceSettings(BaseConfig):
    """HuggingFace configuration."""

    token: str | None = Field(
        default=None,
        alias="HF_TOKEN",
    )
    
# =============================================================================
# LLM
# =============================================================================
class LLMSettings(BaseConfig):
    """LLM configuration."""

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )

    default_llm: str = Field(
        default="qwen3:8b",
        alias="DEFAULT_LLM",
    )

# =============================================================================
# Speech Intelligence
# =============================================================================
class SpeechSettings(BaseConfig):
    """Speech recognition, VAD, language detection, and diarization configuration."""

    whisper_model: str = Field(
        default="base",
        alias="WHISPER_MODEL",
    )

    device: Literal["cpu", "cuda"] = Field(
        default="cpu",
        alias="WHISPER_DEVICE",
    )

    compute_type: str = Field(
        default="int8",
        alias="WHISPER_COMPUTE_TYPE",
    )

    beam_size: int = Field(
        default=5,
        alias="WHISPER_BEAM_SIZE",
    )

    vad_enabled: bool = Field(
        default=True,
        alias="SPEECH_VAD_ENABLED",
    )

    vad_threshold: float = Field(
        default=0.5,
        alias="SPEECH_VAD_THRESHOLD",
    )

    vad_min_silence_duration_ms: int = Field(
        default=2000,
        alias="SPEECH_VAD_MIN_SILENCE_DURATION_MS",
    )

    language_detection_fallback_threshold: float = Field(
        default=0.5,
        alias="LANGUAGE_DETECTION_FALLBACK_THRESHOLD",
    )

    diarization_enabled: bool = Field(
        default=False,
        alias="SPEECH_DIARIZATION_ENABLED",
    )

    diarization_model: str = Field(
        default="pyannote/speaker-diarization-3.1",
        alias="DIARIZATION_MODEL",
    )

# =============================================================================
# Chapter & Topic Intelligence
# =============================================================================
class ChapterSettings(BaseConfig):
    """Topic segmentation and chapter detection configuration."""

    use_embedding_segmentation: bool = Field(
        default=True,
        alias="CHAPTER_USE_EMBEDDING_SEGMENTATION",
    )

    topic_similarity_threshold: float = Field(
        default=0.6,
        alias="CHAPTER_TOPIC_SIMILARITY_THRESHOLD",
    )

    min_topic_segments: int = Field(
        default=3,
        alias="CHAPTER_MIN_TOPIC_SEGMENTS",
    )

    chapter_similarity_threshold: float = Field(
        default=0.5,
        alias="CHAPTER_SIMILARITY_THRESHOLD",
    )

    max_topics_per_chapter: int = Field(
        default=4,
        alias="CHAPTER_MAX_TOPICS_PER_CHAPTER",
    )

    min_chapter_duration_seconds: float = Field(
        default=15.0,
        alias="CHAPTER_MIN_DURATION_SECONDS",
    )

    use_llm_labeling: bool = Field(
        default=True,
        alias="CHAPTER_USE_LLM_LABELING",
    )

# =============================================================================
# Quiz Generation
# =============================================================================
class QuizSettings(BaseConfig):
    """Quiz generation configuration."""

    enabled: bool = Field(
        default=True,
        alias="QUIZ_LLM_ENABLED",
    )

    mcq_count: int = Field(
        default=3,
        alias="QUIZ_MCQ_COUNT",
    )

    true_false_count: int = Field(
        default=2,
        alias="QUIZ_TRUE_FALSE_COUNT",
    )

    short_answer_count: int = Field(
        default=2,
        alias="QUIZ_SHORT_ANSWER_COUNT",
    )

    max_context_chars: int = Field(
        default=6000,
        alias="QUIZ_MAX_CONTEXT_CHARS",
    )

# =============================================================================
# Flashcard Generation
# =============================================================================
class FlashcardSettings(BaseConfig):
    """Flashcard generation configuration."""

    enabled: bool = Field(
        default=True,
        alias="FLASHCARD_LLM_ENABLED",
    )

    card_count: int = Field(
        default=8,
        alias="FLASHCARD_COUNT",
    )

    max_context_chars: int = Field(
        default=6000,
        alias="FLASHCARD_MAX_CONTEXT_CHARS",
    )

# =============================================================================
# Knowledge Graph Extraction
# =============================================================================
class KnowledgeGraphSettings(BaseConfig):
    """Entity/relation extraction configuration."""

    enabled: bool = Field(
        default=True,
        alias="KG_LLM_ENABLED",
    )

    max_entities_per_chunk: int = Field(
        default=15,
        alias="KG_MAX_ENTITIES_PER_CHUNK",
    )

    max_relations_per_chunk: int = Field(
        default=20,
        alias="KG_MAX_RELATIONS_PER_CHUNK",
    )

    max_context_chars: int = Field(
        default=4000,
        alias="KG_MAX_CONTEXT_CHARS",
    )

    min_confidence: float = Field(
        default=0.0,
        alias="KG_MIN_CONFIDENCE",
    )

# =============================================================================
# Retrieval & Reranking
# =============================================================================
class RetrievalSettings(BaseConfig):
    """Retrieval and reranking configuration."""

    cross_encoder_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="CROSS_ENCODER_MODEL",
    )

    rrf_k: int = Field(
        default=60,
        alias="RETRIEVAL_RRF_K",
    )

    candidate_multiplier: int = Field(
        default=4,
        alias="RETRIEVAL_CANDIDATE_MULTIPLIER",
    )

# =============================================================================
# AI Quality Evaluation
# =============================================================================
class EvaluationSettings(BaseConfig):
    """AI quality evaluation (retrieval/RAG/generation/performance) configuration."""

    enabled: bool = Field(
        default=True,
        alias="EVALUATION_ENABLED",
    )

    default_top_k: int = Field(
        default=5,
        alias="EVALUATION_DEFAULT_TOP_K",
    )

    bertscore_model: str | None = Field(
        default=None,
        alias="EVALUATION_BERTSCORE_MODEL",
    )

    bertscore_lang: str = Field(
        default="en",
        alias="EVALUATION_BERTSCORE_LANG",
    )

    llm_judge_enabled: bool = Field(
        default=False,
        alias="EVALUATION_LLM_JUDGE_ENABLED",
    )

    latency_iterations: int = Field(
        default=10,
        alias="EVALUATION_LATENCY_ITERATIONS",
    )

# =============================================================================
# Logging
# =============================================================================
class LogSettings(BaseConfig):
    """Application/worker logging configuration."""

    level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    json_format: bool = Field(
        default=False,
        alias="LOG_JSON",
    )

# =============================================================================
# Celery / Worker
# =============================================================================
class CelerySettings(BaseConfig):
    """
    Production Celery worker configuration.

    `task_queue` is the queue a worker process consumes from by
    default when no explicit `-Q` is passed on the command line (see
    app/workers/celery_app.py) - "celery_cpu" and "celery_gpu" are
    declared as separate queues so an operator can route the existing
    process_video task to a GPU-equipped worker fleet (by starting a
    worker with `-Q celery_gpu` and WHISPER_DEVICE=cuda) without any
    code changes, while the default single-worker/single-queue setup
    (both dev and prod Compose) keeps working unchanged.
    """

    task_queue: str = Field(
        default="celery_cpu",
        alias="CELERY_TASK_QUEUE",
    )

    worker_prefetch_multiplier: int = Field(
        default=1,
        alias="CELERY_WORKER_PREFETCH_MULTIPLIER",
    )

    worker_max_tasks_per_child: int = Field(
        default=50,
        alias="CELERY_WORKER_MAX_TASKS_PER_CHILD",
    )

    task_time_limit: int = Field(
        default=3600,
        alias="CELERY_TASK_TIME_LIMIT",
    )

    task_soft_time_limit: int = Field(
        default=3300,
        alias="CELERY_TASK_SOFT_TIME_LIMIT",
    )

    task_max_retries: int = Field(
        default=3,
        alias="CELERY_TASK_MAX_RETRIES",
    )

    task_retry_backoff_max: int = Field(
        default=60,
        alias="CELERY_TASK_RETRY_BACKOFF_MAX",
    )

# =============================================================================
# Metrics
# =============================================================================
class MetricsSettings(BaseConfig):
    """Prometheus metrics configuration."""

    enabled: bool = Field(
        default=True,
        alias="METRICS_ENABLED",
    )

    worker_metrics_port: int = Field(
        default=9100,
        alias="METRICS_WORKER_PORT",
    )

# =============================================================================
# Storage
# =============================================================================
class StorageSettings(BaseConfig):
    """
    Storage backend selection for generated/uploaded artifacts.

    "local" (default) uses the existing STORAGE_DIR filesystem layout
    unchanged. "s3" is opt-in and targets any S3-compatible endpoint
    (AWS S3 or MinIO) via boto3, which already resolves credentials
    from the standard AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/IAM role
    chain - no custom credential settings are introduced here.
    """

    backend: Literal["local", "s3"] = Field(
        default="local",
        alias="STORAGE_BACKEND",
    )

    s3_bucket: str | None = Field(
        default=None,
        alias="STORAGE_S3_BUCKET",
    )

    s3_endpoint_url: str | None = Field(
        default=None,
        alias="STORAGE_S3_ENDPOINT_URL",
    )

    s3_region: str | None = Field(
        default=None,
        alias="STORAGE_S3_REGION",
    )

# =============================================================================
# Global Settings Instance
# =============================================================================
class Settings(BaseModel):
    """
    Main application settings.
    Aggregates all configuration sections.
    """
    app: AppSettings = Field(default_factory=AppSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    huggingface: HuggingFaceSettings =Field(default_factory=HuggingFaceSettings)
    llm: LLMSettings =Field(default_factory=LLMSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    speech: SpeechSettings = Field(default_factory=SpeechSettings)
    chapter: ChapterSettings = Field(default_factory=ChapterSettings)
    quiz: QuizSettings = Field(default_factory=QuizSettings)
    flashcard: FlashcardSettings = Field(default_factory=FlashcardSettings)
    knowledge_graph: KnowledgeGraphSettings = Field(default_factory=KnowledgeGraphSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    logging: LogSettings = Field(default_factory=LogSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings instance.
    """
    return Settings()
settings = get_settings()
