// cv2html.js — renders any JobHuntKit CV markdown (a built cv.md, a master file, or a
// hand-written file with no @id scheme at all) into a clean, single-column, ATS-safe HTML page:
// no columns, no icons, no photo — just solid typography and spacing. Companion to
// cv2html-photo.js (two-column, circular photo, more attractive but less ATS-safe).
//
// Usage: node cv2html.js <input.md> <output.html> [title]
//
// Because the input may be a master file rather than a built artifact, this converter cleans
// its own input rather than assuming build_cv.py already did:
//   - every "<!-- ... -->" comment is stripped, including the "<!-- @id -->" content markers
//     a master carries (they're not stripped upstream the way a template's doc-comments are —
//     see build_cv.py's COMMENT_RE, which only runs on templates, never on the master itself)
//   - everything from a "<!-- render:stop -->" tag onward is dropped — e.g. a master's trailing
//     "## Notes for tailoring" section, which would otherwise render into the PDF, since this
//     converter (unlike cv2html-minimal.js) doesn't recognize CV section headings at all and
//     just passes every "##" through
//   - lines starting with "> " (internal tailoring notes / blockquote asides) are stripped, same
//     convention as every other renderer here

const { marked } = require("marked");
const fs = require("fs");
const path = require("path");

const inputPath = process.argv[2];
const outputPath = process.argv[3];
const title = process.argv[4] || path.basename(inputPath, ".md");

const escapeHtml = (s) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Normalize CRLF -> LF unconditionally — confirmed-real bug class (2026-08-01): every regex/
// split below is line-oriented, and a trailing "\r" makes a line silently fail to match instead
// of erroring, which reads as content quietly vanishing.
const raw = fs.readFileSync(inputPath, "utf-8").replace(/\r\n/g, "\n");

// Cut everything from a "<!-- render:stop -->" tag onward, before any other comment stripping —
// once generic comment-stripping runs, the tag itself is gone and there's nothing left to find.
const stopped = raw.replace(/<!--\s*render:stop\s*-->[\s\S]*$/, "");

// Strip every remaining HTML comment, including "<!-- @id -->" markers — mirrors build_cv.py's
// COMMENT_RE, applied here instead of upstream since the input may never have passed through
// build_cv.py at all.
const uncommented = stopped.replace(/<!--[\s\S]*?-->\n?/g, "");

// Strip internal tailoring-note blockquote lines ("> ...") — not for the reader.
const cleaned = uncommented
  .split("\n")
  .filter((line) => !line.trimStart().startsWith(">"))
  .join("\n");

let body = marked.parse(cleaned, { gfm: true });

// Wrap the H1 + immediately-following contact paragraph(s) (1 or 2 <p> lines) in a header
// block, so CSS can style/border them as a unit regardless of whether the contact line is
// split across one or two markdown lines. A master's header (name + four separate one-line
// blocks: location, phone, email, linkedin) has more than two paragraphs after the H1 — only
// the first 1-2 get wrapped, the rest render as plain paragraphs below. Cosmetic, not fixed
// here: this converter renders whatever's there, it doesn't reassemble the header the way
// build_cv.py's minimal pipeline does.
body = body.replace(
  /^(\s*<h1>.*?<\/h1>\s*(?:<p>[\s\S]*?<\/p>\s*){1,2})/,
  '<div class="header">$1</div>'
);

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<style>
  @page { size: A4; margin: 13mm 16mm; }
  html, body {
    margin: 0; padding: 0;
    font-family: "Segoe UI", -apple-system, Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.32;
    color: #1a1a1a;
    background: #ffffff;
  }
  body { max-width: 100%; }
  .header { border-bottom: 1.4pt solid #1a1a1a; padding-bottom: 8pt; margin-bottom: 10pt; }
  .header h1 {
    font-size: 22pt;
    font-weight: 600;
    margin: 0 0 2pt;
    letter-spacing: 0.2px;
  }
  .header p {
    margin: 1pt 0 0;
    font-size: 9.5pt;
    color: #444;
  }
  .header a { color: #444; text-decoration: none; }
  h2 {
    font-size: 10.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    color: #1a1a1a;
    margin: 11pt 0 4pt;
    padding-bottom: 2pt;
    border-bottom: 0.75pt solid #bbb;
    break-after: avoid-page;
    page-break-after: avoid;
  }
  h2:first-of-type { margin-top: 4pt; }
  h3 {
    font-size: 10.8pt;
    font-weight: 700;
    margin: 7pt 0 1pt;
    break-after: avoid-page;
    page-break-after: avoid;
  }
  p { margin: 2.5pt 0; font-size: 10.5pt; }
  ul { margin: 2pt 0 6pt; padding-left: 15pt; }
  li { font-size: 10.3pt; margin: 1.5pt 0; }
  strong { font-weight: 700; color: #000; }
  em { color: #333; }
  a { color: #1a1a1a; }
  hr { display: none; }
  code { font-family: inherit; background: none; }
</style>
</head>
<body>
${body}
</body>
</html>`;

fs.writeFileSync(outputPath, html, "utf-8");
