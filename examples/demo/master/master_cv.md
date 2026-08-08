<!-- @header-name -->
# Robin Vale

<!-- @header-location -->
Rivertown, Meridia

<!-- @header-phone -->
(+1) 555 010 2938

<!-- @header-email -->
robin.vale@example.com

<!-- @header-linkedin -->
[linkedin.com/in/robin-vale](https://www.linkedin.com/in/robin-vale)

> The primary master — the complete inventory, written as a real document you could hand
> someone directly (see `engine/render_cv.sh`/`render_cv_photo.sh` — no build step required to
> render this file as-is). `master_cv_minimal.md` is a *condensation* of this file: every
> `<!-- @id -->` here also exists there, just in terser wording.

## About me

Software engineer who likes taking a rough, half-automated process and turning it into something
reliable and boring. Four years maintaining a production scheduling app used daily by roughly 40
internal staff, plus a handful of small self-directed tools built solo on weekends — an
inventory tracker for a friend's bakery, an open-source status-page generator, and a couple of
smaller experiments that never went anywhere but taught something anyway.

<!-- Not IDed — About me is fully configurable per application, never copied verbatim. This is
the example/fallback wording only. -->

## Education

<!-- @edu-bsc -->
**BSc, Computer Science — Rivertown University** | 2016–2019 · 3y
- Coursework emphasis on distributed systems and databases; capstone project was a small
  peer-to-peer file-sync tool, the first thing that got me interested in the self-directed work
  below.

## Experience

<!-- LOCKED ORDER — see CV_SPEC.md: self-directed, then the current role. Mirrors
master_cv_minimal.md's order; this file additionally carries an earlier internship the minimal
condensation never mentions — see @exp-first-internship below. -->

<!-- @exp-self-directed -->
**Independent Projects — self-directed** | 2022–present · ongoing

<!-- @proj-inventory-tool -->
- Small inventory-tracking web app for a local bakery, replacing a shared spreadsheet (React,
  Node.js, PostgreSQL), solo — from initial interview with the owner about what the spreadsheet
  kept getting wrong, through to a deployed tool still in daily use two years later.

<!-- @proj-status-page -->
- Open-source status-page generator that turns a YAML config into a static site (Python,
  Jinja2), maintained solo with occasional outside contributions — three merged PRs from people
  who found it useful enough to fix their own bugs in.

<!-- Pick 1–2 most relevant when tailoring. Not an @id — this is guidance for application.md,
not renderable content. -->

<!-- @exp-current-role -->
**Software Engineer — Meridian Systems** | Mar 2020–present · 4y · Rivertown (hybrid)
- Maintains and extends a logistics-scheduling web app used by roughly 40 internal staff.
- Introduced automated testing to a previously untested codebase, cutting regression bugs
  reported per release by half.
- Led the migration off a deprecated internal auth library, coordinating with three other teams
  whose services depended on it — zero downtime, zero rollback.

<!-- Unconditional here (not gated by ## Include/## Omit the way templates/minimal-full.md gates
it via templates/full.md) — the full CV is generous by default: no page budget means nothing
needs trimming just to fit. -->
<!-- @exp-course-tutor -->
**Peer Tutor — Rivertown University** | Sep 2018–May 2019 · 4h/week
- Ran weekly study sessions for first-year programming students, focused on the concepts that
  trip people up in their first semester (recursion, pointers, why a for-loop off-by-one bug is
  so easy to make and so hard to see).

<!-- FULL-ONLY — no minimal condensation exists for this id; the complete work history can carry
entries a tailored one-pager never would. -->
<!-- @exp-first-internship -->
**Junior Developer Intern — Local Web Shop** | Jun 2018–Aug 2018 · 3mo
- First paid programming work: small WordPress sites and a handful of PHP bug fixes for local
  business clients. Kept for completeness — it's where I learned that "it works on my machine"
  isn't the same as "it works."

## Skills

<!-- Not IDed — Skills is fully configurable per application: select from
profile/background.md's Skills section, front-loaded to the posting's stack, max ~6 items/line.
The lines below are the default/example selection, not locked text. -->
**Languages:** TypeScript, JavaScript, Node.js, Python, SQL
**Frameworks/Tools:** React, PostgreSQL, Docker
**Practices:** automated testing, CI/CD

<!-- LOCKED, identical wording on every CV, see CV_SPEC.md — shared verbatim with
master_cv_minimal.md's @skill-note. -->
<!-- @skill-note -->
*Main technologies for this role — full list on request.*

## Languages

<!-- LOCKED, byte-identical on every CV — shared verbatim with master_cv_minimal.md's
@languages-line. -->
<!-- @languages-line -->
English (native) · Spanish (B1)

## Volunteer work

<!-- Unconditional here, same reasoning as @exp-course-tutor above. -->
<!-- @vol-community -->
**Community volunteering** | 2021–present · Rivertown
- Weekend shifts at a local food bank, most Saturdays — started during a slow stretch at work
  and kept going because the crew's good company.

<!-- render:stop -->

## Notes for tailoring (this section is never copied into a generated CV)

Full rules live in `CV_SPEC.md` (this folder) — read it before writing an `application.md`.
Summary:

- This file is the primary master — edit it first, then condense the same change into
  `master_cv_minimal.md`.
- Experience order is locked: self-directed, then the current role (see `CV_SPEC.md`). Peer
  Tutor and Volunteer work are unconditional here (unlike the minimal pipeline, where they're
  optional per application — see `application.md`'s `## Include`/`## Omit`).
- `@exp-first-internship` has no minimal counterpart by design — the complete record, not the
  tailored pitch.
