# Prompt Log

AI tool used throughout: Claude Code (Anthropic), operating directly on the repository files, running the server, and driving a real browser to click through the UI for verification.

## Baseline (before either feature)

**Prompt:** "Read the course brief and the actual state of the task-tracker repo, and tell me what's missing before we can build the two mid-course features on top of it."
**Returned:** An assessment that only the Module 1 skeleton existed — no PATCH/DELETE endpoints wired up (despite `storage.py` already having the functions), no frontend, no git repo, no real pytest suite.
**Accepted:** The assessment and the plan to complete that baseline first, as its own commit, before starting feature work.

**Prompt:** "Wire up the missing PATCH and DELETE endpoints using the storage functions that already exist, add CORS so a separate frontend can call the API, and replace the manual verify_a.py print-script with real pytest tests."
**Returned:** `PATCH /tasks/{id}` and `DELETE /tasks/{id}` added to `main.py`; `CORSMiddleware` added; `verify_a.py`'s assertions rewritten as `tests/test_models.py`, plus a new `tests/test_tasks_api.py` covering the endpoints, with a `conftest.py` fixture that resets in-memory storage between tests.
**Accepted:** As-is. All 19 baseline tests passed on the first run.

---

## Feature 1: Due dates + overdue filter

**Weak prompt (first attempt):** "Add due dates to tasks."
**Why it's weak:** No validation rule, no statement of whether overdue is computed client- or server-side, no filter behavior, no test expectations — the AI would have to guess several product decisions.
**Rewritten, stronger prompt:** "Add an optional `due_date` field (ISO date) to the task create/update/response models. Compute `overdue` server-side as a response field — true when `due_date` is in the past and status isn't Done — rather than storing it, so it can't go stale. Add an optional `?overdue=true` filter on GET /tasks. Then wire the due date into the modal and add an overdue pill on cards plus an 'Overdue only' toggle in the filter bar."
**Returned:** The `due_date` field, the `overdue` computed field, the query filter, and the full frontend wiring (modal field, card pill, filter checkbox).
**Accepted:** Backend as-is. **Edited:** the overdue rule was refined mid-implementation to explicitly exclude `Done` tasks (see `user-stories.md` for the corrected assumption) before it was ever run, based on re-reading the requirement rather than after a failing test.

**Prompt:** "Add pytest tests for due dates covering: valid due date, invalid format, overdue detection, a Done task with a past due date (should not be overdue), updating the due date, and the overdue filter."
**Returned:** Six tests in `tests/test_due_dates.py`.
**Accepted:** As-is — all passed against the implementation on the first run (25/25 total).

**Prompt:** "Start the backend and frontend, open it in a browser, and actually create an overdue task and a future-dated task, then confirm the pill styling and the overdue filter both work — don't just trust the code."
**Returned:** A live walkthrough: created "Overdue task" (due 2026-08-01, before the seed's simulated "today"), confirmed the red "Overdue: 2026-08-01" pill rendered; created "Future task" (due 2026-09-01); toggled "Overdue only" and confirmed only the overdue task remained visible.
**Accepted:** As-is — this caught nothing wrong for this feature, but it's the same manual pass that caught the `confirm()` dialog bug described below.

---

## Feature 2: Tags / labels

**Weak prompt (first attempt):** "Add tags."
**Why it's weak:** Doesn't say whether tags are a list or string, what counts as invalid, or how filtering should behave.
**Rewritten, stronger prompt:** "Add a `tags` field (list of strings) to the task models. Trim whitespace on each tag, reject blank tags and more than 10 tags per task with a 422, and add a case-insensitive `?tag=` filter on GET /tasks. Then add a comma-separated tags input to the modal, render tag chips on cards, and add a tag filter box."
**Returned:** `tags: list[str]` on all three models with a shared `_validate_tags` helper, the `?tag=` filter in `storage.py`/`main.py`, and the frontend chips/input/filter.
**Accepted:** Backend validation logic as-is. **Rejected mid-implementation:** an initial instinct to store tags as a single comma-separated string internally (the brief allows this) — rejected in favor of a native list, because per-tag validation and the tag filter are both simpler against a list. See `mini-adr.md`.

**Prompt:** "Add pytest tests for tags: create with tags, reject a blank tag, reject too many tags, update tags, filter by tag, and confirm tags survive an unrelated update (e.g. changing only status)."
**Returned:** Six tests in `tests/test_tags.py`, all passing on the first run (31/31 total).
**Accepted:** As-is.

**Prompt:** "Same as before — actually run this in the browser. Create a tagged task, confirm the chips render, then filter by one of its tags and confirm the other task disappears."
**Returned:** Created "Fix login bug" tagged `urgent, backend`; confirmed both chips rendered on the card. Created "Write docs" tagged `docs`. Typed "backend" into the tag filter and confirmed only "Fix login bug" remained visible.
**Accepted:** As-is.

---

## A bug the manual browser pass caught (not feature-specific)

**What happened:** The AI's first implementation of task delete used the browser's native `confirm()` dialog. When actually clicking Delete in the automated browser session, nothing happened — the console showed `confirm() returned false: native JavaScript dialogs are disabled in this browser`.
**Prompt:** "Delete isn't working when I click it — check the console."
**Returned:** The console warning explaining native dialogs are suppressed in this browser context.
**Edited:** Replaced `confirm()` with an inline two-click "Delete" → "Confirm delete?" pattern on the button itself, which doesn't depend on a blocking native dialog. Re-tested in the browser and delete worked correctly afterward. This is called out in `verification.md` as well, since it's a concrete example of AI output being wrong until it was actually run, not just read.

---

## Revision round: explicit-null updates

Facilitator feedback: `PATCH /tasks/{id}` with `{"title": null}` returned `200` and stored the null, and nothing tested it.

**Weak prompt (first attempt):** "Fix the null title bug."
**Why it's weak:** Names a symptom and asks for a fix, so the likely output is a one-line `if payload.title is None: raise` patch on the title field only — leaving the identical hole open on `description`, `status`, `priority`, and `tags`, and leaving the unvalidated write path in storage untouched.
**Rewritten, stronger prompt:** "In `PATCH /tasks/{id}`, an explicit `{\"title\": null}` returns 200 and stores null. Explain why the existing `validate_title` field validator doesn't catch it, and check whether `storage.update_task` writes it unvalidated. Then fix it so that for every non-nullable update field an explicit null returns 422 while an *omitted* field still means 'leave unchanged'. `assignee` and `due_date` must stay nullable — null clears them. Don't change the create path."
**Returned:** The two-part diagnosis (field validator short-circuits on `None` because omitted and explicit-null are indistinguishable after parsing; `model_copy(update=...)` skips validation on write), plus a `model_validator(mode="before")` that inspects the raw dict and a `TaskResponse.model_validate(...)` replacement in storage.
**Accepted:** Both changes. **Edited:** the nullable-field allowlist was initially inlined in the validator as a literal set — pulled out to a module-level `NULLABLE_UPDATE_FIELDS` constant with a comment, since "which fields may be null" is a design decision worth stating once and in the open rather than burying in a comprehension.

**Prompt:** "Write pytest tests for this. Cover: null title → 422; the stored task is unchanged after that rejected request; the same rejection for description/status/priority/tags; null assignee and due_date still clear them with 200; and an omitted field still leaves the task unchanged."
**Returned:** `tests/test_update_nulls.py` — the four same-shaped rejection cases parametrized, the rest written out individually.
**Edited:** Each parametrized rejection case originally asserted only the `422`. Added a second assertion re-fetching the task and checking the old value survived — the original report was as much about the *stored* value as about the status code, and a 422 alone wouldn't have proven the write was blocked.

**Prompt:** "Break test: disable the new null guard and re-run only the new test file. I expect the rejection tests to fail and the assignee/due-date and omitted-field tests to still pass."
**Returned:** 6 failed, 2 passed — matching the prediction exactly, which is what makes the result meaningful (the two survivors don't depend on the guard). Restored → 39 passed. Logged in `verification.md` as Break Test 3.
**Rejected:** an offer to also apply the same strictness to `POST /tasks` — the create path already rejects a null title, since `title` there is a required non-optional `str`, so the change would have been churn.
