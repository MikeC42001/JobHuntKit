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

> Master inventory for the one-column minimal layout (`render_cv_minimal.sh`). Every locked
> block below carries a stable `<!-- @id -->` marker on its own line, immediately before the
> block it labels (one blank line ends the block). `engine/build_cv.py` reads these by ID to
> assemble each company's `cv-minimal.md` from `applications/offer-pages/<Company>/application.md`
> + a template in `templates/`. See `CV_SPEC.md` (this folder) for what's locked vs.
> configurable, and never hand-edit a generated `cv-minimal.md` — edit `application.md` and
> re-run the generator instead.

## About me

Software engineer who likes taking a rough, half-automated process and turning it into
something reliable and boring. Four years maintaining a production scheduling app, plus a
handful of small self-directed tools built solo.

<!-- Not IDed — About me is fully configurable per application, never copied verbatim. This is
the example/fallback wording only. -->

## Education

<!-- @edu-bsc -->
**BSc, Computer Science — Rivertown University** | 2016–2019 · 3y

## Experience

<!-- LOCKED ORDER — see CV_SPEC.md: self-directed, then the current role. -->

<!-- @exp-self-directed -->
**Independent Projects — self-directed** | 2022–present · ongoing

<!-- @proj-inventory-tool -->
- Small inventory-tracking web app for a local bakery, replacing a shared spreadsheet (React,
  Node.js, PostgreSQL), solo.

<!-- @proj-status-page -->
- Open-source status-page generator that turns a YAML config into a static site (Python,
  Jinja2), maintained solo with occasional outside contributions.

<!-- Pick 1–2 most relevant when tailoring. Not an @id — this is guidance for application.md,
not renderable content. -->

<!-- @exp-current-role -->
**Software Engineer — Meridian Systems** | Mar 2020–present · 4y · Rivertown (hybrid)
- Maintains and extends a logistics-scheduling web app used by roughly 40 internal staff.
- Introduced automated testing to a previously untested codebase, cutting regression bugs
  reported per release by half.

<!-- OPTIONAL spine entry. Include via application.md's ## Include if relevant; declare in
## Omit with a reason otherwise. -->
<!-- @exp-course-tutor -->
**Peer Tutor — Rivertown University** | Sep 2018–May 2019 · 4h/week
- Ran weekly study sessions for first-year programming students.

## Skills

<!-- Not IDed — Skills is fully configurable per application: select from
profile/background.md's Skills section, front-loaded to the posting's stack, max ~6 items/line.
The lines below are the default/example selection, not locked text. -->
**Languages:** TypeScript, JavaScript, Node.js, Python, SQL
**Frameworks/Tools:** React, PostgreSQL, Docker
**Practices:** automated testing, CI/CD

<!-- LOCKED, identical wording on every CV, see CV_SPEC.md -->
<!-- @skill-note -->
*Main technologies for this role — full list on request.*

## Languages

<!-- LOCKED, byte-identical on every CV -->
<!-- @languages-line -->
English (native) · Spanish (B1)

## Volunteer work

<!-- OPTIONAL spine entry (whole section). Include via application.md's ## Include if the
one-page budget allows; declare in ## Omit with a reason otherwise. -->
<!-- @vol-community -->
**Community volunteering** | 2021–present · Rivertown
- Weekend shifts at a local food bank.

## Notes for tailoring (this section is never copied into a generated CV)

Full rules live in `CV_SPEC.md` (this folder) — read it before writing an `application.md`.
Summary:

- Experience order is locked: self-directed, then the current role (see `CV_SPEC.md`).
  Peer Tutor and Volunteer work are optional, per application — but declare the omission in
  `application.md`'s `## Omit` so a coverage report doesn't flag it as silent.
- Pick 1–2 portfolio projects most relevant to the role, not both.
