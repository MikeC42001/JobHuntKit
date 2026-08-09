# SPEC.md — the format contract

This is the mechanical reference for how the two masters + `templates/<name>.md` +
`applications/offer-pages/<Company>/application.md` become a rendered CV. It's the *format*
layer — syntax and parser behavior, true for every JobHuntKit user. Your own *personal policy*
(which entries are locked, what never goes on a CV) belongs in your own `master/CV_SPEC.md`
instead — see `templates/CV_SPEC.md` for that skeleton.

If you're doing your first setup, read `docs/GETTING-STARTED.md` first; come back here when you
need the exact rules.

## Who owns what

A chain, not two unrelated files: `master_cv.md` is the primary master (the complete inventory,
`@id`-tagged); `master_cv_minimal.md` is a *condensation* of it — same ids, terser wording. One
`application.md` per company drives both pipelines:

```
master_cv.md ──condensed to──> master_cv_minimal.md
     │                                  │
     ▼ templates/full.md                ▼ templates/minimal-full.md
     │  (roomier, generous)             │  (which slots exist, one-page discipline)
     └──────────────┬───────────────────┘
                     │
        <Company>/application.md   (the per-posting pitch; "pipelines:" front-matter
                     │              key selects minimal, full, or both — default minimal)
        ┌────────────┴────────────┐
        ▼ build_cv.py             ▼ build_cv.py
<Company>/cv.md            <Company>/cv-minimal.md
        │                                  │
render_cv.sh /              render_cv_minimal.sh
render_cv_photo.sh                         │
        ▼                                  ▼
      PDF                                PDF
        ▲                                  ▲
check_cv.py --pipeline full     check_cv.py (spine, from config.json)
                                            ▲
                              cv2html-minimal.js (heading order)
```

Two places carry structural knowledge that the master/template alone can't express: `config.json`
(which Experience entries are locked, and in what order — see `docs/CONFIG.md`, shared by both
pipelines) and `cv2html-minimal.js` (which section headings exist at all, and what order they
render in, independent of the file's own order). `cv2html-photo.js` has its own, different
section model (a hardcoded left-column order plus a sidebar fallback — see "The full CV —
id-agnostic rendering" below); only `cv2html.js` has no section model at all.

There's also a second, simpler path to the full CV that skips the build entirely — no template,
no `application.md`, no validator, just any CV markdown straight into a renderer:

```
<any CV markdown, e.g. master_cv.md itself>
        └─> render_cv.sh  or  render_cv_photo.sh  ─> PDF
```

Use the built `cv.md` path above when you want per-company selection (the same `## Include`/
`## Omit` the minimal pipeline uses); point a renderer straight at `master_cv.md` when you just
want the whole thing, right now, with no per-company anything.

## Generated files are build artifacts — never hand-edit

`cv-minimal.md` and `cv.md` in every company folder, and every rendered PDF, are generated. Edit
`application.md` and re-run `build_cv.py` — a hand-edit is silently overwritten by the next
build. Per-company prose belongs in `application.md`, which the generator reads but never
overwrites, so there's nothing left for a re-run to clobber.

## The `@id` marker convention (both masters)

Identical rules for `master_cv.md` and `master_cv_minimal.md` — the same `parse_master()` reads
either, selected by which pipeline's calling it.

- Marker is `<!-- @id -->` alone on its own line, immediately before the block it labels
  (`build_cv.py`'s `MARKER_RE`).
- ID charset: letters, digits, `_`, `-`. No spaces, no `@` inside the id itself.
- A block runs from the line after the marker to the **first blank line** or EOF (`parse_master`).
  A blank line mid-entry silently truncates it — the easiest way to lose a new entry's later
  bullets.
- Comment lines inside a block are skipped, not emitted.
- A duplicate ID anywhere in *one* master is a hard build error. Duplicating an id *across* the
  two masters is not an error — it's required. See "Id inheritance" below.
- Content is copied **verbatim**, bullets and all — an Experience/Education block is
  `**Title** | right-side` plus its own `- ` bullets; a project block is just the `- ` bullet.

### Id inheritance

Every id in `master_cv_minimal.md` must also exist in `master_cv.md` — the minimal master is a
condensation of the full one, not an independent file. The reverse doesn't hold: the full master
may carry ids the condensation skips entirely (an older role, extra detail not worth a tailored
one-pager's space — see the demo's `exp-first-internship` for a worked example). Nothing enforces
this at build time (a missing id only surfaces as a hard error the moment some template actually
references it), but `tests/test_build_cv.py` pins it for both the demo and the blank starter
templates, so a check exists even though no runtime script asserts it.

### ID prefixes

| Prefix | Meaning | Functional? |
|---|---|---|
| `proj-` | portfolio project bullets | **Yes** — `check_cv.py --coverage`'s report auto-discovers every `proj-*` block in the master. A new one shows SILENT on every application until each one declares it in `## Omit` (or uses it) — that's the intended nudge, not a bug. |
| `exp-` | Experience entries | Naming convention only. Which ones are locked, and in what order, is `config.json`'s `spine.locked_order`. |
| `edu-` | Education entries | Convention only; the structure check matches the *rendered title text* against `spine.education.required_titles`, not the id. |
| `vol-` | Volunteer work | Convention only. |
| bare (`skill-note`, `languages-line`, ...) | one-off locked lines | Anything listed in `spine.verbatim_ids` is compared byte-for-byte against every application's rendered output. |

Rule of thumb: use `proj-` if and only if it's a portfolio-project bullet — that's the only
prefix that opts an item into coverage tracking automatically.

## Template placeholder grammar (`{{...}}`)

| Syntax | Behaviour |
|---|---|
| `{{@id}}` | Locked, verbatim from the master. **Hard build error** if the id is missing — a locked slot must always resolve. |
| `{{@id?}}` | Optional — resolves to `id`'s content if it's in `application.md`'s `## Include`, otherwise to nothing. |
| `{{@id?section:Heading}}` | Optional *whole section* — resolves to `## Heading` plus the block if included, otherwise to nothing. |
| `{{FIELD}}` | From `application.md`'s matching `## Field`. **Hard error** if that section is missing. |
| `{{FIELD\|@id}}` | Same, falling back to master content when the section is absent. |
| `{{FIELD\|literal}}` / `{{FIELD\|}}` | Same, falling back to a literal (often empty). |
| `{{PROJECTS}}` | Expands `application.md`'s `## Projects` in list order; a bare `proj-id` pulls the master text, `proj-id: text` overrides the framing for that application only. |
| `{{COMPANY}}` / `{{ROLE}}` | From `application.md`'s front matter. |

What "resolves to nothing" actually does: the token is substituted with an empty string, then
any run of 3+ consecutive newlines in the whole output collapses to a single blank line
(`build_cv.py`'s `_sub`/`re.sub(r"\n{3,}", "\n\n", ...)`). A token *alone on its own line*
therefore disappears cleanly. A token sharing a line with other text does not — the rest of that
line's text is left behind. Optional slots belong on their own line for this reason.

**Token precedence matters, and it's not what the syntax looks like.** `resolve_token` checks
`PROJECTS`, then whether the token contains `|`, then whether it starts with `@`, then
`COMPANY`/`ROLE`, then falls through to a plain `FIELD` lookup. The `|` check runs *before* the
`@` check — so `{{@id|fallback}}` is **not** "resolve `@id`, falling back to `fallback`". It's
parsed as `FIELD_TOKEN = "@id"`, which is never a real field name (`FIELD_HEADINGS` values are
plain uppercase tokens like `TAGLINE`, never `@`-prefixed), so it always falls through to the
literal-fallback branch and resolves to `fallback`, silently ignoring `@id`. The only supported
locked-with-fallback form is `{{FIELD|@id}}` — field first, `@id` as the fallback — never the
reverse.

**One more special case:** `{{CONTACT_SUFFIX|...}}` gets a single leading space prepended to
whatever it resolves to, if non-empty (`build_cv.py`'s `resolve_token`) — the template places it
immediately after the location with no separator, so the space is added here rather than asking
every `application.md` to remember a leading space in its own text.

One trap worth knowing: HTML comments in a template are stripped, but a doc-comment whose own
*prose* contains a literal `-->` truncates the non-greedy strip early and leaks raw text into
the output — `build_cv.py` hard-fails rather than shipping that. If you're writing a comment
that needs to describe HTML-comment syntax, don't use the literal closing sequence inside it.

## `application.md` syntax

One per company, at `applications/offer-pages/<Company>/application.md`. Markdown, the same
`## `-heading convention as everything else in this toolkit — no YAML/TOML body (see
`build_cv.py`'s module docstring for why avoiding a third-party parser matters here).

```markdown
---
template: minimal-full
company: <Company>
role: <Role>
pipelines: minimal, full
---

## Tagline
## About me
## Contact suffix
## Projects
- proj-id
- proj-id: custom framing text for this application only
## Skills
**Label:** item, item, item
## Dissertation depth
## Include
- optional-spine-id
## Omit
- optional-spine-id: one-line reason
## Notes
```

- **Front matter:** `template` picks a file from `templates/` by basename (no `.md`) — **required
  even for a `pipelines: full`-only application**, whose value is then ignored (`build_cv.py`'s
  `build_company()` uses `cfg.pipeline("full")["template"]` instead). `company`/`role` are for
  humans and for `check_cv.py`'s output labels — not consumed by the renderer directly, but read
  via `{{COMPANY}}`/`{{ROLE}}`. `pipelines` is optional and comma-separated; absent entirely (every
  pre-existing `application.md`) means `["minimal"]` — see "The full CV" below.
- **`## Dissertation depth`:** the fifth and least obvious `FIELD_HEADINGS` entry
  (`engine/build_cv.py`), mapping to `{{EDU_MSC_DISSERTATION}}`. Easy to miss because it's the
  only field named after specific content rather than a generic slot — if your template doesn't
  use `{{EDU_MSC_DISSERTATION}}`, you'll never need this heading.
- **`## Projects`:** a bare `proj-id` pulls the master's canonical bullet text; `proj-id: text`
  overrides the framing for this application only — the master text is untouched. Order in this
  list is the order they render in.
- **`## Include`:** lists optional-spine IDs to add for this application. An id absent from
  both `## Include` and `## Omit` is not included, and `check_cv.py --coverage` flags it SILENT.
- **`## Omit`:** declares a deliberate absence, with a reason. Applies to optional-spine IDs
  only — a locked ID can't be omitted here (the generator errors if one is missing from the
  master itself, not if `application.md` tries to omit it).
- **`## Notes`:** free text, never enters the generated file. Interview prep, honest-gap
  framing, why this template/pitch was chosen — anything you want to keep next to the
  application without it reaching the CV.
- An **unrecognized** `## Heading` in `application.md` is a build error, not a silent skip.
  `projects` / `include` / `omit` / `notes` are reserved section names and can't be reused as a
  field name.
- **"Optional" does not mean "untracked."** Declare every omission in `## Omit` with a one-line
  reason. `check_cv.py --coverage` reports anything missing *without* an `## Omit` entry as
  SILENT — that's the signal something was forgotten rather than decided.

## Cover letters — a different shape entirely

`cover_letter.md` has no `@id` scheme, no template, and nothing generates it — it's a hand-
written source file, not a build artifact, the one exception to "everything under a company
folder except application.md is generated." Structure by convention, not enforced by a parser:

```
Dear <Company> team,

<2-4 body paragraphs>

<closing line>

Best regards,
<Name>
<contact line>

---
<anything here — draft notes, review reminders — is stripped before rendering>
```

`engine/render_letter.sh` (via `render-support/letter2html.js`) applies exactly two mechanical
rules: everything from a lone `---` line onward is cut, and the final paragraph (the signature
block) is rendered with real line breaks between its lines instead of collapsing into one run-on
line the way plain markdown treats a single-newline-separated paragraph. No `{{...}}` tokens, no
`@id` markers — write it as you'd write the letter.

## The full CV — id-agnostic rendering

`engine/render_cv.sh` (single-column, ATS-safe, no photo) and `engine/render_cv_photo.sh`
(two-column, circular photo) render **any** CV markdown, not just a build artifact: a built
`cv.md`, either master file pointed at directly, or a hand-written file with no `@id` scheme at
all. Unlike `render_cv_minimal.sh`, they don't assume `build_cv.py` already cleaned the input —
`render-support/cv2html.js` and `render-support/cv2html-photo.js` do that themselves:

1. Every `<!-- ... -->` comment is stripped, including `<!-- @id -->` content markers — a master
   file carries these and nothing upstream removes them before this converter sees the file.
2. A `<!-- render:stop -->` tag cuts everything from that line onward. Drop it above any section
   that shouldn't reach the PDF — e.g. a master's `## Notes for tailoring`, which would otherwise
   render like any other section. `cv2html.js` has no section model at all and passes every `## `
   through as markdown; `cv2html-photo.js` *does* recognize section headings (a hardcoded
   `leftOrder` for the main column, everything else falls into the sidebar) but has no
   `render:stop`-aware exemption for an unwanted section either — the tag is the only way to
   keep something out of either renderer's output.
3. `> ` lines are stripped, same convention as every other renderer here.

There is no validator on this path — `check_cv.py` runs on the build side, where ids exist.
Point either renderer at a loose file and it renders straight through, unvalidated, by design.

That's the build-free path — render the master (or anything) as-is. There's also a *built*
full CV: `application.md`'s `pipelines: minimal, full` opts a company into `build_cv.py` also
producing `<Company>/cv.md` from `master_cv.md` + `templates/full.md`, with the same per-company
`## Include`/`## Omit`/`## Projects` selection the minimal pipeline uses, then validated by
`check_cv.py --pipeline full`. `templates/full.md`'s own convention: most spine entries are
unconditional `{{@id}}` rather than `{{@id?}}` — the full CV is generous by default, since
there's no page budget forcing a choice — so `spine.optional_ids` (shared config with the
minimal pipeline) mostly doesn't apply there. `check_cv.py --coverage --pipeline full` only
reports an id as gated if the full template actually contains `{{@id?}}`/`{{@id?section:H}}`
for it (`gated_optional_ids()`) — reporting a shared `optional_ids` entry as DELIBERATE/SILENT
when the full template made it unconditional would be actively wrong, not just noisy.

Note `render_cv_minimal.sh --style c` is also two-column, for an unrelated reason (a ledger-grid
layout choice within the one-page tailored pipeline) — it is not the same thing as
`render_cv_photo.sh`'s multi-page, full-inventory two-column layout, despite both being
two-column PDFs.

## Renderer compatibility contract

`build_cv.py` must emit output the renderer (`cv2html-minimal.js`) reads correctly. Violating
any of these silently drops content from the PDF — confirmed against the actual parser, not
assumed:

1. **LF line endings, UTF-8, no BOM.** Write with `open(path, "w", newline="\n",
   encoding="utf-8")`. Python's default text mode on Windows reintroduces CRLF, which is a real
   bug class this toolkit has hit before — CRLF silently empties a section while the heading
   still renders.
2. First non-blank line: the CV owner's name as an H1 (e.g. `# Robin Vale`), coming from the
   master's `@header-name` id.
3. Tagline (if present): a standalone `*text*` line, zero asterisks inside, before the first
   `## `.
4. Section headings must be exactly one of the recognized aliases (case-insensitive): six
   canonical sections, each with English and Portuguese (accented and unaccented) variants —
   `about me`/`resumo`/`sobre mim`, `education`/`formação`, `experience`/`experiência`,
   `volunteer work`/`voluntariado`/`trabalho voluntário`, `skills`/`competências`,
   `languages`/`línguas`/`idiomas` — the full list is `cv2html-minimal.js`'s `HEADING_ALIASES`
   constant, not reproduced verbatim here since it's the single source of truth. **`config.json`'s
   `spine.heading_aliases` does not extend this list — the renderer never reads `config.json` at
   all.** That key only feeds `check_cv.py`'s own, independent copy of the alias map, used for
   *validation*; configuring it makes the validator accept a heading the renderer still doesn't
   recognize, which then renders generically at the end rather than in its proper section. The
   two lists must be kept in sync by hand if you add an alias — see "Recipes" below. Anything not
   in the renderer's own list still renders, but generically at the end — not an error, just not
   what you want.
5. Entry headers (Education/Experience/Volunteer): `**Title** | right-side text` — at column 0,
   no bullet prefix, no `**` inside the title, exactly one `|`.
6. Nothing before the first entry header in a section — it is silently discarded.
7. Skills lines: colon **inside** the bold — `**Languages:** …`, not `**Languages**: …`.
8. A verbatim locked line (`spine.verbatim_ids`) is prose, not a `**Label:**` line — avoid the
   soft-wrap-continuation behavior the renderer applies to labeled lines.
9. Section order in the emitted file is cosmetic — the renderer hardcodes render order
   regardless. Templates still declare a sensible order for human readability of the generated
   file.
10. Emit a `> GENERATED FILE — edit application.md, not this file` line near the top. `>` lines
    are stripped at render, so it's visible in source, invisible in the PDF.
11. Strip every `<!-- @id -->` / `<!-- ... -->` comment before writing — none should reach the
    output file.
12. Target the `limits.soft_line_budget` in `config.json` (default 57 lines) so
    `verify_cvs.py`'s one-page gate passes.

## Validator (`check_cv.py`) contract

- **Structure check** (default, all companies or one): confirms Experience order matches
  `spine.locked_order`, every locked Experience id is present, every entry in
  `spine.education.required_titles` is present (and any title flagged in
  `spine.education.require_detail_for` isn't stripped to a bare URL), and every id in
  `spine.verbatim_ids` appears byte-for-byte in the rendered output.
- **Coverage check** (`--coverage [company]`): for each master item id, reports PRESENT /
  DELIBERATE (in `## Omit`) / SILENT (missing, undeclared) — every id in `spine.optional_ids`,
  plus every `proj-*` block auto-discovered from the master.
- Exit 0 only if there are zero structure FAILs. Coverage SILENT entries print but don't fail
  the exit code — they're a prompt to decide, not a hard gate.
- A fresh root with nothing configured in `config.json`'s `spine` block prints a `NOT
  CONFIGURED` banner (exit 0) instead of a false "all OK" — see `docs/CONFIG.md`.
- `--pipeline full` runs either check against `cv.md`/`master_cv.md` instead of
  `cv-minimal.md`/`master_cv_minimal.md`. Same `spine` config either way — locked order,
  verbatim ids, and education titles aren't per-pipeline — but coverage only reports an
  `optional_ids` entry as gated if the pipeline's own template actually gates it (see "The full
  CV — id-agnostic rendering" above).

## Recipes — what to touch, in order

Every recipe below touches `master_cv.md` first (full wording), then condenses the same block
into `master_cv_minimal.md` (same id, terser) — see "Id inheritance" above. Skip the second half
if the entry only belongs in the complete record.

**Add a new portfolio project.** Add a `<!-- @proj-<slug> -->` block to the master(s). Reference
it from any `application.md`'s `## Projects`. Run `check_cv.py --coverage` afterward — every
application that doesn't reference the new project now shows it SILENT until you declare it in
`## Omit` (or add it).

**Add a new optional (non-locked) entry.** Add a `<!-- @exp-<slug> -->` (or `vol-<slug>`) block
to the master(s), add its id to `config.json`'s `spine.optional_ids`, and reference it via
`## Include` on whichever `application.md`s should carry it. If the template uses
`{{@id?section:Heading}}` for a whole optional section, make sure the heading text matches.
`templates/full.md`'s own convention is to make this id *unconditional* instead — an intentional
difference, not an oversight, see "The full CV — id-agnostic rendering" above.

**Add a new locked entry.** Same block shape, but add the id to `spine.locked_order` (and give
`templates/minimal-full.md` an unconditional `{{@id}}` slot) instead of `optional_ids`. This
changes **every** company's next minimal build, not just new ones — decide deliberately, not as
a side effect of adding one application.

**Add a new configurable field.** Add a `## Field Name` heading to your `application.md`s that
should carry it, and reference it from the template as `{{FIELD_NAME}}` (or with a fallback,
`{{FIELD_NAME|literal}}`). You'll also need a `FIELD_HEADINGS` entry in `engine/build_cv.py`
mapping the heading text to the token name — this is genuinely the one place format extension
touches code, since the heading-to-token map is a Python dict, not data-driven.

**Add a new section to the renderer.** The renderer (not the generator) decides which sections
exist at all — `cv2html-minimal.js`'s heading-alias list and `check_cv.py`'s own copy are
independent and must be kept in sync by hand if you add one.
