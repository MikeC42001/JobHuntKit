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

> The primary master — the complete inventory, written as a real document you could hand
> someone directly (see `engine/render_cv.sh`/`render_cv_photo.sh` — no build step required to
> render this file as-is). `master/master_cv_minimal.md` is a *condensation* of this file: every
> `<!-- @id -->` here should also exist there, just in terser wording — see `docs/SPEC.md`'s "The
> full CV — id-agnostic rendering" for the id-inheritance rule. Full format rules: `docs/SPEC.md`.

## About me

Placeholder — three to five sentences summarizing who you are professionally: the full version,
not the one-line elevator pitch. This section is fully configurable per application the same way
`master_cv_minimal.md`'s is (see the comment below), so what you write here is just the
fallback/example wording.

<!-- Not IDed — About me is fully configurable per application, never copied verbatim. This is
the example/fallback wording only. -->

## Education

<!-- @edu-degree -->
**Degree, Field — Institution** | YYYY–YYYY · Nyr
- Optional detail line: honors, relevant coursework, thesis topic. The minimal condensation of
  this block drops the detail line entirely — that's the point of condensing.

## Experience

<!-- LOCKED ORDER — decide your own locked order in CV_SPEC.md. Mirrors master_cv_minimal.md's
order; this file may additionally carry roles the minimal condensation never mentions (older or
less relevant work still worth keeping in the complete record) — see @exp-earliest-role below. -->

<!-- @exp-previous-role -->
**Role Title — Organization** | Mon YYYY–Mon YYYY · Nyr
- One bullet describing scope or impact — the full version can carry two or three bullets where
  the minimal condensation keeps only one.
- A second bullet, kept here even though the minimal condensation omits it.

<!-- @proj-example -->
- One portfolio-project bullet, fuller version — independent/side work you want available to any
  application.md's ## Projects list. Nest project bullets under whichever Experience entry
  represents your self-directed/independent work, or delete this block if you have none.

<!-- Pick which projects are most relevant when tailoring. Not an @id — this is guidance for
application.md, not renderable content. -->

<!-- @exp-current-role -->
**Role Title — Organization** | Mon YYYY–present · Nyr
- One bullet.
- Another bullet.
- A third bullet the minimal condensation trims for space.

<!-- Unconditional here (not gated by ## Include/## Omit the way master_cv_minimal.md's
templates/minimal-full.md gates it) — the full CV is generous by default: no page budget means
nothing needs trimming just to fit. See templates/full.md. -->
<!-- @exp-optional -->
**Role Title — Organization** | Mon YYYY–Mon YYYY · duration
- One bullet.

<!-- FULL-ONLY — no minimal condensation exists for this id; the complete work history can carry
entries a tailored one-pager never would. Delete if you don't want a full-only entry. -->
<!-- @exp-earliest-role -->
**Earlier Role Title — Organization** | Mon YYYY–Mon YYYY · Nyr
- One bullet, kept for completeness even though it never appears on a tailored CV.

## Skills

<!-- Not IDed — Skills is fully configurable per application, same as master_cv_minimal.md.
The lines below are placeholder wording, not locked text. -->
**Languages:** item, item, item
**Frameworks/Tools:** item, item
**Practices:** item, item

<!-- LOCKED, identical wording on every CV, see CV_SPEC.md — shared verbatim with
master_cv_minimal.md's @skill-note. -->
<!-- @skill-note -->
*Main technologies for this role — full list on request.*

## Languages

<!-- LOCKED, byte-identical on every CV — shared verbatim with master_cv_minimal.md's
@languages-line. -->
<!-- @languages-line -->
Your language (native) · Another language (level)

## Volunteer work

<!-- Unconditional here, same reasoning as @exp-optional above. -->
<!-- @vol-example -->
**Volunteer role** | YYYY–present · Location
- One bullet.

<!-- render:stop -->

## Notes for tailoring (this section is never copied into a generated CV)

Full rules live in `CV_SPEC.md` (this folder) and `docs/SPEC.md` (format contract) — read both
before writing your first `application.md`. Summary:

- This file is the primary master — edit it first, then condense the same change into
  `master_cv_minimal.md`. `agents/cv-setup.md` walks that two-step flow.
- Every id here that also exists in `master_cv_minimal.md` must carry the same id name — that's
  what lets one background fact update both files without them drifting apart. This file may
  carry extra ids the minimal condensation skips (see `@exp-earliest-role`); the reverse must
  never happen.
- Delete any block you don't need, and remove its id from `config.json`'s `spine.optional_ids`
  (shared config between both pipelines) to match.
