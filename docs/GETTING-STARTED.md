# Getting started

This walks through going from a fresh clone to your own first tailored CV. If you just want to
see the mechanism work first, `bash demo.sh` runs the whole pipeline on a fictional persona in
about a minute — no setup required, and a good way to sanity-check your machine before touching
your own data.

Before any of it: you need Python 3.8+, Node.js 22+, and a Chromium-family browser, and on Windows
you need to be in Git Bash. `bash scripts/preflight.sh` tells you where you stand;
[INSTALL.md](INSTALL.md) covers getting there per platform.

## 1. Choose where your data lives

```bash
git clone <this repo> && cd JobHuntKit
python scripts/init_workspace.py                      # root = this checkout (fast path)
# or:
python scripts/init_workspace.py --root ~/my-cv-data  # root = anywhere else
```

Two honest tradeoffs, pick the one that fits:

- **Root = this checkout** (no `--root`) is the fastest path — one command, nothing to remember
  afterward, every following command in this guide works with no `--root` flag. The cost:
  `master/`, `profile/`, `applications/`, `produced/`, `images/`, and `config.json` are all
  already `.gitignore`d here (see `.gitignore` at the repo root), so `git status` stays clean and
  none of it can accidentally get committed to this repo. If you `git pull` engine updates later,
  your data sits right alongside the code being updated, which is fine as long as you know
  that's the shape.
- **`--root` pointing outside the checkout** (your own private repo, a synced folder, anywhere)
  fully decouples data from code. This is the right choice if you intend to `git pull` engine
  updates regularly and want zero chance of the two tangling. **You only pass `--root` once**:
  `init_workspace.py` remembers it in `.jobhuntkit-root` (gitignored) and later commands find it
  on their own. To override for a single command, pass `--root` again; to point a whole shell
  somewhere else, `export JOBHUNTKIT_ROOT=<your dir>`; to forget it entirely, delete
  `.jobhuntkit-root`.

Whenever the root isn't the plain default, commands print one line saying which rule chose it —
an env var or a remembered pointer is otherwise invisible at the call site, and the pointer
survives reboots.

### How a root is identified

Every root contains a `.jobhuntkit` marker file holding the constant `jobhuntkit-root/1`. That,
not the presence of `config.json`, is what makes a directory a root — `config.json` is far too
common a filename, and keying on it meant any unrelated project containing one could be claimed
as your root. `init_workspace.py` writes the marker, including into an older root that predates
it (a one-time upgrade, reported when it happens).

`init_workspace.py` is safe to re-run any time — it never overwrites a file that could hold your
data, and reports what it skipped. `--check` previews what it would do without writing anything.

## 2. Fill in the basics

In the order the script's own "Next" output suggests:

1. **`config.json`** — at minimum, `person.name` and `person.file_prefix` (used to name output
   files). Leave `spine` empty for now — you'll come back to it in step 4.
2. **`profile/background.md`** — write down everything about your background, raw and
   unstructured. Nothing parses this file; it's your own raw material for step 3. See
   `docs/CONFIG.md` for what feeds off `config.json` instead.
3. **`master/master_cv.md`** — the primary master: distil `background.md` into `@id`-tagged
   blocks, full wording, no length pressure — this is the complete record. The file has a worked
   comment on every block explaining what it's for; the full marker syntax is in `docs/SPEC.md`.
4. **`master/master_cv_minimal.md`** — condense the same blocks, same `@id`s, terser wording.
   This is the file the tailored one-page pipeline pulls locked content from. The full-CV
   pipeline (built via `application.md`'s `pipelines:` key) reads the full master from step 3;
   `render_cv.sh`/`render_cv_photo.sh` are id-agnostic and render whatever file you point them
   at — either master, a built `cv.md`, or a hand-written file with no `@id` scheme at all.

If you'd rather have an agent do steps 2–4 as a guided conversation instead of writing them by
hand, see `agents/cv-setup.md` (Bootstrap mode) — it walks through the same decisions
interactively, including the locked-spine question in the next step below.

## 3. Decide what's locked

**This is the one genuinely consequential decision in the whole setup.** Open
`master/CV_SPEC.md` and answer: which 1–4 entries should *always* appear on every CV this
generates, no exceptions? Write them down there, then mirror the decision into `config.json`'s
`spine.locked_order` (the ids) and `spine.education.required_titles` (education entries, by
rendered title text, not id).

A locked spine is what keeps every future CV consistent instead of drifting the way
hand-copied ones do — once it's set, `check_cv.py` can actually verify something instead of
trusting you to remember. It's fine to leave it short; there's nothing special about any
particular count.

## 4. Your first application

`init_workspace.py` already created a placeholder at
`applications/offer-pages/Example Company/application.md` so the commands below have something
to work on immediately. Rename that folder to your first real posting and edit its
`application.md` (full syntax: `docs/SPEC.md`), or delete it and write your own from
`templates/application.md`'s shape.

```bash
python engine/build_cv.py --all             # assembles cv-minimal.md for every application
python engine/check_cv.py                   # validates the locked spine actually landed
```

Right after step 3, `check_cv.py` may still print `NOT CONFIGURED` — that's correct, not a bug.
It means `config.json`'s `spine` block is still effectively empty (see
`Config.spine_configured` in `engine/config.py`), and the checker deliberately refuses to claim
"all OK" while it isn't actually checking anything. Once `spine.locked_order` (or
`required_titles`, or `verbatim_ids`) has at least one entry, this becomes a real gate.

## 5. Render and verify

```bash
bash engine/render_cv_minimal.sh --photo images/me.png "applications/offer-pages/<Company>/cv-minimal.md"
python engine/verify_cvs.py
```

`--photo` is required — put a photo anywhere under `images/` first (that directory is also
gitignored at the default root). `verify_cvs.py` confirms the rendered PDF is exactly one page
(or whatever `config.json`'s `limits.max_pages` says); if it isn't, trim content (fewer
projects, a shorter About me) rather than shrinking margins.

Four visual variants exist for this renderer — `--style a|b|c|z` (default `a`), each a
different CSS treatment of the same content. See `docs/CUSTOMIZING.md` for what each looks like
and how to add another.

## 6. Optional: the full CV

The tailored, one-page `cv-minimal.pdf` above is what you send per application. If you also want
a long-form CV — the complete record, no page budget — point a renderer straight at the master
you wrote in step 3, no build step needed:

```bash
bash engine/render_cv.sh "master/master_cv.md"                              # single-column, ATS-safe
bash engine/render_cv_photo.sh --photo images/me.png "master/master_cv.md"  # two-column, with photo -> cv-photo.pdf
```

If you'd rather have it built and validated per company the same way `cv-minimal.md` is (using
the same `application.md` selections), add `pipelines: minimal, full` to that company's front
matter and re-run `engine/build_cv.py` — this also writes `cv.md`, which needs its own checks
before rendering, since the two commands in step 4 only validate `cv-minimal.md`:

```bash
python engine/check_cv.py --pipeline full "applications/offer-pages/<Company>"
bash engine/render_cv.sh "applications/offer-pages/<Company>/cv.md"
python engine/verify_cvs.py --max-pages 0 "applications/offer-pages/<Company>/generate-pdfs/cv.pdf"
```

`--max-pages 0` disables the one-page gate — the full CV has no page budget by design, so
`verify_cvs.py` here just reports the count instead of failing it. See `docs/CONFIG.md`'s
`pipelines` section for the config, and `docs/NO-AI.md`'s "The full CV" for the complete rundown.

## What's next

- Full format reference, once you're past the basics: `docs/SPEC.md`.
- Every `config.json` key explained: `docs/CONFIG.md`.
- Running the whole pipeline by hand, no agent involved: `docs/NO-AI.md`.
- Changing how the PDF looks, or adding a posting-source extractor: `docs/CUSTOMIZING.md` and
  `docs/EXTRACTORS.md`.
- Open questions and proposed work that aren't decided yet: `community/OPEN_QUESTIONS.md`.
- Contributing back to the engine itself: `CONTRIBUTING.md`.
