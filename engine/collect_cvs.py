#!/usr/bin/env python3
"""collect_cvs.py — stage rendered CVs into a send-me-these-next folder.

Every renderer drops its output at applications/offer-pages/<Company>/generate-pdfs/cv-minimal.pdf
— fine for the build pipeline, useless for actually sending: a folder full of identically-named
files buried one level deep each, under a filename no recruiter should ever see.

This copies each one out to <root>/produced/to_send/<file_prefix>_<Company>.pdf, so there's a
single folder to eyeball before applying. Once you've actually sent one, move it into
<root>/produced/sent/ — that's both the manual archive and the "stop showing me this" signal: a
company already in sent/ is skipped on the next run and won't reappear in to_send/.

Usage:
    python engine/collect_cvs.py                    # copy everything not already in sent/
    python engine/collect_cvs.py --force             # re-copy everything, even what's in sent/
    python engine/collect_cvs.py --force Attio Acme  # re-copy just these (folder or display name)

Exit code 0 if every company's source PDF exists (copied, skipped, or stale — all fine), 1 if any
source PDF is missing (unrendered — run render_cv_minimal.sh first).
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


def default_targets(cfg):
    pattern = os.path.join(cfg.offer_pages_dir, "*", "generate-pdfs", "cv-minimal.pdf")
    return sorted(glob.glob(pattern))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("--force", nargs="*", metavar="COMPANY", default=None,
                         help="re-copy even companies already in sent/. With no names, applies "
                              "to every company; with names, only to those (folder or display "
                              "name, case-insensitive).")
    args = parser.parse_args()

    cfg = cfgmod.resolve(args.root)
    force_all = args.force is not None and len(args.force) == 0
    force_companies = args.force or []

    os.makedirs(to_send_dir(cfg), exist_ok=True)
    os.makedirs(os.path.join(cfg.produced_dir, "sent"), exist_ok=True)

    targets = default_targets(cfg)
    if not targets:
        print("collect_cvs: no rendered CVs found under applications/offer-pages/*/generate-pdfs/.", file=sys.stderr)
        return 1

    missing = []
    copied = []
    skipped = []
    stale = []

    for src in targets:
        company = company_label(src)
        to_send_path = to_send_pdf_path(cfg, company)

        if not os.path.isfile(src):
            print(f"{company:15s}  MISSING SOURCE -- {src}")
            missing.append(company)
            continue

        already_sent = is_sent(cfg, company)
        forced = force_all or any(matches_force_arg(cfg, company, arg) for arg in force_companies)

        if already_sent and not forced:
            sent_path = sent_pdf_path(cfg, company)
            src_mtime = os.path.getmtime(src)
            sent_mtime = os.path.getmtime(sent_path)
            if src_mtime > sent_mtime:
                print(f"{company:15s}  STALE -- sent copy is older than the current source (edited since sending)")
                stale.append(company)
            else:
                print(f"{company:15s}  skipped (already in sent/)")
            skipped.append(company)
            continue

        shutil.copy2(src, to_send_path)
        note = " (forced, was in sent/)" if already_sent and forced else ""
        print(f"{company:15s}  copied -> to_send/{os.path.basename(to_send_path)}{note}")
        copied.append(company)

    print()
    print(f"collect_cvs: {len(copied)} copied, {len(skipped)} skipped, {len(stale)} stale, {len(missing)} missing source.")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
