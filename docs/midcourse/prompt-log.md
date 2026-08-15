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
**Accepted:** Backend as-is. **Edited:** the overdue rule was refined mid-implementation to explicitly exclude `Done` tasks (see `userstories.md` for the corrected assumption) before it was ever run, based on re-reading the requirement rather than after a failing test.

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
