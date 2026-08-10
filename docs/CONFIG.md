# CONFIG.md — every `config.json` key

> **Finding the root comes first.** `config.json` describes a root; it does not identify one.
> A root is identified by a `.jobhuntkit` marker file containing `jobhuntkit-root/1`, and is
> resolved in this order:
>
> ```
> --root  >  $JOBHUNTKIT_ROOT  >  .jobhuntkit-root  >  walk up from cwd  >  the checkout
> ```
>
> `.jobhuntkit-root` is written (gitignored) when `init_workspace.py` is given an external
> `--root`, so you pass the flag once rather than every time. Delete it to forget. Whenever the
> answer isn't the plain default, the resolving command prints which rule fired.

`config.json` is deliberately JSON, not YAML/TOML — see `engine/build_cv.py`'s module docstring
for why avoiding a third-party parser dependency matters for a clone-and-run toolkit. Missing
keys fall back to the defaults below, so a fresh clone with no `config.json` at all still runs
(with spine checking disabled — see `spine` below).

Full shape — every key `engine/config.py`'s `DEFAULT_CONFIG` ships:

```jsonc
{
  "person": { "name": "", "file_prefix": "CV", "letter_prefix": null },
  "render": { "default_photo": null, "default_style": "a", "browser_bin": null },
  "spine": {
    "locked_order": [],
    "title_markers": {},
    "optional_ids": [],
    "verbatim_ids": [],
    "education": { "required_titles": [], "require_detail_for": [] },
    "heading_aliases": {}
  },
  "limits": { "soft_line_budget": 57, "max_pages": 1 },
  "display_names": {},
  "pipelines": {
    "minimal": { "master": "master/master_cv_minimal.md", "template": "minimal-full", "out": "cv-minimal.md" },
    "full": { "master": "master/master_cv.md", "template": "full", "out": "cv.md" }
  }
}
```

**`config.example.json` is not this block copy-pasted** — it's the same shape but with two
placeholder values meant to be replaced (`person.name: "Your Name"`, `person.file_prefix:
"Your_Name"`) where `DEFAULT_CONFIG` has real defaults (`""`, `"CV"`). Every other key matches
exactly. Copy the example file to get started; treat this doc's block as the reference for what
each key *means* and what it falls back to if omitted.

## `person`

| Key | Default | Read by |
|---|---|---|
| `name` | `""` | Nothing programmatically — it's for your own reference. The CV's actual name line comes from the master's `@header-name` block. |
| `file_prefix` | `"CV"` | Every script that names an output file, e.g. `{file_prefix}_{Company}.pdf`. |
| `letter_prefix` | `null` | `null` means "derive as `CoverLetter_<file_prefix>`" — set explicitly only if you want a genuinely different prefix, not just the `CoverLetter_` convention. |

## `render`

| Key | Default | Notes |
|---|---|---|
| `default_photo` | `null` | **Root-relative.** `null` means `--photo` is required on the command line every time; set this once (e.g. `"images/me.png"`) to stop typing it. Honored by `render_cv_minimal.sh` and `render_cv_photo.sh` only — `render_cv.sh` and `render_letter.sh` have no `--photo` flag at all. |
| `default_style` | `"a"` | **Which of the four CSS style families** (`a`\|`b`\|`c`\|`z`, see `docs/CUSTOMIZING.md`) `render_cv_minimal.sh --style` falls back to when the flag isn't passed. Consumed only by `cv2html-minimal.js` — the other three renderers ignore this key entirely, since they have no style variants. |
| `browser_bin` | `null` | `null` means auto-detect (Chrome/Chromium/Edge/Brave on PATH, then well-known install locations). Set this only if auto-detection picks the wrong browser or finds none — see `engine/lib.sh`'s `find_browser()`. |

## `spine` — the locked-content contract `check_cv.py` validates against

| Key | Default | Notes |
|---|---|---|
| `locked_order` | `[]` | Experience entry ids that must be present, **in this order**, on every generated CV. |
| `title_markers` | `{}` | `{id: [substring, ...]}` — how `check_cv.py` recognizes which rendered entry corresponds to which id, by matching a substring in the entry's title line. Can name ids that aren't in `locked_order` too (e.g. an optional entry you still want recognized for coverage reporting). |
| `optional_ids` | `[]` | Ids that are valid to reference from an `application.md`'s `## Include`, and that `--coverage` tracks as PRESENT/DELIBERATE/SILENT. |
| `verbatim_ids` | `[]` | Ids whose master content must appear **byte-for-byte** somewhere in every generated CV's output — for locked lines that aren't a full Experience/Education entry (a skills note, a languages line). |
| `education.required_titles` | `[]` | Substrings that must appear in some Education entry's title (matched against the *rendered* title text, not an id — e.g. `"BSc"`). |
| `education.require_detail_for` | `[]` | Of the required titles, which ones must also have a real detail line under them — not just a bare URL. |
| `heading_aliases` | `{}` | `{"canonical key": ["alternate heading text", ...]}` — lets a non-English or reworded section heading (e.g. a translated "Experience") still map onto the checker's canonical section keys. |

**`spine_configured`** (`engine/config.py`'s `Config.spine_configured`) is `False` until at
least one of `locked_order`, `education.required_titles`, or `verbatim_ids` is non-empty. While
it's `False`, `check_cv.py` prints a `NOT CONFIGURED` banner and exits 0 rather than a
misleading "all OK" — see `docs/SPEC.md`'s validator contract. This is what makes a fresh clone
safe to run against immediately: there's genuinely nothing to check yet, and the tool says so.

## `limits`

| Key | Default | Read by |
|---|---|---|
| `soft_line_budget` | `57` | `build_cv.py` prints a non-fatal `WARNING` if a generated CV exceeds this many lines — an early signal before you find out the hard way from `verify_cvs.py`. **Minimal pipeline only** — the full pipeline never checks it, by design (there's no one-page discipline to protect there). |
| `max_pages` | `1` | `verify_cvs.py`'s default page-count gate. Override per run with `--max-pages N`; `--max-pages 0` disables the gate entirely, which is how the full-CV pipeline's multi-page `cv.md` gets verified without touching this global default. |

## `display_names`

| Key | Default | Notes |
|---|---|---|
| *(any)* | `{}` | `{"raw-name": "Display Name"}` — cosmetic renaming for anywhere a raw identifier (a project slug, a tool name) would otherwise render literally. Optional; only add entries where the raw form actually looks wrong. |

## `pipelines`

Makes `build_cv.py` data-driven instead of hardcoding a single master/template/output-filename
triple — this is what lets one `application.md` build both the tailored one-pager and the full
CV. Each entry: `master` (root-relative path), `template` (name under `templates/`, no `.md`),
`out` (filename written into the company folder).

| Key | Default | Notes |
|---|---|---|
| `minimal.master` | `master/master_cv_minimal.md` | |
| `minimal.template` | `minimal-full` | Only a fallback — `application.md`'s own front-matter `template:` key always wins for this pipeline (per-company template choice, unchanged from before this key existed). |
| `minimal.out` | `cv-minimal.md` | |
| `full.master` | `master/master_cv.md` | |
| `full.template` | `full` | Unlike `minimal`, there's no per-company override — one template for the full CV, no per-application choice needed. |
| `full.out` | `cv.md` | |

An `application.md` opts into building a pipeline via a `pipelines:` front-matter key
(comma-separated, e.g. `pipelines: minimal, full`). No `pipelines:` key at all means exactly
`minimal` — every `application.md` written before this key existed keeps building identically.
See `docs/SPEC.md`'s "The full CV — id-agnostic rendering".

## Where this fits

`config.json` is the *format*-adjacent configuration layer — it's what makes `check_cv.py` and
the renderers generic across users. Your own *policy* decisions (which specific entries are
locked, and why) belong in `master/CV_SPEC.md` as prose, cross-referenced from here by id. See
`docs/GETTING-STARTED.md` step 3 for the order to fill these in.
