# User Stories — Mid-Course Project

## Feature 1: Due dates + overdue filter

**US-1.1 — Set a due date when creating a task**
As a user, I want to set an optional due date when I create a task, so I can track when it needs to be finished.
- Acceptance criteria:
  - `POST /tasks` accepts an optional `due_date` (ISO `YYYY-MM-DD`).
  - A malformed date (e.g. `"not-a-date"`) is rejected with `422`.
  - Omitting `due_date` still creates the task successfully (it's optional).

**US-1.2 — Update a task's due date**
As a user, I want to change a task's due date after creating it, so I can reschedule work.
- Acceptance criteria:
  - `PATCH /tasks/{id}` accepts `due_date` and updates only that field.
  - Other fields (title, tags, etc.) are unaffected by the update.

**US-1.3 — See at a glance which tasks are overdue**
As a user, I want overdue tasks visually flagged on the board, so I don't have to check each due date manually.
- Acceptance criteria:
  - A task is "overdue" if `due_date` is in the past **and** status is not `Done`.
  - Cards with a due date show a pill; overdue ones are styled distinctly (red) from tasks that are merely upcoming.

**US-1.4 — Filter the board to only overdue tasks**
As a user, I want to filter the board down to only overdue tasks, so I can focus on what's late.
- Acceptance criteria:
  - `GET /tasks?overdue=true` returns only tasks currently overdue.
  - The frontend has an "Overdue only" toggle that applies this filter live.

**AI assumption corrected:** the AI's first pass treated "overdue" purely as `due_date < today`, without considering task status. On review, this was wrong — a completed task with a past due date isn't meaningfully "overdue," it's just finished late. The rule was corrected to also exclude any task with `status == Done`, and a dedicated test (`test_done_task_with_past_due_date_is_not_overdue`) was added specifically to lock that behavior in.

---

## Feature 2: Tags / labels

**US-2.1 — Add tags when creating a task**
As a user, I want to attach tags (e.g. "urgent", "backend") to a task, so I can categorize work.
- Acceptance criteria:
  - `POST /tasks` accepts an optional `tags` list.
  - Each tag is trimmed of surrounding whitespace before saving.
  - A blank tag (empty or whitespace-only) is rejected with `422`.
  - More than 10 tags on one task is rejected with `422`.

**US-2.2 — Edit a task's tags**
As a user, I want to add or remove tags on an existing task, so I can keep categorization current.
- Acceptance criteria:
  - `PATCH /tasks/{id}` accepts a new `tags` list and replaces the old one.
  - Updating an unrelated field (e.g. status) does not clear or change existing tags.

**US-2.3 — See tags on task cards**
As a user, I want to see a task's tags directly on its card, so I don't have to open it to know what it's tagged with.
- Acceptance criteria:
  - Each tag renders as a small chip on the card.
  - A task with no tags shows no chips (no empty/placeholder chip).

**US-2.4 — Filter the board by tag**
As a user, I want to filter tasks by a single tag, so I can see only the work in that category.
- Acceptance criteria:
  - `GET /tasks?tag=backend` returns only tasks that have that tag.
  - Matching is case-insensitive (`Backend` matches a task tagged `backend`).

**AI assumption corrected:** the course brief suggested tags could be modeled "as a list or normalized comma-separated field." The AI's first instinct leaned toward storing a single comma-separated string internally (closer to the brief's second option), since it looked simpler. On review, this was rejected — a native list is simpler to validate per-tag (trim/reject-blank/max-length checks apply cleanly to each list item) and simpler to query for the tag filter. The comma-separated format was kept only at the frontend edge, where the modal's text input is split into a list before being sent to the API.
