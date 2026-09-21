# Grafana (local/dev monitoring profile)

| File | Purpose |
|------|---------|
| `datasource.yml` | Auto-provisions the local Prometheus datasource. |
| `dashboard-provider.yml` | Tells Grafana to load dashboards from the mounted directory. |
| `dashboard.json` | Minimal "AI Video Platform - Overview" dashboard: request rate, p95 request latency, 5xx error rate, Celery task success/failure rate, p95 Celery task duration, active processing jobs. |

## Usage

```bash
docker compose --profile monitoring up -d
# Grafana UI: http://localhost:3001 (default login: admin / admin, or GRAFANA_ADMIN_PASSWORD if set)
```

The dashboard and Prometheus datasource are provisioned automatically - no manual setup needed. Not mandatory for local development; only starts when the `monitoring` Compose profile is enabled.

## What is NOT included

This is intentionally a small, single dashboard - not a comprehensive observability suite. Add panels as real operational needs arise rather than speculatively.
