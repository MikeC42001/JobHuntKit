"""extractors/generic.py — the always-matches stdlib-only fallback.

Turns any HTML page into a plain text dump: not a clean extraction (nav/sidebar/other-page
chrome comes along with it, since this is a text dump, not a readability engine), just small
enough and text-only enough to skim for the actual role content and hand-write a curated
posting.md from. Good enough for a simple, text-heavy job page; not a general-purpose HTML
readability engine. matches() always returns 1 so dispatch never comes up empty — every other
extractor beats this one whenever it's actually confident.

No third-party dependency (no bs4/lxml) — uses only html.parser.HTMLParser from the stdlib, so
the engine's "clone and run, no pip install" property holds for extraction too.
"""

from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from .base import PostingDraft

# Elements whose content should never appear in the extracted text.
SKIP_CONTENT_TAGS = {"script", "style", "noscript", "svg", "head", "template"}

# Block-level elements: force a line break around them so paragraphs don't run together.
BLOCK_TAGS = {
    "p", "div", "li", "br", "tr", "section", "article", "header", "footer",
    "ul", "ol", "table", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
}


class PostingTextExtractor(HTMLParser):
    """The tag-stripping engine underlying GenericExtractor — also reused by linkedin.py, since a
    LinkedIn job page still benefits from the same script/style/nav-noise stripping once its
    job-page container has been confirmed present."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self._skip_depth = 0
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag in SKIP_CONTENT_TAGS:
            self._skip_depth += 1
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in SKIP_CONTENT_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._in_title:
            if self.title is None:
                self.title = data.strip()
            return
        if self._skip_depth:
            return
        self._chunks.append(data)

    def text(self):
        raw = "".join(self._chunks)
        # Collapse runs of horizontal whitespace, then collapse blank-line runs, then strip each
        # line — the block-tag newlines above are what give this any paragraph structure at all.
        lines = [" ".join(line.split()) for line in raw.split("\n")]
        out_lines = []
        blank_run = False
        for line in lines:
            if line:
                out_lines.append(line)
                blank_run = False
            elif not blank_run:
                out_lines.append("")
                blank_run = True
        return "\n".join(out_lines).strip("\n")


class GenericExtractor:
    name = "generic"

    def matches(self, *, html: str, url: Optional[str], path: Path) -> int:
        return 1

    def extract(self, *, html: str, url: Optional[str]) -> PostingDraft:
        parser = PostingTextExtractor()
        parser.feed(html)
        return PostingDraft(
            title=parser.title,
            company=None,
            location=None,
            work_mode=None,
            salary=None,
            seniority=None,
            body=parser.text(),
            source=self.name,
            apply_url=url,
        )
