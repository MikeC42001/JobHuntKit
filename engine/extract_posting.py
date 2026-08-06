#!/usr/bin/env python3
"""extract_posting.py — turn a saved job-posting page (or a plaintext/pasted file) into a
posting_extracted.md, via the pluggable engine/extractors/ registry.

Not a clean extraction on its own — the point is to get something small and text-only enough to
skim for the actual role content and hand-write a curated posting.md from (see
docs/EXTRACTORS.md). Which extractor ran, the source, and today's date are recorded in the
output's header, so a bad extraction is traceable back to what produced it.

Usage:
    python engine/extract_posting.py "applications/offer-pages/<Company>/<file>.html"
    python engine/extract_posting.py <file> --extractor linkedin   # force one, skip dispatch
    python engine/extract_posting.py <file> --url "https://..."     # record the source URL
    python engine/extract_posting.py --list-extractors

Writes posting_extracted.md beside the source file (fixed name, not derived from the source
filename — matches the existing convention). Prints the output path on success.

Exit code 1 if the source file is missing, or if the picked extractor recognizes the input as its
site but refuses to extract it (e.g. a saved LinkedIn feed card instead of the actual job page —
see extractors/linkedin.py). Exit 0 for --list-extractors.

No --root: like md_to_email_txt.py, this takes an explicit file path and never resolves anything
root-relative — there's no root-scoped state for it to need.
"""

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extractors import ExtractionError, list_extractors, pick  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("html_path", nargs="?", help="path to a saved HTML page or plaintext file")
    parser.add_argument("--extractor", help="force a specific extractor by name, skip auto-dispatch")
    parser.add_argument("--list-extractors", action="store_true", help="print every registered extractor and exit")
    parser.add_argument("--url", help="the posting's source URL, recorded in the output header")
    args = parser.parse_args()

    if args.list_extractors:
        for name in list_extractors():
            print(name)
        return 0

    if not args.html_path:
        parser.error("pass a path, or --list-extractors")

    if not os.path.isfile(args.html_path):
        print(f"extract_posting: not found: {args.html_path}", file=sys.stderr)
        return 1

    path = Path(args.html_path)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    extractor, confidence = pick(html=html, url=args.url, path=path, forced_name=args.extractor)

    try:
        draft = extractor.extract(html=html, url=args.url)
    except ExtractionError as e:
        print(f"extract_posting: {extractor.name} extractor refused this input: {e}", file=sys.stderr)
        return 1

    out_path = path.parent / "posting_extracted.md"
    heading = draft.title or path.name
    today = datetime.date.today().isoformat()

    header_lines = [f"_Extracted from `{path.name}` via the `{extractor.name}` extractor (confidence {confidence}), {today}._"]
    if args.url:
        header_lines.append(f"_Source URL: {args.url}_")

    content = (
        f"# {heading}\n\n"
        + "\n".join(header_lines) + "\n\n"
        "---\n\n"
        f"{draft.body}\n"
    )
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    print(f"extract_posting: wrote {out_path} via '{extractor.name}' extractor ({len(draft.body)} chars of body text)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
