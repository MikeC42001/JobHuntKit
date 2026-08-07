# SPEC.md — the format contract

This is the mechanical reference for how `master/master_cv_minimal.md` +
`templates/<name>.md` + `applications/offer-pages/<Company>/application.md` become a rendered
CV. It's the *format* layer — syntax and parser behavior, true for every JobHuntKit user. Your
own *personal policy* (which entries are locked, what never goes on a CV) belongs in your own
`master/CV_SPEC.md` instead — see `templates/CV_SPEC.md` for that skeleton.

If you're doing your first setup, read `docs/GETTING-STARTED.md` first; come back here when you
need the exact rules.

## Who owns what

```
master_cv_minimal.md      (locked wording, addressed by @id)
templates/*.md             (which slots exist, in what order)
<Company>/application.md   (the per-posting pitch)
        └─> build_cv.py ─> <Company>/cv-minimal.md ─> render_cv_minimal.sh ─> PDF
                              ▲                            ▲
                   check_cv.py (spine, from config.json)   cv2html-minimal.js (heading order)
```

Two places carry structural knowledge that the master/template alone can't express: `config.json`
(which Experience entries are locked, and in what order — see `docs/CONFIG.md`) and
`cv2html-minimal.js` (which section headings exist at all, and what order they render in,
independent of the file's own order).

## Generated files are build artifacts — never hand-edit

`cv-minimal.md` in every company folder, and every rendered PDF, are generated. Edit
`application.md` and re-run `build_cv.py` — a hand-edit is silently overwritten by the next
build. Per-company prose belongs in `application.md`, which the generator reads but never
overwrites, so there's nothing left for a re-run to clobber.

## The `@id` marker convention (`master_cv_minimal.md`)

- Marker is `<!-- @id -->` alone on its own line, immediately before the block it labels
  (`build_cv.py`'s `MARKER_RE`).
- ID charset: letters, digits, `_`, `-`. No spaces, no `@` inside the id itself.
- A block runs from the line after the marker to the **first blank line** or EOF (`parse_master`).
  A blank line mid-entry silently truncates it — the easiest way to lose a new entry's later
  bullets.
- Comment lines inside a block are skipped, not emitted.
- A duplicate ID anywhere in the master is a hard build error.
- Content is copied **verbatim**, bullets and all — an Experience/Education block is
  `**Title** | right-side` plus its own `- ` bullets; a project block is just the `- ` bullet.

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
| `{{@id?}}` | Optional — rendered only if `id` is in `application.md`'s `## Include`; otherwise the line and an adjacent blank line are dropped entirely. |
| `{{@id?section:Heading}}` | Optional *whole section* — emits `## Heading` plus the block if included, or drops both if not. |
| `{{FIELD}}` | From `application.md`'s matching `## Field`. **Hard error** if that section is missing. |
| `{{FIELD\|@id}}` | Same, falling back to master content when the section is absent. |
| `{{FIELD\|literal}}` / `{{FIELD\|}}` | Same, falling back to a literal (often empty). |
| `{{PROJECTS}}` | Expands `application.md`'s `## Projects` in list order; a bare `proj-id` pulls the master text, `proj-id: text` overrides the framing for that application only. |
| `{{COMPANY}}` / `{{ROLE}}` | From `application.md`'s front matter. |

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
---

## Tagline
## About me
## Contact suffix
## Projects
- proj-id
- proj-id: custom framing text for this application only
## Skills
**Label:** item, item, item
## Include
- optional-spine-id
## Omit
- optional-spine-id: one-line reason
## Notes
```

- **Front matter:** `template` picks a file from `templates/` by basename (no `.md`).
  `company`/`role` are for humans and for `check_cv.py`'s output labels — not consumed by the
  renderer directly, but read via `{{COMPANY}}`/`{{ROLE}}`.
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
4. Section headings must be exactly one of the recognized aliases (case-insensitive):
   `about me`, `education`, `experience`, `volunteer work`, `skills`, `languages`, plus any
   extra alias you configure in `config.json`'s `spine.heading_aliases`. Anything else still
   renders, but generically at the end — not an error, just not what you want.
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

## Recipes — what to touch, in order

**Add a new portfolio project.** Add a `<!-- @proj-<slug> -->` block to the master. Reference it
from any `application.md`'s `## Projects`. Run `check_cv.py --coverage` afterward — every
application that doesn't reference the new project now shows it SILENT until you declare it in
`## Omit` (or add it).

**Add a new optional (non-locked) entry.** Add a `<!-- @exp-<slug> -->` (or `vol-<slug>`) block
to the master, add its id to `config.json`'s `spine.optional_ids`, and reference it via
`## Include` on whichever `application.md`s should carry it. If the template uses
`{{@id?section:Heading}}` for a whole optional section, make sure the heading text matches.

**Add a new locked entry.** Same block shape, but add the id to `spine.locked_order` (and give
the template an unconditional `{{@id}}` slot) instead of `optional_ids`. This changes **every**
company's next build, not just new ones — decide deliberately, not as a side effect of adding
one application.

**Add a new configurable field.** Add a `## Field Name` heading to your `application.md`s that
should carry it, and reference it from the template as `{{FIELD_NAME}}` (or with a fallback,
`{{FIELD_NAME|literal}}`). You'll also need a `FIELD_HEADINGS` entry in `engine/build_cv.py`
mapping the heading text to the token name — this is genuinely the one place format extension
touches code, since the heading-to-token map is a Python dict, not data-driven.

**Add a new section to the renderer.** The renderer (not the generator) decides which sections
exist at all — `cv2html-minimal.js`'s heading-alias list and `check_cv.py`'s own copy are
independent and must be kept in sync by hand if you add one.
