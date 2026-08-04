# JobHuntKit

**Description:** Open-source toolkit that generates tailored, one-page CVs per job posting from
a tagged master CV + a per-posting selection file. Extracted and genericized from Miguel's
private `job-hunt/` pipeline (in the Projetos meta-repo) — that private folder is never touched,
moved, or migrated by this project; see `[[project_jobhuntkit]]` in MEMORY.md for the split.

**Collaborators:** Solo (MC)
**GitHub:** `MikeC42001/JobHuntKit`, **private** (started private deliberately, 2026-08-04 — flip
to public with `gh repo edit MikeC42001/JobHuntKit --visibility public` once it's ready to show)
**Stack:** Python 3.8+ (stdlib only), Node.js (`marked` for markdown→HTML), Bash renderers →
headless Chrome/Chromium/Edge/Brave `--print-to-pdf`. No build system, no pip dependencies for
the engine itself.

**License:** MIT (`LICENSE`). Bundled IBM Plex fonts are SIL OFL 1.1 (`NOTICE` +
`engine/render-support/fonts/OFL.txt`).

---

## Architecture in one line

The engine (`engine/`) never contains personal data — everything a person writes lives at a
"root" resolved at runtime (`--root`, `$JOBHUNTKIT_ROOT`, or the repo checkout by default). A
master CV file tags every reusable block with a stable `<!-- @id -->` marker; a template says
which slots exist and in what order; a per-company `application.md` selects/overrides from the
master. `engine/build_cv.py` assembles the three into `cv-minimal.md`; `engine/check_cv.py`
validates the locked spine landed correctly and reports coverage; `engine/render_cv_minimal.sh`
renders it to PDF; `engine/verify_cvs.py` gates page count.

## Current state (M0 complete; M1 in progress, 2026-08-04)

Working end-to-end: clone → `bash demo.sh` → build → validate → render → verify → one-page PDF,
cross-platform-safe (macOS/Linux fixes in `engine/lib.sh` are code-reviewed but only tested live
on Windows so far — see Next below). Demo persona "Robin Vale" (`examples/demo/`) is entirely
fictional, applying to a fictional "Orbital Dynamics." Golden-file
(`examples/demo/expected/cv-minimal.md`) and rendered output
(`examples/demo/output/cv-minimal.{pdf,png}`) are committed. Pushed to GitHub (private)
2026-08-04 — `main` + `dev` both on `origin`.

**`engine/check_cv.py` built (2026-08-04):** structure mode validates locked-experience order,
required education titles (+ a bare-URL guard on any title flagged `require_detail_for`), and
every `spine.verbatim_ids` entry appearing byte-for-byte in the rendered output — all sourced
from `config.json`'s `spine` block, zero hardcoded employer/title strings (the private repo's
`check_cv.py` had a real person's employer name compiled into `TITLE_MARKERS`; this doesn't).
`--coverage` reports optional-id + `proj-*` presence/omission/silence per application; its "N of
TOTAL" denominator is computed by counting a resolved template's unconditional `{{@id}}` slots,
not a hardcoded magic number, so it can't go stale when someone edits their template. A fresh/
unconfigured root prints a `NOT CONFIGURED` banner (exit 0) instead of a false "all OK" — see
`Config.spine_configured` in `engine/config.py`. Also fixed while here: `config.py` now forces
UTF-8 stdout/stderr for every engine script — Windows otherwise defaults to the console codepage
and mangles an em dash or accented character. Verified: demo.sh end-to-end, a hand-built
broken-spine fixture (reordered entries + dropped verbatim lines both caught), and the
NOT CONFIGURED path on an empty config.

**Not yet built** (see the plan file this session produced, in this machine's
`~/.claude/plans/` history, for the full M1–M4 breakdown):
- Rest of M1: `tests/` (golden-file + broken-spine fixture, formalized as pytest — currently only
  manually verified), CI, `scripts/sync.sh` + `engine.manifest` + `scripts/audit_public.py` — the
  manifest-driven pull/push mechanism that lets Miguel improve the engine from either the public
  or private checkout without personal data ever crossing into the public repo
- Blank starter `templates/` for a real user's own data, `docs/{GETTING-STARTED,SPEC,NO-AI,CONFIG}.md`
- Agent instructions (`agents/CONTEXT.md`, `cv-setup.md`, `cv-tailor.md`) + Claude Code skills,
  Cursor rules, and a generated ChatGPT-paste variant
- `scan_applications.py`, `collect_cvs.py`, `collect_letters.py`, cover-letter rendering
- `engine/extractors/` — pluggable posting extraction (LinkedIn/Greenhouse/Lever/Workday/Indeed),
  a registry + confidence-based dispatch, so adding a new job board is a self-contained
  contribution rather than a rewrite of one fixed script

## Relationship to the private `job-hunt/` folder

Deliberately **not** dogfooded yet, and diverging by design rather than forking/syncing from day
one — see `[[project_jobhuntkit]]` for the reasoning and the leak-prevention mechanism
(`engine.manifest`-bounded sync, planned for M1) that makes future syncing safe once built.

## End of Day Checklist

1. Commit all open changes on the current feature branch (never straight to `main`)
2. Push to remote once one exists
3. Update this file's "Current state" section if the milestone changed
4. Update `MEMORY.md` (`project_jobhuntkit`) if something stable and non-obvious changed
5. Update `Projects_Status.md`'s JobHuntKit row

---

> Last updated: 2026-08-04 (check_cv.py session)
