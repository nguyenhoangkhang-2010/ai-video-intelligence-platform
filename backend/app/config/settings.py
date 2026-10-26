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

from pydantic import BaseModel, Field, field_validator, model_validator
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
# Substrings of SECRET_KEY that mark it as a copy-pasted example
# value rather than a real secret - case-insensitive. min_length=32
# below only proves the value is *long enough*; it does not and
# cannot prove it is actually secret (`.env.example`'s own
# "CHANGE_ME_TO_A_LONG_RANDOM_VALUE" happens to be exactly 32
# characters, so it passes that check while being a publicly-known
# value in this very repo). Settings.reject_placeholder_secret_key
# below is the actual guard against shipping one of these to
# production.
_PLACEHOLDER_SECRET_KEY_MARKERS = (
    "change_me",
    "changeme",
    "example",
    "insecure",
    "replace_me",
    "your_secret",
    "secret_key_here",
    "todo",
)


class SecuritySettings(BaseConfig):
    """Security configuration."""
    secret_key: str = Field(
        ...,
        alias="SECRET_KEY",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Short-lived, resource-scoped media token (see
    # app.auth.jwt.create_media_token) - issued per-video via
    # GET /videos/{id}/media-token and used ONLY as the ?token=
    # query param on <video>/<img> element URLs, so the user's
    # long-lived main access token never has to appear in a URL
    # (browser history, server/proxy access logs, Referer headers).
    # Short enough that a leaked media URL is worthless within
    # minutes; long enough to cover a page load plus normal playback
    # start (React Query refetches a new one before this expires -
    # see frontend hooks/useMediaToken.ts).
    media_token_expire_seconds: int = Field(
        default=300,
        alias="MEDIA_TOKEN_EXPIRE_SECONDS",
    )

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

    # Selects which LLMProvider implementation ai.llm.factory.
    # get_llm_provider() returns. "ollama" is the only implementation
    # today; this exists so a future provider is a config value and a
    # new factory branch, not a change to every call site that
    # currently constructs OllamaClient() directly.
    provider: Literal["ollama"] = Field(
        default="ollama",
        alias="LLM_PROVIDER",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )

    default_llm: str = Field(
        default="qwen3:8b",
        alias="DEFAULT_LLM",
    )

    request_timeout_seconds: int = Field(
        default=300,
        alias="OLLAMA_TIMEOUT_SECONDS",
    )

    # Reasoning ("thinking") mode for models that have one (qwen3).
    # Off by default: every generator in this project wants the final
    # answer only, and on CPU the hidden reasoning tokens cost ~2.8x
    # wall time per call (docs/benchmarks/pipeline-performance.md).
    # Leave empty (OLLAMA_THINK=) to not send the option at all, for
    # models/Ollama versions that reject it.
    think: bool | None = Field(
        default=False,
        alias="OLLAMA_THINK",
    )

    @field_validator("think", mode="before")
    @classmethod
    def _empty_think_means_unset(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

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

    max_context_chars: int = Field(
        default=6000,
        alias="CHAPTER_MAX_CONTEXT_CHARS",
    )

# =============================================================================
# Visual understanding
# =============================================================================
class VisionSettings(BaseConfig):
    """Keyframe analysis with a vision-language model (ai.vision)."""

    enabled: bool = Field(
        default=True,
        alias="VISION_ENABLED",
    )

    # Any Ollama vision model. qwen2.5vl reads Vietnamese on-screen
    # text; the 3B size keeps CPU inference at ~10-30 s per frame.
    model: str = Field(
        default="qwen2.5vl:3b",
        alias="VISION_MODEL",
    )

    max_frames: int = Field(
        default=20,
        alias="VISION_MAX_FRAMES",
    )

    scene_threshold: float = Field(
        default=0.3,
        alias="VISION_SCENE_THRESHOLD",
    )

    min_gap_seconds: float = Field(
        default=4.0,
        alias="VISION_MIN_GAP_SECONDS",
    )

    max_gap_seconds: float = Field(
        default=30.0,
        alias="VISION_MAX_GAP_SECONDS",
    )

    frame_width: int = Field(
        default=768,
        alias="VISION_FRAME_WIDTH",
    )

    # Cosine similarity (BGE-M3) between a frame's description and what
    # was said around it, at or above which the frame is treated as
    # illustrating the speech rather than as unrelated b-roll.
    related_threshold: float = Field(
        default=0.45,
        alias="VISION_RELATED_THRESHOLD",
    )

# =============================================================================
# Summarization
# =============================================================================
class SummarySettings(BaseConfig):
    """Summarization configuration."""

    max_context_chars: int = Field(
        default=12000,
        alias="SUMMARY_MAX_CONTEXT_CHARS",
    )

# =============================================================================
# Translation
# =============================================================================
class TranslationSettings(BaseConfig):
    """Translation configuration."""

    max_context_chars: int = Field(
        default=12000,
        alias="TRANSLATION_MAX_CONTEXT_CHARS",
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
        default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
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

    hybrid_enabled: bool = Field(
        default=True,
        alias="RETRIEVAL_HYBRID_ENABLED",
    )

    reranking_enabled: bool = Field(
        default=True,
        alias="RETRIEVAL_RERANKING_ENABLED",
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

    # How long the Redis broker holds an unacked message invisible to
    # other workers before redelivering it (Celery's Redis transport
    # `visibility_timeout`, default 3600s/1h if unset - confirmed live:
    # a task in flight when its worker container was recreated stayed
    # stuck PENDING for the full default before this was set, directly
    # contradicting task_acks_late's documented intent of "redelivered
    # rather than silently lost"). Safe to keep well below
    # task_time_limit here specifically because a redelivered task for
    # an already-claimed/finished job is a guaranteed no-op (see the
    # atomic PENDING->RUNNING claim in ProcessingPipeline.run) - an
    # occasional premature redelivery costs nothing, while a crashed
    # worker's job sitting invisible for up to an hour is a real
    # "stuck job" incident.
    broker_visibility_timeout: int = Field(
        default=1800,
        alias="CELERY_BROKER_VISIBILITY_TIMEOUT",
    )

    # How old a PENDING job with no started_at must be before it's
    # treated as orphaned (its original .delay() call likely never
    # arrived - see UploadPipeline.process's dual-write gap) rather
    # than merely a normal dispatch still in flight. 5 minutes is
    # generous relative to how fast a Celery .delay() call actually
    # returns (milliseconds) - this only exists to rule out false
    # positives from ordinary request latency, not to detect genuine
    # delay.
    dispatch_grace_period_seconds: int = Field(
        default=300,
        alias="CELERY_DISPATCH_GRACE_PERIOD_SECONDS",
    )

    # Bounds ProcessingJobService.reconcile_orphaned_dispatch's
    # re-dispatch retries, so a permanently-undispatchable job (e.g.
    # the broker itself is down) reaches a clean terminal FAILED
    # state instead of being retried forever.
    max_dispatch_attempts: int = Field(
        default=3,
        alias="CELERY_MAX_DISPATCH_ATTEMPTS",
    )

    # How often the worker that owns a RUNNING job refreshes its
    # heartbeat_at (app.workers.heartbeat.JobHeartbeat).
    job_heartbeat_interval_seconds: int = Field(
        default=15,
        alias="CELERY_JOB_HEARTBEAT_INTERVAL_SECONDS",
    )

    # How long a RUNNING job's heartbeat may stay quiet before the job
    # is treated as orphaned (its worker died: container restart,
    # engine crash, OOM kill). Deliberately many intervals long, so a
    # briefly stalled database write or a busy CPU never makes a live
    # job look dead.
    job_heartbeat_timeout_seconds: int = Field(
        default=180,
        alias="CELERY_JOB_HEARTBEAT_TIMEOUT_SECONDS",
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

    max_upload_size_mb: int = Field(
        default=5000,
        alias="STORAGE_MAX_UPLOAD_SIZE_MB",
    )

    allowed_upload_extensions: list[str] = Field(
        default=[".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"],
        alias="STORAGE_ALLOWED_UPLOAD_EXTENSIONS",
    )

# =============================================================================
# Rate Limiting
# =============================================================================
class RateLimitSettings(BaseConfig):
    """
    Redis-backed rate limiting for abuse-prone endpoints (login,
    register, upload, search, RAG chat, flashcard export). Reuses the
    same Redis instance Celery already requires - no new
    infrastructure dependency. Every limit is env-driven so an
    operator can tune or disable it per deployment without a code
    change; defaults are generous enough that normal local development
    (a handful of requests while testing a feature) never trips them,
    while still providing real protection in production.
    """

    enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="RATE_LIMIT_REDIS_URL",
    )

    # (limit, window_seconds) per category, keyed by client IP.
    login_limit: int = Field(default=10, alias="RATE_LIMIT_LOGIN_PER_MINUTE")
    register_limit: int = Field(default=5, alias="RATE_LIMIT_REGISTER_PER_MINUTE")
    upload_limit: int = Field(default=20, alias="RATE_LIMIT_UPLOAD_PER_HOUR")
    search_limit: int = Field(default=30, alias="RATE_LIMIT_SEARCH_PER_MINUTE")
    export_limit: int = Field(default=20, alias="RATE_LIMIT_EXPORT_PER_MINUTE")
    retry_limit: int = Field(default=20, alias="RATE_LIMIT_RETRY_PER_HOUR")

    # Direct-peer IPs allowed to supply a trustworthy X-Forwarded-For.
    # Empty by default - request.client.host (the real TCP peer) is
    # always used unless a hop is explicitly trusted. In the
    # documented production topology (nginx in front of uvicorn,
    # deployment/nginx/nginx.conf), uvicorn is started WITHOUT
    # --proxy-headers, so request.client.host there is nginx's own
    # container IP for every request - the rate limiter would
    # otherwise be keying every real client behind the proxy under
    # one shared bucket (a trivial way for one user to lock out
    # everyone else's login attempts). Set this to nginx's container
    # IP or the Compose network's CIDR to restore real per-client
    # limiting in that deployment - find it with `docker network
    # inspect <project>_default` or by pinning nginx a static IP in
    # the Compose network config. Deliberately NOT set by default
    # here: guessing wrong would silently trust an untrusted peer's
    # self-reported header, which is worse than today's "one shared
    # bucket" behavior.
    trusted_proxy_ips: list[str] = Field(
        default=[],
        alias="RATE_LIMIT_TRUSTED_PROXIES",
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
    vision: VisionSettings = Field(default_factory=VisionSettings)
    summary: SummarySettings = Field(default_factory=SummarySettings)
    translation: TranslationSettings = Field(default_factory=TranslationSettings)
    quiz: QuizSettings = Field(default_factory=QuizSettings)
    flashcard: FlashcardSettings = Field(default_factory=FlashcardSettings)
    knowledge_graph: KnowledgeGraphSettings = Field(default_factory=KnowledgeGraphSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    logging: LogSettings = Field(default_factory=LogSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    @model_validator(mode="after")
    def reject_placeholder_secret_key_in_production(self) -> "Settings":
        """
        SecuritySettings.secret_key's min_length=32 only proves the
        value is long enough - it cannot prove it is actually secret.
        `.env.example`'s own "CHANGE_ME_TO_A_LONG_RANDOM_VALUE" is
        exactly 32 characters, so it passes that check while being a
        publicly-known value in this repo's own history: an operator
        who copies .env.example to .env/.env.production without
        changing SECRET_KEY would otherwise deploy a production
        instance signing every JWT (including media tokens) with a
        secret anyone can read on GitHub.

        Only enforced when ENVIRONMENT=production - development/
        testing keep working with any placeholder, since that is
        exactly what local development uses .env.example's defaults
        for.
        """
        if self.app.environment != "production":
            return self

        lowered = self.security.secret_key.lower()

        if any(
            marker in lowered
            for marker in _PLACEHOLDER_SECRET_KEY_MARKERS
        ):
            raise ValueError(
                "SECRET_KEY looks like a placeholder/example value "
                "(matches a known marker such as 'CHANGE_ME' or "
                "'example'). Refusing to start with ENVIRONMENT="
                "production and an unchanged example secret - "
                "generate a real random value (e.g. `openssl rand "
                "-hex 32`) and set it as SECRET_KEY before deploying."
            )

        return self

@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings instance.
    """
    return Settings()
settings = get_settings()
