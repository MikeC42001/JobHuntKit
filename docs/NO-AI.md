# NO-AI.md — running the pipeline entirely by hand

Nothing about JobHuntKit requires an agent. Every step below is a plain command; `agents/cv-setup.md`
and `agents/cv-tailor.md` just automate the same judgment calls an agent is better suited to
(drafting prose, deciding what to include). Both paths produce the exact same files — they never
diverge in what's valid, only in who's typing.

All commands below run from the repo root (or wherever your root is, plus `--root <dir>` on
each). Needs `python3` and `node` on `PATH`, plus Chrome, Edge, Chromium, or Brave installed.
Close any PDF that's open in a viewer before rendering — the render scripts detect the file lock
and warn instead of silently failing to overwrite it.

## The current pipeline (M0–M3: scan, extract, build, validate, render, verify, stage)

```bash
# 0. Scan — what needs attention right now
python engine/scan_applications.py                                # full table, every company
python engine/scan_applications.py --target new                   # just the NEW ones, paths only
python engine/scan_applications.py --target stale                 # not-sent + stale only
python engine/scan_applications.py --target "<Company>"           # one company, by folder or display name

# 1. Extract — turn a saved posting page (or a .txt/pasted file) into something skimmable
python engine/extract_posting.py "applications/offer-pages/<Company>/<file>.html"
python engine/extract_posting.py --list-extractors                # see what's registered
python engine/extract_posting.py <file> --extractor linkedin       # force one, skip dispatch

# 2. Build — assembles cv-minimal.md from master + template + application.md
python engine/build_cv.py "applications/offer-pages/<Company>"   # one company
python engine/build_cv.py --all                                  # every company
python engine/build_cv.py --all --check                          # dry run — diffs only, writes nothing

# 3. Validate
python engine/check_cv.py "applications/offer-pages/<Company>"   # structure gate, one company
python engine/check_cv.py                                        # structure gate, every company
python engine/check_cv.py --coverage                             # what's present / omitted / SILENT

# 4. Render
bash engine/render_cv_minimal.sh --photo images/<photo>.png \
  "applications/offer-pages/<Company>/cv-minimal.md"

# 5. One-page gate
python engine/verify_cvs.py
python engine/verify_cvs.py "applications/offer-pages/<Company>/generate-pdfs/cv-minimal.pdf"

# 6. Stage — copy the finished PDF somewhere reviewable
python engine/collect_cvs.py                                     # everything not already sent
python engine/collect_cvs.py --force                             # re-copy everything, even sent
python engine/collect_cvs.py --force "<Company>"                 # re-copy just this one
```

Cover letters are a separate, optional track — see "Cover letters" below; they're not part of
the numbered sequence above because not every application needs one drafted through this tool.

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
- **`collect_cvs.py --force` never narrows the run** — it only decides whether companies already
  in `produced/sent/` get re-copied too. `--force` with no names re-copies everyone; `--force
  <names>` re-copies just those.
- **`--target stale`/`--target not-sent` exclude anything already SENT or DECLINED.** A
  SENT+STALE company is reported in the full scan table but never auto-targeted by either — name
  it directly (`--target "<Company>"`) if you want to rebuild it anyway.
- **A posting extractor can refuse.** `extract_posting.py`'s `linkedin` extractor raises instead
  of writing an empty `posting_extracted.md` when the saved page turns out to be a feed
  card/search-results snippet rather than the actual job page — re-save the right page, or pass
  `--extractor generic` if you want the raw dump anyway.

### Copy-paste recipe — one new company, chained

```bash
C="<Company>"
python engine/extract_posting.py "applications/offer-pages/$C/posting.html" && \
python engine/build_cv.py "applications/offer-pages/$C" && \
python engine/check_cv.py "applications/offer-pages/$C" && \
bash engine/render_cv_minimal.sh --photo images/<photo>.png "applications/offer-pages/$C/cv-minimal.md" && \
python engine/verify_cvs.py "applications/offer-pages/$C/generate-pdfs/cv-minimal.pdf" && \
python engine/collect_cvs.py --force "$C"
```

(Skip the `extract_posting.py` line if you already hand-wrote `posting.md` — extraction is only
needed when starting from a saved HTML page.)

### After any change to the master or a template

```bash
python engine/build_cv.py --all --check    # dry run first — see the blast radius before committing to it
python engine/build_cv.py --all
python engine/check_cv.py                  # structure gate, must pass (or print NOT CONFIGURED)
python engine/check_cv.py --coverage       # anything new: PRESENT or DELIBERATE, never SILENT
```

Lead with `--all --check` — the dry-run diff is the cheapest way to see exactly what a master
edit changes across every application before you commit to it. `engine/scan_applications.py`
reuses this same diff logic to classify every company as STALE, so a bare scan afterward tells
you at a glance which applications the edit actually touched.

## Cover letters

A cover letter has no template and no `@id` scheme — it's freehand prose, written directly as
`applications/offer-pages/<Company>/cover_letter.md`: a greeting paragraph, 2–4 body paragraphs, a
closing, then a signature block (name / contact line). Everything from a lone `---` line onward is
treated as internal draft/review notes and stripped before rendering — never reaches the PDF or
the email text.

```bash
bash engine/render_letter.sh "applications/offer-pages/<Company>/cover_letter.md"
python engine/collect_letters.py "<Company>"                     # exactly one company, no bulk mode
python engine/md_to_email_txt.py "applications/offer-pages/<Company>/cover_letter.md"  # optional: paste-ready plain text
```

`collect_letters.py` deliberately has no `--all`/bulk mode — letters are reviewed one company at a
time, on purpose. `render_letter.sh` takes no `--photo`/`--style`; a letter has neither.

## The full CV — no build step

`render_cv.sh` and `render_cv_photo.sh` render any CV markdown directly — a master file, a
hand-written file, or a built `cv-minimal.md`/`cv.md`. No `build_cv.py`, no `check_cv.py`, no
template. This is the long-form document you keep current, as opposed to the one-page, tailored
`cv-minimal.pdf` from the numbered sequence above.

```bash
bash engine/render_cv.sh "master/master_cv_minimal.md"                    # single-column, ATS-safe
bash engine/render_cv_photo.sh --photo images/<photo>.png \
  "master/master_cv_minimal.md"                                          # two-column, with photo
python engine/verify_cvs.py --max-pages 0 "master/generate-pdfs/cv.pdf"  # report page count, no gate
```

Both converters strip every `<!-- ... -->` comment themselves (a master's `<!-- @id -->` markers
never reach the PDF) and honor a `<!-- render:stop -->` tag — put one above any section that
shouldn't render at all, e.g. a master's `## Notes for tailoring`. See `docs/SPEC.md`'s "id-
agnostic rendering" section for the full contract. `--photo` on `render_cv_photo.sh` falls back
to `config.json`'s `render.default_photo`, same as `render_cv_minimal.sh`; `render_cv.sh` has no
`--photo` at all.

## Not yet built (planned for a later milestone)

- The rest of the extractor family — Greenhouse, Lever, Workday, Indeed (see
  `docs/EXTRACTORS.md`; filed as `good first issue`s). `linkedin`, `plaintext`, and `generic` are
  in.
- `scripts/build_paste_prompts.py` — a generated ChatGPT-paste variant of the agent instructions.
- `templates/minimal-lean.md` — a roomier, spine-only template variant.
- A dedicated `master/master_cv.md` + `templates/full.md` pair with its own `build_cv.py`
  pipeline (a `cv.md` built and validated per company, the way `cv-minimal.md` is today). For
  now `render_cv.sh`/`render_cv_photo.sh` work directly off `master_cv_minimal.md`.
- Posting-change detection (re-fetching or diffing a live posting after it's been saved). Genuine
  gap today — `extract_posting.py` records which extractor ran and when, but nothing re-checks a
  posting after that.

## "Sent" is just a folder move

`collect_cvs.py`/`collect_letters.py` stage a rendered PDF into `produced/to_send/`. Moving it from
there into `produced/sent/` (or `produced/not_sent/`, for "decided not to apply") *is* the sent/
declined signal every other script reads — nothing needs a database, and `scan_applications.py`'s
table reflects it on the very next run.
