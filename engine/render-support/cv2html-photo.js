// cv2html-photo.js — renders any JobHuntKit CV markdown into a modern two-column HTML page
// with a circular photo in the header band. Companion to cv2html.js (the plain, ATS-safe,
// single-column, no-photo renderer) — this one trades some ATS-parsing safety for a more
// attractive human-facing layout. Id-agnostic, same as cv2html.js: works on a built cv.md, a
// master file pointed at directly, or a hand-written file with no @id scheme.
//
// Usage: node cv2html-photo.js <input.md> <output.html> <absolute-photo-path> [title]
//
// Assumes the same loose shape as cv2html.js's input:
//   # Name
//   contact line(s) as plain paragraph(s)
//   > optional blockquote tailoring notes (stripped, never rendered)
//   ## Summary / About me
//   ## Experience
//   ## Education
//   ## Skills   (lines like "**Label:** item, item, item")
// Any other ## section found is not dropped — it's appended to the sidebar under its own
// heading, so nothing silently disappears if the input doesn't match this shape exactly (e.g.
// a master uses "## About me" rather than "## Summary" — it still renders, just in the
// sidebar rather than the featured left column).
//
// Because the input may be a master file rather than a built artifact, this converter cleans
// its own input the same way cv2html.js does — see that file's header comment for why:
//   - every "<!-- ... -->" comment is stripped, including "<!-- @id -->" content markers
//   - everything from a "<!-- render:stop -->" tag onward is dropped (e.g. a master's
//     trailing "## Notes for tailoring" section)
//   - lines starting with "> " are stripped

const { marked } = require("marked");
const fs = require("fs");
const path = require("path");

const inputPath = process.argv[2];
const outputPath = process.argv[3];
const photoPath = process.argv[4];
const title = process.argv[5] || path.basename(inputPath, ".md");

const escapeHtml = (s) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Normalize CRLF -> LF unconditionally, regardless of what wrote this file (a script, an
// editor, git autocrlf, ...). The Skills-line regex below matches per-line via "\n" splits,
// and a trailing "\r" makes it silently fail to match (JS treats \r as a line terminator
// that "." can't cross and an unflagged "$" won't extend past) — producing an empty-looking
// section instead of an error. Confirmed root cause of a real content-loss bug 2026-08-01 —
// never remove this line.
const raw = fs.readFileSync(inputPath, "utf-8").replace(/\r\n/g, "\n");

// Cut everything from a "<!-- render:stop -->" tag onward, before any other comment stripping —
// once generic comment-stripping runs, the tag itself is gone and there's nothing left to find.
const stopped = raw.replace(/<!--\s*render:stop\s*-->[\s\S]*$/, "");

// Strip every remaining HTML comment, including "<!-- @id -->" markers — mirrors build_cv.py's
// COMMENT_RE, applied here instead of upstream since the input may never have passed through
// build_cv.py at all.
const uncommented = stopped.replace(/<!--[\s\S]*?-->\n?/g, "");

// Strip internal tailoring-note blockquote lines ("> ...") before anything else.
const cleaned = uncommented
  .split("\n")
  .filter((line) => !line.trimStart().startsWith(">"))
  .join("\n");

// Split into: header block (everything before the first "## " heading) + named sections.
const parts = cleaned.split(/^## (.+)$/m);
const headerMd = parts[0];
const sections = {}; // lowercased heading -> raw markdown body
const order = []; // original-case heading names, in source order
for (let i = 1; i < parts.length; i += 2) {
  const name = parts[i].trim();
  const body = parts[i + 1] || "";
  sections[name.toLowerCase()] = body;
  order.push(name);
}

function renderSection(name, bodyMd, headingClass) {
  if (bodyMd === undefined) return "";
  const html = marked.parse(bodyMd.trim(), { gfm: true });
  return `<div class="section"><h2 class="${headingClass}">${name}</h2>${html}</div>`;
}

// Skills: parse "**Label:** item, item, item" lines into tag-pill groups instead of the
// default marked <p> rendering — same source data, a different presentation.
function renderSkills(bodyMd) {
  if (bodyMd === undefined) return "";
  const lines = bodyMd.trim().split("\n").filter((l) => l.trim());
  let html = '<div class="section"><h2 class="side-heading">Skills</h2>';
  for (const line of lines) {
    const m = line.match(/^\*\*(.+?):\*\*\s*(.+)$/);
    if (!m) continue;
    const label = m[1];
    const items = m[2].split(",").map((s) => s.trim()).filter(Boolean);
    html += `<div class="skill-group"><div class="skill-label">${label}</div><div class="skill-pills">`;
    for (const item of items) {
      html += `<span class="pill">${item}</span>`;
    }
    html += `</div></div>`;
  }
  html += "</div>";
  return html;
}

// Header: H1 name + following contact paragraph(s).
const headerHtml = marked.parse(headerMd.trim(), { gfm: true });

// Left column: Summary (or About me), Experience, Education, in that fixed order (whichever
// exist).
const leftOrder = ["summary", "about me", "experience", "education"];
let leftHtml = "";
let leftFirst = true;
for (const key of leftOrder) {
  if (sections[key] === undefined) continue;
  const isFirst = leftFirst;
  leftFirst = false;
  leftHtml += renderSection(
    isFirst ? "" : capitalize(key),
    sections[key],
    isFirst ? "sr-only" : "main-heading"
  );
}
// The first left-column section renders without a visible heading (styled as the intro
// paragraph, like the reference layout) — done above by passing an empty heading name and
// hiding it via CSS.

// Right column: Skills first, then any section not already placed in the left column
// (nothing gets silently dropped even if the input has a section this script doesn't expect).
let rightHtml = renderSkills(sections["skills"]);
for (const name of order) {
  const key = name.toLowerCase();
  if (leftOrder.includes(key) || key === "skills") continue;
  rightHtml += renderSection(name, sections[key], "side-heading");
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const photoDataUri = (() => {
  const ext = path.extname(photoPath).toLowerCase();
  const mime = ext === ".png" ? "image/png" : "image/jpeg";
  const buf = fs.readFileSync(photoPath);
  return `data:${mime};base64,${buf.toString("base64")}`;
})();

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<style>
  @page { size: A4; margin: 10mm 13mm; }
  :root {
    --accent: #33475b;      /* slate/blue accent — distinct from any reference CV's palette */
    --accent-light: #eef1f4;
    --text: #1a1a1a;
    --muted: #5a5a5a;
    --rule: #d5d9dd;
  }
  html, body {
    margin: 0; padding: 0;
    font-family: "Segoe UI", -apple-system, Helvetica, Arial, sans-serif;
    font-size: 9.7pt;
    line-height: 1.26;
    color: var(--text);
    background: #ffffff;
  }
  body { max-width: 100%; }

  /* Header band: name/contact on the left, photo on the right */
  .header-band {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14pt;
    border-bottom: 1.6pt solid var(--accent);
    padding-bottom: 6pt;
    margin-bottom: 8pt;
  }
  .header-text { min-width: 0; }
  .header-band h1 {
    font-size: 22pt;
    font-weight: 700;
    margin: 0 0 3pt;
    color: var(--accent);
    letter-spacing: 0.2px;
  }
  .header-band p {
    margin: 1pt 0 0;
    font-size: 9.5pt;
    color: var(--muted);
  }
  .header-band a { color: var(--muted); text-decoration: none; }
  .photo {
    width: 68pt;
    height: 68pt;
    border-radius: 50%;
    object-fit: cover;
    border: 2pt solid var(--accent-light);
    flex-shrink: 0;
  }

  /* Two-column body */
  .body-grid {
    display: flex;
    gap: 18pt;
  }
  .col-main { flex: 0 0 62%; max-width: 62%; }
  .col-side { flex: 0 0 34%; max-width: 34%; }

  .section { margin-bottom: 6pt; }
  h2.main-heading, h2.side-heading {
    font-size: 9.6pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--accent);
    margin: 0 0 3pt;
    padding-bottom: 1.5pt;
    border-bottom: 1pt solid var(--rule);
  }
  h2.sr-only { display: none; }

  /* First left-column section's intro paragraph (no visible heading, italic, like the
     reference layout) */
  .col-main .section:first-child p {
    font-style: italic;
    color: var(--muted);
    margin: 0 0 7pt;
  }

  p { margin: 2pt 0; font-size: 9.7pt; }
  ul { margin: 1.5pt 0 5pt; padding-left: 12pt; }
  li { font-size: 9.4pt; margin: 1pt 0; }
  strong { font-weight: 700; color: #000; }
  em { color: var(--muted); }
  a { color: var(--accent); }
  hr { display: none; }
  code { font-family: inherit; background: none; }

  /* Skill tag-pills */
  .skill-group { margin-bottom: 7pt; }
  .skill-label {
    font-weight: 700;
    font-size: 9pt;
    color: var(--text);
    margin-bottom: 3pt;
  }
  .skill-pills { display: flex; flex-wrap: wrap; gap: 3pt 4pt; }
  .pill {
    display: inline-block;
    background: var(--accent-light);
    color: var(--accent);
    border-radius: 9pt;
    padding: 2pt 7pt;
    font-size: 8.3pt;
    font-weight: 600;
    white-space: nowrap;
  }
</style>
</head>
<body>
<div class="header-band">
  <div class="header-text">${headerHtml}</div>
  <img class="photo" src="${photoDataUri}" alt="">
</div>
<div class="body-grid">
  <div class="col-main">${leftHtml}</div>
  <div class="col-side">${rightHtml}</div>
</div>
</body>
</html>`;

fs.writeFileSync(outputPath, html, "utf-8");
