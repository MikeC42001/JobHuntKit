"""Regression tests for content invariants in agents/*.md — the agent instruction files
themselves aren't executable, so a bug in them (a missing required flag, a stale file reference)
has no test coverage unless we grep for the specific claim, the same way test_community.py pins
community.sh's read-only guarantee.
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
README_PATH = os.path.join(REPO_ROOT, "README.md")

# README.md carries a copy-paste bootstrap prompt under this heading, as a blockquote. Every
# backticked path inside it is a file someone's agent will be told to open on a fresh clone.
BOOTSTRAP_HEADING = "## Or let an agent set it up"
BACKTICKED_PATH_RE = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|py|sh|json))`")

# Only actual invocations (the "! bash ..." lines Claude Code runs), not prose mentions of the
# script's name in a sentence.
RENDER_MINIMAL_CALL_RE = re.compile(r"^\s*!\s*bash engine/render_cv_minimal\.sh\b.*$", re.MULTILINE)


def _lines_calling_render_minimal(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return RENDER_MINIMAL_CALL_RE.findall(text)


def test_every_render_cv_minimal_call_in_agent_docs_includes_photo():
    """render_cv_minimal.sh hard-exits 1 without --photo unless config.json's
    render.default_photo is set (which it isn't, by default) — see render_cv_minimal.sh's own
    argument parsing. Regression test for a real bug: agents/cv-tailor.md shipped three calls
    missing the flag, so following its own instructions against a fresh root failed every time."""
    offending = {}
    for name in ("cv-tailor.md", "cv-setup.md"):
        path = os.path.join(AGENTS_DIR, name)
        calls = _lines_calling_render_minimal(path)
        missing = [call for call in calls if "--photo" not in call]
        if missing:
            offending[name] = missing

    assert offending == {}, (
        f"render_cv_minimal.sh call(s) missing the required --photo flag: {offending}"
    )


def test_context_md_write_allowlist_covers_both_masters():
    """agents/CONTEXT.md is the one source of truth for file ownership — cv-setup.md instructs
    writing master/master_cv.md first, then condensing into master/master_cv_minimal.md, so
    CONTEXT.md's allowlist must name both or it silently forbids the primary master."""
    path = os.path.join(AGENTS_DIR, "CONTEXT.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    ownership_section = text.split("## File ownership", 1)[1]
    may_write, never_write = ownership_section.split("must **never** write", 1)

    assert "master/master_cv.md" in may_write
    assert "master/master_cv_minimal.md" in may_write
    assert "cv.md" in never_write, "cv.md is as generated as cv-minimal.md and must stay listed"
    assert "cv-minimal.md" in never_write


def _bootstrap_prompt_block():
    """The blockquote body under BOOTSTRAP_HEADING. Asserts its way there rather than returning
    an empty string, so a renamed heading fails loudly instead of passing vacuously."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert BOOTSTRAP_HEADING in text, (
        f"README.md lost the {BOOTSTRAP_HEADING!r} section — it's the only documented path from "
        "'I have an agent open' to a working clone, so don't drop it silently."
    )
    section = text.split(BOOTSTRAP_HEADING, 1)[1].split("\n## ", 1)[0]
    quoted = [ln.lstrip("> ").rstrip() for ln in section.splitlines() if ln.startswith(">")]
    return "\n".join(quoted)


def test_bootstrap_prompt_references_only_real_files():
    """README's copy-paste prompt names the files an agent should read on a fresh clone. Rename
    or move one and every new user's agent gets sent at a path that doesn't exist — the same
    failure mode as cv-tailor.md's missing --photo, and nothing else in the suite would catch it."""
    prompt = _bootstrap_prompt_block()
    assert prompt.strip(), "the bootstrap prompt blockquote is empty"

    paths = BACKTICKED_PATH_RE.findall(prompt)
    assert paths, "no backticked file paths found in the bootstrap prompt — did its format change?"

    missing = [p for p in paths if not os.path.exists(os.path.join(REPO_ROOT, p))]
    assert missing == [], f"bootstrap prompt references nonexistent path(s): {missing}"


def test_readme_agent_section_promises_a_real_claude_command():
    """That section tells Claude Code users they can skip the prompt and run /cv-setup, which is
    only true if the command file is actually shipped in the repo."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    section = text.split(BOOTSTRAP_HEADING, 1)[1].split("\n## ", 1)[0]

    if "/cv-setup" in section:
        command_file = os.path.join(REPO_ROOT, ".claude", "commands", "cv-setup.md")
        assert os.path.exists(command_file), (
            "README promises `/cv-setup` works after cloning, but "
            ".claude/commands/cv-setup.md isn't in the repo"
        )
