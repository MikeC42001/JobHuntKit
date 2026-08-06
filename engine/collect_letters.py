#!/usr/bin/env python3
"""collect_letters.py — stage ONE rendered cover letter into the send-me-these-next folder.

Deliberately different from collect_cvs.py's "copy everything not yet sent" default: cover
letters are written and reviewed one company at a time, on purpose — you name the company, every
time. There is no bare/--all mode here.

Copies applications/offer-pages/<Company>/generate-pdfs/cover_letter.pdf to
<root>/produced/to_send/<letter_prefix>_<Company>.pdf, alongside the CV of the same name. Once
sent, move it into <root>/produced/sent/ — same manual-archive / "stop showing me this" signal as
the CVs, tracked independently per company (a company can have its CV sent but its letter still
pending, or vice versa).

Usage:
    python engine/collect_letters.py Acme            # stage just Acme's rendered letter
    python engine/collect_letters.py --force Acme     # re-stage even if already in sent/

Exit code 0 on a successful copy or skip, 1 if the named company has no rendered cover letter, or
if no company was given at all.
"""

import argparse
import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod  # noqa: E402
from cv_common import (  # noqa: E402
    company_label,
    is_sent,
    matches_force_arg,
    sent_pdf_path,
    to_send_dir,
    to_send_pdf_path,
)


def all_rendered_letters(cfg):
    pattern = os.path.join(cfg.offer_pages_dir, "*", "generate-pdfs", "cover_letter.pdf")
    return sorted(glob.glob(pattern))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("company", help="exactly one company (folder or display name)")
    parser.add_argument("--force", action="store_true",
                         help="re-stage even if already in sent/")
    args = parser.parse_args()

    cfg = cfgmod.resolve(args.root)

    os.makedirs(to_send_dir(cfg), exist_ok=True)
    os.makedirs(os.path.join(cfg.produced_dir, "sent"), exist_ok=True)

    matches = [src for src in all_rendered_letters(cfg) if matches_force_arg(cfg, company_label(src), args.company)]

    if not matches:
        print(f"collect_letters: no rendered cover letter found for '{args.company}'.", file=sys.stderr)
        print('  (render one first: bash engine/render_letter.sh "applications/offer-pages/<Company>/cover_letter.md")', file=sys.stderr)
        return 1

    src = matches[0]
    company = company_label(src)
    to_send_path = to_send_pdf_path(cfg, company, prefix=cfg.letter_prefix)

    already_sent = is_sent(cfg, company, prefix=cfg.letter_prefix)

    if already_sent and not args.force:
        sent_path = sent_pdf_path(cfg, company, prefix=cfg.letter_prefix)
        src_mtime = os.path.getmtime(src)
        sent_mtime = os.path.getmtime(sent_path)
        if src_mtime > sent_mtime:
            print(f"{company}: STALE -- sent copy is older than the current source (edited since sending). Use --force to re-stage.")
        else:
            print(f"{company}: already in sent/ -- nothing to do. Use --force to re-stage anyway.")
        return 0

    shutil.copy2(src, to_send_path)
    note = " (forced, was in sent/)" if already_sent and args.force else ""
    print(f"{company}: copied -> to_send/{os.path.basename(to_send_path)}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
