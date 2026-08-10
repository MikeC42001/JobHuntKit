#!/usr/bin/env python3
"""init_workspace.py — scaffolds a fresh data root from templates/.

Sources always come from this repo checkout; destinations always go to the resolved root (see
engine/config.py's find_root() — `--root` > $JOBHUNTKIT_ROOT > walk up from cwd for a
config.json > this checkout). Two kinds of source, handled differently:

  templates/minimal-full.md   — an engine-owned CV template, read IN PLACE by build_cv.py at
                                 <root>/templates/. When root is this checkout, source and
                                 destination are the same file; elsewhere it's copied.
  templates/<other>.md        — STARTER files, copied once into master/, profile/, and
                                 applications/offer-pages/<Example>/ — yours to edit from then on.

Overwrite policy: nothing that could hold personal data is ever overwritten, by any flag —
config.json, master/, profile/, and every application.md are always skip-if-exists. --force
re-copies only the engine-owned CV template(s), for "give me the pristine one back". Re-running
this script with no flags is always a safe, idempotent no-op once a root is scaffolded.

Usage:
    python scripts/init_workspace.py                    # root = this checkout
    python scripts/init_workspace.py --root my-cv-data  # root = anywhere else
    python scripts/init_workspace.py --check             # dry run, writes nothing
    python scripts/init_workspace.py --force              # re-copy engine-owned CV template(s)
    python scripts/init_workspace.py --no-example         # skip the example company folder

Exit code 0 on success (including a fully idempotent no-op, or --check). Exit 1 if a source file
is missing from this checkout (broken/partial clone — every missing source is reported before
anything is written) or the resolved root exists but is not a directory.
"""

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, os.path.join(REPO_ROOT, "engine"))
import config as cfgmod  # noqa: E402

# (source path relative to REPO_ROOT/templates, destination relative to root) — the CV build
# templates, read in place when root == this checkout, copied elsewhere. Personal in the sense
# that a user will eventually customize them, but they hold no personal data, so --force may
# touch them. "full.md" drives the full-CV pipeline (master_cv.md -> cv.md), alongside
# "minimal-full.md" for the tailored one-pager (master_cv_minimal.md -> cv-minimal.md).
CV_TEMPLATES = ["minimal-full.md", "full.md"]

# (source path relative to REPO_ROOT, destination relative to root) — copied once, never by
# --force. Order is the order they're reported in. "master_cv.md" is the primary master (the
# complete inventory); "master_cv_minimal.md" is its condensation — see docs/SPEC.md's "The full
# CV — id-agnostic rendering" for how the two relate.
STARTER_FILES = [
    ("config.example.json", "config.json"),
    ("templates/master_cv.md", "master/master_cv.md"),
    ("templates/master_cv_minimal.md", "master/master_cv_minimal.md"),
    ("templates/CV_SPEC.md", "master/CV_SPEC.md"),
    ("templates/background.md", "profile/background.md"),
    ("templates/applications-README.md", "applications/README.md"),
]

EXAMPLE_COMPANY = "Example Company"
EXAMPLE_COMPANY_SOURCE = "templates/application.md"

# Created empty. produced/to_send/, produced/sent/, and produced/not_sent/ are the exact paths
# collect_cvs.py/collect_letters.py (M3) compute for staging and for the "move the PDF to mark
# it sent/declined" convention — creating them now makes that convention visible/self-documenting
# from the very first run.
EMPTY_DIRS = [
    "master",
    "profile",
    "templates",
    "images",
    os.path.join("applications", "offer-pages"),
    os.path.join("produced", "to_send"),
    os.path.join("produced", "sent"),
    os.path.join("produced", "not_sent"),
]


def copy_text(src, dst):
    """Read-normalize-write, same as build_cv.py — never shutil.copy2. This repo checkout may
    have CRLF line endings in its working tree (no .gitattributes forces LF), and a byte copy
    would propagate that into every scaffolded file: the same bug class engine/config.py's
    UTF-8-forcing fix already exists for."""
    with open(src, "r", encoding="utf-8", newline="") as f:
        text = f.read().replace("\r\n", "\n")
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def resolve_root(explicit_root):
    """Like cfgmod.find_root(), but reports which rule fired and refuses a walk-up match onto an
    unrelated directory that merely happens to contain a config.json (a common filename) with
    none of the shape this script is about to scaffold."""
    if explicit_root:
        return os.path.abspath(explicit_root), "--root"

    env_root = os.environ.get("JOBHUNTKIT_ROOT")
    if env_root:
        return os.path.abspath(env_root), "$JOBHUNTKIT_ROOT"

    probe = os.path.abspath(os.getcwd())
    while True:
        if os.path.isfile(os.path.join(probe, "config.json")):
            looks_like_a_root = any(
                os.path.isdir(os.path.join(probe, d)) for d in ("master", "templates", "applications")
            )
            if not looks_like_a_root:
                return None, probe
            return probe, "an existing config.json found above the current directory"
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent

    return REPO_ROOT, "this repo checkout"


def scaffold(root, check_only, force, with_example):
    report = []  # (status, relative_path)
    missing_sources = []

    def rel(dst):
        return os.path.relpath(dst, root).replace(os.sep, "/")

    for d in EMPTY_DIRS:
        dst = os.path.join(root, d)
        if os.path.isdir(dst):
            continue
        report.append(("would create" if check_only else "created", rel(dst) + "/"))
        if not check_only:
            os.makedirs(dst, exist_ok=True)

    for template_name in CV_TEMPLATES:
        src = os.path.join(REPO_ROOT, "templates", template_name)
        dst = os.path.join(root, "templates", template_name)
        if not os.path.isfile(src):
            missing_sources.append(src)
            continue
        if os.path.isfile(dst) and os.path.exists(src) and os.path.samefile(src, dst):
            report.append(("in place", rel(dst) + "  (root is this checkout)"))
            continue
        if os.path.isfile(dst) and not force:
            report.append(("kept", rel(dst)))
            continue
        existed = os.path.isfile(dst)
        if check_only:
            report.append(("would replace" if existed else "would write", rel(dst)))
            continue
        copy_text(src, dst)
        report.append(("replaced" if existed else "wrote", rel(dst)))

    for src_rel, dst_rel in STARTER_FILES:
        src = os.path.join(REPO_ROOT, src_rel)
        dst = os.path.join(root, dst_rel)
        if not os.path.isfile(src):
            missing_sources.append(src)
            continue
        if os.path.isfile(dst):
            report.append(("kept", rel(dst)))
            continue
        report.append(("would write" if check_only else "wrote", rel(dst)))
        if not check_only:
            copy_text(src, dst)

    if with_example:
        src = os.path.join(REPO_ROOT, EXAMPLE_COMPANY_SOURCE)
        dst = os.path.join(root, "applications", "offer-pages", EXAMPLE_COMPANY, "application.md")
        if not os.path.isfile(src):
            missing_sources.append(src)
        elif os.path.isfile(dst):
            report.append(("kept", rel(dst)))
        else:
            report.append(("would write" if check_only else "wrote", rel(dst)))
            if not check_only:
                copy_text(src, dst)

    return report, missing_sources


def print_report(root, rule, report, check_only):
    prefix = "init_workspace: root resolved from "
    print(f"{prefix}{rule}:")
    print(f"  {root}")
    print()
    for status, path in report:
        print(f"  {status:<13} {path}")
    print()

    written = sum(1 for s, _ in report if s in ("wrote", "would write", "replaced", "would replace"))
    kept = sum(1 for s, _ in report if s == "kept")
    created = sum(1 for s, _ in report if s in ("created", "would create"))
    file_verb = "would write" if check_only else "written"
    dir_verb = "would create" if check_only else "created"
    print(f"init_workspace: {written} file(s) {file_verb}, {kept} kept, {created} director(ies) {dir_verb}.")

    if check_only:
        return

    print()
    print("Next:")
    print("  1. config.json                    your name and file_prefix")
    print("  2. profile/background.md          everything about you, raw — nothing parses it")
    print("  3. master/master_cv.md            distil that into @id-tagged blocks — the primary")
    print("                                    master, full wording, no length pressure")
    print("  4. master/master_cv_minimal.md    condense the same blocks, same @id, terser —")
    print("                                    every minimal id must also exist in the full master")
    print("  5. master/CV_SPEC.md              decide what's locked vs. per-application")
    print(f'  6. rename "{EXAMPLE_COMPANY}" under applications/offer-pages/ to your first real')
    print("     posting, and edit its application.md")
    # If the root isn't this checkout, every later command needs --root too. Printing them
    # without it sends someone who deliberately chose a separate root at the wrong data.
    external = os.path.abspath(root) != os.path.abspath(REPO_ROOT)
    root_flag = f" --root {root}" if external else ""
    print(f"  7. python engine/build_cv.py{root_flag} --all")
    print(f"     python engine/check_cv.py{root_flag}")
    if external:
        print()
        print("Your data root is not this checkout, so every engine command needs --root (above),")
        print(f"or export JOBHUNTKIT_ROOT={root} once and drop the flag.")
    print()
    print("Full walkthrough: docs/GETTING-STARTED.md")
    print()
    if external:
        print("Your data lives outside this checkout, so nothing above is at risk of being")
        print("committed here. Version it separately if you want history for it.")
    else:
        print("Nothing under master/, profile/, applications/, produced/, or images/, and no")
        print("config.json, is ever committed from this checkout — .gitignore already excludes them.")
    print("--force only ever re-copies engine-owned CV template(s), never anything above.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("--check", action="store_true", help="dry run — print what would happen, write nothing")
    parser.add_argument("--force", action="store_true",
                         help="re-copy engine-owned CV template(s) that already exist "
                              "(never config.json, master/, profile/, or any application.md)")
    parser.add_argument("--no-example", action="store_true",
                         help="skip creating the placeholder 'Example Company' application")
    args = parser.parse_args(argv)

    root, rule = resolve_root(args.root)
    if root is None:
        print(f"init_workspace: found a config.json at {rule}, but no master/, templates/, or "
              f"applications/ alongside it — that doesn't look like a JobHuntKit root.",
              file=sys.stderr)
        print("init_workspace: pass --root explicitly to scaffold there anyway, or a different "
              "directory.", file=sys.stderr)
        return 1

    if os.path.exists(root) and not os.path.isdir(root):
        print(f"init_workspace: {root} exists and is not a directory.", file=sys.stderr)
        return 1

    report, missing_sources = scaffold(root, args.check, args.force, not args.no_example)

    if missing_sources:
        print("init_workspace: missing source file(s) — this looks like a broken or partial "
              "checkout, nothing was written:", file=sys.stderr)
        for src in missing_sources:
            print(f"  {src}", file=sys.stderr)
        return 1

    print_report(root, rule, report, args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
