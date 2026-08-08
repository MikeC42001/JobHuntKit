# agents/cv-tailor.md — scan, draft, build, validate, render, and stage tailored CVs

Read `agents/CONTEXT.md` first (root-finding, file ownership, never-auto-commit) — this file
assumes you've already done Step 0 there. Every command below runs from the root you found there;
paths are written relative to it.

Wraps `engine/scan_applications.py`, `engine/extract_posting.py`, `engine/build_cv.py`,
`engine/check_cv.py`, `engine/render_cv_minimal.sh`, `engine/verify_cvs.py`, and
`engine/collect_cvs.py` into one pass — the full loop from "what needs attention" to "a reviewed
PDF sitting in `produced/to_send/`."

**Argument:** the instruction's argument — optional. Resolve in this order:

1. Empty → default scope (see Step 1).
2. Exactly `all`, `not-sent`, or `stale` (case-insensitive) → force scope, see Step 1's table.
3. Exactly `render` (case-insensitive) → **Render-only mode**, every company (see below) —
   re-render existing `cv-minimal.md` files, no rebuild, no drafting.
4. Starts with `render ` followed by a company name → **Render-only mode**, just that company.
5. Starts with `http://` or `https://` → a URL for a brand-new posting (Step 2b).
6. Otherwise, check if it matches an existing company (folder or display name) via
   `engine/scan_applications.py --target "<argument>"` — if it matches, force-rebuild just that
   company.
7. If none of the above matched anything, treat the whole argument as pasted job-posting text for
   a brand-new posting (Step 2b) — not a URL, not a known company, so it must be posting content
   handed to you directly.

If genuinely ambiguous (e.g. a short string that isn't a known company and doesn't read like a
job posting), ask rather than guess.

---

## Render-only mode (`render` / `render <Company>`)

For when the *renderer* changed (CSS, a template, a font) but the *content* didn't — re-rendering
from scratch would be correct but wasteful, since nothing about `application.md` or the master
needs re-drafting or re-validating. Skips Steps 1–4 entirely: no scan-driven targeting, no intake,
no `build_cv.py`, no `check_cv.py`. Just re-render whatever `cv-minimal.md` files already exist on
disk, verify, and re-stage.

**`render` (every company):**

    ! python engine/scan_applications.py --target all

For each path printed, re-render:

    ! bash engine/render_cv_minimal.sh "<path>/cv-minimal.md"
    ! python engine/verify_cvs.py

Then re-stage everyone, forced (so an unchanged-since-last-collect PDF still gets re-copied with
its refreshed render):

    ! python engine/collect_cvs.py --force

**`render <Company>` (one company):**

    ! bash engine/render_cv_minimal.sh "applications/offer-pages/<Company>/cv-minimal.md"
    ! python engine/verify_cvs.py "applications/offer-pages/<Company>/generate-pdfs/cv-minimal.pdf"
    ! python engine/collect_cvs.py --force "<Company>"

**Report:** how many companies were re-rendered, any page-count failures from `verify_cvs.py`
(don't ignore these — a renderer change that pushes something to 2 pages is exactly what this
mode exists to catch), and confirmation PDFs are refreshed in `produced/to_send/`. No auto-commit.

---

## Step 1 — Scan

    ! python engine/scan_applications.py

Print the full table — this is the "is anything outdated relative to the master" signal worth
surfacing every run, independent of what actually gets touched this run.

Resolve the target list for this run:

| Argument | Target list |
|---|---|
| (empty) | every NEW company (from the table above) |
| `all` | every company with an `application.md` (CURRENT + STALE, sent or not) |
| `not-sent` | every company with an `application.md` that is not sent (any staleness) |
| `stale` | `engine/scan_applications.py --target stale` (not-sent + stale only — a sent+stale company is reported but never auto-targeted this way) |
| `<Company>` | just that one company (get its path via `engine/scan_applications.py --target "<Company>"`) |
| URL or pasted text | the brand-new posting from Step 2b, **plus** every NEW folder-based company (same as the empty-argument default — a paste never suppresses the folder scan) |

If the resolved target list is empty, report "nothing to do" and stop — don't run the later steps
for no reason.

## Step 2a — Intake: folder-based NEW companies

For each company `scan_applications.py` classified NEW (has raw content, no `application.md`
yet):

1. If the raw content is a saved HTML file (not `posting.md`/`posting_extracted.md` already),
   run:

       ! python engine/extract_posting.py "applications/offer-pages/<Company>/<file>.html"

   Read the resulting `posting_extracted.md` — it's a rough dump, not a clean extraction (the
   `linkedin` extractor strips known nav/sidebar chrome when it recognizes a real job-details
   page, but still leaves the actual role content mixed with some page noise; the `generic`
   fallback strips nothing site-specific at all). If the extractor refused with an error (a saved
   LinkedIn *feed card* instead of the real job page is the known case — see
   `docs/EXTRACTORS.md`), tell the person and ask for the right page instead of guessing. If
   `posting.md` doesn't exist yet, write it: a clean, curated summary in the same style as any
   existing `posting.md` in this root (company/role/work-arrangement/salary/seniority header,
   then the actual requirements).
2. Continue to Step 3 (drafting `application.md`) for this company.

## Step 2b — Intake: a brand-new posting from the argument (URL or pasted text)

Only runs when the argument was a URL or pasted posting text (see the argument resolution above).

1. If it's a URL, fetch it to get the posting content. If it's pasted text, use it directly.
2. Infer the company name and role from the content. Create
   `applications/offer-pages/<Company>/` (name it the way the company brands itself — existing
   folders in this root may not agree on a casing convention, so match whatever's already there
   if unsure).
3. Write `posting.md` — same curated-summary convention as any existing one.
4. Continue to Step 3 for this company.

## Step 3 — Draft application.md (every NEW company from 2a/2b)

Follow `docs/SPEC.md` and, if this root has one, `master/CV_SPEC.md` exactly — this is the same
judgment work already done for every existing company, repeated per new one:

1. Read `posting.md`, `profile/background.md` (especially any "what this shows for a CV/
   application" notes), and any target-roles or preferences file the root has, if one exists.
2. Write `applications/offer-pages/<Company>/application.md`: front matter (`template:`, the
   name of whichever template this root uses — `minimal-full` for the starter, `company:`,
   `role:`), then the fields the template's `docs/SPEC.md` documents — typically Tagline, About
   me, Contact suffix, `## Projects` (from the master's `@proj-*` blocks, framed for this
   posting), Skills (selected from `background.md`'s inventory, front-loaded to the posting's
   stack), plus any configurable field the master defines (e.g. dissertation depth).
3. Declare **every** unused optional/project item in `## Omit` with a one-line reason — never
   leave one undeclared (that's what `check_cv.py --coverage`'s SILENT category exists to catch).
   If an optional entry or volunteer work should appear, add it to `## Include` instead.
4. Add a row to `applications/README.md`'s tracker (status `drafting`).

## Step 4 — Build + validate

For every target company (NEW ones just drafted, plus any forced by the argument):

    ! python engine/build_cv.py "applications/offer-pages/<Company>"
    ! python engine/check_cv.py "applications/offer-pages/<Company>"

Then a coverage check across the whole batch:

    ! python engine/check_cv.py --coverage

Every company just drafted must show **zero SILENT** items. If one shows up, go back to Step 3
and either include or explicitly omit it — don't leave the run with an undeclared gap.

## Step 5 — Render + verify

For every target company:

    ! bash engine/render_cv_minimal.sh "applications/offer-pages/<Company>/cv-minimal.md"

Then verify page count for just this run's targets:

    ! python engine/verify_cvs.py applications/offer-pages/<Company1>/generate-pdfs/cv-minimal.pdf applications/offer-pages/<Company2>/generate-pdfs/cv-minimal.pdf ...

If any company isn't exactly one page, that's a real problem — go back and trim (fewer projects,
shorter About me), don't ignore it.

## Step 6 — Stage

    ! python engine/collect_cvs.py --force <Company1> <Company2> ...

Force-list exactly this run's targets, so a brand-new company gets copied to `produced/to_send/`
even though it was never "sent" before, and a forced not-sent/stale rebuild re-copies even if
`collect_cvs.py`'s own mtime check would otherwise call it unchanged.

## Step 6b — Optional: draft a cover letter (one company at a time, never automatic)

Not part of the default run — only offer this per company, and only after its CV is built,
validated, and rendered. Cover letters have no template and no `@id` scheme: they're freehand
prose written directly as `applications/offer-pages/<Company>/cover_letter.md` (greeting, 2–4
body paragraphs, closing, then a `Best regards,` / name / contact signature block, then a `---`
divider and any draft notes — everything from that divider onward is stripped at render time, see
`docs/SPEC.md`).

If asked to draft one:

1. Write `cover_letter.md`, grounded in `posting.md` and this company's `application.md` — don't
   just restate the CV, make the case for why this posting specifically.
2. Render and stage it, one company at a time (matches `collect_letters.py`'s own one-at-a-time
   design — never batch this):

       ! bash engine/render_letter.sh "applications/offer-pages/<Company>/cover_letter.md"
       ! python engine/collect_letters.py "<Company>"

3. If a plain-text version for pasting into an email body is useful, offer:

       ! python engine/md_to_email_txt.py "applications/offer-pages/<Company>/cover_letter.md"

## Step 6c — Optional: render the full CV (not tied to any one company, never automatic)

Not part of the default run. This is upkeep on the long-form CV — the document handed to
someone directly, as opposed to a per-posting `cv-minimal.pdf` — so it only makes sense to offer
after a master edit, not as part of tailoring a specific application.

If asked to render it:

    ! bash engine/render_cv.sh "master/master_cv_minimal.md"
    ! bash engine/render_cv_photo.sh --photo images/<photo>.png "master/master_cv_minimal.md"

Both take any CV markdown directly — no `build_cv.py`, no `check_cv.py`, no template. They clean
their own input (strip `<!-- ... -->` comments, honor a `<!-- render:stop -->` tag — see
`docs/SPEC.md`'s "id-agnostic rendering" section), so pointing either at the master works with no
assembly step. There's nothing to verify against a page-count gate by default; if asked, report
the page count without failing on it:

    ! python engine/verify_cvs.py --max-pages 0 "master/generate-pdfs/cv.pdf"

## Step 7 — Report

One summary, not a play-by-play:

- New companies drafted (with a one-line note on the angle each was framed with).
- Stale/forced companies rebuilt, if any were targeted, and *why* they were stale (application.md
  edit vs. master content change — `scan_applications.py`'s diff makes this visible if you look at
  it, worth calling out which).
- The full staleness FYI list from Step 1, even for companies not touched this run.
- Coverage result (should be 0 SILENT for anything drafted this run).
- Where the PDFs landed (`produced/to_send/`) and that the person should review them before
  sending — this instruction never sends anything itself.
- Any cover letters drafted this run (Step 6b), if that was asked for.
- Whether the full CV was re-rendered this run (Step 6c), if that was asked for.

No auto-commit. Git stays manual — mention what changed so the person can review before
committing.
