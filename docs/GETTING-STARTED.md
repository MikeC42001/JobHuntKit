# Getting started

This walks through going from a fresh clone to your own first tailored CV. If you just want to
see the mechanism work first, `bash demo.sh` runs the whole pipeline on a fictional persona in
about a minute — no setup required, and a good way to sanity-check your machine (Python, Node,
a Chromium-family browser) before touching your own data.

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
  already `.gitignore`d here (verified — see `docs/SPEC.md`'s "who owns what"), so `git status`
  stays clean and none of it can accidentally get committed to this repo. If you `git pull`
  engine updates later, your data sits right alongside the code being updated, which is fine as
  long as you know that's the shape.
- **`--root` pointing outside the checkout** (your own private repo, a synced folder, anywhere)
  fully decouples data from code. This is the right choice if you intend to `git pull` engine
  updates regularly and want zero chance of the two tangling. Every command below still works —
  just add `--root <your dir>` to each one, or `export JOBHUNTKIT_ROOT=<your dir>` once per
  shell so you don't have to repeat it.

`init_workspace.py` is safe to re-run any time — it never overwrites a file that could hold your
data, and reports what it skipped. `--check` previews what it would do without writing anything.

## 2. Fill in the basics

In the order the script's own "Next" output suggests:

1. **`config.json`** — at minimum, `person.name` and `person.file_prefix` (used to name output
   files). Leave `spine` empty for now — you'll come back to it in step 4.
2. **`profile/background.md`** — write down everything about your background, raw and
   unstructured. Nothing parses this file; it's your own raw material for step 3. See
   `docs/CONFIG.md` for what feeds off `config.json` instead.
3. **`master/master_cv_minimal.md`** — distil `background.md` into `@id`-tagged blocks. The file
   has a worked comment on every block explaining what it's for; the full marker syntax is in
   `docs/SPEC.md`. This is the file every generated CV pulls locked content from.

If you'd rather have an agent do steps 2–3 as a guided conversation instead of writing them by
hand, see `agents/cv-setup.md` (Bootstrap mode) — it walks through the same decisions
interactively, including the locked-spine question in step 4 below.

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

## What's next

- Full format reference, once you're past the basics: `docs/SPEC.md`.
- Every `config.json` key explained: `docs/CONFIG.md`.
- Running the whole pipeline by hand, no agent involved: `docs/NO-AI.md`.
- Contributing back to the engine itself: `CONTRIBUTING.md`.
