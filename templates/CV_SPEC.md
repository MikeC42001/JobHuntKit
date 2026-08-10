# CV_SPEC.md — your locked-vs-configurable decisions

This is the file every JobHuntKit user writes once, early on, to record *their own* answers to
"what always appears on my CV, and what changes per application?" The format rules that make
`application.md` parseable at all (placeholder syntax, entry-header format, etc.) live in the
toolkit's published `docs/SPEC.md` — this file is just the personal policy layer on top of that.

Read `docs/GETTING-STARTED.md` before filling this in — it walks through the whole first-run
sequence and explains why a locked spine is worth the up-front decision.

One spine, two masters: `master/master_cv.md` (the primary, complete inventory) and
`master/master_cv_minimal.md` (a condensation of it — same ids, terser wording). The decisions
below apply to both; `config.json`'s `spine` block isn't per-pipeline. See `docs/SPEC.md`'s "The
full CV — id-agnostic rendering" for how the two masters relate.

## Locked spine (always present, always in this order)

1. `` — which Experience id, and why it's non-negotiable.
2. `` — same.

A locked spine can be as short as one entry. There's nothing magic about a specific count —
list exactly what you've decided always belongs.

## Optional entries (declare via `## Include` / `## Omit` per application)

- `` — when to include it, and what makes it a distraction otherwise.

## Portfolio projects (pick 1–2 per application, `## Projects`)

- `` — what kind of posting this project is a good lead for.

## Locked, byte-identical on every CV

- `skill-note` — or whatever your own bare-line locked ids are.
- `languages-line`

## Education

- `` — which education entries are always present, and any that are candidates for omission.

## Never on a CV that goes out the door

State your own rule here once rather than remembering it per application. Typical entries: an
employer under NDA, a grade you don't want printed, a product name that isn't public yet.
