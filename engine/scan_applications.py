#!/usr/bin/env python3
"""scan_applications.py — classifies every offer-pages company for the cv-tailor agent flow.

Answers two questions per company, independently:
  - Is there an application.md yet? If not, is there raw posting content (HTML/posting.md/
    posting_extracted.md) waiting to be drafted from? -> NEW / INCOMPLETE / (has one ->) CURRENT
    or STALE.
  - STALE means build_cv.py would produce different output than what's on disk right now — either
    application.md was edited, or the master content changed since this company was last built.
    Computed by literally reusing build_cv.py's build_company() in its diff mode, the same
    function build_cv.py --check itself calls — not a re-implementation that could drift from
    what the real build does.
  - Is it sent yet? Reuses cv_common.is_sent() — the same cv/produced/sent/ signal
    collect_cvs.py has always used. Tracked independently for the CV and (if one was ever
    rendered) the cover letter, since collect_cvs.py and collect_letters.py stage/archive them
    separately.
  - Was it deliberately declined? cv_common.is_declined() — the produced/not_sent/ signal, so a
    company you decided not to pursue reads as DECLINED, not as "still needs sending."

Usage:
    python engine/scan_applications.py                    # full classification table, all companies
    python engine/scan_applications.py --target new        # paths only (one per line), for scripting
    python engine/scan_applications.py --target not-sent    #   has application.md, not sent, any staleness
    python engine/scan_applications.py --target stale       #   not-sent AND stale only (the safe default —
                                                              #   a sent+stale company is reported but never
                                                              #   auto-targeted this way)
    python engine/scan_applications.py --target all         #   every company with an application.md
    python engine/scan_applications.py --target "<Company>" #   one company, matched by folder or display name

Exit code 0 unless a company's application.md fails to parse/build (a real error, printed to
stderr) — a company merely being NEW or STALE is not a failure.
"""

import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod  # noqa: E402
from build_cv import BuildError, build_company, parse_master  # noqa: E402
from cv_common import (  # noqa: E402
    all_company_dirs,
    company_label,
    is_declined,
    is_sent,
    matches_force_arg,
)

RAW_CONTENT_GLOBS = ["*.html", "posting.md", "posting_extracted.md"]


def artifact_state(cfg, company, has_artifact, prefix=None):
    """None if the artifact doesn't exist at all (e.g. no cover letter written for this company).
    Otherwise one of SENT / DECLINED / pending."""
    if not has_artifact:
        return None
    if is_sent(cfg, company, prefix=prefix):
        return "SENT"
    if is_declined(cfg, company, prefix=prefix):
        return "DECLINED"
    return "pending"


def has_raw_content(company_dir):
    return any(glob.glob(os.path.join(company_dir, pattern)) for pattern in RAW_CONTENT_GLOBS)


def classify(cfg, company_dir, master):
    """Returns (status, detail) where status is one of
    NEW / INCOMPLETE / CURRENT / STALE / ERROR."""
    app_path = os.path.join(company_dir, "application.md")
    if not os.path.isfile(app_path):
        if has_raw_content(company_dir):
            return "NEW", None
        return "INCOMPLETE", "no application.md and no raw posting content (html/posting.md)"

    try:
        _label, diff, _warning = build_company(cfg, company_dir, master, check_only=True)
    except BuildError as e:
        return "ERROR", str(e)
    return ("STALE" if diff else "CURRENT"), None


def scan_all(cfg):
    master = parse_master(cfg.master_path)
    rows = []
    for company_dir in all_company_dirs(cfg):
        company = company_label(company_dir)
        status, detail = classify(cfg, company_dir, master)
        active = status in ("CURRENT", "STALE", "ERROR")
        has_letter = os.path.isfile(os.path.join(company_dir, "generate-pdfs", "cover_letter.pdf"))
        cv_state = artifact_state(cfg, company, active) if active else None
        letter_state = artifact_state(cfg, company, active and has_letter, prefix=cfg.letter_prefix)
        rows.append({
            "company": company,
            "dir": company_dir,
            "status": status,
            "detail": detail,
            "cv_state": cv_state,
            "letter_state": letter_state,
            # kept for any external caller still reading the old boolean field
            "sent": cv_state == "SENT",
        })
    return rows


def relpath(cfg, company_dir):
    return os.path.relpath(company_dir, cfg.root).replace(os.sep, "/")


def print_report(rows):
    for r in rows:
        if r["status"] in ("NEW", "INCOMPLETE"):
            cv_tag = ""
        else:
            cv_tag = f"  CV:{r['cv_state']}"
        letter_tag = f"  Letter:{r['letter_state']}" if r["letter_state"] else ""
        detail = f"  -- {r['detail']}" if r["detail"] else ""
        print(f"{r['company']:15s}  {r['status']:10s}{cv_tag}{letter_tag}{detail}")

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    stale_sent = sum(1 for r in rows if r["status"] == "STALE" and r["cv_state"] == "SENT")
    declined = sum(1 for r in rows if r["cv_state"] == "DECLINED")
    print()
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    print(f"scan_applications: {len(rows)} companies — {summary}")
    if stale_sent:
        print(f"  ({stale_sent} of the STALE compan{'y is' if stale_sent == 1 else 'ies are'} "
              f"already SENT — won't be touched by --target stale; use --target all or name it "
              f"directly if you want to rebuild it anyway)")
    if declined:
        print(f"  ({declined} compan{'y is' if declined == 1 else 'ies are'} DECLINED — excluded "
              f"from --target not-sent/stale; name it directly if you want to touch it anyway)")


def resolve_target(cfg, rows, target):
    t = target.lower()
    if t == "new":
        return [r for r in rows if r["status"] == "NEW"]
    if t == "not-sent":
        return [r for r in rows if r["status"] in ("CURRENT", "STALE") and r["cv_state"] == "pending"]
    if t == "stale":
        return [r for r in rows if r["status"] == "STALE" and r["cv_state"] == "pending"]
    if t == "all":
        return [r for r in rows if r["status"] in ("CURRENT", "STALE")]
    # single company, matched by folder or display name
    matches = [r for r in rows if matches_force_arg(cfg, r["company"], target)]
    return matches


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("--target", help="new | not-sent | stale | all | <Company>")
    args = parser.parse_args()

    cfg = cfgmod.resolve(args.root)

    if not os.path.isfile(cfg.master_path):
        print(f"scan_applications: master not found at {cfg.master_path}", file=sys.stderr)
        return 1

    rows = scan_all(cfg)
    errors = [r for r in rows if r["status"] == "ERROR"]

    if args.target:
        targets = resolve_target(cfg, rows, args.target)
        for r in targets:
            print(relpath(cfg, r["dir"]))
        if not targets:
            print(f"scan_applications: no companies matched --target {args.target!r}", file=sys.stderr)
    else:
        print_report(rows)

    if errors:
        print(file=sys.stderr)
        print(f"scan_applications: {len(errors)} compan{'y' if len(errors)==1 else 'ies'} failed to build:", file=sys.stderr)
        for r in errors:
            print(f"  {r['company']}: {r['detail']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
