# Prometheus (local/dev monitoring profile)

| File | Purpose |
|------|---------|
| `prometheus.yml` | Scrape config: API `/metrics` + Celery worker exporter(s). |
| `alerts.yml` | A few justified alert rules (API down, high 5xx rate, high Celery failure rate, growing job backlog). Evaluated by Prometheus itself; no Alertmanager is configured, so alerts are visible in Prometheus's own UI but not routed/notified anywhere - wire up Alertmanager if you need paging/notifications. |

## Usage

```bash
docker compose --profile monitoring up -d
# Prometheus UI: http://localhost:9090
```

Requires the `api`/`celery` services to already be running (`docker compose up`) - Prometheus only scrapes them, it doesn't start them.

## What is NOT included

Long-term storage/retention tuning, remote-write, federation, and Alertmanager are all left to a real deployment's own monitoring stack - this is a minimal local/dev starting point, not a production observability platform.
