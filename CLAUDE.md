# JobHuntKit

**Description:** Open-source toolkit that generates tailored, one-page CVs per job posting from
a tagged master CV + a per-posting selection file.

**Collaborators:** Solo (MikeC42001)
**GitHub:** `MikeC42001/JobHuntKit`, **private** (started private deliberately, 2026-08-04 — flip
to public with `gh repo edit MikeC42001/JobHuntKit --visibility public` once it's ready to show)
**Public identity:** in any tracked file, refer to the maintainer only as `MikeC42001` — never a
first name, full name, or initials. `LICENSE`'s copyright line included.
**Stack:** Python 3.8+ (stdlib only), Node.js (`marked` for markdown→HTML), Bash renderers →
headless Chrome/Chromium/Edge/Brave `--print-to-pdf`. No build system, no pip dependencies for
the engine itself.

**License:** MIT (`LICENSE`). Bundled IBM Plex fonts are SIL OFL 1.1 (`NOTICE` +
`engine/render-support/fonts/OFL.txt`).

---

## Working conventions

**Never open a GitHub issue without MikeC42001's explicit approval in the current conversation.**
Draft the body, show it, wait for a yes — then (and only then) `gh issue create`. Same rule for
`gh issue edit --add-label`/`--remove-label` and `gh issue close`: those are the two approval
gates in `community/README.md`'s lifecycle, and an issue is public, permanent, and notifies
watchers, so it's an outward-facing action, not a note-to-self. **Reading is unrestricted** —
`gh issue list`/`gh issue view` any time. See `community/README.md` for the full open-question →
issue → resolved lifecycle and `community/community.sh` for reading it back (read-only by
construction — no write calls anywhere in that script; `community.sh status` confirms).

## Architecture in one line

The engine (`engine/`) never contains personal data — everything a person writes lives at a
"root" resolved at runtime (`--root`, `$JOBHUNTKIT_ROOT`, or the repo checkout by default). A
master CV file tags every reusable block with a stable `<!-- @id -->` marker; a template says
which slots exist and in what order; a per-company `application.md` selects/overrides from the
master. `engine/build_cv.py` assembles the three into `cv-minimal.md`; `engine/check_cv.py`
validates the locked spine landed correctly and reports coverage; `engine/render_cv_minimal.sh`
renders it to PDF; `engine/verify_cvs.py` gates page count.

## Current state

**Released `v0.1.0` (2026-08-10), still private.** `main` = `58c177c`, byte-identical to `dev`,
all 6 CI jobs green. The repo has its description and 12 topics set; only the manual
social-preview upload (Settings → General, no `gh` support) and the visibility flip remain.

Milestones M0–M4 are all complete and merged. What works, end to end:

- `bash demo.sh` runs the whole pipeline against the fictional `examples/demo/` persona —
  build → validate → render → verify → one-page PDF, plus the full CV, the photo variant, and a
  cover letter. CI runs it for real on Linux and macOS, so "cross-platform" is verified rather
  than assumed.
- **Two pipelines from one `application.md`**: the tailored one-pager (`cv-minimal.md`) and the
  long-form full CV (`cv.md`), opted into per company via a `pipelines:` front-matter key.
- **Two masters**: `master/master_cv.md` is the complete inventory; `master_cv_minimal.md` is its
  condensation, sharing the same `@id`s.
- **Four renderers** (minimal with four styles, full single-column, full with photo, letter), all
  id-agnostic — they clean their own input, so they render a built file, a master, or hand-written
  markdown with no build step.
- **The full loop**: `scan_applications.py` classifies every company, `extract_posting.py` turns a
  saved posting into something skimmable, `collect_cvs.py`/`collect_letters.py` stage PDFs for
  sending.
- **Agent layer**: `agents/{CONTEXT,cv-setup,cv-tailor,interview-prep}.md`, wired up as Claude Code
  skills/commands, a Cursor rule, and a generic `AGENTS.md`. Pointer-based, one source of truth.
- **The privacy mechanism**: `engine.manifest` + `scripts/sync.sh` + `scripts/audit_public.py`,
  enforced in CI and by an installable pre-commit hook.
- **111 tests**, pure-Python, no browser or Node needed.

Deliberately not built: posting-change detection, extractors beyond
generic/plaintext/LinkedIn, and anything else parked in
[`community/OPEN_QUESTIONS.md`](community/OPEN_QUESTIONS.md) as Q-001 … Q-005.

### Where the history lives

This section is a snapshot, not a record. Two places carry the past, for two different readers:

| Want | Read |
|---|---|
| What changed in a release, in brief | [`CHANGELOG.md`](CHANGELOG.md) — one entry per tag, written for people using the toolkit |
| Why it's built this way, what broke, what was tried and rejected | [`logs/YYYY_MM_log.md`](logs/) — one entry per working session, full context, oldest first |

Start with `logs/` when picking work back up: it keeps the dead ends and the reasoning, which is
the expensive part to reconstruct. `CHANGELOG.md` won't have them, by design.

## Known follow-ups (not blocking the release)

Recorded here rather than only in a next-session prompt, since those get overwritten each session.
Resolved items move to [`logs/`](logs/) — this list is only what's still open.

1. **`audit_public.py` only inspects tracked files.** `git_tracked_files()` is the input, so an
   untracked file is invisible to the gate — including one that was just added specifically to
   be checked. It reported a clean 119 files while both new social-card PNGs sat unstaged and
   unexamined, which reads as reassurance when it's actually silence. Worth a warning line when
   the working tree has untracked non-ignored files, so a clean result can't be mistaken for
   full coverage.
2. **README banner using the light social card.** `.github/social-preview-light.png` currently
   has no consumer. GitHub renders theme-aware images in a README via `<picture>` +
   `prefers-color-scheme`, which is the one place a light/dark pair actually works (the social
   preview itself cannot).

## End of Day Checklist

1. Commit all open changes on the current feature branch (never straight to `main`)
2. Push to remote once one exists
3. Update this file's "Current state" section if the milestone changed
4. Update `MEMORY.md` (`project_jobhuntkit`) if something stable and non-obvious changed
5. Update `Projects_Status.md`'s JobHuntKit row

---

> Last updated: 2026-08-10 — `v0.1.0` tagged on `main`, repo still private.
> This file holds standing facts only; the dated narrative lives in [`logs/`](logs/) and the
> release summary in [`CHANGELOG.md`](CHANGELOG.md). Keep it that way — it was 468 lines before
> the split, and 341 of them were history filed under "Current state".
