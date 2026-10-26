.PHONY: up down build logs logs-worker ps shell worker-shell test migrate down-v

# Start the development stack (backend, worker, redis, db) in the background.
up:
	docker compose up --build -d

# Stop the development stack (containers removed, named volumes kept).
down:
	docker compose down

# Rebuild images without starting containers.
build:
	docker compose build

# Follow API logs.
logs:
	docker compose logs -f api

# Follow Celery worker logs.
logs-worker:
	docker compose logs -f celery

# List running services.
ps:
	docker compose ps

# Open a shell in the running API container.
shell:
	docker compose exec api bash

# Open a shell in the running Celery worker container.
worker-shell:
	docker compose exec celery bash

# Run the backend test suite inside the API container.
test:
	docker compose exec api pytest tests -q

# Apply database migrations inside the API container.
migrate:
	docker compose exec api alembic upgrade head

# Stop the stack and remove named volumes (destroys local db/redis data).
down-v:
	docker compose down -v
