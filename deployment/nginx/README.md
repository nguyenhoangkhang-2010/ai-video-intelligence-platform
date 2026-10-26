# nginx reverse proxy

`nginx.conf` is the single public entry point for the production stack (`deployment/docker/docker-compose.prod.yml`): it listens on port 80 and proxies:

- `/api/`, `/docs`, `/openapi.json` -> the `api` service (FastAPI backend)
- everything else -> the `frontend` service (Next.js app, once it exists)

It is mounted read-only into the official `nginx:1.27-alpine` image - there is no custom nginx Docker image to build.

## Not included (Phase 12 scope)

TLS/certificates, rate limiting, caching, and other production-hardening concerns are intentionally left out here. Add them once a real target environment/provider is chosen (Phase 13).
