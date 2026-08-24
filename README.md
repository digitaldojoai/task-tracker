# Task Tracker

A small FastAPI + vanilla JS Kanban-style task tracker, built for the AUB Assisted Coding Course. See [`docs/midcourse/`](docs/midcourse/) for the Mid-Course Project documentation (user stories, design decisions, prompt log, verification evidence, and reflection).

## Project layout

```
backend/app/      FastAPI REST API (in-memory storage, no database)
backend/tests/    pytest suite (39 tests)
frontend/         Static HTML/CSS/JS Kanban board (no build tooling required)
docs/             Project documentation: midcourse/ and final project evidence
.github/workflows/ci.yml   CI: pytest + Docker /health check
Dockerfile        Container image for the API
AGENTS.md         Working rules for AI assistants in this repo
```

The final project brief refers to `app/` and `tests/` at the repository root. In
this repo they live under `backend/`:

| Brief refers to | Location here    |
| --------------- | ---------------- |
| `app/`          | `backend/app/`   |
| `tests/`        | `backend/tests/` |
| `frontend/`     | `frontend/`      |

## Run the backend

From `backend/`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API is served at http://127.0.0.1:8000. Interactive docs at http://127.0.0.1:8000/docs.

See [`backend/README.md`](backend/README.md) for full details (Windows instructions, environment variables, etc.).

## Run the frontend

The frontend is plain static files — no npm install needed. From `frontend/`, with the backend already running on port 8000:

```bash
python3 -m http.server 5500
```

Then open http://127.0.0.1:5500 in a browser. (Any static file server works — this just avoids `file://` CORS restrictions.)

## Run the tests

From `backend/`, with the virtual environment active:

```bash
pytest
```

39 tests: task model validation, baseline CRUD endpoints, due dates / overdue filtering, tags, and explicit-null handling on partial updates.

## Features

- **Task CRUD**: create, list (with status/priority filters), get, update, delete.
- **Due dates + overdue filter**: optional due date per task; tasks overdue (past-due and not Done) are flagged on the board and can be filtered with `?overdue=true`.
- **Tags**: optional tags per task (max 10, 30 chars each); tag chips on cards and a `?tag=` filter.
- **Strict partial updates**: on `PATCH /tasks/{id}`, omitting a field leaves it unchanged, and an explicit `null` is rejected with `422` for every field except `assignee` and `due_date`, where null clears the value.

## Final Project

Branch reviewed: `final-project`

### What this submission demonstrates

- The existing Task Tracker still runs inside the intended course scope — no new product features were added.
- CI runs the pytest suite on push and pull request.
- The Docker image builds and runs with `/health` returning 200.
- AI review, security, and ownership evidence is in [`docs/`](docs/).

### How to run locally

Backend, from `backend/`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend, from `frontend/`, in a second terminal with the API already running:

```bash
python3 -m http.server 5500
```

Then open http://127.0.0.1:5500.

### How to run tests

From `backend/`, with the virtualenv active:

```bash
pytest
```

### How to run with Docker

From the repository root:

```bash
docker build -t task-tracker .
docker run --rm -d --name task-tracker -p 8000:8000 task-tracker
curl -i http://127.0.0.1:8000/health
docker rm -f task-tracker
```

Expected: `HTTP/1.1 200 OK` with `{"status":"ok","timestamp":"..."}`.

The image contains only `backend/app/` and its dependencies. `.env`, `venv/`, and
the test suite are excluded by [`.dockerignore`](.dockerignore), and the container
runs as the non-root user `appuser` (UID 10001).

### Evidence files

- [`docs/release-evidence.md`](docs/release-evidence.md) — baseline, CI, Docker, and documentation claim checks.
- [`docs/final-ai-review.md`](docs/final-ai-review.md) — AI code review and security mini-logs, manual check, ownership statement.
- [`docs/ai-playbook.md`](docs/ai-playbook.md) — personal rules for working with AI.
- [`AGENTS.md`](AGENTS.md) — repo-specific guardrails for AI assistants.

### AI assistance summary

AI helped draft or review: the CI workflow, the Dockerfile and `.dockerignore`,
the final project documentation, and a read-only security pass over
`backend/app/` and `frontend/app.js`.

I verified the work by: running `pytest` (39 passed), starting the API and
checking `/health`, `POST/PATCH/DELETE /tasks`, the `?overdue=` and `?tag=`
filters and the 404/422 responses with `curl`, serving the frontend and
confirming the board loads, reading every generated diff line by line, and
requiring a green GitHub Actions run before treating CI and Docker as verified.

One AI suggestion I rejected or corrected: AI proposed moving `backend/app/` and
`backend/tests/` to the repository root so the layout matched the brief's example
literally. I rejected it — relocating a working, already-graded application to
satisfy a document is churn with real breakage risk (`uvicorn app.main:app` and
the pytest imports both depend on the current layout), so I documented the
mapping in this README and in `AGENTS.md` instead. Full details, plus the other
suggestions I corrected, are in [`docs/final-ai-review.md`](docs/final-ai-review.md).
