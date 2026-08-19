# Verification

## Baseline check

Before any mid-course feature work, the incomplete Module 1 skeleton was completed and verified as its own commit (`62fcc9d`):

- `GET /health` → `200 {"status": "ok", "timestamp": ...}`
- Created a task via the API, listed it, fetched it by id, moved it through the Kanban UI from To Do → In Progress via the edit modal, and deleted it — confirmed in a real browser (Create → 201, list reflects it, PATCH moves status, DELETE removes it and a subsequent GET on that id returns 404).
- Baseline pytest run: **19 passed, 0 failed.**

## Backend test results (final, after both features)

```
$ ./venv/bin/python -m pytest -q
.......................................                                  [100%]
39 passed in 0.40s
```

Breakdown: 8 model-validation tests (`test_models.py`), 11 baseline CRUD/filter tests (`test_tasks_api.py`), 6 due-date/overdue tests (`test_due_dates.py`), 6 tag tests (`test_tags.py`), 8 explicit-null update tests (`test_update_nulls.py`, added in revision) = 39 total, 20 of which are new for this mid-course project (only 4 were required).

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

---

## Revision after facilitator feedback

Feedback received: *"Sending an explicit null value for title in a task update is accepted with a 200 response and stores the invalid value. This case is not covered by any tests."* Confirmed by hand before changing anything:

```
$ curl -s -X PATCH localhost:8000/tasks/$ID -H 'Content-Type: application/json' -d '{"title": null}'
200 {"id": "...", "title": null, ...}
```

**Root cause (two independent defects, both needed fixing):**

1. `TaskUpdate.title` is `Optional[str] = None`, so an *omitted* title and an *explicit null* title both deserialize to `None`. The `validate_title` field validator short-circuits on `None` (correctly, for the omitted case) — so an explicit null slipped through validation.
2. `storage.update_task` merged the payload with `task.model_copy(update=...)`. `model_copy` does **not** re-validate, so even a `None` that should have been impossible got written straight into the stored `TaskResponse`, whose `title` field is a non-optional `str`. That is why the response serialized `"title": null` instead of erroring.

**Fix:**

- `models.py`: a `@model_validator(mode="before")` on `TaskUpdate` inspects the raw payload dict — the one place where "omitted" and "explicitly null" are still distinguishable — and rejects an explicit null for any field outside `NULLABLE_UPDATE_FIELDS`. `assignee` and `due_date` stay nullable on purpose: sending null for those is the only way to *clear* them, which the frontend relies on.
- `storage.py`: `model_copy(update=...)` replaced with `TaskResponse.model_validate({...})`, so merged state is re-validated on every update. (`overdue` is excluded from the dump first — it is a computed field and `TaskResponse` sets `extra="forbid"`.) This is defence in depth: the model validator is the real fix, but storage no longer writes anything unchecked.

**Tests added:** `tests/test_update_nulls.py`, 8 cases — null title rejected with `422`; stored task unchanged after the rejected update; parametrized rejection for `description`, `status`, `priority`, `tags` (each also asserting the stored value survived); `assignee`/`due_date` still clearable with null → `200`; and omitted fields still meaning "leave unchanged."

**Break Test 3 — disabled the new null guard** (early `return data` at the top of `reject_explicit_nulls`), to confirm the new tests fail for the stated reason rather than passing vacuously:

```
FAILED tests/test_update_nulls.py::test_update_title_to_null_rejected
FAILED tests/test_update_nulls.py::test_update_title_to_null_does_not_change_stored_task
FAILED tests/test_update_nulls.py::test_non_nullable_fields_rejected_as_null[description-notes]
FAILED tests/test_update_nulls.py::test_non_nullable_fields_rejected_as_null[status-InProgress]
FAILED tests/test_update_nulls.py::test_non_nullable_fields_rejected_as_null[priority-High]
FAILED tests/test_update_nulls.py::test_non_nullable_fields_rejected_as_null[tags-value3]
6 failed, 2 passed in 2.71s
```

The two that still passed are exactly the ones that should: clearing `assignee`/`due_date` and the omitted-field case don't depend on the guard. Restored → **39 passed**.

**Behavior contract re-run after the revision:** full suite green at 39 passed; the 31 pre-existing tests all still pass unchanged, confirming the stricter validation didn't break any legitimate update path.

**Documentation fix:** `docs/midcourse/userstories.md` renamed to `docs/midcourse/user-stories.md` (hyphenated, as the brief requires); references in `mini-adr.md` and `prompt-log.md` updated to match.
