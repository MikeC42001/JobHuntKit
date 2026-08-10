"""extractors/base.py — the contract every posting extractor implements.

Two methods, both stateless (a new instance per call is fine, and the registry does exactly
that): matches() scores how confident this extractor is that it can handle a given input, and
extract() does the actual work. See docs/EXTRACTORS.md for the how-to; this file is the contract
those docs describe.

Python 3.8 target — this repo has no third-party dependencies for the engine, and a stdlib-only
install has to work on whatever Python 3.8+ a user already has. Use typing.Optional, not the
3.10+ "X | None" syntax, anywhere in this package.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol


@dataclass
class PostingDraft:
    """What an extractor hands back — the raw material a person (or an agent) curates into
    posting.md. Every field except body/source/apply_url is best-effort and may be None; nothing
    downstream should assume a field is populated."""

    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    work_mode: Optional[str]
    salary: Optional[str]
    seniority: Optional[str]
    body: str  # cleaned markdown-ish text — the requirements/description content
    source: str  # this extractor's name, recorded in posting_extracted.md's header
    apply_url: Optional[str]


class Extractor(Protocol):
    """An extractor is any object with a `name` attribute and these two methods — no base class
    to inherit from, just this shape. See generic.py for the always-matches fallback and
    linkedin.py for a real site-specific example."""

    name: str

    def matches(self, *, html: str, url: Optional[str], path: Path) -> int:
        """0 = cannot handle this input at all. 1-100 = confidence, higher wins. Must never
        raise — an extractor that can't tell should return 0, not throw."""
        ...

    def extract(self, *, html: str, url: Optional[str]) -> PostingDraft:
        """Only called on the extractor that won dispatch. May raise ExtractionError (see
        __init__.py) if the input looks like this extractor's site but doesn't actually contain
        a full job posting — loud failure beats emitting a content-free PostingDraft."""
        ...
