#!/bin/sh
# Entrypoint for both the "api" and "celery"/"celery-gpu" containers
# (same image, different `command:` in docker-compose.yml - see
# Dockerfile / deployment/docker/backend.Dockerfile).
#
# Runs `alembic upgrade head` once before starting the real process,
# so `docker compose up --build` on a clean database works without
# anyone needing to know migrations exist, let alone run them by
# hand. `alembic upgrade head` is itself idempotent (a no-op once the
# database is already at head), so this is safe on every restart, not
# just the first one - it does not re-run already-applied migrations.
#
# Only one service should actually run this: with `api` and `celery`
# both starting as soon as Postgres is healthy, two containers racing
# to create the same tables at once on a truly fresh database is a
# real failure mode. RUN_MIGRATIONS_ON_START designates the "api"
# service as the single migrator (see docker-compose.yml /
# docker-compose.prod.yml, where celery/celery-gpu set it to
# "false") rather than adding a distributed lock for a two-service
# case that doesn't need one.
set -e

if [ "${RUN_MIGRATIONS_ON_START:-true}" = "true" ]; then
    echo "[entrypoint] Running database migrations (alembic upgrade head)..."
    alembic upgrade head
    echo "[entrypoint] Migrations up to date."
fi

exec "$@"
