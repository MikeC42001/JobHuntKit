# EXTRACTORS.md — adding a posting extractor

`engine/extract_posting.py` turns a saved job-posting page (or a plaintext/pasted file) into a
`posting_extracted.md` — not a clean extraction, just something small and text-only enough to
skim for the actual role content and hand-write a curated `posting.md` from. Every job board has
a different DOM, so extraction is a registry of small, independent extractors under
`engine/extractors/`, not one fixed parser.

This is the best "good first issue" this repo can offer: a bounded, one-file contract, no
understanding of the CV engine required, and each contribution ships with its own fixture — it
can't accidentally break another extractor's behavior.

## The contract

Two methods (`engine/extractors/base.py`):

```python
class Extractor(Protocol):
    name: str

    def matches(self, *, html: str, url: Optional[str], path: Path) -> int:
        """0 = can't handle this. 1-100 = confidence, higher wins. Never raises."""
        ...

    def extract(self, *, html: str, url: Optional[str]) -> PostingDraft:
        """Only called on the extractor that won dispatch."""
        ...
```

`matches()` scores on cheap signals, cheapest first: the URL's host (if one was passed via
`--url`), then `<meta property="og:...">` tags, then site-specific DOM fingerprints (a class
name, an `id`, a `data-*` attribute your target site's real pages carry). No network access, no
third-party dependency — everything stays stdlib `html.parser`, which is what keeps this
toolkit's "clone and run, no pip install" property true for extraction too. See
`engine/extractors/linkedin.py` for a worked example, including the pattern for refusing a page
that matches your site but isn't actually a job-details page (see "Refuse, don't guess" below).

## Steps

1. **Create `engine/extractors/<yoursite>.py`** implementing the two methods above. Reuse
   `extractors.generic.PostingTextExtractor` for the actual tag-stripping if your site's page is
   still fundamentally an HTML document once you've confirmed the right container is present —
   most extractors will look like "find markers, strip tags, done."
2. **Register it** in `engine/extractors/__init__.py`'s `_REGISTRY` list. Order only matters as a
   tiebreaker between equal `matches()` scores.
3. **Add a fixture** at `tests/fixtures/postings/<yoursite>/{input.html,expected.md}` — hand-
   written *minimal* synthetic HTML reproducing only the structural quirk your extractor keys on
   (a couple of nav/noise elements plus the real container), never a real saved page. Real pages
   are unusable as fixtures on two counts: they carry someone else's personal/third-party data,
   and they're several MB each with a sidecar asset folder. Generate `expected.md` by actually
   running your extractor against the fixture and saving its `.body` output — don't hand-transcribe
   what you expect it to produce.
4. **Add a test** to `tests/test_extractors.py`: your extractor's `matches()` claims your fixture
   and does *not* claim another extractor's fixture; `extract()` output matches `expected.md`.
5. **Run** `python -m pytest tests/test_extractors.py`, `ruff check engine scripts tests`, and
   `python3 scripts/audit_public.py` — a synthetic fixture with a realistic-looking email or
   phone number will trip the leak gate; use `example.com`/`example.org` addresses and avoid
   phone-shaped digit strings.

## Refuse, don't guess

If your site can produce a page that *matches* your extractor but doesn't actually contain a job
posting (a search-results listing, a feed card, a "sign in to view" wall), have `extract()` raise
`extractors.ExtractionError` with a message telling the person what to do instead — re-save the
right page, or fall back to `--extractor generic`. A loud, actionable failure beats silently
writing a content-free `posting_extracted.md` that someone won't notice is empty until they're
confused why `application.md` has nothing to work from. `linkedin.py`'s feed-card refusal is the
worked example — it exists because exactly that silent-failure case happened once in production
use of the private pipeline this package was ported from.

## What's already covered

`generic` (always matches, lowest confidence — the fallback of last resort), `plaintext` (`.txt`
files and pasted text, no markup to strip), `linkedin` (job-details pages, refuses feed cards).
Greenhouse, Lever, Workday, and Indeed are open — each has fairly stable, inspectable markup (a
`data-automation-id` here, a `.posting-headline` there) that would make for a clean single-file
contribution, but whether any of them are actually worth building is an open question
(`community/OPEN_QUESTIONS.md`'s Q-003), not yet approved work.
