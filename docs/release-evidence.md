# Release Evidence

All commands below were actually run on the dates shown, and the results are
pasted as they were returned.

## Baseline

- **Branch:** `final-project` (commit `305318e` at the time of the baseline run)
- **Date:** 2026-08-24
- **Local app run command:**
  ```bash
  cd backend
  source venv/bin/activate
  uvicorn app.main:app --port 8000
  ```
- **/health result:** `curl -s -i http://127.0.0.1:8000/health`
  ```
  HTTP/1.1 200 OK
  server: uvicorn
  content-type: application/json

  {"status":"ok","timestamp":"2026-08-24T18:17:42.790449+00:00"}
  ```
- **Frontend check:** served with `python3 -m http.server 5500` from `frontend/`,
  with the API running on port 8000. `GET http://127.0.0.1:5500/` returned 200,
  and the served HTML contains all three Kanban columns
  (`data-status="ToDo"`, `data-status="InProgress"`, `data-status="Done"`);
  `app.js` and `styles.css` both returned 200, and the API returned
  `access-control-allow-origin: *` for `Origin: http://127.0.0.1:5500`, so the
  board can load tasks. Opened at http://127.0.0.1:5500 in a browser: the
  three-column Kanban board is still visible and the "+ Add task" create/edit
  modal still opens and saves.
- **Test command:**
  ```bash
  cd backend && ./venv/bin/python -m pytest -q
  ```
- **Test result:** `39 passed in 0.28s` — no failures, so nothing to record as
  pre-existing or introduced.

### Baseline API smoke test

Run with `curl` against the local server, beyond the test suite:

| Request                                        | Result                                                    |
| ---------------------------------------------- | --------------------------------------------------------- |
| `POST /tasks` (title, priority, due_date, tags) | `201 Created`, body includes `"overdue":true` for a past due date |
| `GET /tasks?overdue=true`                       | 1 task returned                                            |
| `GET /tasks?tag=BASELINE`                       | 1 task returned — tag filter is case-insensitive           |
| `PATCH /tasks/{id}` with `{"title":null}`       | `422`                                                      |
| `PATCH /tasks/{id}` with `{"assignee":null}`    | `200` — nullable field cleared                             |
| `GET /tasks/does-not-exist`                     | `404` `{"detail":"Task with id does-not-exist not found"}`  |
| `DELETE /tasks/{id}`                            | `204`                                                      |
| `DELETE /tasks/{id}` again                      | `404`                                                      |

### Scope check

`backend/app/` and `frontend/` were **not modified** during the final project.
Confirmed with `git diff --stat 305318e -- backend/app frontend` (empty output).
Two real findings in `backend/app/` were recorded in
[`final-ai-review.md`](final-ai-review.md) and deliberately left unfixed, because
neither breaks a documented promise and fixing them would mean changing protected
application behaviour that nobody asked for.

## CI evidence

- **Workflow file:** [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- **Triggers:** `push` on all branches and `pull_request`.
- **Latest run link:** https://github.com/digitaldojoai/task-tracker/actions/runs/32762461626
  — run `32762461626` on `final-project`, commit `50a5921`, 2026-08-24. **Green
  on the first attempt**, both jobs passing:
  ```
  ✓ docker build and /health in 20s
  ✓ pytest in 12s
  ```
  Actual output from the `pytest` job:
  ```
  platform linux -- Python 3.13.15, pytest-8.3.4, pluggy-1.6.0
  ============================== 39 passed in 0.19s ==============================
  ```
  The 39 tests that pass in CI are the same 39 that pass locally.
- **Test command used by CI:** `pytest -v`, run from the `backend/` working
  directory after `pip install -r requirements.txt`.
- **Python version:** pinned to `"3.13"` in `actions/setup-python@v5`, matching
  the local Python 3.13.7 used for development. Not `3.x`, not unspecified.
- **Shortcut check:** the workflow contains no `continue-on-error`, no `|| true`,
  and no conditional or skipped pytest step. Verified with:
  ```bash
  grep -nE "continue-on-error|\|\| true" .github/workflows/ci.yml   # no matches
  ```
  The only `if:` conditions in the file are `if: always()` on the two cleanup
  steps (dumping container logs and removing the container), which run *in
  addition to* the checks rather than bypassing them. The two `if` blocks inside
  the shell scripts both `exit 1` on failure.

## Docker evidence

Docker is not installed on the development machine used for this project, so the
image is built and verified **in GitHub Actions** rather than locally. This is
recorded honestly rather than pasting output that was never produced here; the
Actions run is reproducible evidence anyone can re-open.

**Evidence:** the `docker build and /health` job of run
[`32762461626`](https://github.com/digitaldojoai/task-tracker/actions/runs/32762461626),
2026-08-24. Real output from that job's log:

```
#12 naming to docker.io/library/task-tracker:ci done
HTTP status: 200
{"status":"ok","timestamp":"2026-08-24T18:27:05.401907+00:00"}
container UID: 10001
no .env file inside the image
```

- **Build command:** `docker build -t task-tracker:ci .` (run by the `docker` job)
- **Run command:** `docker run -d --name task-tracker-ci -p 8000:8000 task-tracker:ci`
- **/health check:** the workflow polls `http://127.0.0.1:8000/health`, prints the
  HTTP status and body, then asserts both:
  ```bash
  test "$code" = "200"
  grep -q '"status":"ok"' /tmp/health.json
  ```
  A non-200 response fails the job.
- **Non-root check:** implemented. The image creates `appuser` (UID 10001) and
  sets `USER appuser`. CI asserts it at runtime with
  `docker exec task-tracker-ci id -u` and `test "$uid" != "0"`.
- **No-baked-secrets check:** [`.dockerignore`](../.dockerignore) excludes `.env`,
  `*.env`, `backend/venv/`, and all caches from the build context, and the
  `Dockerfile` copies only `backend/requirements.txt` and `backend/app`. CI
  additionally asserts at runtime that no `.env` file exists inside the image.
- **Runtime command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000` — no
  `--reload` (a development-only flag), and `--host 0.0.0.0` so the published
  port is reachable.

### Local equivalent

For anyone who does have Docker, the README documents the same three commands:

```bash
docker build -t task-tracker .
docker run --rm -d --name task-tracker -p 8000:8000 task-tracker
curl -i http://127.0.0.1:8000/health
```

## Documentation claim-vs-reality log

Every claim below was checked against the repository or the running application,
not against memory.

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| README: "`pytest` … 39 tests" | Ran `./venv/bin/python -m pytest -q` from `backend/` | **True** — `39 passed in 0.28s` | None |
| README: "`GET /health` returns 200 with `{"status":"ok", …}`" | `curl -s -i http://127.0.0.1:8000/health` against the local server | **True** — `HTTP/1.1 200 OK`, body `{"status":"ok","timestamp":"2026-08-24T18:17:42.790449+00:00"}` | None |
| README: "an explicit `null` is rejected with `422` for every field except `assignee` and `due_date`, where null clears the value" (PATCH schema/status-code claim) | `curl -X PATCH` with `{"title":null}` → **422**; with `{"assignee":null}` → **200** | **True** as written (the claim is scoped to `PATCH`). Note: `POST /tasks` with `{"description":null}` returns **201**, so create and update differ — see `final-ai-review.md` | None to `app/`; the asymmetry is recorded as a finding |
| README: "tags … and a `?tag=` filter" | `curl "…/tasks?tag=BASELINE"` for a task tagged `baseline` → 1 result | **True**, and the filter is case-insensitive (`storage.py` lowercases both sides) | Clarified in this log; behaviour was undocumented, not wrong |
| README (root) project layout listed only `backend/`, `frontend/`, `docs/` | Compared against `git ls-files` after adding CI/Docker files | **Stale** — did not mention `Dockerfile`, `.dockerignore`, `.github/`, or `AGENTS.md`, and gave no mapping for the brief's `app/`/`tests/` | **Updated** the layout block in `README.md` and added the brief-to-repo path mapping table |
| CI claim: "pytest runs on push and pull request" | Read `.github/workflows/ci.yml`; confirmed green Actions run on `final-project` | **True** | None |
| Docker claim: "no secrets are baked into the image" | Read `.dockerignore` + `Dockerfile`; CI asserts no `.env` inside the running container | **True** | None |
| Repo claim: "no real secrets in the repository" | `git log --all --name-only -- '*.env'` (no results) and a regex scan of `git log --all -p` for key/token/password patterns (no results); `git ls-files \| grep -i env` returns only `backend/.env.example` | **True** — `backend/.env` has never been committed on any branch | None |
