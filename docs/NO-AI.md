# NO-AI.md — running the pipeline entirely by hand

Nothing about JobHuntKit requires an agent. Every step below is a plain command; `agents/cv-setup.md`
and (eventually) `agents/cv-tailor.md` just automate the same judgment calls an agent is better
suited to (drafting prose, deciding what to include). Both paths produce the exact same files —
they never diverge in what's valid, only in who's typing.

All commands below run from the repo root (or wherever your root is, plus `--root <dir>` on
each). Needs `python3` and `node` on `PATH`, plus Chrome, Edge, Chromium, or Brave installed.
Close any PDF that's open in a viewer before rendering — the render scripts detect the file lock
and warn instead of silently failing to overwrite it.

## The current pipeline (M0–M2: build, validate, render, verify)

```bash
# 1. Build — assembles cv-minimal.md from master + template + application.md
python engine/build_cv.py "applications/offer-pages/<Company>"   # one company
python engine/build_cv.py --all                                  # every company
python engine/build_cv.py --all --check                          # dry run — diffs only, writes nothing

# 2. Validate
python engine/check_cv.py "applications/offer-pages/<Company>"   # structure gate, one company
python engine/check_cv.py                                        # structure gate, every company
python engine/check_cv.py --coverage                             # what's present / omitted / SILENT

# 3. Render
bash engine/render_cv_minimal.sh --photo images/<photo>.png \
  "applications/offer-pages/<Company>/cv-minimal.md"

# 4. One-page gate
python engine/verify_cvs.py
python engine/verify_cvs.py "applications/offer-pages/<Company>/generate-pdfs/cv-minimal.pdf"
```

Load-bearing details, easy to miss on a first read:

- **Zero SILENT items is the bar** for anything you just drafted. If `check_cv.py --coverage`
  shows one, go back and either include the item or explicitly declare it in `## Omit` with a
  one-line reason — don't leave a run with an undeclared gap.
- **If the rendered PDF isn't exactly one page, trim** (fewer projects, a shorter About me) —
  don't ignore it or fight the margins instead.
- **`cv-minimal.md` and every rendered PDF are build artifacts.** A hand-edit is silently
  overwritten by the next `build_cv.py`/render pass — edit `application.md`, never the generated
  file.
- **`check_cv.py --coverage` always exits 0.** SILENT is a prompt to decide, not a hard gate —
  only structure mode (no `--coverage`) fails the exit code.
- **`--photo` is required on `render_cv_minimal.sh`**, with no default unless you've set
  `config.json`'s `render.default_photo`.

### Copy-paste recipe — one new company, chained

```bash
C="<Company>"
python engine/build_cv.py "applications/offer-pages/$C" && \
python engine/check_cv.py "applications/offer-pages/$C" && \
bash engine/render_cv_minimal.sh --photo images/<photo>.png "applications/offer-pages/$C/cv-minimal.md" && \
python engine/verify_cvs.py "applications/offer-pages/$C/generate-pdfs/cv-minimal.pdf"
```

### After any change to the master or a template

```bash
python engine/build_cv.py --all --check    # dry run first — see the blast radius before committing to it
python engine/build_cv.py --all
python engine/check_cv.py                  # structure gate, must pass (or print NOT CONFIGURED)
python engine/check_cv.py --coverage       # anything new: PRESENT or DELIBERATE, never SILENT
```

Lead with `--all --check` — the dry-run diff is the cheapest way to see exactly what a master
edit changes across every application before you commit to it.

## Not yet built (planned for a later milestone)

The following are part of the toolkit's design but don't exist yet — don't expect these
commands to work today:

- `engine/scan_applications.py` — classifies each company folder as NEW/CURRENT/STALE/SENT so
  you know what needs attention without checking each one by hand.
- `engine/extract_posting.py` + `engine/extractors/` — turns a saved job-posting page into a
  clean, curated `posting.md`.
- `engine/collect_cvs.py` / `engine/collect_letters.py` — stages finished PDFs into a
  `produced/to_send/` folder for review before you actually send anything.
- Cover letters (`engine/render_letter.sh`, `engine/md_to_email_txt.py`).

Until then, the four commands in "The current pipeline" above are the complete loop: write
`application.md` by hand (see `docs/SPEC.md` for the exact syntax), build, validate, render,
verify.

## "Sent" is just a folder move

Once staging (`collect_cvs.py`) exists, moving a PDF between `produced/to_send/` and
`produced/sent/` *is* the sent/not-sent signal other scripts read — nothing needs a database.
Today, without that script, tracking is entirely up to `applications/README.md` (created by
`init_workspace.py` as an empty table) — update it yourself as you apply.
