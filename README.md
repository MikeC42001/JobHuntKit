# JobHuntKit

A small, opinionated toolkit that turns one master CV and a per-posting selection file into a
validated, one-page, tailored PDF — markdown in, PDF out, no hand-copying, no drift between
applications.

![Sample generated CV](examples/demo/output/cv-minimal.png)

*(Robin Vale and Orbital Dynamics are fictional — the image above is a snapshot of `demo.sh`'s
output, committed at `examples/demo/output/` since `generate-pdfs/` itself is gitignored.)*

## Why

Hand-tailoring a CV per application means re-typing the same wording over and over, and it's
easy for one application to quietly lose an entry the others have. This toolkit inverts that:
you write your full background **once**, as a set of tagged blocks (a "master"), and a small
generator assembles each application's CV by selecting from it. A structural spine — entries
that must appear on every CV, in a fixed order — is enforced by a validator, not by memory.

It is deliberately opinionated: **one page, a locked spine, generated output you never
hand-edit.** If that's not the shape of CV you want, this probably isn't the tool for you — but
if it is, it removes an entire category of copy-paste mistakes.

## 60-second demo

```bash
git clone https://github.com/MikeC42001/JobHuntKit && cd JobHuntKit
bash demo.sh
```

That's it — no `pip install`, no config. It builds and renders a fictional CV for a fictional
persona ("Robin Vale," applying to a fictional company) using nothing but `python3`, `node`, and
whichever Chrome/Edge/Chromium/Brave you already have installed. Requirements: Python 3.8+, a
recent Node.js, and one Chromium-family browser. Windows users: run it from Git Bash.

## How it works

A chain, not two unrelated files: `master/master_cv.md` is the primary master — the complete
inventory, written as a real document. `master/master_cv_minimal.md` is a *condensation* of it —
same `@id`s, terser wording, one-page discipline. One `application.md` per company drives both:

```
master/master_cv.md                                    master/master_cv_minimal.md
(primary — complete inventory,          condensed to   (terser wording, same @id namespace)
 written as a real document)          ───────────────>
        │                                                       │
        ▼   templates/full.md                                  ▼   templates/minimal-full.md
        │   (roomier, generous by default)                      │   (one-page discipline)
        │                                                       │
        └──────────────────┬────────────────────────────────────┘
                            │
        applications/offer-pages/<Company>/application.md
        (the pitch: tagline, About me, which projects, what to omit and why —
         drives BOTH pipelines; opt into "full" via a "pipelines: minimal, full"
         front-matter key, default is "minimal" only)
                            │
              ┌─────────────┴─────────────┐
              ▼   engine/build_cv.py       ▼   engine/build_cv.py
   <Company>/cv-minimal.md                 <Company>/cv.md
              │                                         │
   engine/check_cv.py               engine/check_cv.py --pipeline full
              │                                         │
   engine/render_cv_minimal.sh    engine/render_cv.sh / render_cv_photo.sh
              ▼                                         ▼
   .../generate-pdfs/cv-minimal.pdf     .../generate-pdfs/cv.pdf · cv-photo.pdf
```

In one line: **`cv-minimal.pdf` is what you send; the full CV is what you have.**
`application.md` is the only file you hand-edit per application — every `cv*.md` and every
rendered PDF is generated; edit `application.md` and re-run instead of touching them, or the next
build silently overwrites your change.

There's also a simpler, build-free path for the full CV: `render_cv.sh`/`render_cv_photo.sh` are
**id-agnostic** — point either straight at `master/master_cv.md` (or any hand-written CV
markdown, no `@id` scheme required) and get a PDF, no `application.md`, no `build_cv.py` step.
Both strip `<!-- ... -->` comments themselves (so a master's `<!-- @id -->` markers never reach
the PDF) and honor a `<!-- render:stop -->` tag for anything that shouldn't render at all, like a
master's "Notes for tailoring" section. Use the built `cv.md` path when you want per-company
selection (`## Include`/`## Omit`, same as the tailored pipeline); point at the master directly
when you just want the whole thing, right now, no per-company anything.

There's no validator on the direct-render path — `check_cv.py` runs only where `@id`s exist,
i.e. on a built `cv-minimal.md`/`cv.md` (`--pipeline full` for the latter). See `docs/SPEC.md`'s
"The full CV — id-agnostic rendering" for the full contract.

## Quickstart with your own data

```bash
python scripts/init_workspace.py    # scaffolds config.json, master/, profile/, applications/,
                                     # templates/, images/, produced/ from templates/
```

Fill in `config.json`, `profile/background.md`, and `master/master_cv.md` (then condense it into
`master/master_cv_minimal.md` — same ids, terser wording), decide your locked spine, then
build/validate/render/verify the same way `demo.sh` does. Full walkthrough, in order:
**[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)**.

`--root` can point anywhere, including outside this checkout entirely — your own private repo,
for instance — so the engine never needs to touch your data directly:

```bash
python3 scripts/init_workspace.py --root ~/my-cv-data
python3 engine/build_cv.py --root ~/my-cv-data --all
```

Format contract (`@id` marker rules, `{{...}}` placeholder grammar, the locked-vs-optional spine
concept): [docs/SPEC.md](docs/SPEC.md). Every `config.json` key: [docs/CONFIG.md](docs/CONFIG.md).
Running the whole pipeline by hand, no agent involved: [docs/NO-AI.md](docs/NO-AI.md).

**Which file do I edit?**

| I want to change... | Edit |
|---|---|
| CV wording | `master/master_cv.md` first, then condense the same `@id` into `master_cv_minimal.md` |
| what one company's CV includes | that company's `application.md` (`## Include`/`## Omit`/`## Projects`) |
| which sections exist | `templates/minimal-full.md` / `templates/full.md` |
| the PDF's actual look | the matching `engine/render-support/cv2html*.js` |
| the default CV style | `config.json` → `render.default_style` |
| add a new PDF style | → [docs/CUSTOMIZING.md](docs/CUSTOMIZING.md) |

## Scripts

| Script | Does |
|---|---|
| `demo.sh` | Runs the whole pipeline end to end against `examples/demo/` — the 60-second demo above |
| `scripts/init_workspace.py` | Scaffolds a fresh data root from `templates/` — config.json, master/, profile/, applications/, templates/, images/, produced/ |
| `scripts/make_avatar.py` | One-off helper: draws a simple initials-in-a-circle placeholder avatar PNG, for anyone who wants a photo without a stock image or licensing question. Requires Pillow (`pip install pillow`), a dev-only dependency — not part of the render pipeline |
| `scripts/audit_public.py` | The leak gate — refuses to `sync.sh push` (and fails CI's `lint` job) if personal data, an unexpected binary, or an absolute path would leave the engine |
| `scripts/sync.sh` | Manifest-bounded `pull`/`push` between a canonical checkout and any data root — see `engine.manifest` |
| `scripts/install_hooks.sh` | Wires `audit_public.py` into a pre-commit hook (one-time, per clone) |
| `engine/scan_applications.py` | Classifies every company as NEW/CURRENT/STALE/SENT/DECLINED, independently for the CV and the cover letter |
| `engine/extract_posting.py` | Turns a saved job-posting page (or `.txt`/pasted text) into a skimmable dump, via the pluggable `engine/extractors/` registry — see `docs/EXTRACTORS.md` |
| `engine/build_cv.py` | Assembles `cv-minimal.md` (and `cv.md`, if `application.md` opts in — see `pipelines:` in `docs/CONFIG.md`) from a master + template + `application.md` |
| `engine/check_cv.py` | Validates the locked spine landed correctly (`structure`, the default) and reports what's present/omitted/silently-missing per application (`--coverage`); `--pipeline full` checks `cv.md` instead |
| `engine/verify_cvs.py` | Confirms a rendered PDF is exactly one page (or whatever `limits.max_pages`/`--max-pages` says; `--max-pages 0` disables the gate) — the default target glob is `cv-minimal.pdf` only |
| `engine/render_cv_minimal.sh` | Renders `cv-minimal.md` to a one-page PDF; `--photo` is required (or set `render.default_photo`); `--style a\|b\|c\|z` picks the CSS style, see `docs/CUSTOMIZING.md` |
| `engine/render_cv.sh` | Renders any CV markdown (built, a master, or hand-written) to a single-column, ATS-safe PDF — no build step, no photo |
| `engine/render_cv_photo.sh` | Same id-agnostic rendering, but two-column with a required circular photo — the full-CV companion to `render_cv_minimal.sh` |
| `engine/render_letter.sh` | Renders `cover_letter.md` to a clean, prose-only PDF — no `--photo`/`--style`, a letter has neither |
| `engine/md_to_email_txt.py` | Flattens a hand-wrapped cover letter into paste-ready plain email text |
| `engine/collect_cvs.py` | Stages rendered `cv-minimal.pdf`s into `produced/to_send/` for review (the full CV's `cv.pdf`/`cv-photo.pdf` have no collect step — review those from `generate-pdfs/` directly) |
| `engine/collect_letters.py` | Same, for one cover letter at a time — no bulk mode, by design |
| `engine/lib.sh` | Shared cross-platform browser discovery (`find_browser`), the headless print flags, and `config_get()` — sourced by every renderer |
| `engine/config.py` | Root resolution (`--root` / `$JOBHUNTKIT_ROOT` / walk-up) and `config.json` loading — imported by every Python script above |
| `engine/cv_common.py` | Shared helpers for the "is this sent/declined" folder-move convention, used by `scan_applications.py` and both `collect_*.py` scripts |
| `community/community.sh` | Read-only `gh`/`git` wrapper for `community/`'s open-question → issue → resolved lifecycle — see `community/README.md` |

## Status

Working: build, validate (structure + coverage), render, verify, and now onboarding — blank
starter templates, `scripts/init_workspace.py`, the published format contract
(`docs/SPEC.md`/`docs/CONFIG.md`/`docs/GETTING-STARTED.md`/`docs/NO-AI.md`), and portable agent
instructions (`agents/CONTEXT.md` + `agents/cv-setup.md`, wired up as a Claude Code skill/command
and a Cursor rule) — all cross-platform. `check_cv.py`'s locked spine, education requirements,
and verbatim-line checks are entirely `config.json`-driven; a fresh root with nothing configured
prints a clear "not configured" message rather than a false "all OK". A leak gate
(`scripts/audit_public.py`) and a manifest-bounded sync mechanism (`engine.manifest` +
`scripts/sync.sh`) are also in — `bash scripts/install_hooks.sh` wires the same check into a
pre-commit hook. Now also in: the full loop — `scan_applications.py` (what needs attention),
`extract_posting.py` + a pluggable `engine/extractors/` registry (`linkedin`, `plaintext`,
`generic` today; `docs/EXTRACTORS.md` is the how-to for adding one), `collect_cvs.py`/
`collect_letters.py` (staging finished PDFs for review), cover letters (`render_letter.sh`,
`md_to_email_txt.py`), and `agents/cv-tailor.md` wiring all of it into one agent-driven pass. A
109-test pytest suite covers all of the above (see Running tests below), and CI
(`.github/workflows/ci.yml`) runs it on every push across three jobs: `lint` (`ruff`, the leak
gate for real — not just the local pre-commit hook — and `shellcheck -x` on every tracked `.sh`
file), `test` (the pytest suite on ubuntu/macos/windows), and `render-matrix` (`node --check` on
every JS converter, then the real `demo.sh` on ubuntu and macOS, not just the Windows machine
this was built on). Now also in: the full-CV
pipeline — two masters (`master_cv.md` primary, `master_cv_minimal.md` its condensation, shared
`@id` namespace with an inheritance rule pinned by tests), a second `build_cv.py`/`check_cv.py`
pipeline (`cv.md`, same per-company selections as `cv-minimal.md`, opt in via an
`application.md`'s `pipelines:` front-matter key), and id-agnostic renderers
(`render_cv.sh`/`render_cv_photo.sh`) that clean their own input (comment stripping, a
`<!-- render:stop -->` tag) so a master file also renders directly with no build step at all.
`verify_cvs.py --max-pages` lets a multi-page artifact be checked (or the gate disabled
entirely) without touching the global one-page default. Not yet built: posting-change detection
(re-checking a saved posting after the fact). Extractors for Greenhouse/Lever/Workday/Indeed, a
generated ChatGPT-paste variant of the agent instructions, and a roomier spine-only template were
all considered and turned into open questions rather than decided work — see
[`community/OPEN_QUESTIONS.md`](community/OPEN_QUESTIONS.md). Open questions and proposed work
are tracked in [`community/`](community/), not GitHub Milestones (there aren't any) — see
`community/README.md` for the lifecycle and `community/community.sh` for reading it back from
the terminal.

## Running tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/
```

Pure-Python, no browser or Node.js needed — 109 tests across `build_cv.py` (golden-file diff
against `examples/demo/expected/`), `check_cv.py` (broken-spine fixtures, coverage math),
`audit_public.py`/`sync.sh` (leak-gate fixtures, plus an end-to-end check that a root's private
content never enters `sync.sh push`'s scanned or copied file list), `init_workspace.py`,
`scan_applications.py`, `collect_cvs.py`/`collect_letters.py`, `extract_posting.py` + the
extractor registry, `md_to_email_txt.py`, `verify_cvs.py`, `community/community.sh`'s read-only
guarantee, and content checks against the agent instruction files themselves (`agents/*.md`).

## Config

Everything person-specific lives in `config.json` (JSON, not YAML — no extra dependency to
parse it). Copy `config.example.json` to get started — it has every key `DEFAULT_CONFIG` does,
though `person.name`/`person.file_prefix` are placeholders to replace rather than real defaults
(see `docs/CONFIG.md`). At minimum you'll want those two, plus optionally `render.default_photo`.

## Requirements

- Python 3.8+ (stdlib only — no `pip install` for the engine itself)
- Node.js (the renderer installs its one dependency, `marked`, on first run)
- A Chromium-family browser — Chrome, Edge, Chromium, or Brave. Auto-detected; override with
  `BROWSER_BIN=/path/to/browser` or `render.browser_bin` in `config.json`.

## Privacy

The engine (`engine/`) never contains personal data — everything you write lives in a data
root that's resolved at runtime (`--root`, `$JOBHUNTKIT_ROOT`, or this checkout by default).
Nothing in this repo's history, other than the fictional demo persona, is real.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — the short version: never commit real CV data, run
`bash scripts/install_hooks.sh` once per clone, and `python -m pytest tests/` +
`ruff check engine scripts tests` before a PR.

## License

MIT — see `LICENSE`. Bundled fonts (IBM Plex) are SIL OFL 1.1; see `NOTICE`.
