# Production Docker artifacts

| File | Purpose |
|------|---------|
| `backend.Dockerfile` | Multi-stage, hardened production image for the FastAPI backend. Also used, with a different `command:`, for the Celery worker. |
| `frontend.Dockerfile` | Multi-stage production image for the Next.js frontend (`frontend/`). Cannot be built yet - see note below. |
| `docker-compose.prod.yml` | Production/staging stack composing `db`, `redis`, `api`, `worker`, `nginx`, and (profile-gated) `worker-gpu` / `frontend`. |

## Usage

Run from the repository root, with a `.env.production` file (never committed) providing real values for the variables listed in `.env.example`:

```bash
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production up -d --build

# Optional GPU worker (requires the NVIDIA Container Toolkit on the host):
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production --profile gpu up -d --build
```

`api`/`worker`/`db`/`redis` have per-service CPU/memory limits, configurable via the `*_CPU_LIMIT`/`*_MEMORY_LIMIT` variables in `.env.example` (conservative starting points, not universally-correct values - see `docs/deployment.md`). See that same doc for the full CPU/GPU worker queue-routing model, retries, backup/recovery, and deployment/rollback procedure.

## Relationship to the root Dockerfile / docker-compose.yml

The root `./Dockerfile` and `./docker-compose.yml` are for **local development** only (bind-mounted storage, published ports for every service, simpler single-stage image). This directory is the **production** counterpart: multi-stage builds, no bind mounts, no unnecessary published ports, `nginx` as the sole public entry point.

## Known limitation

`frontend/` is currently an empty scaffold (no application code, no lockfile), so `frontend.Dockerfile` cannot actually be built until real Next.js code and a `package-lock.json` exist. The `frontend` service is defined under the `frontend` Compose profile so the rest of the stack is unaffected.
