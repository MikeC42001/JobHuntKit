"""Tests for engine/extractors/ — the pluggable posting-extraction registry.

Every extractor's fixture lives under tests/fixtures/postings/<name>/. What's asserted per
extractor: matches() claims its own fixture and does not claim a competitor's, and extract()'s
body matches the fixture's expected.md byte-for-byte (modulo trailing newline).
"""

import os
from pathlib import Path

import extractors
from extractors.generic import GenericExtractor
from extractors.linkedin import LinkedInExtractor
from extractors.plaintext import PlaintextExtractor
from conftest import FIXTURES_DIR

POSTINGS_DIR = os.path.join(FIXTURES_DIR, "postings")


def _fixture(name, input_name="input.html"):
    d = os.path.join(POSTINGS_DIR, name)
    with open(os.path.join(d, input_name), "r", encoding="utf-8") as f:
        html = f.read()
    expected_path = os.path.join(d, "expected.md")
    expected = None
    if os.path.isfile(expected_path):
        with open(expected_path, "r", encoding="utf-8") as f:
            expected = f.read().rstrip("\n")
    return html, expected


# ---------------------------------------------------------------------------
# registry / dispatch
# ---------------------------------------------------------------------------

def test_list_extractors_includes_every_registered_one():
    names = extractors.list_extractors()
    assert names == ["linkedin", "plaintext", "generic"]


def test_get_extractor_by_name():
    assert isinstance(extractors.get_extractor("linkedin"), LinkedInExtractor)


def test_get_extractor_unknown_name_raises_keyerror():
    try:
        extractors.get_extractor("nonexistent")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_pick_dispatches_to_highest_confidence():
    html, _ = _fixture("linkedin")
    chosen, score = extractors.pick(html=html, url=None, path=Path("input.html"))
    assert chosen.name == "linkedin"
    assert score > 0


def test_pick_forced_name_skips_dispatch():
    html, _ = _fixture("linkedin")  # a page linkedin.py would normally win
    chosen, _ = extractors.pick(html=html, url=None, path=Path("input.html"), forced_name="generic")
    assert chosen.name == "generic"


def test_generic_always_matches_with_low_confidence():
    assert GenericExtractor().matches(html="<p>anything at all</p>", url=None, path=Path("x.html")) >= 1


# ---------------------------------------------------------------------------
# generic
# ---------------------------------------------------------------------------

def test_generic_extracts_the_fixture():
    html, expected = _fixture("generic")
    draft = GenericExtractor().extract(html=html, url=None)
    assert draft.body == expected
    assert draft.source == "generic"
    assert GenericExtractor().matches(html=html, url=None, path=Path("input.html")) >= 1


def test_generic_does_not_outscore_linkedin_on_the_linkedin_fixture():
    html, _ = _fixture("linkedin")
    generic_score = GenericExtractor().matches(html=html, url=None, path=Path("input.html"))
    linkedin_score = LinkedInExtractor().matches(html=html, url=None, path=Path("input.html"))
    assert linkedin_score > generic_score


# ---------------------------------------------------------------------------
# plaintext
# ---------------------------------------------------------------------------

def test_plaintext_extracts_the_fixture():
    html, expected = _fixture("plaintext", input_name="input.txt")
    draft = PlaintextExtractor().extract(html=html, url=None)
    assert draft.body == expected
    assert draft.source == "plaintext"


def test_plaintext_matches_txt_extension_with_high_confidence():
    html, _ = _fixture("plaintext", input_name="input.txt")
    score = PlaintextExtractor().matches(html=html, url=None, path=Path("input.txt"))
    assert score >= 50


def test_plaintext_does_not_claim_real_html():
    html, _ = _fixture("generic")
    score = PlaintextExtractor().matches(html=html, url=None, path=Path("input.html"))
    assert score == 0


# ---------------------------------------------------------------------------
# linkedin
# ---------------------------------------------------------------------------

def test_linkedin_extracts_the_job_page_fixture():
    html, expected = _fixture("linkedin")
    draft = LinkedInExtractor().extract(html=html, url="https://www.linkedin.com/jobs/view/12345")
    assert draft.body == expected
    assert draft.title == "Platform Engineer at Riverstone Labs"
    assert draft.source == "linkedin"
    assert LinkedInExtractor().matches(html=html, url=None, path=Path("input.html")) >= 70


def test_linkedin_refuses_a_feed_card():
    html, _ = _fixture("linkedin-feedcard")
    try:
        LinkedInExtractor().extract(html=html, url=None)
        assert False, "expected ExtractionError on a feed-card page"
    except extractors.ExtractionError as e:
        assert "feed card" in str(e) or "search-results" in str(e)


def test_linkedin_feedcard_still_recognized_as_linkedin_by_matches():
    """matches() should still report high confidence — it's extract() that refuses, not
    dispatch, so a bad extraction is traceable rather than silently falling through to generic."""
    html, _ = _fixture("linkedin-feedcard")
    score = LinkedInExtractor().matches(html=html, url="https://www.linkedin.com/jobs/search/", path=Path("input.html"))
    assert score >= 50


def test_linkedin_does_not_claim_an_unrelated_page():
    html, _ = _fixture("generic")
    score = LinkedInExtractor().matches(html=html, url=None, path=Path("input.html"))
    assert score == 0
