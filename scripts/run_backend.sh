#!/usr/bin/env bash
# Run the FastAPI backend directly on the host (no Docker) for local
# development - requires the dependencies in requirements/requirements.txt
# to already be installed in the active Python environment, and a
# reachable Postgres/Redis (see .env.example DATABASE_URL/REDIS_URL).
set -euo pipefail

cd "$(dirname "$0")/../backend"

export PYTHONPATH="$(pwd)"

uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
