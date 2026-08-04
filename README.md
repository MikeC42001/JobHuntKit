# JobHuntKit

A small, opinionated toolkit that turns one master CV and a per-posting selection file into a
validated, one-page, tailored PDF — markdown in, PDF out, no hand-copying, no drift between
applications.

![Sample generated CV](examples/demo/output/cv-minimal.png)

*(Robin Vale and Orbital Dynamics are fictional — the image above is `demo.sh`'s output.)*

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

```
master/master_cv_minimal.md   (everything you could say, tagged with @id blocks)
templates/minimal-full.md     (which slots exist, in what order, which are locked)
applications/offer-pages/<Company>/application.md
                               (the pitch for this one posting — tagline, About me,
                                which projects, what to omit and why)
        │
        ▼   engine/build_cv.py
applications/offer-pages/<Company>/cv-minimal.md
        │
        ▼   engine/render_cv_minimal.sh
applications/offer-pages/<Company>/generate-pdfs/cv-minimal.pdf
```

`application.md` is the only file you hand-edit per application. `cv-minimal.md` and the PDF
are generated — edit `application.md` and re-run instead of touching them, or the next build
silently overwrites your change.

## Quickstart with your own data

Blank starter templates and a guided setup flow are on the roadmap (see Status below); for now,
`examples/demo/` is also the fastest way to start your own — it's a complete, working root, so
copying it and replacing the content is a working starting point today:

```bash
cp -r examples/demo my-cv-data
cd my-cv-data
$EDITOR config.json                        # your name, contact prefix, photo, locked spine
$EDITOR master/master_cv_minimal.md         # your own @id-tagged background
$EDITOR templates/minimal-full.md           # only if you need slots the demo doesn't have
# replace applications/offer-pages/Orbital Dynamics/ with your own applications/offer-pages/<Company>/
cd ..
python3 engine/build_cv.py --root my-cv-data "my-cv-data/applications/offer-pages/<Company>"
python3 engine/check_cv.py --root my-cv-data     # confirms your locked spine actually landed
bash engine/render_cv_minimal.sh --root my-cv-data "my-cv-data/applications/offer-pages/<Company>/cv-minimal.md"
python3 engine/verify_cvs.py --root my-cv-data
```

`--root` can point anywhere, including outside this checkout entirely — your own private repo,
for instance — so the engine never needs to touch your data directly:

```bash
python3 engine/build_cv.py --root ~/my-cv-data --all
```

The `@id` marker rules, the `{{...}}` placeholder grammar, and the locked-vs-optional spine
concept are documented inline in `examples/demo/templates/minimal-full.md`'s header comment and
`examples/demo/master/CV_SPEC.md` — read those before writing your own until the standalone docs
land.

## Scripts

| Script | Does |
|---|---|
| `engine/build_cv.py` | Assembles `cv-minimal.md` from the master + template + `application.md` |
| `engine/check_cv.py` | Validates the locked spine landed correctly (`structure`, the default) and reports what's present/omitted/silently-missing per application (`--coverage`) |
| `engine/verify_cvs.py` | Confirms a rendered PDF is exactly one page (or whatever `limits.max_pages` says) |
| `engine/render_cv_minimal.sh` | Renders `cv-minimal.md` to a one-column PDF with a circular photo |
| `engine/lib.sh` | Shared cross-platform browser discovery, sourced by the renderers |

## Status

Working: build, validate (structure + coverage), render, verify — on a fictional demo persona,
cross-platform. `check_cv.py`'s locked spine, education requirements, and verbatim-line checks
are entirely `config.json`-driven; a fresh clone with nothing configured prints a clear
"not configured" message rather than a false "all OK". A leak gate (`scripts/audit_public.py`)
and a manifest-bounded sync mechanism (`engine.manifest` + `scripts/sync.sh`) are also in —
`bash scripts/install_hooks.sh` wires the same check into a pre-commit hook. Not yet built:
a formal test suite + CI, posting scanning and staging, cover letters, blank starter templates
for your own data, agent instructions (Claude Code / Cursor / ChatGPT), and pluggable posting
extractors for sites beyond a plain saved HTML page. Tracked as milestones in this repo's issues.

## Config

Everything person-specific lives in `config.json` (JSON, not YAML — no extra dependency to
parse it). Copy `config.example.json` to get started — it lists every key with its default.
At minimum you'll want `person.name`, `person.file_prefix`, and optionally `render.default_photo`.

## Requirements

- Python 3.8+ (stdlib only — no `pip install` for the engine itself)
- Node.js (the renderer installs its one dependency, `marked`, on first run)
- A Chromium-family browser — Chrome, Edge, Chromium, or Brave. Auto-detected; override with
  `BROWSER_BIN=/path/to/browser` or `render.browser_bin` in `config.json`.

## Privacy

The engine (`engine/`) never contains personal data — everything you write lives in a data
root that's resolved at runtime (`--root`, `$JOBHUNTKIT_ROOT`, or this checkout by default).
Nothing in this repo's history, other than the fictional demo persona, is real.

## License

MIT — see `LICENSE`. Bundled fonts (IBM Plex) are SIL OFL 1.1; see `NOTICE`.
