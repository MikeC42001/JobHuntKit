#!/usr/bin/env python3
"""check_cv.py — structure gate + coverage report for cv-minimal.md files.

Two independent checks, matching verify_cvs.py's style (per-file line, summary, exit 1 on
failure).

STRUCTURE (default) reads each company's cv-minimal.md and confirms your locked spine actually
landed correctly: Experience order, Education (every required title present, and any title
flagged in config.json's spine.education.require_detail_for isn't stripped to a bare URL),
and every id in spine.verbatim_ids appearing byte-for-byte somewhere in the output. This is the
kind of check that catches an entry silently missing or reordered on one application out of
twenty — the class of bug a manual read-through misses.

COVERAGE (--coverage) answers "what from the master is present here, deliberately left out, or
silently missing" for a company's application.md — every id in spine.optional_ids, plus every
`proj-*` block auto-discovered from the master. Requires application.md; a company with only a
posting saved (no application.md yet) is reported as such, not guessed at.

Everything spine-shaped (which entries are locked and in what order, which title substrings
identify them, which ids must appear verbatim, which education titles need a detail line) comes
from config.json's `spine` block — see docs/CONFIG.md. A fresh clone with no spine configured
prints a NOT CONFIGURED banner instead of a false "all OK": see cfg.spine_configured.

Usage:
    python engine/check_cv.py                                # structure sweep, every company
    python engine/check_cv.py applications/offer-pages/Acme    # structure check, one company
    python engine/check_cv.py --coverage                       # coverage sweep, every migrated company
    python engine/check_cv.py --coverage applications/offer-pages/Acme
    python engine/check_cv.py --root path/to/your/data

Exit code: structure mode returns 1 if any company FAILs. Coverage mode always returns 0 — a
SILENT item is a prompt to decide, not a hard gate.
"""

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod
from build_cv import COMMENT_RE, TOKEN_RE, parse_application, parse_master  # noqa: E402

ENTRY_HEAD = re.compile(r"^\*\*(.+?)\*\*\s*\|\s*(.+)$")
BARE_URL_RE = re.compile(r"^https?://\S+$")


# ---------------------------------------------------------------------------
# cv-minimal.md structural parsing (independent of build_cv.py — this reads the *output* shape,
# which both a generated file and any hand-written one in the same convention share)
# ---------------------------------------------------------------------------

def alias_to_canon(cfg):
    """Maps a heading's own text (lowercased) to a canonical key. With no configured aliases,
    canon == the heading's own lowercase text (English works out of the box); config.json's
    spine.heading_aliases lets other-language headings ("Experiência") map onto the same
    canonical key ("experience") the checks below key off of."""
    mapping = {}
    for canon, aliases in cfg.heading_aliases_extra.items():
        for alias in aliases:
            mapping[alias.lower()] = canon
    return mapping


def split_sections(text, alias_map):
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    sections = {}
    for j in range(1, len(parts), 2):
        heading = parts[j].strip()
        canon = alias_map.get(heading.lower(), heading.lower())
        sections[canon] = parts[j + 1]
    return sections


def parse_entries(body):
    """Returns [(title, body_lines), ...] in source order, mirroring the renderer's own
    entry-grouping (a line before the first entry header is discarded)."""
    entries = []
    current = None
    for raw_line in body.split("\n"):
        line = raw_line.rstrip()
        m = ENTRY_HEAD.match(line) if line.strip() else None
        if m:
            current = (m.group(1), [])
            entries.append(current)
        elif current is not None and line.strip():
            current[1].append(line.strip())
    return entries


def identify(cfg, title):
    """title substring -> locked-spine id, used to recognize entries in rendered output. Config
    order matters: spine.title_markers is a dict of id -> [substrings, ...], walked in the order
    config.json declares it."""
    for spine_id, markers in cfg.title_markers.items():
        for marker in markers:
            if marker in title:
                return spine_id
    return None


# ---------------------------------------------------------------------------
# Structure check
# ---------------------------------------------------------------------------

def check_structure(cfg, company_dir, alias_map):
    path = os.path.join(company_dir, "cv-minimal.md")
    if not os.path.isfile(path):
        return [f"MISSING {path}"]

    with open(path, "r", encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    sections = split_sections(text, alias_map)
    failures = []

    # --- Experience: locked order + locked entries present ---
    exp_entries = parse_entries(sections.get("experience", ""))
    seen_positions = {}
    for idx, (title, _body) in enumerate(exp_entries):
        spine_id = identify(cfg, title)
        if spine_id and spine_id not in seen_positions:
            seen_positions[spine_id] = idx

    locked_order = cfg.locked_order
    for spine_id in locked_order:
        if spine_id not in seen_positions:
            pretty = spine_id.replace("exp-", "").replace("-", " ")
            failures.append(f"experience: '{pretty}' entry missing")

    present_order = [sid for sid in locked_order if sid in seen_positions]
    positions = [seen_positions[sid] for sid in present_order]
    if positions != sorted(positions):
        pretty_order = ", ".join(sid.replace("exp-", "") for sid in locked_order)
        failures.append(
            f"experience order wrong: found {[p.replace('exp-', '') for p in present_order]} "
            f"at positions {positions} (expected ascending: {pretty_order})"
        )

    # --- Education: every required title present, flagged ones aren't a bare URL ---
    edu_entries = parse_entries(sections.get("education", ""))
    titles = [t for t, _ in edu_entries]
    for required in cfg.education_required_titles:
        if not any(required in t for t in titles):
            failures.append(f"education: {required} entry missing")

    require_detail_for = cfg.education_require_detail_for
    for title, body_lines in edu_entries:
        matched = next((req for req in require_detail_for if req in title), None)
        if not matched:
            continue
        content_lines = [line for line in body_lines if line.strip()]
        if not content_lines:
            failures.append(f"education: {matched} has no detail line at all")
        elif len(content_lines) == 1 and BARE_URL_RE.match(content_lines[0].strip()):
            failures.append(
                f"education: {matched} detail stripped to a bare URL, no descriptive sentence"
            )

    # --- Verbatim ids: each one appears byte-for-byte somewhere in the rendered output ---
    master = parse_master(cfg.master_path)
    for vid in cfg.verbatim_ids:
        expected = master.get(vid)
        if expected is None:
            failures.append(f"verbatim check: @{vid} not found in master (config.json refers to it)")
            continue
        if expected not in text:
            failures.append(f"verbatim: @{vid} content not found anywhere in the output (dropped or altered)")

    return failures


def find_all_company_dirs(cfg):
    return sorted(
        os.path.dirname(p)
        for p in glob.glob(os.path.join(cfg.offer_pages_dir, "*", "cv-minimal.md"))
    )


def run_structure(cfg, targets):
    if not cfg.spine_configured:
        print("check_cv: NOT CONFIGURED — no locked spine, required education titles, or")
        print("  verbatim ids set in config.json's \"spine\" block. Structure checking is a")
        print("  no-op until you define one. Run cv-setup (or edit config.json by hand) first.")
        return 0

    alias_map = alias_to_canon(cfg)
    total_failures = 0
    for company_dir in targets:
        label = os.path.basename(company_dir)
        failures = check_structure(cfg, company_dir, alias_map)
        if failures:
            print(label)
            for f in failures:
                print(f"  FAIL  {f}")
            total_failures += len(failures)
        else:
            print(f"{label:15s}  OK")
    print()
    if total_failures:
        print(f"check_cv: {total_failures} failure(s) across {len(targets)} companies.")
        return 1
    print(f"check_cv: all {len(targets)} companies OK.")
    return 0


# ---------------------------------------------------------------------------
# Coverage report
# ---------------------------------------------------------------------------

def count_locked_slots(template_text):
    """Counts a template's unconditional {{@id}} slots — i.e. what a fresh company always
    inherits from the master with no per-application decision involved. Excludes {{@id?}} /
    {{@id?section:H}} (optional — a real per-application choice) and {{FIELD}} / {{FIELD|@id}}
    (configurable, even if it has a locked fallback). Mirrors build_cv.py's own token grammar so
    this can never drift from what the generator actually treats as "always resolves, no
    choice involved" — used to size coverage's "N of TOTAL" denominator without a hardcoded
    magic number that goes stale the moment someone edits a template."""
    cleaned = COMMENT_RE.sub("", template_text)
    count = 0
    for m in TOKEN_RE.finditer(cleaned):
        token = m.group(1).strip()
        if not token.startswith("@"):
            continue
        rest = token[1:]
        if rest.endswith("?") or "?section:" in rest:
            continue
        count += 1
    return count


def run_coverage(cfg, targets):
    master = parse_master(cfg.master_path)
    proj_ids = sorted(k for k in master if k.startswith("proj-"))
    optional_ids = cfg.optional_ids
    template_locked_count_cache = {}

    for company_dir in targets:
        label = os.path.basename(company_dir)
        app_path = os.path.join(company_dir, "application.md")
        if not os.path.isfile(app_path):
            print(f"{label} — NOT MIGRATED (no application.md yet)")
            print()
            continue

        app = parse_application(app_path)
        used_proj_ids = {pid for pid, _ in app["projects"]}
        omit = app["omit"]
        include = set(app["include_ids"])

        rows = []  # (id, state, reason_or_None)
        for pid in optional_ids:
            if pid in include:
                rows.append((pid, "PRESENT", None))
            elif pid in omit:
                rows.append((pid, "DELIBERATE", omit[pid]))
            else:
                rows.append((pid, "SILENT", None))
        for pid in proj_ids:
            if pid in used_proj_ids:
                rows.append((pid, "PRESENT", None))
            elif pid in omit:
                rows.append((pid, "DELIBERATE", omit[pid]))
            else:
                rows.append((pid, "SILENT", None))

        template_name = app["front_matter"].get("template")
        if template_name not in template_locked_count_cache:
            template_path = os.path.join(cfg.templates_dir, f"{template_name}.md")
            locked_count = 0
            if template_name and os.path.isfile(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    locked_count = count_locked_slots(f.read())
            template_locked_count_cache[template_name] = locked_count
        locked_count = template_locked_count_cache[template_name]

        present = sum(1 for _, s, _ in rows if s == "PRESENT")
        total = len(rows) + locked_count
        print(f"{label} — {present + locked_count} of {total} master items present")
        print()

        deliberate = [(pid, r) for pid, s, r in rows if s == "DELIBERATE"]
        if deliberate:
            print("  DELIBERATE (declared in ## Omit)")
            for pid, reason in deliberate:
                print(f"    {pid:20s} {reason}")
            print()

        silent = [pid for pid, s, _ in rows if s == "SILENT"]
        if silent:
            print("  SILENT (missing, undeclared)  <-- these are the ones to look at")
            for pid in silent:
                print(f"    {pid}")
            print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("company_dir", nargs="?", help="path to one applications/offer-pages/<Company> folder")
    parser.add_argument("--coverage", action="store_true", help="run the coverage report instead of the structure check")
    args = parser.parse_args()

    cfg = cfgmod.resolve(args.root)

    if not os.path.isfile(cfg.master_path):
        print(f"check_cv: master not found at {cfg.master_path}", file=sys.stderr)
        return 1

    targets = [os.path.abspath(args.company_dir)] if args.company_dir else find_all_company_dirs(cfg)
    if not targets:
        print("check_cv: no companies found.", file=sys.stderr)
        return 1

    if args.coverage:
        return run_coverage(cfg, targets)
    return run_structure(cfg, targets)


if __name__ == "__main__":
    sys.exit(main())
