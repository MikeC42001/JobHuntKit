# agents/CONTEXT.md — shared preamble for every JobHuntKit agent instruction

Read this before `cv-setup.md`, `cv-tailor.md`, or `interview-prep.md` — all three assume you've
already done the steps below. This file is the one source of truth for root-finding and file ownership;
the Claude Code skill, the slash command, and the Cursor rule are all thin pointers back to it,
never copies.

## Step 0 — locate the root

Find a directory containing `config.json` and a sibling `engine/build_cv.py`, checking the
current working directory then its parents. If nothing is found:

- No `config.json` anywhere above cwd → this is a fresh clone with no data root yet. **Ask where
  the data should live before scaffolding**, and explain the choice:
  - *Inside the clone* — `python scripts/init_workspace.py`. Nothing to configure, and the
    content paths are gitignored, so CV data can't reach this repo's history by accident. Best
    for trying it out.
  - *Its own directory* — `python scripts/init_workspace.py --root <path>`. The CV data can then
    live in a private repo of its own, and `git pull` on this checkout never touches it. Best if
    this is going to get real use.

  Then re-probe. If they chose a separate root, every later command this session needs the same
  `--root <path>`, or `$JOBHUNTKIT_ROOT` set once.
- Still ambiguous (e.g. you're not inside a JobHuntKit checkout at all) → ask: "Where's the
  JobHuntKit root for this session?" Don't guess a path.

Every path referenced below (`config.json`, `master/...`, `profile/...`, `applications/...`) is
relative to that root, once found. **Never reference an absolute machine path in anything you
write** — a hardcoded path breaks the moment this instruction is handed to someone on a
different machine, which is the whole point of it living in this public repo.

## File ownership

You may write: `applications/offer-pages/<Company>/application.md`, `posting.md`, `notes.md`,
`cover_letter.md`, `interview_prep_*.md`, `profile/background.md`, `master/master_cv.md`,
`master/master_cv_minimal.md`, `master/CV_SPEC.md`, `applications/README.md`, `config.json`
(only its non-spine keys unless a task explicitly asks you to change the spine).

You must **never** write: `cv-minimal.md` or `cv.md` (both generated — see `docs/SPEC.md`,
"build artifacts"), anything under `generate-pdfs/` or `produced/` (rendered output, also
generated).

**Never auto-commit.** Report what changed and let the person decide when to commit — same rule
as every other agent-driven flow in this toolkit.

## Where the actual mechanics live

This file only covers orientation. Format rules (marker syntax, placeholder grammar,
`application.md` headings) are in `docs/SPEC.md`. Every `config.json` key is in `docs/CONFIG.md`.
Which file to edit for content vs. structure vs. the PDF's visual look — including how to add a
new CV style — is `docs/CUSTOMIZING.md`. Don't re-derive any of these from scratch — read them.
