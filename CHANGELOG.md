# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-08-10

First release. Everything below is new, since nothing shipped before this.

### Added

**Engine — the core build/validate pipeline**
- `engine/build_cv.py` — assembles a per-company `cv-minimal.md` (and, opt-in, `cv.md`) from a
  master + template + `application.md`. Dual-pipeline design: one `application.md` can build
  both the tailored one-pager and the long-form full CV via a `pipelines:` front-matter key.
- `engine/check_cv.py` — validates the locked spine landed correctly (structure mode) and
  reports present/omitted/silent items per application (`--coverage`), entirely driven by
  `config.json`'s `spine` block. `--pipeline full` runs the same checks against the full CV.
- `engine/verify_cvs.py` — confirms a rendered PDF is exactly one page by default;
  `--max-pages N` overrides per run, `0` disables the gate for the full CV's multi-page output.
- `engine/config.py` — root resolution (`--root` / `$JOBHUNTKIT_ROOT` / walk-up) and
  `config.json` loading, shared by every script.

**Rendering — four renderers, one style family**
- `engine/render_cv_minimal.sh` — the tailored one-pager, four visual styles (`--style
  a|b|c|z`), photo required.
- `engine/render_cv.sh` / `engine/render_cv_photo.sh` — id-agnostic full-CV renderers (no build
  step required): point either at a built `cv.md`, a master file, or any hand-written markdown.
  Single-column ATS-safe, or two-column with a circular photo.
- `engine/render_letter.sh` — cover letter rendering, prose-only.
- All four share `engine/lib.sh` (cross-platform browser discovery) and embed IBM Plex fonts as
  base64 `data:` URIs — no network request at render time, reproducible in CI.

**The full loop**
- `engine/scan_applications.py` — classifies every company as NEW/INCOMPLETE/CURRENT/STALE/
  ERROR, plus independent CV/letter sent/declined/pending state.
- `engine/extract_posting.py` + a pluggable `engine/extractors/` registry
  (`generic`/`plaintext`/`linkedin` shipped) — turns a saved posting page into something
  skimmable to hand-curate into `posting.md`.
- `engine/collect_cvs.py` / `engine/collect_letters.py` — stage rendered output into
  `produced/to_send/`; the "sent" signal is just a folder move, no database.
- `engine/md_to_email_txt.py` — flattens a cover letter into paste-ready plain text.

**Onboarding**
- `scripts/init_workspace.py` — scaffolds a fresh data root from `templates/`, safe to re-run,
  never overwrites anything that could hold personal data.
- Blank starter `templates/` (two masters, both CV templates, `CV_SPEC.md`, `background.md`,
  a worked `application.md` example).
- `docs/{SPEC,CONFIG,GETTING-STARTED,NO-AI,EXTRACTORS,CUSTOMIZING}.md` — the full format
  contract, every config key, a first-run walkthrough, running the pipeline entirely by hand,
  how to add a posting extractor, and which file to edit for content vs. structure vs. look.

**Agents**
- `agents/{CONTEXT,cv-setup,cv-tailor,interview-prep}.md` — portable instructions for an
  agentic coding tool, wired up as Claude Code skills/commands, a Cursor rule, and a generic
  `AGENTS.md` entry point. All pointer-based — one source of truth, no copies.

**Privacy — the mechanism that makes this project safe to develop in public**
- `engine.manifest` + `scripts/sync.sh` — a whitelist-bounded pull/push mechanism between a
  canonical checkout and any data root; content paths are structurally invisible to it.
- `scripts/audit_public.py` — the leak gate: refuses to push on any unexpected binary, email/
  phone outside a small allowlist, absolute path, or a term from a gitignored `.private-terms`
  wordlist. Enforced in CI (not just a local pre-commit hook) and by
  `scripts/install_hooks.sh`.

**Quality**
- 111 pytest tests, pure-Python, no browser/Node required — golden-file diffs, structure/
  coverage fixtures, leak-gate fixtures, scaffolding, scan/collect/extractor logic, and content
  checks against the agent instruction files themselves.
- CI (`.github/workflows/ci.yml`), three jobs: `lint` (`ruff`, the leak gate for real,
  `shellcheck -x` on every tracked shell script), `test` (the full suite on
  ubuntu/macos/windows), `render-matrix` (`node --check` on every JS converter, then the real
  `demo.sh` end to end on ubuntu and macOS).

**Community**
- `community/` — an issue-orchestration folder: a hand-written `OPEN_QUESTIONS.md` staging area
  before an idea becomes a public GitHub issue, then scoped work, then a resolution derived from
  `git tag --contains` on the closing PR's merge commit. `community/community.sh` reads it all
  back, structurally read-only.

[0.1.0]: https://github.com/MikeC42001/JobHuntKit/releases/tag/v0.1.0
