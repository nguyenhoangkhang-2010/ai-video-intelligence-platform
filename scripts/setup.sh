#!/usr/bin/env bash
# One-time local development setup: creates .env from the example
# file (if missing) and creates the local storage directories the
# backend expects. Does not install Python/Node dependencies - use
# Docker Compose (recommended) or your own virtualenv/npm install for
# that.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - fill in real values before running anything beyond local defaults."
else
    echo ".env already exists - leaving it untouched."
fi

mkdir -p storage/videos storage/audio storage/subtitles storage/thumbnails

echo "Setup complete. Next steps:"
echo "  docker compose up --build     # start backend, worker, redis, db"
echo "  make migrate                  # apply database migrations"
