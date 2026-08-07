// letter2html.js — renders a JobHuntKit cover_letter.md into a clean, prose-only HTML page (no
// CV-style section headers or entry layout, just readable paragraphs).
//
// Usage: node letter2html.js <input.md> <output.html> [title]
//
// A cover letter has no @id scheme, no template, no front matter — it's plain hand-written
// markdown: greeting paragraph, 2-4 body paragraphs, closing paragraph, then a signature block
// (name / contact line). Everything from a lone "---" line onward is internal draft/review
// notes and is never rendered — see docs/SPEC.md's build-artifact rules for the equivalent
// convention on the CV side.

const { marked } = require("marked");
const fs = require("fs");
const path = require("path");

const inputPath = process.argv[2];
const outputPath = process.argv[3];
const title = process.argv[4] || path.basename(inputPath, ".md");

// Normalize CRLF -> LF unconditionally — same confirmed-real bug class as cv2html-minimal.js
// (2026-08-01): every regex/split below is line-oriented, and a trailing "\r" makes lines fail
// to match silently instead of erroring, which reads as a paragraph quietly vanishing.
const raw = fs.readFileSync(inputPath, "utf-8").replace(/\r\n/g, "\n");

// Strip internal tailoring-note blockquote lines ("> ...") — same convention as the CV renderer.
const withoutNotes = raw
  .split("\n")
  .filter((line) => !line.trimStart().startsWith(">"))
  .join("\n");

// Cut everything from the first lone "---" line onward — internal draft/review footer, never
// meant to reach the rendered letter.
const lines = withoutNotes.split("\n");
const cutAt = lines.findIndex((line) => line.trim() === "---");
const cleaned = (cutAt === -1 ? lines : lines.slice(0, cutAt)).join("\n").trim();

// The closing block (e.g. "Best regards," / name / contact line) is the letter's last
// paragraph. Plain markdown collapses single line breaks within a paragraph into one run-on
// line, which is wrong for a signature — pull it out and render it with real line breaks
// instead of relying on every letter remembering a trailing-double-space trick.
const escapeHtml = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const paragraphs = cleaned.split(/\n\n+/);
const signature = paragraphs.pop() || "";
const bodyHtml = marked.parse(paragraphs.join("\n\n"), { gfm: true });
const signatureHtml = `<p class="signature">${signature
  .split("\n")
  .map((l) => l.trim())
  .filter(Boolean)
  .map(escapeHtml)
  .join("<br>\n")}</p>`;

const body = `${bodyHtml}\n${signatureHtml}`;

// --- Fonts --------------------------------------------------------------------------------
// Base64-embedded, no network at render time — same technique as cv2html-minimal.js. A system
// font stack ("Segoe UI" etc.) doesn't exist on the Linux/macOS CI runners, so this can't rely
// on one the way the original private-repo renderer did.

function loadFontBase64(filename) {
  return fs.readFileSync(path.join(__dirname, "fonts", filename)).toString("base64");
}

const sansReg = loadFontBase64("IBMPlexSans-Regular.woff2");
const sansSemi = loadFontBase64("IBMPlexSans-SemiBold.woff2");

const fontFaceCss = `
  @font-face { font-family: "Plex Sans"; font-weight: 400; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${sansReg}) format("woff2"); }
  @font-face { font-family: "Plex Sans"; font-weight: 600; font-style: normal; font-display: swap; src: url(data:font/woff2;base64,${sansSemi}) format("woff2"); }`;

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<style>
${fontFaceCss}
  @page { size: A4; margin: 22mm 24mm; }
  html, body {
    margin: 0; padding: 0;
    font-family: "Plex Sans", -apple-system, Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    background: #ffffff;
  }
  p { margin: 0 0 11pt; text-align: justify; hyphens: auto; }
  p.signature { margin-top: 2pt; line-height: 1.35; text-align: left; }
  strong { font-weight: 600; color: #000; }
  a { color: #1a1a1a; }
  hr { display: none; }
</style>
</head>
<body>
${body}
</body>
</html>`;

fs.writeFileSync(outputPath, html, "utf-8");
