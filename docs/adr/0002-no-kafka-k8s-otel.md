# 0002 - No Kafka, Kubernetes, or OpenTelemetry at this scale

## Status
Accepted (ongoing - revisit if the trigger conditions below occur).

## Context
This stack already has Redis (Celery broker/result backend) and a
single FastAPI + Celery-worker deployment (`docker-compose.yml`,
`deployment/docker/`). It's tempting to reach for the infrastructure
a large-scale version of this product would eventually need.

## Decision
Explicitly not adopted, each for a specific reason:

- **Kafka** - would be a second message broker alongside Celery/Redis
  for no capability this project currently needs (no multi-consumer-
  group fan-out, no event replay requirement, no cross-service event
  bus - there's one producer of work, one consumer type).
- **Kubernetes** - the deployment is a handful of long-lived
  containers (api, worker, db, redis, nginx, frontend) on one host;
  nothing here needs pod autoscaling, rolling multi-replica
  deployments, or scheduling across a cluster. Docker Compose
  (`docker-compose.yml` for development, `deployment/docker/
  docker-compose.prod.yml` for the single-host production stack) is
  the actual, only deployment target. An earlier `deployment/
  kubernetes/*.yaml` directory existed in this repo as unfilled
  scaffolding (four 0-byte files, never implemented or used) and
  contradicted this ADR's own position by implying K8s was a real
  deployment option - it has been deleted rather than backfilled,
  since nothing here currently needs it.
- **OpenTelemetry/Jaeger/Tempo** - a full distributed-tracing stack
  for a single-process-per-service system with no cross-service call
  chains to trace. Prometheus metrics (`app/core/metrics.py`,
  `app/workers/metrics.py`, `app/workers/pipeline_metrics.py`) plus
  structured logs already answer "is it slow, and where" for this
  topology; tracing earns its cost once there are multiple services
  whose call chain isn't obvious from the code.

## Consequences
- Lower operational burden: no cluster to run, no second broker's
  consumer-group/partition model to reason about, no trace collector/
  storage backend to maintain.
- Revisit Kafka if a second, independent consumer of the same events
  appears (e.g. an analytics pipeline that must not share Celery's
  queue). Revisit Kubernetes if the deployment needs to scale the API
  and worker independently across multiple hosts, or needs zero-
  downtime multi-replica rollouts. Revisit tracing if the system
  decomposes into multiple network-separated services whose latency
  can no longer be attributed from one process's logs/metrics alone.
