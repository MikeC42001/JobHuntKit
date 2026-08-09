# CUSTOMIZING.md — which file do I edit?

Three separate layers, each owned by a different file. Mixing them up is the single most common
confusion working on this toolkit — "I changed the template but the PDF didn't move that
section" (render order is hardcoded, not template order) is the classic version of it. This doc
is the map; `docs/SPEC.md` and `docs/CONFIG.md` are the mechanical reference for each layer's
own rules.

## The three layers

| Layer | Answers | Owned by |
|---|---|---|
| **Content** | What does the CV say? | `master/master_cv.md`, `master/master_cv_minimal.md`, each company's `application.md` |
| **Structure** | Which sections exist, and in what order do they *appear in the source file*? | `templates/*.md` |
| **Look** | Fonts, margins, columns, colors — what order sections actually *render in the PDF* | `engine/render-support/cv2html*.js` |

The structure/look split is the trap: for the **minimal** pipeline, the template's section order
is cosmetic — `cv2html-minimal.js` hardcodes its own render order (`fixedOrder`, line 101)
regardless of what order `templates/minimal-full.md` puts things in. Reordering the template
changes the `.md` file and nothing in the PDF. For the **full** pipeline it's the opposite:
`cv2html.js` has no section model at all, so `templates/full.md`'s order *is* the PDF's order.

## Which file do I edit?

| I want to change... | Edit |
|---|---|
| The wording of a job/skill/project entry | `master/master_cv.md` first (full wording), then condense the same `@id` into `master/master_cv_minimal.md` (terser) — see `docs/SPEC.md`'s "Id inheritance" |
| What one company's CV includes | that company's `application.md` — `## Include`/`## Omit`/`## Projects` |
| Which sections exist, and their order in the source file | `templates/minimal-full.md` (one-pager) or `templates/full.md` (long-form) |
| The PDF's actual look — fonts, margins, colors | the matching `engine/render-support/cv2html*.js` (see the table below) |
| Which of the four minimal styles is the default | `config.json` → `render.default_style` |
| A new posting-source extractor (LinkedIn, Greenhouse, ...) | `docs/EXTRACTORS.md` |
| Add a brand new PDF variant | this doc, below |

## The four renderers

Each `render_*.sh` script is a thin wrapper: resolve `--root`, find a browser, run one JS
converter to produce HTML, then `--print-to-pdf` it. **All CSS lives inline in the JS
converter — there is no `.css` file anywhere in this repo.**

| Renderer | Converter | Output | Style variants |
|---|---|---|---|
| `render_cv_minimal.sh` | `cv2html-minimal.js` | one-page tailored CV | **`a`(default) `b` `c` `z`** |
| `render_cv.sh` | `cv2html.js` | full CV, single-column, ATS-safe | none |
| `render_cv_photo.sh` | `cv2html-photo.js` | full CV, two-column + photo | none |
| `render_letter.sh` | `letter2html.js` | cover letter | none |

`render_cv.sh` and `render_cv_photo.sh` are **id-agnostic**: point either at a built `cv.md`, a
master file directly, or any hand-written markdown — no `@id` scheme required. See
`docs/SPEC.md`'s "The full CV — id-agnostic rendering" for the comment-stripping contract that
makes this safe.

### Page size and margins are CSS, not a browser flag

`engine/lib.sh`'s `browser_flags()` only sets `--headless`, `--disable-gpu`, and header/footer
suppression — no `--paper-width`/`--margin-*`. Every converter sets its own `@page { size: A4;
margin: ...; }` inside its CSS. For `cv2html-minimal.js`, this means **margins are declared four
separate times, once per style** (`CSS_Z`, `CSS_A`, `CSS_B`, `CSS_C` each carry their own `@page`
line) — not factored into the shared `TOKENS_CSS`. Changing one style's margins doesn't touch
the others.

### Fonts are embedded, not linked

`engine/render-support/fonts/` holds IBM Plex Sans/Mono `.woff2` files, read off disk and
inlined as base64 `data:` URIs — no network request at render time, which is what keeps CI
renders reproducible across ubuntu/macOS/Windows. Not every converter uses them:

| Converter | Fonts |
|---|---|
| `cv2html-minimal.js` styles `a`/`b`/`c` | Plex Sans + Plex Mono (`getFontFaceCss()`) |
| `cv2html-minimal.js` style `z` | none — falls back to `"Segoe UI"` |
| `letter2html.js` | Plex Sans only |
| `cv2html.js`, `cv2html-photo.js` | none — system font stack (`"Segoe UI", -apple-system, ...`) |

The two full-CV renderers not using the bundled fonts means their output looks slightly
different across operating systems — a known gap, not a bug, since ATS-safety was the design
goal there, not pixel-identical rendering.

## The `a`/`b`/`c`/`z` style family, in `cv2html-minimal.js`

Four independent CSS template literals over one shared token set:

| Block | What it is |
|---|---|
| `TOKENS_CSS` | shared palette/spacing tokens, used by `a`/`b`/`c` |
| `CSS_Z` | the original baseline — self-contained, doesn't use `TOKENS_CSS` or the bundled fonts |
| `CSS_A` | "graph spine" — the default |
| `CSS_B` | warm card header |
| `CSS_C` | two-column ledger layout (unrelated to `render_cv_photo.sh`'s two columns — this one stays inside the one-page tailored pipeline) |

Selected by `render_cv_minimal.sh --style a\|b\|c\|z`, falling back to `config.json`'s
`render.default_style`, then `"a"`. Any style but the default writes `cv-minimal-<style>.pdf`
instead of `cv-minimal.pdf`, so a comparison render never clobbers the default file.

## Adding a fifth style, A to Z

Five touchpoints, in order:

1. **`cv2html-minimal.js`, the validation array** (`if (!["a", "b", "c", "z"].includes(style))`)
   — add `"d"`.
2. **`cv2html-minimal.js`, a new CSS block** — `const CSS_D = \`${TOKENS_CSS} ...\`` (or fully
   self-contained like `CSS_Z`, if you don't want the shared tokens).
3. **`cv2html-minimal.js`, the dispatch chain** (`if (style === "z") { ... } else if (style ===
   "a") { ... } else if (style === "b") { ... } else { // style === "c" ... }`) — insert a new
   `} else if (style === "d") { ... }` branch **before** the final `else`. That final `else` is
   style `c`'s fallthrough, not a generic default — appending your branch after it makes it
   unreachable dead code. This is the one real trap in this recipe.
4. **`render_cv_minimal.sh`** — add `d` to the `case "$STYLE" in a|b|c|z) ;; ...` guard, and
   update the three usage comments that spell out the legal values (the top-of-file `Usage:`
   line, the `--style` flag description, and the `Usage:` error message near the bottom).
5. **Optionally**, set `config.json`'s `render.default_style` to `"d"` to make it the default.

Verify: `node --check engine/render-support/cv2html-minimal.js`, then render the demo with the
new style and confirm it writes `cv-minimal-d.pdf` without touching `cv-minimal.pdf` (run from
the repo root — file paths are relative to your shell's cwd, not `--root`, which only affects
config lookups):

```bash
bash engine/render_cv_minimal.sh --style d --photo examples/demo/images/avatar.png \
  "examples/demo/applications/offer-pages/Orbital Dynamics/cv-minimal.md"
```

## Adding a new posting-source extractor

Different layer entirely — see [`docs/EXTRACTORS.md`](EXTRACTORS.md).

## Adding a whole new renderer (not just a style)

More work than a style variant: a new `render_cv_<name>.sh` (copy an existing one, adjust the
usage comment and output filename) plus a new `engine/render-support/cv2html-<name>.js` (copy
the converter closest to what you want — `cv2html.js` if you want no section model,
`cv2html-photo.js` if you want one). No dispatch chain to extend, since each renderer is its own
script — but do add the new `.js` file to `.github/workflows/ci.yml`'s `node --check` list and
`CONTRIBUTING.md`'s pre-PR command, or CI won't catch a syntax error in it.
