# JobHuntKit

**Description:** Open-source toolkit that generates tailored, one-page CVs per job posting from
a tagged master CV + a per-posting selection file. Extracted and genericized from a private CV
pipeline — that private source is never touched, moved, or migrated by this project.

**Collaborators:** Solo (MC)
**GitHub:** `MikeC42001/JobHuntKit`, **private** (started private deliberately, 2026-08-04 — flip
to public with `gh repo edit MikeC42001/JobHuntKit --visibility public` once it's ready to show)
**Stack:** Python 3.8+ (stdlib only), Node.js (`marked` for markdown→HTML), Bash renderers →
headless Chrome/Chromium/Edge/Brave `--print-to-pdf`. No build system, no pip dependencies for
the engine itself.

**License:** MIT (`LICENSE`). Bundled IBM Plex fonts are SIL OFL 1.1 (`NOTICE` +
`engine/render-support/fonts/OFL.txt`).

---

## Working conventions

**Never open a GitHub issue without Miguel's explicit approval in the current conversation.**
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

## Current state (M0-M3 merged to `dev`; M4 release prep in progress, 2026-08-09)

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

**`tests/` (pytest) + CI built (2026-08-05):** 29 tests, pure-Python (no browser/Node needed) —
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

**M2 (onboarding) complete, 2026-08-06, on `feat/m2-onboarding`:** blank starter `templates/`
(`master_cv_minimal.md`, `minimal-full.md`, `application.md`, `background.md`, `CV_SPEC.md`,
`applications-README.md`) — the starter master and starter template deliberately share a
consistent, non-numbered `@id` naming (`edu-degree`, `exp-previous-role`, `exp-current-role`,
`proj-example`, `exp-optional`, `vol-example`, plus the five `header-*` ids and the two bare
locked lines) so `build_cv.py --all` succeeds on a totally fresh root with zero edits — verified
end-to-end, not assumed. `scripts/init_workspace.py` scaffolds a data root from those templates:
default root is the checkout itself (matches `config.py`'s existing fallback), `--root` for
anywhere else; skip-existing by default so no flag can ever clobber a real master CV, `--force`
re-copies only the engine-owned CV template(s); refuses a walk-up match onto an unrelated
directory that merely has *a* `config.json` nearby with none of this toolkit's shape. Caught one
real gap while designing it: `images/` wasn't gitignored and wasn't in `audit_public.py`'s
`FORBIDDEN_PREFIXES` (a scaffolded photo would only have been caught incidentally by the
binary-extension check) — fixed by anchoring `/images/` in `.gitignore`, verified
`examples/demo/images/avatar.png` stays tracked. 10 new tests (`tests/test_init_workspace.py`)
including a subprocess-driven end-to-end run (`init_workspace.py` → `build_cv.py --all` →
`check_cv.py`) asserting the NOT CONFIGURED banner is a real no-op success and not a
false-passing "companies OK", and a `git check-ignore`-based test pinning the safety property the
default root relies on rather than trusting it. `docs/{SPEC,GETTING-STARTED,CONFIG,NO-AI}.md`
and `CONTRIBUTING.md` written by cannibalizing the private `job-hunt/README.md` +
`job-hunt/cv/CV_SPEC.md` (read-only sources, never touched) — every personal number, employer
name, and dated incident stripped; the 12-rule renderer-compatibility contract and the full
placeholder grammar ported near-verbatim since they were already generic. Agent layer:
`agents/CONTEXT.md` (shared root-probe + file-ownership preamble) and `agents/cv-setup.md` (port
of `/job-hunt-rd`, already the most portable of the private commands) + thin pointer adapters
(`.claude/skills/cv-setup/SKILL.md`, `.claude/commands/cv-setup.md`, `.cursor/rules/jobhuntkit.mdc`,
root `AGENTS.md`) — one source of truth, no copies. `engine.manifest` already forward-declared
every new path (`templates/`, `docs/`, `agents/`, `.claude/`, `.cursor/`, `AGENTS.md`,
`CONTRIBUTING.md`), and `scripts/sync.sh` expands directories recursively, so **no changes** to
the manifest, `sync.sh`, `demo.sh`, or CI were needed. `main` still untouched (M2's `v0.1.0` tag,
`main` merge, and the public-visibility flip are a deliberately separate decision after reading
the new docs, not bundled into this branch). `agents/cv-tailor.md` moved to M3 — it wraps
`scan_applications.py`/`collect_cvs.py`, neither of which exists yet.

**M3 (the full loop) complete on `feat/m3-full-loop`, 2026-08-06:** `engine/scan_applications.py`
classifies every company as NEW/INCOMPLETE/CURRENT/STALE/ERROR plus independent CV/letter sent/
declined/pending state, reusing `build_cv.build_company()`'s diff mode directly rather than
reimplementing staleness detection. `engine/collect_cvs.py`/`engine/collect_letters.py` stage
rendered PDFs into `produced/to_send/` — the CV collector's `--force` semantics preserved exactly
(never narrows the run, only decides whether already-sent companies get re-copied), the letter
collector deliberately one-company-per-run with no bulk mode. Cover letters render via
`engine/render_letter.sh` (mirrors `render_cv_minimal.sh`'s structure, no `--photo`/`--style` — a
letter has neither) and `engine/render-support/letter2html.js`, a **tracked** file this time
(the private version's heredoc-rewrite-on-every-run is exactly why it drifted there);
`engine/md_to_email_txt.py` flattens a letter into paste-ready plain text. `demo.sh` grew a fifth
step rendering `examples/demo`'s (previously unrendered) `cover_letter.md`, so CI's cross-platform
`render-matrix` job now exercises the letter renderer on ubuntu/macOS from the first push.

`engine/extractors/` is a small registry (`base.py`'s `PostingDraft`/`Extractor` protocol,
`generic.py` the always-matches fallback, `plaintext.py` for `.txt`/pasted text, `linkedin.py` for
job-details pages) behind a thin `engine/extract_posting.py` CLI (`--extractor` to force one,
`--list-extractors`, `--url`). `linkedin.py` **refuses** a saved feed-card/search-results page
with an actionable error instead of emitting empty content — the concrete fix for a real failure
mode already hit in the private pipeline this was ported from. `docs/EXTRACTORS.md` is the
how-to; Greenhouse/Lever/Workday/Indeed are filed as `good first issue`s rather than built here,
deliberately — a clean plugin API with an open contribution path is a stronger signal than
hand-writing DOM fingerprints for boards with no real postings to test against.

`agents/cv-tailor.md` (port of `/job-hunt`) wires all of it together — the 7-branch argument
ladder, render-only mode, and Steps 1–7 (scan → intake → draft → build+validate with zero SILENT
as the bar → render+verify → stage → report) carry over intact; a new Step 6b offers an optional,
never-automatic cover-letter draft per company, which the private command never had. Adapters
(`.claude/skills/cv-tailor/`, `.claude/commands/cv-tailor.md`, `AGENTS.md`, `.cursor/rules/`)
match the `cv-setup` pattern from M2. 45 new tests (85 total), `ruff` clean, `demo.sh` clean
end-to-end. `main` still untouched — **merge to `main`, the `v0.1.0` tag, and the public-
visibility flip are now deliberately deferred until M4 is complete** (not just M3), a scope
decision made explicitly this session, superseding the earlier plan to decide right after M2.

**M3 merged to `dev` via PR #1, 2026-08-07** (merge commit, not squash, matching this project's
convention). Same session: added a fourth agent skill, `interview-prep`
(`agents/interview-prep.md` + `.claude/skills/interview-prep/`, `.claude/commands/interview-prep.md`,
a Cursor-rule line, `agents/CONTEXT.md`'s file-ownership list extended for `interview_prep_*.md`)
— outside the original M0-M4 scope (that scope is the CV-generation loop specifically), added
because the underlying workflow (prep doc + a live mock-Q&A pass that catches contradictions
against what was already written, factual drift, vague self-praise, and unprofessional framing)
was exercised and validated in the private `job-hunt/` folder first, same pattern as every other
agent skill here.

**Full-CV pipeline added, 2026-08-08, on `feat/m3-full-cv-pipeline`** (PR #2, **merged to `dev`**,
CI green — all 6 jobs including both `render-matrix` legs). This was in M3's original scope and
got dropped when M3 shipped; picked back up as deferred M3, not new scope. `engine/render_cv.sh`
(single-column, ATS-safe, no photo) and `engine/render_cv_photo.sh` (two-column, circular photo)
are ports of the private pipeline's equivalents, look preserved verbatim, rebuilt on this
project's conventions (`engine/lib.sh` helpers, tracked `render-support/cv2html.js`/
`cv2html-photo.js` rather than heredocs). The new capability neither private script had:
**id-agnostic rendering** — both converters clean their own input (strip every
`<!-- ... -->` comment, honor a new `<!-- render:stop -->` tag), so either renders a built
`cv.md`, a master file pointed at directly, or a hand-written file with no `@id` scheme, with no
build step or intermediate file. `engine/verify_cvs.py` gained `--max-pages N` (0 disables the
gate) for checking a multi-page artifact without touching `limits.max_pages`'s 1-page default.
`demo.sh` grew from 5 to 7 steps at this point, rendering `examples/demo/master/master_cv_minimal.md`
through both new renderers. 90/90 tests pass (5 new, all for `--max-pages`), lint clean, leak gate
clean. Also this session: filed the 4 extractor `good first issue`s (#3–#6) and deleted 4 stale
merged branches.

**Second master shipped same day, 2026-08-08, on `feat/second-master-pipeline`** (PR #7, **merged
to `dev`**, CI green — all 6 jobs including both `render-matrix` legs). The follow-up flagged in
PR #2, picked up immediately: `master/master_cv.md` is now the **primary master** — the complete
inventory, `@id`-tagged, a real long-form document — and `master_cv_minimal.md` is explicitly its
**condensation**: same ids, terser wording. Every minimal id must exist in the full master; the
reverse doesn't hold (the demo's `exp-first-internship` is full-only), pinned by tests against
both the demo and the blank starter templates. `templates/full.md` is the long-form build
template — roomier, no page budget, most spine entries **unconditional** `{{@id}}` where the
minimal template gates the same ids behind `{{@id?}}`.

`engine/config.py` gained a `pipelines` block (`Config.pipeline(name)` → resolved master/
template/output path), making `build_cv.py` data-driven instead of hardcoding `cv-minimal.md`.
`build_cv.py` now builds **both** pipelines from **one** `application.md` — an optional
`pipelines:` front-matter key (e.g. `pipelines: minimal, full`) opts a company in; no such key
at all (every pre-existing `application.md`) keeps building exactly as before, verified as an
explicit regression guard against `build_company()`'s original call signature. `check_cv.py
--pipeline full` validates `cv.md` against `master_cv.md`, same `spine.json` config either way.

**A real bug found and fixed by actually running the new code:** coverage's optional-id
reporting blindly trusted the shared `spine.optional_ids` config list — wrong for the full
pipeline, since `templates/full.md` makes those same ids unconditional. `exp-course-tutor` was
reported DELIBERATE (omitted) despite being genuinely present in the rendered `cv.md`. Fixed
with `gated_optional_ids()`, which checks whether the pipeline's *own template* actually gates
an id before reporting it as gated at all — now a regression test.

`agents/cv-setup.md`'s Update mode gained the middle stop: file a new fact into `master_cv.md`
first (full wording), then condense the same block into `master_cv_minimal.md` (same id) — the
one place the chain is actually enforced, since no script can condense prose. `demo.sh` grew
from 7 to 10 steps — the existing build already produced `cv.md` once the demo's
`application.md` opted in, but nothing had checked or rendered it; new steps close that gap, and
the direct-master-render steps switched to `master_cv.md` (the primary) to match the docs.
102/102 tests pass (12 new), lint clean, leak gate clean.

**M4 scope narrowed, 2026-08-09.** The original M0–M4 design doc
(`~/.claude/plans/immutable-marinating-volcano.md`) scoped M4 as "Polish" — `CHANGELOG.md`, the
`v0.1.0` tag, GitHub metadata, README badges. `scripts/build_paste_prompts.py` and
`templates/minimal-lean.md` had drifted onto M4's list even though they were M3-scoped, deferred
items — they're out again, and (same reasoning as the extractor issues below) turned into
`community/OPEN_QUESTIONS.md`'s **Q-004** and **Q-005** rather than left as an implied roadmap:
neither exists in the private pipeline, so unlike everything in M3 they're new design work
nobody's validated is wanted. Posting-change detection stays **Q-002**, unscoped. The optional
first `sync.sh pull` into the private `job-hunt/` folder is skipped for this pass — that folder
stays untouched.

Extractors for Greenhouse, Lever, Workday, Indeed (see `docs/EXTRACTORS.md`) were briefly filed
as `good first issue`s (#3–#6, 2026-08-08) then **deleted** the same day (not just closed) — an
early example of the same "filing assumed the answer before asking" mistake. Whether any of
these are worth building is now `community/OPEN_QUESTIONS.md`'s **Q-003**, **not blocking M4**.

**M4 work done, `feat/m4-release-prep`, 2026-08-09** (branch renamed from
`chore/unfile-extractor-issues`, which already held the extractor un-filing — cascade rule, one
branch per milestone). Planned with a research pass that read every doc against the actual code
and found real bugs, not just drift — reshaped the milestone from "add release artifacts" into
"fix what's wrong, then add release artifacts":

- **Tier 1 — correctness bugs, fixed outright.** `agents/cv-tailor.md`'s three
  `render_cv_minimal.sh` calls all omitted `--photo`, which the script hard-exits 1 without (no
  default is configured out of the box) — the flagship tailoring workflow failed for every new
  user, every time. `agents/CONTEXT.md`'s file-ownership lists omitted `master/master_cv.md`
  from may-write (the file `cv-setup.md` is instructed to write first) and `cv.md` from
  never-write (as generated as `cv-minimal.md`). `build_cv.py`'s duplicate-`@id` error always
  named `master_cv_minimal.md` regardless of which master actually had the duplicate.
  `engine.manifest` was missing `pyproject.toml` (configures `ruff`, CI-enforced, never
  propagated by `sync.sh`). Two new regression tests (`tests/test_build_cv.py`,
  `tests/test_agents_docs.py`) pin the fixes — 109/109 tests pass throughout.
- **Tier 2 — documentation accuracy sweep**, file by file: `docs/SPEC.md` (a genuinely false
  claim that `spine.heading_aliases` extends what the renderer recognizes — it doesn't, the
  renderer never reads `config.json`; another false claim that `cv2html-photo.js` has no section
  model, when it does; the real `{{@id?}}` blank-collapse behavior; token precedence;
  `## Dissertation depth`, the fifth `FIELD_HEADINGS` entry missing from the canonical listing),
  `docs/CONFIG.md`, `docs/NO-AI.md`, `README.md` (Scripts table was missing 8 real scripts),
  `docs/GETTING-STARTED.md` + `scripts/init_workspace.py` (the script's printed onboarding
  sequence still taught the pre-second-master flow — fixed and verified by actually running it),
  `CONTRIBUTING.md`, `AGENTS.md`, and `templates/*.md` headers (the two-master relationship was
  documented in one direction only).
- **Tier 3 — orientation layer.** New `docs/CUSTOMIZING.md`: which file to edit for content vs.
  structure vs. the PDF's visual look, plus a verified 5-touchpoint recipe for adding a new
  `render_cv_minimal.sh --style` (exercised for real against the demo, not just described).
  Registered in all five files that index the docs set. README gained a short pointer table.
- **Tier 4 — release artifacts.** `CHANGELOG.md` (Keep a Changelog, one `[0.1.0]` section,
  grouped by capability), CI/license/Python badges on README (expected to 404 until the public
  flip — the URLs are correct, there's just nothing to point at yet).

**Still open, this milestone:** GitHub topics/description/social preview (`gh repo edit` —
outward-facing, needs explicit approval before running; social preview itself has no `gh`
support, manual web-UI upload). Then, once approved separately: merge to `main`, tag `v0.1.0`,
flip the repo public.

**CI coverage gaps closed, 2026-08-08, on `feat/ci-coverage-gaps`** (PR #9, merge commit
`82bedb7`, all 6 CI jobs green). Auditing what `ci.yml` actually exercised found the leak gate
wasn't actually a CI gate — `audit_public.py`'s logic was unit-tested but nothing in CI ever ran
it against a PR's own tree, so enforcement was 100% local (opt-in pre-commit hook or a manual
`CONTRIBUTING.md` step). `lint` now runs it for real. Also added: `shellcheck -x` for every
tracked `.sh` file (real findings fixed — `SC1091` via `source=` hints, `SC2046`/`SC2086` via
narrow disable comments where word-splitting is genuinely intentional, `SC2015` in
`native_path()`), `node --check` for the four tracked JS converters in `render-matrix`, and
`tests/test_community.py` (hermetic subprocess tests for `community.sh`, including a regression
test pinning its read-only guarantee). One unrelated macOS `render-matrix` Chromium flake
(`Trace/BPT trap`) hit mid-branch — re-ran the job alone, passed clean, confirmed not a
regression before merging.

**`community/` issue-orchestration folder merged to `dev` same day** (PR #8, merge commit
`738e569`, all 6 CI jobs green). Prompted by filing #3–#6 without a pre-approval step earlier the
same session — new standing rule, recorded in `CLAUDE.md` (this file, above), `AGENTS.md`,
`.cursor/rules/jobhuntkit.mdc`, and `community/README.md`: never open, label, or close a GitHub
issue without explicit approval first; reading stays unrestricted. Three-stage lifecycle —
`community/OPEN_QUESTIONS.md` (hand-written) → `question`-labelled issue (ranked by reactions,
`sort:reactions-+1-desc`) → promoted to scoped work → resolution **derived**, not written
(`closedByPullRequestsReferences` → PR's merge commit → `git tag --contains`). `community/
community.sh` is a read-only `gh`/`git` wrapper, verified structurally incapable of writing to
GitHub. Also corrected `README.md`'s false "tracked as milestones" claim (zero GitHub Milestones
exist on this repo) to point at `community/` instead. `engine.manifest` gained a `community/`
line. Full design rationale (why Discussions/Milestones were rejected, the verification
approach) in `MEMORY.md`'s `project_jobhuntkit` entry.

## Relationship to the private `job-hunt/` folder

Deliberately **not** dogfooded yet, and diverging by design rather than forking/syncing from day
one — see `[[project_jobhuntkit]]` for the reasoning. The leak-prevention mechanism
(`engine.manifest`-bounded `sync.sh` + `audit_public.py`) is now **built and verified** (see
Current state above), which is what makes eventually syncing the private folder to this engine
safe — the first real `sync.sh pull` was optional for this M4 pass and deliberately skipped
(2026-08-09), still last on the list whenever it does happen.

## End of Day Checklist

1. Commit all open changes on the current feature branch (never straight to `main`)
2. Push to remote once one exists
3. Update this file's "Current state" section if the milestone changed
4. Update `MEMORY.md` (`project_jobhuntkit`) if something stable and non-obvious changed
5. Update `Projects_Status.md`'s JobHuntKit row

---

> Last updated: 2026-08-09 (M4 scope narrowed to release essentials — build_paste_prompts.py and
> minimal-lean.md moved to Q-004/Q-005, extractor good-first-issues deleted and tracked as Q-003;
> Tier 1 real-bug fixes (cv-tailor.md --photo, CONTEXT.md ownership lists, build_cv.py duplicate-
> id message, engine.manifest); a full documentation-accuracy sweep across SPEC/CONFIG/NO-AI/
> README/GETTING-STARTED/CONTRIBUTING/AGENTS/templates headers, including fixing
> init_workspace.py's stale onboarding sequence; new docs/CUSTOMIZING.md + README pointer table;
> CHANGELOG.md + badges — all on `feat/m4-release-prep`, not yet merged to `dev`)
