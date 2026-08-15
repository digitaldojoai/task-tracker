# Task Tracker API

A FastAPI backend for the Task Tracker learning project, extended in the Mid-Course Project with due dates/overdue filtering and tags. See [`../docs/midcourse/`](../docs/midcourse/) for that work.

This module uses in-memory storage (no database) — data resets whenever the server restarts. The API supports full task CRUD (`GET/POST /tasks`, `GET/PATCH/DELETE /tasks/{id}`), filterable by status, priority, overdue, and tag.

## Requirements

- Python 3.9 or newer

## Setup

All commands are run from the `backend/` directory.

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run

From `backend/`, with the virtual environment active:

```bash
uvicorn app.main:app --reload --port 8000
```

`app.main:app` is an import path, not a file path. Uvicorn must be invoked from `backend/` so that the `app` package is importable. Running from the repository root fails with `ModuleNotFoundError: No module named 'app'`.

`--reload` is for local development only.

The API is served at http://127.0.0.1:8000

## Test the health endpoint

```bash
curl -i http://127.0.0.1:8000/health
```

Windows PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected: HTTP 200 with

```json
{ "status": "ok", "timestamp": "2026-07-21T15:04:05.123456+00:00" }
```

## API documentation

Interactive Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

## Environment variables

| Variable  | Default       | Purpose          |
| --------- | ------------- | ---------------- |
| `APP_ENV` | `development` | Environment name |

The port is set with `uvicorn --port`, not via environment variable.

## Tests

With the virtual environment active, from `backend/`:

```bash
pytest
```

## Notes on dependency versions

FastAPI, Uvicorn, and python-dotenv are pinned; Pydantic is a compatible range so it can resolve alongside FastAPI. After installing, run `pip freeze` and confirm the pinned versions match your environment.