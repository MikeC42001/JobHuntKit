// cv2html-minimal.js — renders a JobHuntKit cv-minimal.md into a one-column HTML page with a
// circular photo in the header. Companion to cv2html.js (plain ATS-safe) and cv2html-photo.js
// (two-column) — this is the third, most condensed style family.
//
// Usage: node cv2html-minimal.js <input.md> <output.html> <absolute-photo-path> [style]
//   style: a | b | c | z (default: a — the toolkit's picked direction)
//     a — "graph spine": an ember rule with a node per entry runs down Experience/Education/
//         Volunteer work, echoing a dependency-graph shape.
//     z — the original design (Segoe UI, slate-blue accent), preserved as a permanent baseline
//         and fallback. Not restyled — kept so there's always a known-good option.
//     b — "warm card header": a filled manila header band with a hard ember left edge; body
//         stays plain and quiet.
//     c — "ledger": a strict two-column grid, mono section labels in a left gutter, one hairline
//         spine, content in a wide right column. Most typographic, biggest departure from z.
//   a/b/c share one warm Claude-orange token palette and embed IBM Plex Sans + Mono from
//   render-support/fonts/ (base64, no network at render time). z keeps its own original tokens
//   and Segoe UI — it does not reference the new palette or fonts at all.
//
// Assumes the master_cv_minimal.md / cv-minimal.md shape:
//   # Name
//   contact line(s) as plain paragraph(s)
//   *optional tagline line, its own paragraph, wrapped in single asterisks* — opt-in; renders
//     under the name in every style. A file with no such line renders exactly as before.
//   > optional blockquote tailoring notes (stripped, never rendered)
//   ## About me
//   ## Education
//   ## Experience
//   ## Skills
//   ## Languages
// Education/Experience/Volunteer-work entries use: **Title** | right-aligned date/duration/
// location — split on the first "|", right-aligned everything after it.
// Skills lines use: **Label:** value, value, value — rendered (a/b/c) as a two-column
// label/value grid instead of a single bold run-on line; z keeps its original one-line-per-
// category rendering.
// Any other ## section is not dropped — appended at the end under its own heading, so nothing
// silently disappears if a future cv-minimal.md adds a section.

const { marked } = require("marked");
const fs = require("fs");
const path = require("path");

const inputPath = process.argv[2];
const outputPath = process.argv[3];
const photoPath = process.argv[4];
const style = (process.argv[5] || "a").toLowerCase();

if (!["a", "b", "c", "z"].includes(style)) {
  console.error(`cv2html-minimal: unknown style "${style}" — expected a, b, c, or z.`);
  process.exit(1);
}

// Normalize CRLF -> LF unconditionally, regardless of what wrote this file (a script, an
// editor, git autocrlf, ...). Every regex below matches per-line via "\n" splits, and a
// trailing "\r" makes those regexes silently fail to match (JS treats \r as a line
// terminator that "." can't cross and an unflagged "$" won't extend past) — which produces
// an empty-looking section (heading present, body silently dropped) instead of an error.
// Confirmed root cause of a real content-loss bug 2026-08-01 — never remove this line.
const raw = fs.readFileSync(inputPath, "utf-8").replace(/\r\n/g, "\n");

// Strip internal tailoring-note blockquote lines ("> ...") before anything else.
const cleaned = raw
  .split("\n")
  .filter((line) => !line.trimStart().startsWith(">"))
  .join("\n");

// Split into: header block (before the first "## " heading) + named sections.
const parts = cleaned.split(/^## (.+)$/m);
const headerMd = parts[0];

// Canonical section keys, plus recognized heading-text variants (English + Portuguese) that map
// to each — lets a fully-translated cv-minimal.md (Portuguese headings, e.g. "## Resumo") still
// get the right layout treatment (about-me styling, right-aligned entry dates, etc.) instead of
// falling through to the generic "any other section" renderer.
const HEADING_ALIASES = {
  "about me": ["about me", "resumo", "sobre mim"],
  education: ["education", "formação", "formacao"],
  experience: ["experience", "experiência", "experiencia"],
  "volunteer work": ["volunteer work", "voluntariado", "trabalho voluntário"],
  skills: ["skills", "competências", "competencias"],
  languages: ["languages", "línguas", "linguas", "idiomas"],
};
function canonicalKeyFor(rawNameLower) {
  for (const [canon, aliases] of Object.entries(HEADING_ALIASES)) {
    if (aliases.includes(rawNameLower)) return canon;
  }
  return rawNameLower;
}

const sections = {}; // canonical key -> raw markdown body
const sectionLabels = {}; // canonical key -> heading text as actually authored (for display)
const order = []; // original heading text, in document order
for (let i = 1; i < parts.length; i += 2) {
  const name = parts[i].trim();
  const body = parts[i + 1] || "";
  const canon = canonicalKeyFor(name.toLowerCase());
  sections[canon] = body;
  sectionLabels[canon] = name;
  order.push(name);
}

const fixedOrder = ["about me", "experience", "education", "volunteer work", "skills", "languages"];

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// --- Header parsing: name line / optional tagline line / contact line(s) --------------------
// Split once, shared by every style. A tagline is a standalone line wrapped in single asterisks
// (*...*, not **...**) appearing anywhere after the name — opt-in, most files won't have one.
// nameMd and contactMd are parsed independently rather than as one blob so each style can lay
// them out differently; parsing them separately produces the same HTML marked would have
// produced for each as part of one blob parse (block-level constructs don't interact across a
// blank-line boundary), so this is not a behavior change for files without a tagline.
function splitHeader(headerMdRaw) {
  const lines = headerMdRaw.split("\n");
  let i = 0;
  while (i < lines.length && lines[i].trim() === "") i++;
  const nameLine = lines[i] || "";
  const afterName = lines.slice(i + 1);

  let taglineInner = null;
  const contactLines = [];
  for (const line of afterName) {
    const trimmed = line.trim();
    const m = !taglineInner ? trimmed.match(/^\*([^*]+)\*$/) : null;
    if (m) {
      taglineInner = m[1];
    } else {
      contactLines.push(line);
    }
  }
  return { nameLine, contactMd: contactLines.join("\n"), taglineInner };
}

const { nameLine, contactMd, taglineInner } = splitHeader(headerMd);
const nameHtml = marked.parse(nameLine.trim(), { gfm: true });
const contactHtml = marked.parse(contactMd.trim(), { gfm: true });
const taglineHtml = taglineInner ? marked.parseInline(taglineInner, { gfm: true }) : null;
const taglineP = taglineHtml ? `<p class="tagline">${taglineHtml}</p>` : "";

// --- Shared content renderers -----------------------------------------------------------------

const ENTRY_HEAD = /^\*\*(.+?)\*\*\s*\|\s*(.+)$/;

// Splits a section's raw markdown into per-entry chunks wherever a "**Title** | date" line
// appears, rendering each as a title/date header row + the entry's own body markdown below it.
function renderEntries(bodyMd) {
  if (bodyMd === undefined) return "";
  const lines = bodyMd.split("\n");
  const entries = [];
  let current = null;
  for (const line of lines) {
    const m = line.match(ENTRY_HEAD);
    if (m) {
      if (current) entries.push(current);
      current = { title: m[1], right: m[2], bodyLines: [] };
    } else if (current) {
      current.bodyLines.push(line);
    }
  }
  if (current) entries.push(current);

  return entries
    .map((e) => {
      const bodyHtml = marked.parse(e.bodyLines.join("\n").trim(), { gfm: true });
      return `<div class="entry">
        <div class="entry-head">
          <span class="entry-title">${e.title}</span>
          <span class="entry-date">${e.right}</span>
        </div>
        ${bodyHtml}
      </div>`;
    })
    .join("");
}

function renderPlain(name, bodyMd, headingClass) {
  if (bodyMd === undefined) return "";
  const html = marked.parse(bodyMd.trim(), { gfm: true });
  return `<div class="section"><h2 class="${headingClass}">${name}</h2>${html}</div>`;
}

// z only: one line in, one <p> out — marked would otherwise merge consecutive
// "**Label:** items" lines (no blank line between them in the source) into a single flowing
// paragraph, which defeats the point of keeping each category scannable on its own line.
function renderLinePerParagraph(name, bodyMd, headingClass) {
  if (bodyMd === undefined) return "";
  const lines = bodyMd.trim().split("\n").filter((l) => l.trim());
  const html = lines.map((l) => `<p>${marked.parseInline(l.trim())}</p>`).join("");
  return `<div class="section"><h2 class="${headingClass}">${name}</h2>${html}</div>`;
}

// a/b/c only: "**Label:** value, value, value" -> a label/value row instead of a bold run-on
// line. A new row starts only on a line matching the label convention — any line after it
// without a label is a soft-wrapped continuation of that row's value (a long skills line, e.g.
// Hire & Trust's "IA/Produto" one, can legitimately wrap across two physical lines in the
// source) and gets appended, not treated as its own standalone line. Missing that distinction
// was a confirmed real bug 2026-08-01: the continuation line fell through to the no-label
// fallback and rendered as a stray <p> outside the flex row, flush at the left margin instead
// of following the value it belongs to.
function renderSkillsGrid(bodyMd) {
  if (bodyMd === undefined) return "";
  const lines = bodyMd.trim().split("\n");
  const rows = [];
  let current = null;
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;
    const m = line.match(/^\*\*(.+?):\*\*\s*(.+)$/);
    if (m) {
      if (current) rows.push(current);
      current = { label: m[1], valueParts: [m[2]] };
    } else if (/^\*[^*]+\*$/.test(line)) {
      // Single-asterisk-wrapped italic line (e.g. build_cv.py's "*Main technologies for this
      // role — full list on request.*" closing note) is never a continuation of the previous
      // label's value, even immediately after one with a blank line between them in the source
      // — it's a standalone closing remark. Without this branch, the soft-wrap-continuation
      // logic below (added for Hire&Trust's 2-line Product/AI value) silently swallows it into
      // the last skills row. Confirmed real bug, 2026-08-02, rendering the generator's
      // @skill-note. `[^*]+` (not `.+`) is what keeps this from also matching `**bold**`.
      if (current) rows.push(current);
      current = null;
      rows.push({ label: null, valueParts: [line], isNote: true });
    } else if (current) {
      current.valueParts.push(line);
    } else {
      rows.push({ label: null, valueParts: [line] });
    }
  }
  if (current) rows.push(current);

  return rows
    .map((r) => {
      const valueHtml = marked.parseInline(r.valueParts.join(" "));
      if (r.label === null) return `<p class="${r.isNote ? "skill-note" : ""}">${valueHtml}</p>`;
      // <wbr> after "/" gives the browser an explicit, word-preserving break point (e.g.
      // "frameworks/tools" -> "frameworks/" then "tools"). Needed because this render pipeline
      // does not reliably treat "/" as a soft-wrap opportunity on its own — without it, a label
      // wider than the 68pt column just overflows straight into the value column instead of
      // wrapping (confirmed real bug, 2026-08-01, on "Frameworks/Tools"). Never breaks mid-word.
      const labelHtml = marked.parseInline(r.label).replace(/\//g, "/<wbr>");
      return `<div class="skill-row"><span class="skill-label">${labelHtml}</span><span class="skill-value">${valueHtml}</span></div>`;
    })
    .join("");
}

const photoDataUri = (() => {
  const ext = path.extname(photoPath).toLowerCase();
  const mime = ext === ".png" ? "image/png" : "image/jpeg";
  const buf = fs.readFileSync(photoPath);
  return `data:${mime};base64,${buf.toString("base64")}`;
})();

// --- Fonts (a/b/c only) -------------------------------------------------------------------------

function loadFontBase64(filename) {
  return fs.readFileSync(path.join(__dirname, "fonts", filename)).toString("base64");
}

function getFontFaceCss() {
  const sansReg = loadFontBase64("IBMPlexSans-Regular.woff2");
  const sansSemi = loadFontBase64("IBMPlexSans-SemiBold.woff2");
  const monoReg = loadFontBase64("IBMPlexMono-Regular.woff2");
  const monoMed = loadFontBase64("IBMPlexMono-Medium.woff2");
  const monoSemi = loadFontBase64("IBMPlexMono-SemiBold.woff2");
  const monoBold = loadFontBase64("IBMPlexMono-Bold.woff2");
  return `
  @font-face { font-family: "Plex Sans"; font-weight: 400; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${sansReg}) format("woff2"); }
  @font-face { font-family: "Plex Sans"; font-weight: 600; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${sansSemi}) format("woff2"); }
  @font-face { font-family: "Plex Mono"; font-weight: 400; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${monoReg}) format("woff2"); }
  @font-face { font-family: "Plex Mono"; font-weight: 500; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${monoMed}) format("woff2"); }
  @font-face { font-family: "Plex Mono"; font-weight: 600; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${monoSemi}) format("woff2"); }
  @font-face { font-family: "Plex Mono"; font-weight: 700; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${monoBold}) format("woff2"); }`;
}

// Warm Claude-orange token palette, shared by a/b/c only. --ember at 3.1:1 contrast on white is
// fine for rules/graphics/large type but fails small text, so anything set small uses
// --ember-deep (5.9:1, WCAG AA) instead — a CV belonging to someone whose MSc thesis evaluated
// LLMs on WCAG-grounded accessibility issues should itself clear AA.
const TOKENS_CSS = `
  :root {
    --ink: #1C1917;
    --ember: #D97757;
    --ember-deep: #A8442A;
    --manila: #EBDBBC;
    --slate: #6B6560;
    --rule: #E4DDD6;
  }
  html, body {
    margin: 0; padding: 0;
    font-family: "Plex Sans", "Segoe UI", -apple-system, Helvetica, Arial, sans-serif;
    font-size: 10.2pt;
    line-height: 1.42;
    color: var(--ink);
    background: #ffffff;
  }
  h1 { font-family: "Plex Sans"; font-weight: 600; font-size: 25pt; letter-spacing: -0.4pt; margin: 0; color: var(--ink); }
  .tagline { font-family: "Plex Mono"; font-weight: 500; font-size: 9.5pt; color: var(--ember-deep); letter-spacing: 0.3pt; margin: 3pt 0 2pt; }
  .header-band p, .header-c-text > p, .header-card p { font-family: "Plex Mono"; font-weight: 400; font-size: 8.8pt; color: var(--slate); margin: 1pt 0; }
  .header-band a, .header-c-text a, .header-card a { color: var(--slate); text-decoration: none; white-space: nowrap; }

  .section { margin-bottom: 8pt; }
  h2.heading {
    font-family: "Plex Mono";
    font-weight: 500;
    font-size: 8.8pt;
    text-transform: uppercase;
    letter-spacing: 1.4pt;
    color: var(--ember-deep);
    margin: 0 0 6pt;
    break-after: avoid-page;
    page-break-after: avoid;
  }
  .about-me p { font-size: 10.8pt; margin: 0; color: var(--ink); }

  .entry { margin-bottom: 7pt; }
  .entry-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12pt; }
  .entry-title { font-family: "Plex Sans"; font-weight: 600; font-size: 10.8pt; color: var(--ink); }
  .entry-date { font-family: "Plex Mono"; font-weight: 400; font-size: 8.8pt; color: var(--slate); white-space: nowrap; text-align: right; font-variant-numeric: tabular-nums; }

  .skill-row { display: flex; gap: 8pt; margin: 2.5pt 0; align-items: baseline; }
  .skill-label {
    font-family: "Plex Mono"; font-weight: 700; font-size: 8.6pt; color: var(--ink);
    text-transform: lowercase;
    width: 68pt; flex-shrink: 0; min-width: 0;
    padding-top: 0.5pt;
    /* No overflow-wrap:anywhere here on purpose — that broke labels mid-letter (a real bug,
       flagged 2026-08-01). Word-preserving breaks come from an explicit <wbr> after every "/"
       in the label markup (see renderSkillsGrid) rather than relying on automatic line-breaking,
       which does not reliably treat "/" as a break point in this render pipeline — without the
       <wbr>, a label wider than 68pt just overflowed straight into the value column instead of
       wrapping. min-width:0 overrides the flex-item default (min-width:auto sizes a flex item to
       its content's intrinsic width, which fought the fixed 68pt column for the same reason). */
  }
  .skill-value { font-size: 10pt; color: var(--ink); flex: 1; min-width: 0; }
  /* Smaller + muted so the closing "full list on request" note reads as a footnote, not another
     skills row — it was rendering at the same 10pt as .skill-value with no label column to
     constrain its width, so the note visually dominated the section it's meant to be secondary
     to. Flagged 2026-08-02. */
  .skill-note { font-size: 8pt; color: var(--slate); margin: 4pt 0 0; }

  p { margin: 3pt 0; font-size: 10pt; }
  ul { margin: 3pt 0 5pt; padding-left: 14pt; }
  li { font-size: 10pt; margin: 2pt 0; }
  strong { font-weight: 600; color: var(--ink); }
  a { color: var(--ember-deep); }
  hr { display: none; }
  code { font-family: inherit; background: none; }
`;

// --- Section-body builders -----------------------------------------------------------------

// Used by z only — verbatim logic from the original single-style renderer.
function buildBodyZ() {
  let bodyHtml = "";
  for (const key of fixedOrder) {
    if (sections[key] === undefined) continue;
    const label = sectionLabels[key] || capitalize(key);
    if (key === "about me") {
      bodyHtml += `<div class="section about-me">${marked.parse(sections[key].trim(), { gfm: true })}</div>`;
    } else if (key === "education" || key === "experience" || key === "volunteer work") {
      bodyHtml += `<div class="section"><h2 class="heading">${label}</h2>${renderEntries(sections[key])}</div>`;
    } else if (key === "skills") {
      bodyHtml += renderLinePerParagraph(label, sections[key], "heading");
    } else {
      bodyHtml += renderPlain(label, sections[key], "heading");
    }
  }
  for (const name of order) {
    const canon = canonicalKeyFor(name.toLowerCase());
    if (fixedOrder.includes(canon)) continue;
    bodyHtml += renderPlain(name, sections[canon], "heading");
  }
  return bodyHtml;
}

// Used by a and b — same section markup, styled differently by each style's CSS. entriesClass
// lets a add its spine treatment (".entries.spine") while b stays plain (".entries").
function buildBodyShared(entriesClass) {
  let html = "";
  for (const key of fixedOrder) {
    if (sections[key] === undefined) continue;
    const label = sectionLabels[key] || capitalize(key);
    if (key === "about me") {
      html += `<div class="section about-me">${marked.parse(sections[key].trim(), { gfm: true })}</div>`;
    } else if (key === "education" || key === "experience" || key === "volunteer work") {
      html += `<div class="section"><h2 class="heading">${label}</h2><div class="${entriesClass}">${renderEntries(
        sections[key]
      )}</div></div>`;
    } else if (key === "skills") {
      html += `<div class="section"><h2 class="heading">${label}</h2>${renderSkillsGrid(sections[key])}</div>`;
    } else {
      html += renderPlain(label, sections[key], "heading");
    }
  }
  for (const name of order) {
    const canon = canonicalKeyFor(name.toLowerCase());
    if (fixedOrder.includes(canon)) continue;
    html += renderPlain(name, sections[canon], "heading");
  }
  return html;
}

// Used by c — each section becomes a gutter-label + content row instead of a heading + body.
function buildLedger() {
  let html = "";
  for (const key of fixedOrder) {
    if (sections[key] === undefined) continue;
    const label = sectionLabels[key] || capitalize(key);
    let contentHtml;
    if (key === "about me") {
      contentHtml = marked.parse(sections[key].trim(), { gfm: true });
    } else if (key === "education" || key === "experience" || key === "volunteer work") {
      contentHtml = `<div class="entries">${renderEntries(sections[key])}</div>`;
    } else if (key === "skills") {
      contentHtml = renderSkillsGrid(sections[key]);
    } else {
      contentHtml = marked.parse((sections[key] || "").trim(), { gfm: true });
    }
    html += `<div class="ledger-row"><div class="gutter">${label}</div><div class="content">${contentHtml}</div></div>`;
  }
  for (const name of order) {
    const canon = canonicalKeyFor(name.toLowerCase());
    if (fixedOrder.includes(canon) || sections[canon] === undefined) continue;
    html += `<div class="ledger-row"><div class="gutter">${name}</div><div class="content">${marked.parse(
      sections[canon].trim(),
      { gfm: true }
    )}</div></div>`;
  }
  return html;
}

// --- Style assembly -----------------------------------------------------------------

const CSS_Z = `
  @page { size: A4; margin: 14mm 20mm; }
  :root {
    --accent: #33475b;
    --accent-light: #eef1f4;
    --text: #1a1a1a;
    --muted: #666;
    --rule: #d5d9dd;
  }
  html, body {
    margin: 0; padding: 0;
    font-family: "Segoe UI", -apple-system, Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: var(--text);
    background: #ffffff;
  }
  body { max-width: 100%; }

  .header-band {
    display: flex;
    align-items: center;
    gap: 18pt;
    border-bottom: 2pt solid var(--accent);
    padding-bottom: 14pt;
    margin-bottom: 18pt;
  }
  .photo {
    width: 70pt;
    height: 70pt;
    border-radius: 50%;
    object-fit: cover;
    border: 2pt solid var(--accent-light);
    flex-shrink: 0;
  }
  .header-text h1 {
    font-size: 27pt;
    font-weight: 700;
    margin: 0 0 4pt;
    color: var(--accent);
    letter-spacing: 0.2px;
  }
  .header-text p {
    margin: 1pt 0;
    font-size: 10.3pt;
    color: var(--muted);
  }
  .header-text a { color: var(--muted); text-decoration: none; }
  .header-text .tagline { color: var(--accent); font-style: italic; font-size: 10.5pt; margin: 2pt 0 1pt; }

  .section { margin-bottom: 7pt; }
  h2.heading {
    font-size: 11pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--accent);
    margin: 0 0 7pt;
    padding-bottom: 3pt;
    border-bottom: 1pt solid var(--rule);
    break-after: avoid-page;
    page-break-after: avoid;
  }

  .about-me p { font-size: 11.3pt; margin: 0; color: #262626; }

  .entry { margin-bottom: 6pt; }
  .entry-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12pt;
  }
  .entry-title { font-weight: 700; font-size: 11pt; }
  .entry-date {
    font-size: 9.6pt;
    color: var(--muted);
    white-space: nowrap;
    text-align: right;
  }

  p { margin: 3pt 0; font-size: 10.6pt; }
  ul { margin: 3pt 0 4pt; padding-left: 15pt; }
  li { font-size: 10.4pt; margin: 2pt 0; }
  strong { font-weight: 700; color: #000; }
  a { color: var(--accent); }
  hr { display: none; }
  code { font-family: inherit; background: none; }
`;

const CSS_A = `
  @page { size: A4; margin: 14mm 20mm; }
  ${TOKENS_CSS}

  .header-band { display: flex; align-items: center; gap: 16pt; margin-bottom: 5pt; }
  .photo { width: 64pt; height: 64pt; border-radius: 50%; object-fit: cover; border: 2pt solid var(--ember); flex-shrink: 0; }
  /* Ember segment is exactly 68pt — the photo's outer width (64pt + 2pt border each side) — so
     the orange bar sits precisely under the photo instead of stopping at an arbitrary width. */
  .rule-duo { height: 2.2pt; margin-bottom: 18pt; background: linear-gradient(to right, var(--ember) 0, var(--ember) 68pt, var(--rule) 68pt, var(--rule) 100%); }

  /* Breathing room over the shared defaults — content was ending ~74% down the page. */
  .section { margin-bottom: 11pt; }
  .section > h2.heading { display: flex; align-items: baseline; gap: 6pt; margin-bottom: 8pt; }
  .section > h2.heading::after { content: ""; flex: 1; height: 1pt; background: var(--rule); transform: translateY(-1.5pt); }

  /* Graph spine — detached dot-line-dot segments: ". ___ . ___ . __". One 6pt
     solid ember dot per entry, and a separate hairline segment that runs alongside each entry's
     text but stops short of the dot on both ends — never touching it, unlike the earlier
     continuous-rail version (an earlier, now-superseded look with an unbroken vertical rule).
     Genuine sub-clamp width: a plain width:0.1pt box on a solid background gets silently
     clamped to Chrome's print-pipeline minimum of 1 device px (~0.75pt) — confirmed by
     decompiling the emitted PDF content stream (a rect-fill op with width exactly 1 unit at
     the page's 0.75pt/unit scale, regardless of the CSS value requested). transform:scaleX()
     escapes this: Chrome wraps a transformed element in its own Form XObject with a nested
     matrix, and THAT matrix scale is emitted verbatim, uncapped — confirmed by decompiling a
     scaleX(0.05) test box down to a genuine ~0.12pt rect. scaleX(0.15) on a width:1px
     (=0.75pt) box yields a real ~0.35pt line, well under the clamp floor, still solid
     ember at full opacity (Chrome's auto-inserted ExtGState is ca:1, blend mode Normal —
     no transparency side effect).
     Geometry: dot center x = -15.35pt in entry coords (container 16pt padding + axis at
     0.65pt); segment left = axis - (1px pre-transform width)/2 = -15.35 - 0.375 = -15.725pt,
     with transform-origin: center so scaleX shrinks it symmetrically around that axis instead
     of sliding it sideways. Dot spans y 4.65–10.65pt (top: 4.65pt, 6pt tall); segment starts a
     3pt gap below that (top: 13.65pt) and stops a 3pt gap above the NEXT entry's dot (next
     dot's top sits margin-bottom 8.5 + its own top-offset 4.65 = 13.15pt below this entry's
     bottom, so bottom: -10.15pt clears it by 3pt). The last entry has no next dot to stop
     short of, so it gets a short trailing run instead (bottom: -2pt) — the "__" that closes
     the pattern rather than vanishing.
     Clipping guard: container margin-left 4pt keeps the dot's left edge at
     4 + 16 - 18.35 = +1.65pt inside the page content box. An earlier version placed its box
     at -0.95pt and Chrome's print pipeline clipped it — confirmed on the rendered PDF (HTML
     screenshots don't show page clipping, so verify geometry numerically on the rasterized
     PDF, not just visually). */
  .entries.spine { position: relative; margin-left: 4pt; padding-left: 16pt; }
  .entries.spine .entry { position: relative; margin-bottom: 8.5pt; }
  .entries.spine .entry::before {
    content: ""; position: absolute;
    left: -18.35pt; top: 4.65pt;
    width: 6pt; height: 6pt;
    border-radius: 50%;
    background: var(--ember);
  }
  .entries.spine .entry::after {
    content: ""; position: absolute;
    left: -15.725pt; width: 1px;
    top: 13.65pt; bottom: -10.15pt;
    background: var(--ember);
    /* left is exact math-center (axis -15.35 - half of the 0.75pt pre-transform width).
       Fine centering lives entirely in translateX below, NOT in left — Chrome's print
       pipeline snaps left to a coarse ~0.75pt grid before compositing (confirmed by
       sweeping left in an isolated test: the rendered position held flat, then jumped a
       full 0.75pt in one step, then held flat again — sub-0.01pt nudges to left are a
       no-op until they cross that boundary). transform values aren't subject to the same
       snap: sweeping translateX gave smooth, continuous positioning, confirmed by measuring
       coverage-weighted pixel centroids on the rasterized PDF at 32x scale. -0.375pt is the
       measured zero-offset point (line centroid equals dot centroid to within ~0.003pt, i.e.
       raster-measurement noise). If the line ever needs to shift again, adjust translateX
       here, never left. */
    transform: translateX(-0.375pt) scaleX(0.15);
    transform-origin: center;
  }
  .entries.spine .entry:last-child::after { bottom: -2pt; }

  /* Every dot on the page speaks the node language — bullets included (marker only, text
     stays ink). */
  li::marker { color: var(--ember); }
`;

const CSS_B = `
  @page { size: A4; margin: 14mm 20mm; }
  ${TOKENS_CSS}

  .header-card {
    display: flex;
    align-items: center;
    gap: 16pt;
    background: var(--manila);
    border-left: 4pt solid var(--ember);
    padding: 14pt 20mm 14pt calc(20mm - 4pt);
    margin: 0 -20mm 18pt;
  }
  .photo { width: 60pt; height: 60pt; border-radius: 50%; object-fit: cover; border: 2pt solid #fff; flex-shrink: 0; }

  h2.heading { border-bottom: 1pt solid var(--rule); padding-bottom: 3pt; }
  .entries .entry { margin-bottom: 7pt; }
`;

const CSS_C = `
  @page { size: A4; margin: 14mm 20mm; }
  ${TOKENS_CSS}

  .header-c { display: flex; justify-content: flex-end; align-items: flex-start; gap: 14pt; margin-bottom: 10pt; }
  .header-c-text { text-align: right; }
  .header-c-text h1 { font-size: 21pt; }
  .header-c-text .tagline { justify-content: flex-end; }
  .photo-c { width: 50pt; height: 50pt; border-radius: 50%; object-fit: cover; border: 2pt solid var(--ember); flex-shrink: 0; }
  .hr-full { height: 1.4pt; background: var(--ember); margin-bottom: 14pt; }

  .ledger-row { display: flex; gap: 12pt; margin-bottom: 10pt; }
  .ledger-row .gutter {
    width: 66pt; flex-shrink: 0;
    font-family: "Plex Mono"; font-weight: 500; font-size: 8.6pt;
    text-transform: uppercase; letter-spacing: 1.2pt; color: var(--ember-deep);
    border-right: 1pt solid var(--rule);
    padding-right: 8pt; padding-top: 1pt;
  }
  .ledger-row .content { flex: 1; min-width: 0; }
  .ledger-row .section { margin-bottom: 0; }
  h2.heading { display: none; }
`;

let headerBlock;
let bodyHtml;
let cssBlock;
let fontFaceCss = "";

if (style === "z") {
  headerBlock = `<div class="header-band"><img class="photo" src="${photoDataUri}" alt="">
    <div class="header-text">${nameHtml}${taglineP}${contactHtml}</div></div>`;
  bodyHtml = buildBodyZ();
  cssBlock = CSS_Z;
} else if (style === "a") {
  headerBlock = `<div class="header-band"><img class="photo" src="${photoDataUri}" alt="">
    <div>${nameHtml}${taglineP}${contactHtml}</div></div>
    <div class="rule-duo"></div>`;
  bodyHtml = buildBodyShared("entries spine");
  cssBlock = CSS_A;
  fontFaceCss = getFontFaceCss();
} else if (style === "b") {
  headerBlock = `<div class="header-card"><img class="photo" src="${photoDataUri}" alt="">
    <div>${nameHtml}${taglineP}${contactHtml}</div></div>`;
  bodyHtml = buildBodyShared("entries");
  cssBlock = CSS_B;
  fontFaceCss = getFontFaceCss();
} else {
  // style === "c"
  headerBlock = `<div class="header-c"><div class="header-c-text">${nameHtml}${taglineP}${contactHtml}</div>
    <img class="photo-c" src="${photoDataUri}" alt=""></div>
    <div class="hr-full"></div>`;
  bodyHtml = buildLedger();
  cssBlock = CSS_C;
  fontFaceCss = getFontFaceCss();
}

const title = path.basename(inputPath, ".md");

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>${title}</title>
<style>
${fontFaceCss}
${cssBlock}
</style>
</head>
<body>
${headerBlock}
${bodyHtml}
</body>
</html>`;

fs.writeFileSync(outputPath, html, "utf-8");
