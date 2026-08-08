"""Tests for community/community.sh — the read-only gh/git wrapper behind community/README.md's
issue-orchestration lifecycle.

Scope deliberately stays hermetic: these tests never require network access or a real `gh`
session, so they run the same on every contributor's machine and in CI without a GITHUB_TOKEN.
The actual `questions`/`open`/`resolved` output isn't tested here — that needs a real `gh` call
against a real repo's ever-changing issue state, which makes for a flaky, meaningless assertion
(the same reason sync.sh's GitHub-facing paths aren't unit-tested either). What's pinned instead:
argument handling, and — the one property that actually matters — that the script is read-only
by construction, not just by convention.
"""

import os
import re
import subprocess

from conftest import bash_executable

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMUNITY_SH = os.path.join(REPO_ROOT, "community", "community.sh")


def _run(*args):
    return subprocess.run(
        [bash_executable(), COMMUNITY_SH, *args],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )


def test_no_arguments_prints_usage_and_exits_1():
    result = _run()
    assert result.returncode == 1
    assert "Usage:" in result.stderr
    assert "questions|open|resolved|status" in result.stderr


def test_unknown_subcommand_errors_and_exits_1():
    result = _run("not-a-real-subcommand")
    assert result.returncode == 1
    assert "unknown argument" in result.stderr


def test_repo_flag_before_a_bad_subcommand_still_errors():
    """--repo is parsed order-independently — a bad subcommand after it must fail the same way
    as a bad subcommand with no --repo at all, not silently swallow the rest of argv."""
    result = _run("--repo", "owner/repo", "not-a-real-subcommand")
    assert result.returncode == 1
    assert "unknown argument" in result.stderr


# ---------------------------------------------------------------------------
# The read-only guarantee — pinned as a regression test, not just a one-off manual grep
# ---------------------------------------------------------------------------

WRITE_CALL_RE = re.compile(r"\bgh (issue|pr) (create|edit|close|comment)\b")


def test_community_sh_never_calls_a_github_write_command():
    """community/README.md's two approval gates only mean something if this script structurally
    cannot open, label, or close an issue on its own. Check every non-comment line of the actual
    source for the write calls the approval rule forbids — the same check run manually against
    this file when it was written, now permanent."""
    with open(COMMUNITY_SH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    offending = [
        (lineno, line)
        for lineno, line in enumerate(lines, start=1)
        if not line.strip().startswith("#") and WRITE_CALL_RE.search(line)
    ]

    assert offending == [], (
        f"community.sh must never call a GitHub write command outside a comment: {offending}"
    )
