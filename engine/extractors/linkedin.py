"""extractors/linkedin.py — LinkedIn job pages, with a loud refusal for the one real failure
mode already seen in production use: a saved *feed card* (a search-results listing snippet)
instead of the actual job-details page. That happened for real: the saved HTML had no
requirements content at all, and the flow silently fell back to a hand-typed text file.
This extractor is built specifically not to repeat that: if it recognizes
the page as LinkedIn but can't find the job-details container, it raises instead of emitting an
empty PostingDraft.

Markup fingerprints below are current as of the pages this was built against and will drift as
LinkedIn's own markup changes — same caveat every site-specific extractor in this package carries
(see docs/EXTRACTORS.md). A drifted fingerprint degrades to generic.py's dump, not a crash: it's
only ExtractionError, not this whole extractor being picked, that a refusal produces.
"""

import re
from pathlib import Path
from typing import Optional

from .base import PostingDraft
from .generic import PostingTextExtractor


class ExtractionError(Exception):
    """Raised when an extractor recognizes the input as belonging to its site but can't find a
    real job posting in it. Caught by extract_posting.py's CLI and reported as an actionable
    failure instead of silently writing a content-free posting_extracted.md."""


# Matches <meta property="og:X" content="Y"> and the (rarer) content-before-property attribute
# order some pages emit.
_OG_META_RE = re.compile(
    r'<meta[^>]+property=["\']og:([\w:]+)["\'][^>]+content=["\']([^"\']*)["\']', re.IGNORECASE
)
_OG_META_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:([\w:]+)["\']', re.IGNORECASE
)

# Real job-details-page container classes — presence means the actual posting content is here.
_JOB_PAGE_MARKERS = (
    "jobs-description",
    "job-details-jobs-unique-sub-description",
    "jobs-box__html-content",
)
# Feed-card / search-results-listing classes — presence without a job-page marker above means
# this is LinkedIn, but the wrong page.
_FEED_CARD_MARKERS = ("job-card-container", "base-search-card", "jobs-search-results-list")


def _og_tags(html):
    tags = {}
    for pattern, order in ((_OG_META_RE, "prop_content"), (_OG_META_RE_ALT, "content_prop")):
        for a, b in pattern.findall(html):
            prop, content = (a, b) if order == "prop_content" else (b, a)
            tags.setdefault(prop.lower(), content)
    return tags


class LinkedInExtractor:
    name = "linkedin"

    def matches(self, *, html: str, url: Optional[str], path: Path) -> int:
        score = 0
        if url and "linkedin.com" in url.lower():
            score = max(score, 70)
        if _og_tags(html).get("site_name", "").lower() == "linkedin":
            score = max(score, 60)
        lowered = html.lower()
        if any(marker in lowered for marker in _JOB_PAGE_MARKERS):
            score = max(score, 80)
        elif any(marker in lowered for marker in _FEED_CARD_MARKERS):
            score = max(score, 55)  # confidently LinkedIn, just not a job-details page
        return score

    def extract(self, *, html: str, url: Optional[str]) -> PostingDraft:
        lowered = html.lower()
        if not any(marker in lowered for marker in _JOB_PAGE_MARKERS):
            raise ExtractionError(
                "this looks like a saved LinkedIn page but not a job-details page — likely a "
                "feed card or search-results snippet, which has no requirements content to "
                "extract. Re-save the posting's own page (open the job, then Save Page As), or "
                "pass --extractor generic if you want the raw dump anyway."
            )

        og = _og_tags(html)
        parser = PostingTextExtractor()
        parser.feed(html)

        return PostingDraft(
            title=og.get("title") or parser.title,
            company=None,
            location=None,
            work_mode=None,
            salary=None,
            seniority=None,
            body=parser.text(),
            source=self.name,
            apply_url=url,
        )
