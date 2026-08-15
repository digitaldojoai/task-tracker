# Mini-ADR — Due Dates + Overdue Filter, and Tags

## Context

The repository this project was supposed to extend (a finished Modules 1-3 Task Tracker with a working frontend and full CRUD) did not actually exist — only the Module 1 backend skeleton was present (health check + create/list/get, no update/delete wired up, no frontend, no git repo, no real test suite). Before either mid-course feature could be built, the baseline had to be completed: PATCH/DELETE endpoints wired to the existing storage layer, a plain HTML/CSS/JS Kanban frontend, a real pytest suite, and a git repository. That baseline work is committed separately from the two feature commits so the diff for each feature is easy to read on its own.

## Decision: Due dates + overdue filter

- `due_date` is an optional `date` field on the task. Pydantic's built-in `date` type validation handles malformed input automatically (returns `422`), so no custom parsing was needed.
- **Overdue is computed, not stored.** It's a Pydantic `computed_field` on `TaskResponse`, evaluated at serialization time from `due_date` and `status`. The alternative — storing an `overdue: bool` flag and updating it on some schedule — was considered and rejected: it would need a background job or manual recomputation to avoid going stale (a task doesn't become overdue by being edited, it becomes overdue by the calendar advancing). Computing it fresh on every response is simpler and can't drift out of sync.
- A task is overdue only if it's not `Done`. See the corrected assumption in `userstories.md` — the first version didn't account for completed tasks.
- Filtering is a single optional query parameter (`?overdue=true`/`false`) on the existing `GET /tasks`, following the same pattern as the existing `status`/`priority` filters, rather than a separate endpoint.

## Decision: Tags

- Tags are a native `list[str]`, not a comma-separated string, on both the request and response models. See the corrected assumption in `userstories.md` for why the comma-separated option (suggested by the brief) was rejected internally — it's kept only as the frontend input format, parsed into a list before hitting the API.
- Validation caps are deliberately simple: max 10 tags per task, 30 characters per tag, blank tags rejected. No tag taxonomy, no separate `Tag` resource/model, no tag color coding — those were considered and rejected as out of scope for a 3-4 hour sprint. Tags are just short trimmed strings that live on the task.
- Tag filtering (`?tag=backend`) does a case-insensitive exact match against a task's tag list. Partial/substring tag matching was considered and rejected as unnecessary complexity — it overlaps with the (out-of-scope) "Search + combined filters" feature option from the brief.

## Rejected / out of scope

- **Bulk operations, saved views, drag-and-drop reordering** — explicitly called out as optional/overbuild-risk in the brief; skipped.
- **A dedicated tag management endpoint** (rename/delete a tag across all tasks) — not needed for the scope here; tags are edited per-task only.
- **Drag-and-drop status changes on the Kanban board** — the board still groups by status, but moving a task between columns is done through the edit modal's status dropdown rather than drag-and-drop, to keep the frontend small and to keep manual browser verification straightforward (drag-and-drop is harder to test reliably by hand under time pressure).
