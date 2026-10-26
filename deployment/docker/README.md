# Production Docker artifacts

| File | Purpose |
|------|---------|
| `backend.Dockerfile` | Multi-stage, hardened production image for the FastAPI backend. Also used, with a different `command:`, for the Celery worker. |
| `frontend.Dockerfile` | Multi-stage production image for the Next.js frontend (`frontend/`): install deps -> `next build` -> minimal `next start` runtime. |
| `docker-compose.prod.yml` | Production/staging stack composing `db`, `redis`, `api`, `worker`, `nginx`, and (profile-gated) `worker-gpu` / `frontend`. |

## TLS certificate (one-time setup)

`nginx` (see `../nginx/nginx.conf`) terminates HTTPS on port 443 and redirects plain HTTP (port 80) to it. It expects a certificate and key at `../nginx/certs/localhost.crt` / `../nginx/certs/localhost.key` - that directory is gitignored (see the repo root `.gitignore`), so this step is required after every fresh clone:

```bash
cd deployment/nginx/certs
openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout localhost.key -out localhost.crt \
  -subj "//CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

This is a **self-signed** certificate: fine for local/staging HTTPS testing (browsers will show a trust warning you can bypass, or install the cert as a locally-trusted CA), but not what a real public deployment should serve. For a real domain, replace both files with a CA-issued certificate (e.g. via certbot/Let's Encrypt) and restart the `nginx` container - `nginx.conf` itself does not need to change.

Also set `NEXT_PUBLIC_API_URL` in `.env.production` to the HTTPS origin nginx serves (e.g. `https://localhost` for the self-signed local setup, or `https://your-domain` for a real one) - see the comment on that variable in `.env.example`. The browser calls the API through nginx on that same origin; pointing it at the backend's internal port instead breaks the frontend's own CSP (`frontend/next.config.js`) and, on a real deployment, triggers mixed-content blocking.

## Usage

Run from the repository root, with a `.env.production` file (never committed) providing real values for the variables listed in `.env.example`:

```bash
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production up -d --build

# Frontend (opt-in profile - see docker-compose.prod.yml):
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production --profile frontend up -d --build

# Optional GPU worker (requires the NVIDIA Container Toolkit on the host):
docker compose -f deployment/docker/docker-compose.prod.yml \
  --env-file .env.production --profile gpu up -d --build
```

`api`/`worker`/`db`/`redis` have per-service CPU/memory limits, configurable via the `*_CPU_LIMIT`/`*_MEMORY_LIMIT` variables in `.env.example` (conservative starting points, not universally-correct values - see `docs/deployment.md`). See that same doc for the full CPU/GPU worker queue-routing model, retries, backup/recovery, and deployment/rollback procedure.

## Relationship to the root Dockerfile / docker-compose.yml

The root `./Dockerfile` and `./docker-compose.yml` are for **local development** only (bind-mounted storage, published ports for every service, simpler single-stage image, no TLS - the frontend there is normally run with `npm run dev` directly rather than through Docker at all). This directory is the **production** counterpart: multi-stage builds, no bind mounts, no unnecessary published ports, `nginx` as the sole public entry point, terminating HTTPS.
