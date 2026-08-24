# My AI Playbook

Written after finishing the Task Tracker final project. I'm not a programmer — I
direct the work and review what comes back — so these rules are about how I stay
genuinely responsible for code I didn't type.

## When I reach for AI first

- **Reading a codebase I'm about to change.** The single most valuable thing AI
  did all course was open my repo and tell me my assumption was wrong: I thought
  Modules 1-3 had left me a working app, and only the skeleton existed. Ask what
  is actually there before planning anything on top of it.
- **Boilerplate with a known-good shape** — the Dockerfile, the CI workflow, the
  pytest scaffolding. I can't write these from memory, but I *can* read them and
  ask why each line is there, which is enough to own them.
- **Turning a vague want into a specification.** "Add due dates" is a bad
  prompt. Making me state the validation rule, where `overdue` is computed, and
  what the tests should cover is most of the design work.
- **Writing tests for a rule I just decided**, especially the awkward cases — a
  `Done` task with a past due date, an explicit `null` versus an omitted field.
- **Explaining an error message** before I start guessing at it.

## When I do not reach for AI first

- **Deciding what the product should do.** The overdue rule — a finished task
  shouldn't be flagged overdue just because I closed it late — was a judgement
  about how I'd actually use the thing. AI's first version got it wrong and was
  perfectly confident about it.
- **Anything involving real credentials or someone's data.** No exceptions, and
  no "just this once with the values changed."
- **Deciding whether something is in scope.** AI will happily improve code
  nobody asked it to touch. Scope is mine.
- **When I'd be accepting code I can't read.** If I can't follow it, the answer
  is to ask for a smaller step or an explanation, not to paste it in and hope.
- **When it's a thing I'm supposed to be learning.** Getting the answer fast is
  sometimes the worst outcome available.

## My non-negotiables

1. Real secrets, tokens, `.env` contents, and personal data never go into a
   prompt or a commit. `.env.example` with placeholders is the only version that
   gets written down.
2. Nothing is "done" until I've run it — `pytest`, a `curl` against the endpoint,
   or a green CI run. Not "the code looks right."
3. I never report a result I didn't see. When Docker turned out not to be
   installed on my machine, I moved the check into CI and said so, rather than
   pasting a build log I never produced.
4. If I can't explain a line, it doesn't get committed.
5. Protected code stays protected. A finding I'm not asked to fix gets written
   down with reproduction steps, not quietly patched.

## My review rules

- **Read the whole diff, not the summary of it.** The summary is written by the
  same thing that wrote the bug.
- **Test the confident claims first.** AI told me `exclude={'overdue'}` was
  redundant and could be removed. Two lines in a Python shell showed it was
  wrong, and removing it would have broken every update request. Confidence and
  correctness are unrelated variables.
- **Grade findings out loud** — Useful / Noise / Wrong, Valid / False Positive /
  Noise — with a reason. Forcing myself to write the reason is what catches the
  ones I was about to nod along to. A scanner flagged `innerHTML` as XSS; the
  line was `innerHTML = ""`.
- **Click the actual app.** The delete button "worked" in the code and silently
  did nothing in the browser. Only running it found that.
- **Ask for the cause, not the fix.** Asking to "fix the null title" would have
  patched one field. Asking why it happened, and whether it happened elsewhere,
  found a second defect in the storage layer.
- **Be suspicious of a large diff for a small request.** That's scope creep, and
  it's on me if I merge it.

## What I'm still figuring out

- How much to trust an AI security review. This one gave me two real findings, a
  clean false positive, and one "vulnerability" that was just a documented design
  decision. I caught those by checking each one — I don't yet have a faster
  instinct for which is which.
- Where the line sits between a fix that's genuinely in scope and one that's me
  being tidy.
- How this works with other people. Everything here assumes I'm the only
  reviewer. I don't know yet what a team norm looks like — who reviews the AI
  output, or whether "AI wrote this" belongs in the commit message.
- Whether I'm learning enough. It's very easy to ship working code and retain
  nothing, and I can't always tell the difference in the moment.

## Decision Card

| Situation | What I do |
|---|---|
| **New feature** | Write the rule and the test expectations myself first, then let AI implement. Never the reverse. |
| **Code review** | Read the whole diff. Grade each comment Useful / Noise / Wrong with a reason. Test anything stated confidently. |
| **Debugging** | Reproduce it myself first, then ask for the cause — not the fix — and check whether the same hole exists elsewhere. |
| **Infrastructure** | Accept the draft, then justify every line out loud (why this Python version, why non-root, why no `--reload`). Never let a check be able to pass without actually checking. |
| **Never paste** | Credentials, tokens, `.env` values, production logs, anyone's personal data. |
| **My one rule** | If I can't explain it, I don't ship it. |
