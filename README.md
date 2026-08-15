# Task Tracker

A small FastAPI + vanilla JS Kanban-style task tracker, built for the AUB Assisted Coding Course. See [`docs/midcourse/`](docs/midcourse/) for the Mid-Course Project documentation (user stories, design decisions, prompt log, verification evidence, and reflection).

## Project layout

```
backend/    FastAPI REST API (in-memory storage, no database)
frontend/   Static HTML/CSS/JS Kanban board (no build tooling required)
docs/       Project documentation, including docs/midcourse/
```

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

31 tests: task model validation, baseline CRUD endpoints, due dates / overdue filtering, and tags.

## Features

- **Task CRUD**: create, list (with status/priority filters), get, update, delete.
- **Due dates + overdue filter**: optional due date per task; tasks overdue (past-due and not Done) are flagged on the board and can be filtered with `?overdue=true`.
- **Tags**: optional tags per task (max 10, 30 chars each); tag chips on cards and a `?tag=` filter.
