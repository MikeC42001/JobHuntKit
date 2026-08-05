#!/usr/bin/env python3
"""audit_public.py — the leak gate. Scans a set of files for anything that looks like personal
data before it's allowed to reach a public remote.

This exists because "be careful" is not a real safeguard — a mechanism is. It's called from two
places: `scripts/sync.sh push` (scoped to exactly the files about to be copied — refuses to
write anything if this fails) and CI/a pre-commit hook (scoped to every git-tracked file in the
repo). Both callers get the same checks; only the file list and the private-terms wordlist
differ.

Checks (all hard failures — this is a gate, not a linter):
  1. Manifest self-check: engine.manifest must never list a forbidden content prefix
     (profile/, master/, applications/, produced/, workspace/, config.json) — defense in depth
     in case someone edits the manifest by hand.
  2. No scanned path may itself start with a forbidden content prefix, regardless of what the
     manifest says — the same belt-and-suspenders check applied to the actual file list.
  3. No binary file outside a small, explicit allowlist (fonts, the committed demo's own
     image/PDF/PNG outputs). An unexpected binary is exactly the shape of an accidentally-staged
     personal PDF or photo.
  4. No email address outside a small allowlist (the fictional demo persona's + this project's
     own public contact, if any).
  5. No phone-number-shaped string outside a small allowlist (same reasoning).
  6. No machine-absolute path (`C:\\`, `/c/Users/`, `/Users/`, `/home/`) — these leak local
     usernames and directory layout, and are also just wrong for a portable tool.
  7. No term from `.private-terms` (gitignored, never committed — read if present, silently
     empty otherwise so CI's run is deterministic without needing the real wordlist).

Usage:
    python3 scripts/audit_public.py                    # audit every git-tracked file in --root
    python3 scripts/audit_public.py path1.py path2.md   # audit exactly these files
    python3 scripts/audit_public.py --root <dir>
    python3 scripts/audit_public.py --terms-file <path> # override .private-terms location

Exit code 0 if clean, 1 if any finding — safe to use as a real gate.
"""

import argparse
import os
import re
import subprocess
import sys

# Force UTF-8 stdout/stderr — Windows otherwise defaults to the console codepage and mangles an
# em dash. Standalone here (not importing engine/config.py) since this script has to run cleanly
# even before the engine exists in a fresh checkout. See engine/config.py for the fuller version.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

FORBIDDEN_PREFIXES = ["profile/", "master/", "applications/", "produced/", "workspace/"]
FORBIDDEN_EXACT = ["config.json"]

BINARY_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".docx", ".zip", ".exe", ".ico"}
BINARY_ALLOWLIST_PREFIXES = [
    "engine/render-support/fonts/",
]
BINARY_ALLOWLIST_EXACT = [
    "examples/demo/images/avatar.png",
    "examples/demo/output/cv-minimal.pdf",
    "examples/demo/output/cv-minimal.png",
]
# .woff2 is always allowed anywhere under render-support/fonts/ — covered by the prefix above,
# not re-listed here.

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_ALLOWLIST = {"robin.vale@example.com"}

PHONE_RE = re.compile(r"\(?\+\d{1,3}\)?[\s.-]?\d{2,4}[\s.-]?\d{3}[\s.-]?\d{3,4}")
PHONE_ALLOWLIST = {"(+1) 555 010 2938"}

ABS_PATH_RE = re.compile(r"[Cc]:\\|/c/Users/|/Users/[A-Za-z]|/home/[A-Za-z]")
# Generic, non-personal Windows install paths — no username or directory layout leaked, unlike
# what ABS_PATH_RE exists to catch. tests/conftest.py's bash_executable() references these.
ABS_PATH_ALLOWLIST_PREFIXES = ["C:\\Program Files\\Git\\"]

# This file's own source necessarily contains the literal patterns above (they're what it's
# built to detect) — the content-based checks (email/phone/absolute-path/private-terms) would
# otherwise flag audit_public.py itself. Binary and forbidden-prefix checks still apply; those
# have no such false-positive risk. tests/test_audit_public.py has the same problem for the same
# reason: its fixtures are deliberately-fake examples of exactly what these checks detect.
CONTENT_CHECK_SELF_EXCLUDE = {"scripts/audit_public.py", "tests/test_audit_public.py"}

TEXT_READ_ERRORS = (UnicodeDecodeError,)


class Finding:
    def __init__(self, path, category, detail):
        self.path = path
        self.category = category
        self.detail = detail

    def __str__(self):
        return f"  [{self.category}] {self.path}: {self.detail}"


def is_binary_by_extension(path):
    return os.path.splitext(path)[1].lower() in BINARY_EXTENSIONS


def is_allowlisted_binary(rel_path):
    rel_posix = rel_path.replace(os.sep, "/")
    if rel_posix in BINARY_ALLOWLIST_EXACT:
        return True
    return any(rel_posix.startswith(p) for p in BINARY_ALLOWLIST_PREFIXES)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except TEXT_READ_ERRORS:
        return None
    except OSError:
        return None


def load_private_terms(terms_file):
    if not terms_file or not os.path.isfile(terms_file):
        return []
    terms = []
    with open(terms_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            terms.append(line)
    return terms


def check_manifest_self(manifest_path):
    """Check 1 — engine.manifest itself must never list a forbidden content prefix."""
    findings = []
    if not os.path.isfile(manifest_path):
        return findings
    with open(manifest_path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            normalized = line.rstrip("/") + "/" if not line.endswith("/") else line
            for forbidden in FORBIDDEN_PREFIXES:
                if normalized == forbidden or line == forbidden.rstrip("/"):
                    findings.append(Finding(
                        f"{manifest_path}:{lineno}", "manifest-self-check",
                        f"engine.manifest lists forbidden content path '{line}' — removed, not committed",
                    ))
            if line in FORBIDDEN_EXACT:
                findings.append(Finding(
                    f"{manifest_path}:{lineno}", "manifest-self-check",
                    f"engine.manifest lists forbidden content path '{line}'",
                ))
    return findings


def check_file(root, path, terms):
    rel_path = os.path.relpath(path, root)
    rel_posix = rel_path.replace(os.sep, "/")
    findings = []

    # Check 2 — forbidden content prefix, regardless of what the manifest says.
    for forbidden in FORBIDDEN_PREFIXES:
        if rel_posix.startswith(forbidden):
            findings.append(Finding(rel_posix, "forbidden-path",
                                     f"under forbidden content prefix '{forbidden}'"))
    if rel_posix in FORBIDDEN_EXACT:
        findings.append(Finding(rel_posix, "forbidden-path", "forbidden content file"))

    if not os.path.isfile(path):
        return findings

    if rel_posix in CONTENT_CHECK_SELF_EXCLUDE:
        return findings

    # Check 3 — unexpected binary.
    if is_binary_by_extension(rel_posix) and not is_allowlisted_binary(rel_posix):
        findings.append(Finding(rel_posix, "unexpected-binary",
                                 "binary file outside the allowlist — looks like accidentally-staged personal content"))
        return findings  # don't try to text-scan a binary we're already flagging

    text = read_text(path)
    if text is None:
        return findings  # binary we don't recognize by extension; extension check above is the real gate

    for m in EMAIL_RE.finditer(text):
        if m.group(0) not in EMAIL_ALLOWLIST:
            findings.append(Finding(rel_posix, "email", m.group(0)))

    for m in PHONE_RE.finditer(text):
        if m.group(0) not in PHONE_ALLOWLIST:
            findings.append(Finding(rel_posix, "phone-like-string", m.group(0)))

    for m in ABS_PATH_RE.finditer(text):
        start = m.start()
        if any(text[start:start + len(p)] == p for p in ABS_PATH_ALLOWLIST_PREFIXES):
            continue
        findings.append(Finding(rel_posix, "absolute-path", m.group(0)))
        break

    for term in terms:
        if term in text:
            findings.append(Finding(rel_posix, "private-term", f"contains '{term}'"))

    return findings


def git_tracked_files(root):
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [os.path.join(root, p) for p in out.stdout.splitlines() if p.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="specific files to audit (default: every git-tracked file)")
    parser.add_argument("--root", default=REPO_ROOT, help="repo root (default: this script's repo)")
    parser.add_argument("--terms-file", default=None,
                         help="private-terms wordlist path (default: <root>/.private-terms if present)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    terms_file = args.terms_file or os.path.join(root, ".private-terms")
    terms = load_private_terms(terms_file)

    manifest_findings = check_manifest_self(os.path.join(root, "engine.manifest"))

    if args.paths:
        targets = [os.path.abspath(p) for p in args.paths]
    else:
        targets = git_tracked_files(root)
        if targets is None:
            print("audit_public: not a git repo and no explicit paths given — nothing to audit.", file=sys.stderr)
            return 1

    all_findings = list(manifest_findings)
    for path in targets:
        all_findings.extend(check_file(root, path, terms))

    if all_findings:
        print(f"audit_public: {len(all_findings)} finding(s) across {len(targets)} file(s):")
        for f in all_findings:
            print(f)
        print()
        print("audit_public: FAILED — nothing pushed/committed. Fix the above or extend an")
        print("  allowlist in scripts/audit_public.py if a finding is a genuine false positive.")
        return 1

    print(f"audit_public: clean — {len(targets)} file(s) checked, 0 findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
