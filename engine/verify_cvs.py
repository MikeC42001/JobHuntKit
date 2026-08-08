#!/usr/bin/env python3
"""verify_cvs.py — page-count gate for rendered CV PDFs.

This toolkit's default template is a one-page layout by design. Reading the raw PDF bytes and
counting `/Type /Page` object markers is a reliable, dependency-free way to confirm a render
came out exactly the length it should — no PDF library needed.

Usage:
    python engine/verify_cvs.py                          # checks every offer-pages company's cv-minimal.pdf
    python engine/verify_cvs.py path/to/one.pdf other.pdf  # checks specific files instead
    python engine/verify_cvs.py --root path/to/data        # point at a different root
    python engine/verify_cvs.py --max-pages 0 some.pdf     # report page counts, no pass/fail gate
    python engine/verify_cvs.py --max-pages 3 some.pdf     # gate at a different page count

Exit code 0 if every checked PDF matches config.json's limits.max_pages (default 1), 1
otherwise — usable as a real gate, not just a printout. --max-pages overrides that count for
this run only (config.json's limits.max_pages, and the default gate on cv-minimal.pdf, are
unaffected); --max-pages 0 disables the gate entirely, for multi-page artifacts (e.g. the full
CV) that have no fixed length to check against — page counts still print, just without a
pass/fail verdict.

Does NOT check layout/spacing/alignment — those are visual judgment calls and stay manual
(open the PDF and look), not something a pass/fail script should try to automate.
"""

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod

# Matches "/Type /Page" object markers but not "/Type /Pages" (the page-tree node) — the
# trailing [^s] guard is what excludes that false hit.
PAGE_MARKER = re.compile(rb"/Type\s*/Page[^s]")


def count_pages(pdf_path):
    with open(pdf_path, "rb") as f:
        data = f.read()
    return len(PAGE_MARKER.findall(data))


def default_targets(cfg):
    pattern = os.path.join(cfg.offer_pages_dir, "*", "generate-pdfs", "cv-minimal.pdf")
    return sorted(glob.glob(pattern))


def company_label(pdf_path):
    # .../offer-pages/<Company>/generate-pdfs/cv-minimal.pdf -> <Company>
    parts = os.path.normpath(pdf_path).split(os.sep)
    try:
        return parts[parts.index("offer-pages") + 1]
    except (ValueError, IndexError):
        return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("pdfs", nargs="*", help="specific PDF paths to check instead of scanning")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="override the page-count gate for this run (0 disables it entirely); "
        "defaults to config.json's limits.max_pages",
    )
    args = parser.parse_args()

    cfg = cfgmod.resolve(args.root)
    targets = args.pdfs if args.pdfs else default_targets(cfg)

    if not targets:
        print("verify_cvs: no PDFs found to check.", file=sys.stderr)
        return 1

    max_pages = args.max_pages if args.max_pages is not None else cfg.max_pages
    gate_enabled = max_pages != 0

    failures = []
    for path in targets:
        label = company_label(path)
        if not os.path.isfile(path):
            print(f"{label:15s}  MISSING -- {path}")
            failures.append(path)
            continue
        pages = count_pages(path)
        if gate_enabled:
            status = "" if pages == max_pages else f"  <-- NOT {max_pages} PAGE(S)"
            print(f"{label:15s}  {pages} page(s){status}")
            if pages != max_pages:
                failures.append(path)
        else:
            print(f"{label:15s}  {pages} page(s)")

    print()
    if failures:
        print(f"verify_cvs: {len(failures)} of {len(targets)} FAILED.")
        return 1
    print(f"verify_cvs: all {len(targets)} OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
