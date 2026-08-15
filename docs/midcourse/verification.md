# Verification

## Baseline check

Before any mid-course feature work, the incomplete Module 1 skeleton was completed and verified as its own commit (`62fcc9d`):

- `GET /health` → `200 {"status": "ok", "timestamp": ...}`
- Created a task via the API, listed it, fetched it by id, moved it through the Kanban UI from To Do → In Progress via the edit modal, and deleted it — confirmed in a real browser (Create → 201, list reflects it, PATCH moves status, DELETE removes it and a subsequent GET on that id returns 404).
- Baseline pytest run: **19 passed, 0 failed.**

## Backend test results (final, after both features)

```
$ ./venv/bin/python -m pytest -q
...............................                                          [100%]
31 passed in 0.05s
```

Breakdown: 8 model-validation tests (`test_models.py`), 11 baseline CRUD/filter tests (`test_tasks_api.py`), 6 due-date/overdue tests (`test_due_dates.py`), 6 tag tests (`test_tags.py`) = 31 total, 12 of which are new for this mid-course project (only 4 were required).

## Manual browser checks

Run with the backend on `http://127.0.0.1:8000` and the frontend served statically on `http://127.0.0.1:5500`.

- **Due dates:** created a task due 2026-08-01 (in the past relative to the session's date) — card showed a red "Overdue: 2026-08-01" pill. Created a second task due 2026-09-01 — showed a plain (non-red) due pill. Checked "Overdue only" in the filter bar — only the first task remained visible; unchecked it — both reappeared.
- **Tags:** created "Fix login bug" tagged `urgent, backend` — both chips rendered on the card. Created "Write docs" tagged `docs`. Typed "backend" into the tag filter — only "Fix login bug" remained visible.
- **Regression check on existing CRUD:** create/edit/delete were re-tested after both features landed to confirm nothing broke — all still worked (see the delete bug below, which was caught and fixed during this pass).

## Bug found and fixed during manual verification

The original delete flow used the browser's native `confirm()` dialog. In the automated browser session used for testing, clicking Delete visibly did nothing. The browser console showed:

```
[warn] Page dialog suppressed (confirm): "Delete this task?" — native JavaScript
dialogs are disabled in this browser; confirm() returned false to the page.
```

This is exactly the kind of thing that only shows up by actually running the app, not by reading the code — the code looked correct. Fixed by replacing `confirm()` with an inline two-click "Delete" → "Confirm delete?" state on the button itself (no blocking native dialog). Re-tested: first click arms it, second click deletes and closes the modal.

## Behavior contract before/after refactor

**Refactor:** the three endpoints that raise a 404 (`GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`) each duplicated the same `HTTPException(status_code=404, detail=f"Task with id {task_id} not found")`. Extracted into a single `_task_not_found(task_id)` helper in `main.py`.

**Contract check:** full pytest suite run before and after the refactor, same result both times:

```
before: 31 passed in 0.05s
after:  31 passed in 0.05s
```

No behavior changed — same status codes, same error message format, same response bodies. Only the duplication was removed.

## Break Test evidence (≥ 2 tests)

To confirm the new tests actually test something (rather than passing vacuously), two pieces of working code were deliberately broken, the suite was re-run to confirm the *right* test(s) failed, then the code was restored.

**Break 1 — inverted the overdue comparison** (`due_date > today` instead of `due_date < today` in the `overdue` computed field):

```
FAILED tests/test_due_dates.py::test_create_task_with_valid_due_date
FAILED tests/test_due_dates.py::test_overdue_detection_for_past_due_incomplete_task
FAILED tests/test_due_dates.py::test_filter_returns_only_overdue_tasks
3 failed, 28 passed in 0.06s
```

Reverted → suite back to 31 passed.

**Break 2 — removed the blank-tag rejection** in `_validate_tags`:

```
FAILED tests/test_tags.py::test_reject_empty_tag - assert 201 == 422
1 failed, 30 passed in 0.06s
```

Reverted → suite back to 31 passed, and `git status` confirmed the working tree matched the last commit exactly (no accidental leftover edits from the break tests).
