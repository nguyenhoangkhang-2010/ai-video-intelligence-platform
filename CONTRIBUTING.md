# Contributing

Thanks for your interest in **AI Video Intelligence Platform (ReelSense)**. This guide covers how to set up the project, the conventions it follows, and what a pull request needs before it can be merged.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before you start

- **Open an issue first** for anything beyond a typo or a one-line fix. Describe the problem or the change you want to make, so we can agree on the approach before you spend time on it.
- **Bugs:** include what you did, what you expected, what actually happened, and logs if you have them (`docker compose logs api` / `docker compose logs celery`, or the browser console).
- **Security issues:** don't open a public issue. Contact the maintainer privately through the GitHub profile ([@nguyenhoangkhang-2010](https://github.com/nguyenhoangkhang-2010)).

## Project layout

| Path | What lives there |
|---|---|
| `backend/app/` | FastAPI app: `api/v1/endpoints` → `services` → `repositories` → `models`, plus `schemas`, `pipelines` (video processing orchestration) and `workers` (Celery) |
| `backend/ai/` | Pure AI/ML logic (speech, embeddings, retrieval, summarization, translation, chapters, quiz, flashcards). **No FastAPI or database imports here.** |
| `backend/alembic/` | Database migrations |
| `backend/tests/` | Backend test suite (pytest) |
| `frontend/` | Next.js (App Router) + TypeScript + Tailwind UI, Vitest unit tests, Playwright e2e (`frontend/e2e/`) |
| `requirements/` | `requirements.in` (direct dependencies) and `requirements.txt` (compiled lock file) |
| `deployment/`, `monitoring/` | Production compose/images/nginx, Prometheus + Grafana |
| `docs/` | API contract (`docs/api/rest_api.md`), architecture decisions (`docs/adr/`), testing notes (`docs/testing/`), deployment |

## Local setup

**Prerequisites:** Docker Desktop, Node.js 20, Git, and [Ollama](https://ollama.com/) running on the host with the LLM pulled (default `qwen3:8b`: `ollama pull qwen3:8b`). Processing a video loads Whisper, an embedding model and the LLM at the same time, so plan for roughly 16 GB of free RAM; a lighter `WHISPER_MODEL` (e.g. `base` or `small`) helps on smaller machines.

1. **Backend** (PostgreSQL, Redis, API, Celery worker) — from the repository root:

   ```bash
   cp .env.example .env        # set SECRET_KEY and review the comments in the file
   docker compose up --build -d
   ```

   Migrations run automatically when the `api` container starts. The API is published at `http://localhost:8001` (docs at `http://localhost:8001/docs`).

2. **Frontend** — in a second terminal:

   ```bash
   cd frontend
   cp .env.example .env.local  # NEXT_PUBLIC_API_URL defaults to http://localhost:8001
   npm install
   npm run dev
   ```

   Open `http://localhost:3000`. The backend's CORS settings allow `localhost:3000` and `127.0.0.1:3000` by default.

Backend code is built into the Docker image, so after changing backend code or dependencies, rebuild with `docker compose up -d --build`. Never commit `.env`, `.env.local`, or any credentials.

## Branches and commits

- Branch from **`develop`** and open your pull request against **`develop`**. `develop` is merged into `main` for releases.
- Name branches by type: `feat/…`, `fix/…`, `docs/…`, `refactor/…`, `test/…`, `ci/…`, `chore/…` (for example `feat/subtitle-export`).
- Write commit messages in [Conventional Commits](https://www.conventionalcommits.org/) style, with an optional scope:

  ```text
  feat(reliability): make the video pipeline stage-resumable
  fix(deps): pin the full dependency closure via a compiled lock file
  docs: reconcile architecture and deployment documentation
  ```

- Keep each pull request focused on one change. Separate refactors from behavior changes.

## Checks before opening a pull request

CI runs these on every pull request; run them locally first.

**Backend**

```bash
ruff check backend                     # lint (blocking in CI)
cd backend && pytest tests/ -q         # test suite
```

Or inside the running container: `docker compose exec api pytest tests -q`.

**Frontend** (from `frontend/`)

```bash
npm run lint
npx tsc --noEmit
npm run test
npm run build
```

**End-to-end (optional, local only):** `npm run test:e2e` drives a real browser against the running dev stack. See [`docs/testing/e2e.md`](docs/testing/e2e.md) for what it covers, and [`docs/testing/ci-strategy.md`](docs/testing/ci-strategy.md) for which checks are blocking in CI.

## Conventions

### Backend

- Keep the layering: endpoints stay thin, business logic goes in `services`, database access goes in `repositories`.
- Code in `backend/ai/` must stay importable without FastAPI or a database.
- Every video-scoped endpoint must enforce ownership. Add a "not owned → 404" test for any new one.
- Add or update tests with every behavior change. Bug fixes should come with a regression test.
- Rate-limited endpoints run with `RATE_LIMIT_ENABLED=false` in tests (see `backend/tests/conftest.py`); keep tests deterministic and free of real network calls.

### Database migrations

- Change models in `backend/app/models/`, then create a migration from `backend/`:

  ```bash
  alembic revision --autogenerate -m "add subtitle table"
  ```

- Review the generated file before committing; autogenerate isn't always right. Keep the history linear and test with `alembic upgrade head`.

### Dependencies

- **Python:** edit `requirements/requirements.in` (direct dependencies only), then regenerate the lock file `requirements/requirements.txt` with `pip-compile` **inside a container built from the project's Dockerfile**, following the instructions at the top of `requirements.txt`. Don't hand-edit pins, and keep the documented version bounds in `requirements.in` (they fix real incompatibilities).
- **Frontend:** use `npm install <package>` and commit the updated `package-lock.json`.

### Frontend

- All HTTP calls go through the shared client in `frontend/src/lib/axios.ts` via modules in `src/services/`; components use hooks from `src/hooks/`.
- Keep TypeScript types in `src/types/` in sync with the backend's Pydantic response schemas.
- Use the design tokens defined in `src/app/globals.css` and `tailwind.config.ts` instead of hard-coded colors. The visual language is flat: no gradients, blur, or glow effects.
- Interactive elements need accessible names, and anything with keyboard focus must show a visible focus state.

### Documentation

- Update `README.md` or the relevant file in `docs/` when behavior, setup, or the API contract (`docs/api/rest_api.md`) changes.
- For a significant architectural decision where a real alternative was considered, add an ADR in `docs/adr/` (Context / Decision / Consequences).

## Pull request checklist

- [ ] Linked to an issue (or explains why none is needed)
- [ ] Focused on one change, with a clear description of what and why
- [ ] Tests added or updated; backend and frontend checks pass locally
- [ ] Migrations included and reviewed (if models changed)
- [ ] Docs updated (if setup, behavior, or the API changed)
- [ ] No secrets, `.env` files, or large generated artifacts committed

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE) that covers this project.
