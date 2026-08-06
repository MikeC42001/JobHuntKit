<!--
  Template for engine/build_cv.py — one-column minimal CV (render_cv_minimal.sh / cv2html-minimal.js).
  "full" shape: everything that fits on one page, tight spacing. See docs/SPEC.md for the full
  placeholder grammar and the renderer-compatibility contract (LF endings, entry-header format).

  Placeholder syntax build_cv.py understands, `{{ }}` markers:
    {{@id}}           — locked content, copied verbatim from master_cv_minimal.md by that ID.
                         Errors if the ID is missing from the master (a locked slot must resolve).
    {{@id?}}          — optional-locked content, same section as surrounding content: rendered
                         only if `id` appears in application.md's `## Include`; otherwise dropped
                         entirely (not left blank — the surrounding blank line collapses too).
    {{@id?section:H}} — optional-locked whole section: if `id` is included, renders `## H`
                         followed by the locked content at `@id`; if not included, the entire
                         section (heading and all) is dropped.
    {{FIELD}}         — configurable content from application.md's matching `## Field` section,
                         written verbatim (already markdown, e.g. multi-line About me / Skills).
    {{FIELD|@id}}     — configurable with a locked fallback: if application.md has no `## Field`
                         section, use master content at `@id` instead.
    {{FIELD|literal}} — configurable with a literal fallback (often empty, `{{FIELD|}}`) for an
                         optional field with no master equivalent. Used for Contact suffix, e.g.
                         `(remote)` — most applications have none.
    {{PROJECTS}}      — special: renders application.md's `## Projects` list as `- ` bullets,
                         resolving bare `proj-id` against the master and `proj-id: text` as an
                         inline override. Always nested under Experience > self-directed.

  The header (name/location/phone/email/LinkedIn) is itself built from locked @id blocks in the
  master, not hardcoded here — that's what lets the same template serve any person's data root.

  This file is never rendered directly — build_cv.py reads it, resolves every placeholder, strips
  this comment block and every other HTML comment, and writes the result to the company's
  cv-minimal.md.
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

{{@exp-optional?}}

## Skills

{{SKILLS}}

{{@skill-note}}

## Languages

{{@languages-line}}

{{@vol-example?section:Volunteer work}}
