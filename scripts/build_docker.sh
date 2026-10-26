#!/usr/bin/env bash
# Build the project's Docker images locally.
#
# Usage:
#   scripts/build_docker.sh dev            # root (development) backend image
#   scripts/build_docker.sh prod           # deployment/docker/backend.Dockerfile
#   scripts/build_docker.sh frontend-prod  # deployment/docker/frontend.Dockerfile
set -euo pipefail

cd "$(dirname "$0")/.."

target="${1:-dev}"

case "$target" in
    dev)
        docker build -f Dockerfile -t ai-video-backend:dev .
        ;;
    prod)
        docker build -f deployment/docker/backend.Dockerfile -t ai-video-backend:prod .
        ;;
    frontend-prod)
        if [ ! -s frontend/package.json ] || [ ! -f frontend/package-lock.json ]; then
            echo "frontend/ has no installable package.json/lockfile yet - nothing to build." >&2
            exit 1
        fi
        docker build -f deployment/docker/frontend.Dockerfile -t ai-video-frontend:prod frontend
        ;;
    *)
        echo "Unknown target: $target (expected: dev | prod | frontend-prod)" >&2
        exit 1
        ;;
esac
