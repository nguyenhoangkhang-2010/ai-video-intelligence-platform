# Development-oriented backend image, reused by docker-compose.yml for
# both the "api" (uvicorn) and "celery" (worker) services via different
# commands - see section "Celery Worker Container" in README.md. For a
# hardened, multi-stage production image, see
# deployment/docker/backend.Dockerfile instead.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    gcc \
    g++ \
    curl \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

COPY requirements/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./backend/app
COPY backend/ai ./backend/ai
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini

ENV PYTHONPATH=/app/backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# No secrets are baked in - DATABASE_URL/REDIS_URL/SECRET_KEY/etc. are
# always supplied at container-run time via env_file/environment (see
# docker-compose.yml and .env.example), never hardcoded here.

RUN groupadd --system app && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app
USER app

WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]