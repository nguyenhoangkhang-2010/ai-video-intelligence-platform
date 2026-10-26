#!/usr/bin/env bash
# Run the frontend dev server directly on the host (no Docker).
#
# NOTE: frontend/ is currently an empty scaffold (no name/dependencies/
# scripts in package.json, no lockfile) - there is nothing to install
# or run yet. This script becomes usable as soon as real Next.js
# application code and a package-lock.json exist; nothing here needs
# to change when that happens.
set -euo pipefail

cd "$(dirname "$0")/../frontend"

if [ ! -s package.json ] || [ ! -f package-lock.json ]; then
    echo "frontend/ has no installable package.json/lockfile yet - nothing to run." >&2
    exit 1
fi

npm ci
npm run dev
