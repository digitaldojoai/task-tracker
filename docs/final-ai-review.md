# Final AI Review and Ownership Evidence

## AGENTS.md guardrails

[`AGENTS.md`](../AGENTS.md) exists at the repository root.

- **Repo-specific stack and commands included:** yes — Python 3.13 / FastAPI /
  Pydantic v2 / pytest / vanilla JS, with the exact `uvicorn app.main:app`,
  `pytest`, `http.server 5500`, and `docker build`/`docker run` commands, plus
  the note that uvicorn must be started from the repository root or the `app`
  package is not importable.
- **Docs-first / read-first guardrail included:** yes — "Read before you write"
  (read the file and its tests before proposing a diff), "Check the docs against
  the code" (update any doc a change makes false, in the same change), and
  "Verify, don't assert" (no reporting a test result that was not observed).
- **Unexpected app/frontend edits rule included:** yes — `app/` and
  `frontend/` are protected; changes are limited to a small bug fix, security
  fix, or documented correction, must be explained in this file, and the banned
  feature list (comments, auth, real database, notifications, UI redesign) is
  named explicitly.

## AI code review mini-log

**Diff reviewed:** commit `305318e`, "Implement strict null handling in task
updates" — specifically `app/models.py` (new `reject_explicit_nulls`
model validator) and `app/storage.py` (`update_task` re-validating
through `TaskResponse` instead of `model_copy`).

| AI comment | Grade | Reason | Verification or decision |
|---|---|---|---|
| "`model_dump(exclude={'overdue'})` in `storage.update_task` is redundant — Pydantic v2 does not include computed fields in `model_dump()`, so you can drop the `exclude`." | **Wrong** | The premise is false. Pydantic v2 *does* include `@computed_field` values in `model_dump()`, and `TaskResponse` sets `extra="forbid"`, so revalidating the dump without excluding `overdue` raises `ValidationError`. | Tested directly: `"overdue" in t.model_dump()` → `True`, and `TaskResponse.model_validate(t.model_dump())` → `ValidationError`. **Rejected**; the existing comment in `storage.py` explaining the exclusion is correct and stays. |
| "`POST /tasks` still accepts `{"description": null}` and silently coerces it to `""`, while `PATCH` now rejects the same payload with 422. Create and update disagree about the same field." | **Useful** | A real, reproducible inconsistency the diff introduced by hardening only the update path. `TaskCreate.description` is `Optional[str] = ""` and `storage.add_task` does `payload.description or ""`. | Verified over HTTP: `POST /tasks` with `{"description":null}` → **201**; `PATCH /tasks/{id}` with `{"description":null}` → **422**. **Recorded, not fixed** — see "One AI output I rejected or corrected" below for why the fix was declined. |
| "`reject_explicit_nulls` uses `mode='before'` and reads `cls.model_fields`, so a field name that is not on the model falls through this check and is caught later by `extra='forbid'`. Worth confirming the error is still a 422 and not a 500." | **Useful** | Correct reading of the control flow, and it points at a real user-visible contract (status code) rather than style. | Verified: `PATCH` with an unknown field returns **422** from `extra="forbid"`, and `PATCH {"title":null}` returns **422** from the validator. Both paths are client errors, never a 500. **No change needed** — confirmed correct as written. |
| "Add type annotations and a docstring to `reject_explicit_nulls`." | **Noise** | The method already has full annotations (`data: object) -> object`) and the class docstring above it explains the whole rule. The comment was generated without reading the surrounding lines. | Read the file; the suggestion describes code that already exists. **Discarded.** |
| "`update_task` bumps `updated_at` on every call, so a PATCH that sets a field to the value it already had still changes the timestamp." | **Noise** | Technically accurate but not a defect — "last write" is a reasonable meaning for `updated_at`, and nothing in the app or docs promises otherwise. Also note `if not updates: return task` already short-circuits an empty `{}` PATCH without touching the timestamp. | Read `storage.py:54-74`. **No action** — accepted behaviour, not a bug. |

## AI security mini-review

Read-only pass over `app/` and `frontend/app.js`. No files were changed
as a result of this review.

| Finding | File evidence | Grade | Reason | Next action |
|---|---|---|---|---|
| CORS is fully open: `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` — any website can call this API from a user's browser. | [`app/main.py:33-38`](../app/main.py) | **Valid** (low severity here) | The wildcard is real and deliberately permissive. Severity is low *in this scope only*: there is no authentication and no cookie/credential handling (`allow_credentials` is not enabled), so a hostile origin can reach an API that already has no private data to steal. It would be a genuine vulnerability the moment auth is added. | Documented and accepted for the course scope; recorded in `AGENTS.md` as a known, deliberate choice so no future assistant "fixes" it blindly. Tightening it belongs with an auth change, not before. |
| `innerHTML` used in the frontend render path — potential XSS from task titles/tags. | [`frontend/app.js:109`](../frontend/app.js) | **False Positive** | The only `innerHTML` in the file is `list.innerHTML = ""` — assignment of a constant empty string to clear a column, which cannot inject anything. Every value that comes from the API is written with `textContent` via `document.createElement` (23 such uses in the file); there is no `insertAdjacentHTML`, `document.write`, or `eval` anywhere. | Verified with `grep -n "innerHTML\|eval(\|document.write\|insertAdjacentHTML" frontend/app.js` — one match, the empty-string clear. **No change.** A pattern-matching scanner flagged the sink without reading the assignment. |
| Unbounded `description` field: `title` is capped at 200 characters and `tags` at 10 × 30, but `description` has no length limit, so a single request can push an arbitrarily large string into the in-memory store. | [`app/models.py:20-26`](../app/models.py) (`_validate_title`, the 200-character title cap) vs. `description: Optional[str] = ""` with no validator | **Valid** (low severity here) | Confirmed asymmetry, and the only unbounded user-controlled input in the app. Because storage is a process-local dict with no persistence and no auth, the realistic impact is memory growth in a local dev server, not a data breach. | Verified over HTTP: a 200,000-character description returns **201**, while a 300-character title correctly returns **422**. **Recorded, not fixed** — adding a cap changes protected `app/` validation behaviour that no requirement asks for. It is the first thing I would fix if this app were ever exposed beyond localhost. |
| No authentication or rate limiting on any `/tasks` endpoint — anyone who can reach the port can read, edit, and delete every task. | [`app/main.py`](../app/main.py) (no dependencies, no auth middleware) | **Noise** | True but not a finding *for this repo*. "No authentication" is an explicit, documented scope decision for the course project, and the brief names authentication as an off-limits feature. Reporting a deliberate, documented constraint as a vulnerability is noise. | **No action.** Already stated in `AGENTS.md` under known-and-accepted items. |
| Secrets could be baked into the Docker image via `.env` or the local `venv/`. | [`.dockerignore`](../.dockerignore), [`Dockerfile`](../Dockerfile) | **Valid as a risk, already mitigated** | A legitimate thing to check on a new Dockerfile. In this repo the build context excludes `.env`, `*.env`, and `venv/`, and the `Dockerfile` copies only `requirements.txt` and `app/`. | Turned into an enforced check rather than a claim: CI asserts at runtime that no `.env` exists inside the container, and that the container's UID is not 0. A future weakening of `.dockerignore` fails the build. |

## Manual security check

This is the part I did myself, not by reading AI output.

I did not trust "no secrets in the repo" as a statement about the working tree,
because a deleted secret still lives in git history. I checked the **full history
of every branch**:

```bash
git log --all --oneline --name-only -- '*.env'                   # no results
git log --all -p | grep -iE "(api[_-]?key|secret|password|token|BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]{20}|ghp_[A-Za-z0-9]{20})"
git ls-files | grep -i env                                       # .env.example only
```

**Result:** no `.env` has ever been committed on any branch, no
secret-shaped string appears in any commit's contents, and the only tracked env
file is `.env.example`, which contains a single non-sensitive line
(`APP_ENV=development`). I also confirmed `.env` is ignored by `.gitignore`, so
the untracked local file cannot be added by accident.

**Why it matters:** the gitignore rules only protect the *future*. If a secret
had ever been committed and later removed, the repository would still be leaking
it on a public GitHub URL, and no amount of cleaning the working tree would fix
that. The history scan is the only check that actually answers the question the
submission rules ask.

I also confirmed by hand that the two `if` blocks in the CI workflow `exit 1` on
failure rather than merely printing a warning, since a check that reports a
problem without failing the job is the same as no check at all.

## One AI output I rejected or corrected

Three, in order of how much they mattered.

**1. Overruled the AI's recommendation on repository layout — and reversed my own
first decision.** The brief lists `app/`, `frontend/`, and `tests/` at the
repository root; mine were at `backend/app/` and `backend/tests/`, inherited from
earlier modules. AI recommended *keeping* the existing layout and documenting a
mapping table instead, arguing that moving graded, working code is churn and that
the brief's own rule is to protect what already exists. I accepted that at first
and wrote the mapping table.

Then I re-read the submission checklist, which says in plain words to confirm the
branch contains `app/`, `frontend/`, and `tests/`. A mapping table asks a grader
to accept an explanation instead of seeing the thing. Since the checkpoint is
pass/fail and a miss costs a resubmission, I overrode the recommendation and did
the move — but on my terms: `git mv` only, so history is preserved, and **not one
line inside `app/` or `frontend/` changed**. I verified that rather than assuming
it (`git diff -M --stat 305318e` → 4 files changed, 0 insertions, 0 deletions,
plus a per-file checksum comparison), then re-ran the full suite from the new
root — `39 passed` — and confirmed `GET /health` still returns 200.

The AI's reasoning was sound and I still agree with the principle. It was
weighing "avoid churn" against "match the checklist" and could not weigh what the
checklist costs me if it is wrong. That judgement was mine to make.

**2. Rejected: the "redundant `exclude={'overdue'}`" review comment** in the code
review log above. The suggestion was confidently argued and wrong. I did not
argue back from memory — I ran it: `"overdue" in t.model_dump()` returns `True`,
and revalidating without the exclusion raises `ValidationError`. Applying it
would have broken every `PATCH /tasks/{id}` request. This is the clearest example
in the project of why "sounds right" is not a merge criterion.

**3. Downgraded: two real findings, deliberately not fixed.** The
`POST` vs `PATCH` null-`description` asymmetry and the unbounded `description`
length are both genuine and both reproducible. I still declined to change
`app/`. Neither one breaks a documented promise — the README's null rule
is written about `PATCH` and is accurate as written — and the ground rules limit
`app/` changes to small bug fixes and security fixes. Editing validation
behaviour on a working, graded application to satisfy a finding nobody asked me
to act on is scope creep wearing a safety jacket. Recording them with
reproduction steps is the more useful and more honest outcome, and it leaves the
decision with whoever maintains this next.

## Three AI usage rules

1. **Never paste:** real credentials, `.env` contents, API tokens, production
   logs, or anyone's personal data into a prompt or into this repo. Placeholders
   in `.env.example` are the only environment values that get written down.
2. **Always verify:** any AI claim about behaviour gets checked by running it —
   `pytest`, a `curl` against the endpoint, a `grep` over the file, or a green CI
   run. A confident explanation is not evidence, and I do not report a result I
   did not personally observe.
3. **Record AI contributions by:** naming, in `docs/`, the file and command
   involved, grading each AI comment or finding (Useful / Noise / Wrong, Valid /
   False Positive / Noise), and writing down what I rejected and why — not just
   what I accepted.

## Ownership statement

I can explain every line that changed in this submission: `app/` and `frontend/`
are untouched — they were moved to the repository root with `git mv`, and a
rename-aware diff against `305318e` plus a per-file checksum comparison confirm
every one is byte-identical — so what I added is a
Dockerfile, a `.dockerignore`, a CI workflow, `AGENTS.md`, and these evidence
documents, and I can justify each decision in them, from why the container runs
as UID 10001 to why the CI Python version is pinned to `3.13` rather than `3.x`.
Every factual claim in these documents came from running the command and pasting
the real output, including the inconvenient ones — Docker is not installed on my
machine, so I said so and moved that verification into CI instead of pasting a
build log I never saw. Where AI was wrong I caught it by testing rather than by
intuition, and where AI was right but out of scope I wrote the finding down
instead of quietly editing protected code. The parts I am least certain about —
the unbounded `description` field and the wide-open CORS policy — are named as
open risks in this file rather than hidden. That combination of untouched
application code, verified claims, and openly recorded doubts is why I am
comfortable submitting this repository as my own work.
