# Mini-ADR — Due Dates + Overdue Filter, and Tags

## Context

The repository this project was supposed to extend (a finished Modules 1-3 Task Tracker with a working frontend and full CRUD) did not actually exist — only the Module 1 backend skeleton was present (health check + create/list/get, no update/delete wired up, no frontend, no git repo, no real test suite). Before either mid-course feature could be built, the baseline had to be completed: PATCH/DELETE endpoints wired to the existing storage layer, a plain HTML/CSS/JS Kanban frontend, a real pytest suite, and a git repository. That baseline work is committed separately from the two feature commits so the diff for each feature is easy to read on its own.

## Decision: Due dates + overdue filter

- `due_date` is an optional `date` field on the task. Pydantic's built-in `date` type validation handles malformed input automatically (returns `422`), so no custom parsing was needed.
- **Overdue is computed, not stored.** It's a Pydantic `computed_field` on `TaskResponse`, evaluated at serialization time from `due_date` and `status`. The alternative — storing an `overdue: bool` flag and updating it on some schedule — was considered and rejected: it would need a background job or manual recomputation to avoid going stale (a task doesn't become overdue by being edited, it becomes overdue by the calendar advancing). Computing it fresh on every response is simpler and can't drift out of sync.
- A task is overdue only if it's not `Done`. See the corrected assumption in `user-stories.md` — the first version didn't account for completed tasks.
- Filtering is a single optional query parameter (`?overdue=true`/`false`) on the existing `GET /tasks`, following the same pattern as the existing `status`/`priority` filters, rather than a separate endpoint.

## Decision: Tags

- Tags are a native `list[str]`, not a comma-separated string, on both the request and response models. See the corrected assumption in `user-stories.md` for why the comma-separated option (suggested by the brief) was rejected internally — it's kept only as the frontend input format, parsed into a list before hitting the API.
- Validation caps are deliberately simple: max 10 tags per task, 30 characters per tag, blank tags rejected. No tag taxonomy, no separate `Tag` resource/model, no tag color coding — those were considered and rejected as out of scope for a 3-4 hour sprint. Tags are just short trimmed strings that live on the task.
- Tag filtering (`?tag=backend`) does a case-insensitive exact match against a task's tag list. Partial/substring tag matching was considered and rejected as unnecessary complexity — it overlaps with the (out-of-scope) "Search + combined filters" feature option from the brief.

## Decision (revision): explicit null on PATCH is a client error, not a clear

Prompted by facilitator feedback that `{"title": null}` was accepted with a `200`. A partial-update model has three possible meanings for a field, and `Optional[str] = None` only encodes two of them:

| Client sends | Intended meaning | Behavior now |
| --- | --- | --- |
| field omitted | leave unchanged | unchanged, `200` |
| `"assignee": null` / `"due_date": null` | clear the value | cleared, `200` |
| `"title": null` (or description/status/priority/tags) | *nothing coherent* | `422` |

Options considered:

- **Coerce null to a default** (empty title, `ToDo` status). Rejected — it invents user intent from what is almost certainly a client bug, and quietly destroys data.
- **Treat every null as "leave unchanged"** (i.e. keep `exclude_unset` and just stop writing nulls). Rejected — it makes `assignee`/`due_date` impossible to clear through the API, which the frontend's "unassign" path needs.
- **A sentinel type** (`Field(default=UNSET)` with a custom `Unset` marker, so omitted and null are distinct *types* rather than distinguished by `model_fields_set`). This is the fully general solution, and AI suggested it. Rejected as too heavy for two nullable fields: it changes every field's declared type, leaks the sentinel into `storage.py`, and complicates the OpenAPI schema — a lot of machinery to express something an allowlist states in one line.
- **Chosen: an allowlist checked in a `mode="before"` validator.** The raw payload dict is the only place omitted and explicitly-null are still distinguishable, and `NULLABLE_UPDATE_FIELDS` states the design decision in one readable place.

Separately and independently, `storage.update_task` was writing merged state with `model_copy(update=...)`, which performs no validation — that is why an invalid value could reach a stored `TaskResponse` at all. Replaced with `TaskResponse.model_validate(...)`. The validator alone would have closed this specific report; re-validating on write closes the whole class of "something got past the request model" bugs, at the cost of one model construction per update, which is not a meaningful cost for an in-memory store.

## Rejected / out of scope

- **Bulk operations, saved views, drag-and-drop reordering** — explicitly called out as optional/overbuild-risk in the brief; skipped.
- **A dedicated tag management endpoint** (rename/delete a tag across all tasks) — not needed for the scope here; tags are edited per-task only.
- **Drag-and-drop status changes on the Kanban board** — the board still groups by status, but moving a task between columns is done through the edit modal's status dropdown rather than drag-and-drop, to keep the frontend small and to keep manual browser verification straightforward (drag-and-drop is harder to test reliably by hand under time pressure).
