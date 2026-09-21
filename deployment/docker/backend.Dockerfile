# Production backend image: multi-stage build so build-only tooling
# (build-essential/gcc/g++/git) never ends up in the final image.
# Build context is expected to be the repository root, e.g.:
#   docker build -f deployment/docker/backend.Dockerfile -t <name> .
#
# For local development, use the simpler root ./Dockerfile via
# docker-compose.yml instead - it is not replaced by this file.

# ---------- builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

COPY requirements/requirements.txt ./requirements.txt

# Installed into a self-contained venv so the runtime stage can copy
# just this directory - no compiler toolchain, no pip cache, no
# unrelated build artifacts.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only native dependencies (ffmpeg/audio/image libs actually
# used by the AI pipeline; no compiler toolchain).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/app ./backend/app
COPY backend/ai ./backend/ai
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini

ENV PYTHONPATH=/app/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DEBUG=False

# No secrets are baked in - every credential (DATABASE_URL, REDIS_URL,
# SECRET_KEY, HF_TOKEN, OLLAMA_BASE_URL, ...) is supplied at container
# run time only, via the deployment environment/secret store.

RUN groupadd --system app && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app
USER app

WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Same image/command split as development: run with an explicit
# `command:` override (see docker-compose.prod.yml) to get the Celery
# worker instead of the API process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
