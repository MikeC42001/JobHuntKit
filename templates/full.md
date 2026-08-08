<!--
  Template for engine/build_cv.py — the full CV (engine/render_cv.sh / render_cv_photo.sh).
  "full" shape: the complete inventory, no page budget, generous by default. See docs/SPEC.md
  for the full placeholder grammar and "The full CV — id-agnostic rendering" for how this differs
  from templates/minimal-full.md.

  Placeholder syntax — same grammar as minimal-full.md, see that file's header comment or
  docs/SPEC.md for the full reference. The one structural difference from minimal-full.md: most
  spine entries below are UNCONDITIONAL {{@id}}, not {{@id?}} — the full CV doesn't need
  application.md's ## Include to show something, because there's no line budget forcing a
  choice. {{FIELD}} tokens (TAGLINE/ABOUT_ME/SKILLS/CONTACT_SUFFIX) still come from the same
  application.md as the minimal pipeline — see build_cv.py's front-matter "pipelines:" key.

  This file is never rendered directly — build_cv.py reads it, resolves every placeholder, strips
  this comment block and every other HTML comment, and writes the result to the company's cv.md.
-->
{{@header-name}}

{{@header-location}}{{CONTACT_SUFFIX|}} · {{@header-phone}} · {{@header-email}}
{{@header-linkedin}}

> GENERATED FILE — do not hand-edit. Edit application.md, then re-run:
> python engine/build_cv.py "applications/offer-pages/<Company>"
>
> Tailored for: {{COMPANY}} — {{ROLE}}

*{{TAGLINE}}*

## About me

{{ABOUT_ME}}

## Education

{{@edu-degree}}

## Experience

{{@exp-previous-role}}
{{PROJECTS}}

{{@exp-current-role}}

{{@exp-optional}}

{{@exp-earliest-role}}

## Skills

{{SKILLS}}

{{@skill-note}}

## Languages

{{@languages-line}}

## Volunteer work

{{@vol-example}}
