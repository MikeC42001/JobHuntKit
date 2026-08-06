<!-- @header-name -->
# Your Name

<!-- @header-location -->
Your City, Country

<!-- @header-phone -->
YOUR_PHONE_HERE

<!-- @header-email -->
YOUR_EMAIL_HERE

<!-- @header-linkedin -->
[linkedin.com/in/your-handle](https://www.linkedin.com/in/your-handle)

> Master inventory for the one-column minimal layout (`render_cv_minimal.sh`). Every locked
> block below carries a stable `<!-- @id -->` marker on its own line, immediately before the
> block it labels (one blank line ends the block). `engine/build_cv.py` reads these by ID to
> assemble each company's `cv-minimal.md` from `applications/offer-pages/<Company>/application.md`
> + a template in `templates/`. See `CV_SPEC.md` (this folder) for what's locked vs.
> configurable, and never hand-edit a generated `cv-minimal.md` — edit `application.md` and
> re-run the generator instead. Full format rules: `docs/SPEC.md`.

## About me

Placeholder — one to three sentences summarizing who you are professionally. This section is
never copied verbatim into a generated CV (see the comment below), so what you write here is
just the fallback/example wording.

<!-- Not IDed — About me is fully configurable per application, never copied verbatim. This is
the example/fallback wording only. -->

## Education

<!-- @edu-degree -->
**Degree, Field — Institution** | YYYY–YYYY · Nyr

## Experience

<!-- LOCKED ORDER — decide your own locked order in CV_SPEC.md. This starter uses two roles,
oldest first, but a locked spine can be as short as one entry. -->

<!-- @exp-previous-role -->
**Role Title — Organization** | Mon YYYY–Mon YYYY · Nyr
- One bullet describing scope or impact.

<!-- @proj-example -->
- One portfolio-project bullet — independent/side work you want available to any
  application.md's ## Projects list. Nest project bullets under whichever Experience entry
  represents your self-directed/independent work, or delete this block if you have none.

<!-- Pick which projects are most relevant when tailoring. Not an @id — this is guidance for
application.md, not renderable content. -->

<!-- @exp-current-role -->
**Role Title — Organization** | Mon YYYY–present · Nyr
- One bullet.
- Another bullet.

<!-- OPTIONAL spine entry. Include via application.md's ## Include if relevant; declare in
## Omit with a reason otherwise. -->
<!-- @exp-optional -->
**Role Title — Organization** | Mon YYYY–Mon YYYY · duration
- One bullet.

## Skills

<!-- Not IDed — Skills is fully configurable per application: select from
profile/background.md's Skills section, front-loaded to the posting's stack, max ~6 items/line.
The lines below are placeholder wording, not locked text. -->
**Languages:** item, item, item
**Frameworks/Tools:** item, item
**Practices:** item, item

<!-- LOCKED, identical wording on every CV, see CV_SPEC.md -->
<!-- @skill-note -->
*Main technologies for this role — full list on request.*

## Languages

<!-- LOCKED, byte-identical on every CV -->
<!-- @languages-line -->
Your language (native) · Another language (level)

## Volunteer work

<!-- OPTIONAL spine entry (whole section). Include via application.md's ## Include if the
one-page budget allows; declare in ## Omit with a reason otherwise. -->
<!-- @vol-example -->
**Volunteer role** | YYYY–present · Location
- One bullet.

## Notes for tailoring (this section is never copied into a generated CV)

Full rules live in `CV_SPEC.md` (this folder) and `docs/SPEC.md` (format contract) — read both
before writing your first `application.md`. Summary:

- Decide your locked Experience order in `CV_SPEC.md`, then keep this file's block order in
  sync — `check_cv.py` validates against `config.json`'s `spine.locked_order`, not this file's
  order, but keeping them matched avoids confusion.
- Pick 1–2 portfolio projects most relevant to the role, not all of them.
- Delete any `@exp-optional`/`@vol-example`-style block you don't need, and remove its id from
  `config.json`'s `spine.optional_ids` to match.
