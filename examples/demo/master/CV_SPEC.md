# CV_SPEC.md — Robin Vale's locked-vs-configurable decisions

This is a worked example of the file every JobHuntKit user writes once, early on, to record
*their own* answers to "what always appears on my CV, and what changes per application?" The
format rules that make `application.md` parseable at all (placeholder syntax, entry-header
format, etc.) live in the toolkit's published `docs/SPEC.md` — this file is just the personal
policy layer on top of that, worked through for the fictional persona used in `demo.sh`.

One spine, two masters: `master_cv.md` (the primary, complete inventory — includes
`exp-first-internship`, which has no minimal counterpart) and `master_cv_minimal.md` (a
condensation of it — same ids, terser wording, one fewer entry). The decisions below apply to
both; `config.json`'s `spine` block isn't per-pipeline.

## Locked spine (always present, always in this order)

1. `exp-self-directed` — Independent Projects
2. `exp-current-role` — Software Engineer, Meridian Systems

Two entries, not three — Robin doesn't have a third always-include role. A locked spine can be
as short as one entry; there's nothing magic about three, that's just how many Robin has.

## Optional entries — minimal pipeline only (declare via `## Include` / `## Omit` per application)

- `exp-course-tutor` — relevant for anything education-adjacent, otherwise a distraction from a
  four-year-old part-time role. Unconditional in the full CV — see `templates/full.md`.
- `vol-community` — include when there's room; the one-page budget is the usual reason to omit
  it, not a judgment about the entry itself. Unconditional in the full CV, same reasoning.

## Portfolio projects (pick 1–2 per application, `## Projects`)

- `proj-inventory-tool` — leads for anything client-facing/small-business.
- `proj-status-page` — leads for anything infra/ops/open-source-adjacent.

## Locked, byte-identical on every CV

- `skill-note` — the "full list on request" closing line.
- `languages-line` — the language line.

## Education

- `edu-bsc` — the only degree; always present, never a candidate for omission.

## Never on a CV that goes out the door

Nothing withheld for Robin — this section exists because a real user's version of this file
usually has one. Typical entries: an employer under NDA, a grade you don't want printed, a
product name that isn't public yet. State the rule here once rather than remembering it per
application.
