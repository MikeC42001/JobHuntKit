"""extractors/plaintext.py — passthrough for input that isn't HTML at all.

Covers two real cases from the private pipeline this was ported from: a `.txt` file (someone
manually transcribed a posting that couldn't be saved as HTML — a LinkedIn feed snippet with no
real job page behind it, an API response, a screenshot OCR'd by hand) and pasted text handed
directly to the agent flow rather than saved to a file first. Both arrive here as plain text with
no markup to strip, so this is the simplest extractor in the package — no parsing at all, just
whitespace normalization.
"""

from pathlib import Path
from typing import Optional

from .base import PostingDraft

# A cheap "does this look like it has HTML tags in it" probe — good enough to tell prose apart
# from markup without a real parser. Matches "<" immediately followed by a letter or "/", which
# covers "<div", "<p>", "</span>", etc. but not a bare "<" in prose (e.g. "revenue < target").
_LOOKS_LIKE_HTML = ("<html", "<body", "<!doctype", "<div", "<p>", "<span")


class PlaintextExtractor:
    name = "plaintext"

    def matches(self, *, html: str, url: Optional[str], path: Path) -> int:
        if path.suffix.lower() == ".txt":
            return 60
        lowered = html.lower()
        if any(tag in lowered for tag in _LOOKS_LIKE_HTML):
            return 0
        # No .txt extension and no obvious markup — plausibly pasted text saved with some other
        # extension, or piped in directly. Low confidence: generic.py's HTMLParser-based dump is
        # harmless on plain text too (it just won't strip anything), so let a real HTML match
        # always win over this guess.
        return 2

    def extract(self, *, html: str, url: Optional[str]) -> PostingDraft:
        lines = [line.strip() for line in html.splitlines()]
        # Collapse blank-line runs, same convention as generic.py's text(), so output shape is
        # consistent across extractors regardless of which one ran.
        out_lines = []
        blank_run = False
        for line in lines:
            if line:
                out_lines.append(line)
                blank_run = False
            elif not blank_run:
                out_lines.append("")
                blank_run = True
        body = "\n".join(out_lines).strip("\n")
        title = next((line for line in out_lines if line), None)
        return PostingDraft(
            title=title,
            company=None,
            location=None,
            work_mode=None,
            salary=None,
            seniority=None,
            body=body,
            source=self.name,
            apply_url=url,
        )
