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

# Fresh named-volume mounts (production's storage_data - see
# deployment/docker/docker-compose.prod.yml) are created by Docker
# with root ownership on first use, regardless of what the image
# itself baked in at that path via `chown` at build time - a mount
# always wins over whatever was there before. The non-root "app" user
# this image otherwise runs as (see backend.Dockerfile/Dockerfile)
# then can't write into it at all. Found live: a real upload against
# the actual production Docker+HTTPS stack failed with
# PermissionError: [Errno 13] Permission denied: '/app/storage/videos'
# on a completely fresh deployment - not hypothetical.
#
# This entrypoint now runs as root specifically so it CAN chown that
# mount, then drops to "app" (via gosu) for every real workload below -
# nothing application-level ever runs as root. Already-correctly-owned
# paths (dev's bind-mounted ./storage, already owned by the host user
# that ran `docker compose up`) make this a no-op chown, so it's safe
# in both docker-compose.yml (dev) and docker-compose.prod.yml alike.
if [ -d /app/storage ]; then
    chown -R app:app /app/storage
fi

if [ "${RUN_MIGRATIONS_ON_START:-true}" = "true" ]; then
    echo "[entrypoint] Running database migrations (alembic upgrade head)..."
    gosu app alembic upgrade head
    echo "[entrypoint] Migrations up to date."
fi

exec gosu app "$@"
