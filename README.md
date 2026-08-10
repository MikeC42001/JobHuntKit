# JobHuntKit

[![CI](https://github.com/MikeC42001/JobHuntKit/actions/workflows/ci.yml/badge.svg)](https://github.com/MikeC42001/JobHuntKit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

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

## Or let an agent set it up

Every workflow here has agent instructions in [`AGENTS.md`](AGENTS.md), usable from Claude Code,
Cursor, Codex, or anything else that reads that filename convention. To go from nothing to a
working setup, paste this at an agent that can run shell commands:

```text
Clone https://github.com/MikeC42001/JobHuntKit and set it up for me.

Read `AGENTS.md` first, then follow `agents/cv-setup.md` to build my content layer.

Ask me for my real background before writing anything into my CV. Don't invent employers,
dates, or achievements. Leave a placeholder and ask me instead.
```

It will ask where your CV data should live, inside the clone or in its own directory, before
scaffolding anything.

Claude Code users can skip the prompt entirely: clone, then run `/cv-setup`.

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

**v0.1.0.** The full loop works end to end: build, validate, render, verify, stage. CI runs it on
Linux, macOS, and Windows. [CHANGELOG.md](CHANGELOG.md) has the detail.

Not built yet, deliberately:

- **Posting-change detection**, i.e. noticing when a job posting changes after you saved it.
- **More extractors.** `linkedin`, `plaintext`, and `generic` ship today; Greenhouse, Lever,
  Workday, and Indeed don't.

Both are open questions rather than a roadmap. They're weighed in
[`community/OPEN_QUESTIONS.md`](community/OPEN_QUESTIONS.md) before becoming issues, so that's
the place to say you want one.

## Running tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/
```

Pure-Python, no browser or Node.js needed, so the whole suite runs anywhere Python does. The
actual PDF rendering is exercised separately by CI's `render-matrix` job, which runs `demo.sh`
end to end on Linux and macOS.

### What the suite is protecting

The failure mode that matters here isn't a crash. It's a plausible-looking CV. A build that
quietly drops a job, reorders your history, or omits the one project the posting asked about
still produces a clean one-page PDF, and you would send it without noticing. Most of these tests
exist to make that specific kind of quiet wrongness loud:

- **Your output stays byte-identical unless you meant to change it.** `build_cv.py`'s output is
  diffed against a committed golden file, so refactoring the assembler can't silently reword a CV.
- **A broken CV fails instead of rendering.** `check_cv.py`'s fixtures feed it a reordered
  experience section, a dropped verbatim line, and a missing locked entry, then assert each one is
  caught rather than passed through. A related test pins that an unconfigured root prints
  `NOT CONFIGURED` instead of a falsely reassuring "all OK".
- **Personal data cannot leave your machine.** These are the load-bearing ones. They run the real
  `scripts/sync.sh` in a subprocess rather than a reimplementation of it, against a root holding
  fake private content, and assert that content never enters the audit's file list or a push
  destination, not merely that a rule rejected it.
- **Instructions written for agents are checked like code.** `agents/*.md` isn't executable, so a
  missing required flag or a renamed path in it has no coverage unless something greps for the
  claim. `tests/test_agents_docs.py` does, added after a shipped instruction file was found
  telling agents to run a command that exits 1 without a flag it never passed.

The rest is ordinary coverage: `init_workspace.py`, `scan_applications.py`,
`collect_cvs.py`/`collect_letters.py`, `extract_posting.py` and the extractor registry,
`md_to_email_txt.py`, `verify_cvs.py`, and `community/community.sh`'s read-only guarantee.

Run the suite before opening a pull request. CI runs the same one on Linux, macOS, and Windows,
plus `ruff`, `shellcheck`, and the leak gate.

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
`ruff check engine scripts tests .github` before a PR.

## License

MIT — see `LICENSE`. Bundled fonts (IBM Plex) are SIL OFL 1.1; see `NOTICE`.
