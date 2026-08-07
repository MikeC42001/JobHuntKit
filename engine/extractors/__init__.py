"""engine/extractors — pluggable job-posting extraction.

Every job board — LinkedIn, Greenhouse, Lever, Workday, Indeed, a plain company careers page —
has a different DOM, and pasted text or a .txt file isn't HTML at all. One fixed parser can't
keep covering all of that, so extraction is a registry of small, independent extractors instead.
See docs/EXTRACTORS.md to add one: implement matches() + extract(), drop the file in, register it
below, ship a synthetic fixture.

Dispatch picks whichever registered extractor reports the highest confidence from matches();
generic.py always returns at least 1, so there is always a fallback and extraction never comes up
with nothing to run. --extractor <name> (on extract_posting.py's CLI) forces one, skipping
dispatch entirely.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from .base import Extractor, PostingDraft
from .generic import GenericExtractor
from .linkedin import ExtractionError, LinkedInExtractor
from .plaintext import PlaintextExtractor

# Order matters only as a matches()-score tiebreaker (first registered wins a tie) — put
# site-specific extractors before the generic fallbacks.
_REGISTRY: List[Extractor] = [
    LinkedInExtractor(),
    PlaintextExtractor(),
    GenericExtractor(),  # always last — the fallback of last resort
]


def list_extractors() -> List[str]:
    return [e.name for e in _REGISTRY]


def get_extractor(name: str) -> Extractor:
    for e in _REGISTRY:
        if e.name == name:
            return e
    raise KeyError(f"no registered extractor named {name!r} — see list_extractors()")


def pick(*, html: str, url: Optional[str], path: Path, forced_name: Optional[str] = None) -> Tuple[Extractor, int]:
    """Returns (extractor, confidence). With forced_name, uses that extractor unconditionally —
    its matches() score is still computed and returned, but purely informationally, so a forced
    choice with confidence 0 is visibly a deliberate override rather than a real match. Without
    forced_name, picks the highest-confidence extractor in registration order (first wins ties)."""
    if forced_name:
        extractor = get_extractor(forced_name)
        return extractor, extractor.matches(html=html, url=url, path=path)

    best = None
    best_score = -1
    for extractor in _REGISTRY:
        score = extractor.matches(html=html, url=url, path=path)
        if score > best_score:
            best = extractor
            best_score = score
    return best, best_score


__all__ = [
    "Extractor",
    "PostingDraft",
    "ExtractionError",
    "list_extractors",
    "get_extractor",
    "pick",
]
