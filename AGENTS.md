# AGENTS.md — working rules for AI assistants in this repo

Read this file before proposing or making any change.

## What this project is

A small Kanban-style task tracker built for the AUB AI-Assisted Coding course.
It is a teaching project, not a production service. Scope is deliberately fixed.

| Layer     | Stack                                              | Location                    |
| --------- | -------------------------------------------------- | --------------------------- |
| Backend   | Python 3.13, FastAPI, Pydantic v2, Uvicorn          | `app/`                      |
| Storage   | In-memory dict — no database, resets on restart     | `app/storage.py`            |
| Tests     | pytest + httpx (FastAPI `TestClient`)               | `tests/`                    |
| Frontend  | Vanilla HTML/CSS/JS, no build tooling, no framework | `frontend/`                 |
| CI        | GitHub Actions: pytest + Docker `/health` check     | `.github/workflows/ci.yml`  |

## Commands you may assume work

All commands run from the repository root with the virtualenv active.

```bash
python3 -m venv venv && source venv/bin/activate   # first time only
pip install -r requirements.txt                     # first time only
uvicorn app.main:app --reload --port 8000           # run the API
pytest                                              # run the tests (39 currently)
```

`app.main:app` is an import path, not a file path. Uvicorn must be started from
the repository root, or the `app` package is not importable and it fails with
`ModuleNotFoundError`.

Frontend: serve `frontend/` statically (`python3 -m http.server 5500` from that
directory) with the API already running on port 8000. There is no build step.

Docker, from the repository root:

```bash
docker build -t task-tracker .
docker run --rm -p 8000:8000 task-tracker
curl -i http://127.0.0.1:8000/health     # expect HTTP 200
```

## Read-first / docs-first guardrails

1. **Read before you write.** Read the file you intend to change, plus its
   tests, before proposing a diff. Do not infer the contents of a file from its
   name.
2. **Check the docs against the code.** `README.md`, `docs/backend-api.md`, and
   this file make concrete claims (commands, ports, status codes, test counts).
   If a change makes one of them false, update the doc in the same change.
3. **Verify, don't assert.** A change is not done until `pytest` has actually
   been run and its real output reported. Never report a test result you did not
   observe.
4. **No silent scope growth.** If a fix requires touching something outside what
   was asked, stop and say so rather than widening the diff.

## Rules for changing `app/` and `frontend/`

These directories are the graded product of earlier course modules and are
protected.

- **No new product features.** Specifically off-limits: comments, authentication,
  a real database, notifications, and unrelated UI redesigns.
- Only change them for a small bug fix, a security fix, or a correction that a
  document or test already justifies.
- Any such change must be explained in `docs/final-ai-review.md`, naming the file
  and the reason.
- Do not reformat, restructure, or "modernise" working code that nobody asked
  you to touch. Churn is a cost, not a contribution.

## Security and data rules

- **Never** put real credentials, tokens, `.env` contents, production logs, or
  personal/customer data into this repo or into a prompt.
- `.env` is gitignored and must stay untracked. `.env.example`
  holds the placeholder values and is the only env file that is committed.
- The `.dockerignore` deliberately excludes `.env` and `venv/`. Do not weaken it.
- Known and accepted for this course scope, so do not "fix" these without being
  asked: no authentication, `CORSMiddleware` with `allow_origins=["*"]`, and
  in-memory storage. They are documented in `docs/final-ai-review.md`.

## CI rules

`.github/workflows/ci.yml` must keep failing loudly. Do not add
`continue-on-error`, do not append `|| true`, do not make the pytest step
conditional, and keep the Python version pinned to an exact minor version.

## Ownership

If a suggestion cannot be explained line by line by the repository owner, it does
not get committed. Confidence is not evidence — a passing test, a real HTTP
response, or a green CI run is.
