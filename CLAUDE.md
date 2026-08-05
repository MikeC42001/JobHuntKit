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

## Current state (M0 + M1 complete and merged to `dev`, 2026-08-05)

Working end-to-end: clone → `bash demo.sh` → build → validate → render → verify → one-page PDF,
now genuinely cross-platform-verified — the `render-matrix` CI job (PR #1, 2026-08-05) runs
`demo.sh` on ubuntu-latest and macos-latest, not just code-reviewed. That first real run failed
on three real bugs (`mapfile` missing on macOS's bash 3.2, headless Chromium needing
`--no-sandbox` under CI on ubuntu even as non-root, and a test-harness-only Windows bash
resolution issue) — all fixed same-session, all 6 CI jobs (lint, 3× test, 2× render-matrix) now
green. Demo persona "Robin Vale" (`examples/demo/`) is entirely
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

**`engine.manifest` + `scripts/sync.sh` + `scripts/audit_public.py` built (2026-08-04):** the
manifest-driven pull/push mechanism, built specifically before any dogfooding from the private
folder (that was the plan, and it held). `engine.manifest` whitelists exactly the paths
considered "engine"; `sync.sh pull|push` copies only those paths between a canonical repo and
any root; `audit_public.py` is the leak gate `push` always runs first, refusing to write
anything on any finding (unexpected binary, email/phone outside a small allowlist, absolute
path, forbidden content prefix, or a gitignored `.private-terms` term). Verified the actual
guarantee, not just the check: pushed from a root containing a fake `profile/background.md` and
confirmed it never entered the audit's file list or the destination at all — content paths are
structurally invisible to the mechanism, not merely blocked by a rule that could have a gap.
Also verified a pulled copy is a fully working clone (`bash demo.sh` runs clean), and added a
`scripts/hooks/pre-commit` + `scripts/install_hooks.sh` pair (git doesn't track `.git/hooks/`,
so installation is a manual one-time step) — tested to actually block a bad commit.

**`tests/` (pytest) + CI built (2026-08-05):** 27 tests, pure-Python (no browser/Node needed) —
golden-file diff for `build_cv.py`; `check_cv.py` structure fixtures (reordered experience,
dropped verbatim line, missing locked entry, NOT CONFIGURED banner) + coverage math (locked-slot
count proven non-hardcoded, "13 of 14" pinned for the demo); `audit_public.py` fixtures for every
finding category, plus the content-invisibility guarantee exercised **through the real
`scripts/sync.sh`** via subprocess (not a reimplementation) — a fake `profile/` never enters the
audit's file list or a push destination, and a leaked email aborts the push with nothing written.
`tests/test_audit_public.py` was added to `audit_public.py`'s `CONTENT_CHECK_SELF_EXCLUDE`
(same reason as `audit_public.py` itself — its fixtures are deliberately-fake trigger patterns).
`.github/workflows/ci.yml`: `ruff` lint, pytest on ubuntu/macos/windows, and a `render-matrix`
job (ubuntu/macos, via `browser-actions/setup-chrome`) that runs the real `demo.sh`. `tests/`,
`.github/`, and `requirements-dev.txt` added to `engine.manifest`.

**First CI run found 3 real cross-platform bugs (2026-08-05, PR #1):** `scripts/sync.sh` used
`mapfile`, a bash-4+ builtin absent from macOS's default bash 3.2 — every push silently failed
to build its audit file list there. `engine/lib.sh`'s `browser_flags()` only added
`--no-sandbox` under root, but GitHub Actions' ubuntu runners restrict the sandbox helper for
non-root users too, crashing headless Chromium (SIGABRT) — fixed by also checking `$CI=true`.
And `tests/conftest.py`'s new `bash_executable()` helper was needed because spawning `"bash"`
from Python on windows-latest CI resolves to Windows' own WSL launcher stub (errors out with no
distro installed), not Git Bash — test-harness-only, doesn't affect a real user already running
inside Git Bash. Fixing `bash_executable()`'s literal Git-for-Windows path also required adding
an `ABS_PATH_ALLOWLIST_PREFIXES` escape hatch to `audit_public.py`'s own absolute-path check —
generic Program Files install paths, no personal data, but still Windows-drive-letter-shaped.
All 6 CI jobs (lint, 3× test, 2× render-matrix) green. Merged to `dev` via PR #1
(`feat/m1-tests-ci`, merge commit not squash, matching this project's convention).

**Not yet built** (see the plan file this session produced, in this machine's
`~/.claude/plans/` history, for the full M1–M4 breakdown):
- Blank starter `templates/` for a real user's own data, `docs/{GETTING-STARTED,SPEC,NO-AI,CONFIG}.md`
- Agent instructions (`agents/CONTEXT.md`, `cv-setup.md`, `cv-tailor.md`) + Claude Code skills,
  Cursor rules, and a generated ChatGPT-paste variant
- `scan_applications.py`, `collect_cvs.py`, `collect_letters.py`, cover-letter rendering
- `engine/extractors/` — pluggable posting extraction (LinkedIn/Greenhouse/Lever/Workday/Indeed),
  a registry + confidence-based dispatch, so adding a new job board is a self-contained
  contribution rather than a rewrite of one fixed script

## Relationship to the private `job-hunt/` folder

Deliberately **not** dogfooded yet, and diverging by design rather than forking/syncing from day
one — see `[[project_jobhuntkit]]` for the reasoning. The leak-prevention mechanism
(`engine.manifest`-bounded `sync.sh` + `audit_public.py`) is now **built and verified** (see
Current state above), which is what makes eventually syncing the private folder to this engine
safe — actually doing that migration is still M4, deliberately last.

## End of Day Checklist

1. Commit all open changes on the current feature branch (never straight to `main`)
2. Push to remote once one exists
3. Update this file's "Current state" section if the milestone changed
4. Update `MEMORY.md` (`project_jobhuntkit`) if something stable and non-obvious changed
5. Update `Projects_Status.md`'s JobHuntKit row

---

> Last updated: 2026-08-05 (tests/ + CI session)
