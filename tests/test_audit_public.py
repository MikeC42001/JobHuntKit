"""Tests for scripts/audit_public.py — the leak gate — and, at the bottom, an end-to-end test
of the guarantee it exists to provide: a root's private content never even enters sync.sh's
scanned/copied file list, let alone reaches a destination repo.
"""

import os
import subprocess

import audit_public

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# check_file — content checks
# ---------------------------------------------------------------------------

def test_clean_file_has_no_findings(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "Just some ordinary project notes.\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert findings == []


def test_email_outside_allowlist_is_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "Contact me at real.person@gmail.com.\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert any(f.category == "email" for f in findings)


def test_allowlisted_demo_email_is_not_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "robin.vale@example.com\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert not any(f.category == "email" for f in findings)


def test_phone_outside_allowlist_is_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "Call (+351) 912 345 678 anytime.\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert any(f.category == "phone-like-string" for f in findings)


def test_allowlisted_demo_phone_is_not_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "(+1) 555 010 2938\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert not any(f.category == "phone-like-string" for f in findings)


def test_windows_absolute_path_is_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), r"See C:\Users\someone\Documents\cv.md")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert any(f.category == "absolute-path" for f in findings)


def test_posix_absolute_path_is_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "See /Users/someone/Documents/cv.md")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert any(f.category == "absolute-path" for f in findings)


def test_private_term_is_flagged(tmp_path):
    path = _write(str(tmp_path / "docs" / "note.md"), "Applying to Acme Corp next week.\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=["Acme Corp"])
    assert any(f.category == "private-term" for f in findings)


def test_forbidden_content_prefix_is_flagged_regardless_of_file_content(tmp_path):
    path = _write(str(tmp_path / "profile" / "background.md"), "Nothing sensitive in here.\n")
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert any(f.category == "forbidden-path" for f in findings)


def test_unexpected_binary_is_flagged(tmp_path):
    path = str(tmp_path / "examples" / "demo" / "images" / "headshot.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert any(f.category == "unexpected-binary" for f in findings)


def test_allowlisted_binary_is_not_flagged(tmp_path):
    path = str(tmp_path / "examples" / "demo" / "images" / "avatar.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    findings = audit_public.check_file(str(tmp_path), path, terms=[])
    assert findings == []


# ---------------------------------------------------------------------------
# Manifest self-check
# ---------------------------------------------------------------------------

def test_manifest_self_check_flags_forbidden_prefix(tmp_path):
    manifest_path = _write(str(tmp_path / "engine.manifest"), "engine/\nprofile/\n")
    findings = audit_public.check_manifest_self(manifest_path)
    assert any(f.category == "manifest-self-check" for f in findings)


def test_manifest_self_check_clean_manifest_has_no_findings(tmp_path):
    manifest_path = _write(str(tmp_path / "engine.manifest"), "engine/\nscripts/\ndocs/\n")
    findings = audit_public.check_manifest_self(manifest_path)
    assert findings == []


def test_real_engine_manifest_passes_self_check():
    """The actual engine.manifest shipped in this repo must never regress into listing a
    forbidden content prefix."""
    manifest_path = os.path.join(REPO_ROOT, "engine.manifest")
    findings = audit_public.check_manifest_self(manifest_path)
    assert findings == []


def test_self_excluded_sources_produce_no_content_findings():
    """scripts/audit_public.py and this file both necessarily contain literal examples of what
    the content checks detect (that's what makes them useful fixtures/patterns) — confirm
    CONTENT_CHECK_SELF_EXCLUDE actually silences both against the real repo copies, not just a
    tmp_path stand-in."""
    for rel_path in sorted(audit_public.CONTENT_CHECK_SELF_EXCLUDE):
        findings = audit_public.check_file(REPO_ROOT, os.path.join(REPO_ROOT, rel_path), terms=[])
        assert findings == [], (rel_path, findings)


# ---------------------------------------------------------------------------
# Content-invisibility guarantee, end-to-end through the real sync.sh
# ---------------------------------------------------------------------------

def test_sync_push_never_copies_or_scans_forbidden_content(tmp_path):
    """A root containing a fake profile/background.md pushed via the real sync.sh: the audit
    that runs first must succeed (clean — nothing forbidden is even in its file list, since
    engine.manifest never names profile/), and profile/ must never appear at the destination.
    This is the guarantee the M1 session log claims was manually verified — pinned here so a
    future manifest edit that accidentally widens the copied set gets caught automatically."""
    src = tmp_path / "src_root"
    dst = tmp_path / "dst_repo"
    (src / "engine").mkdir(parents=True)
    (src / "engine" / "dummy_tool.py").write_text("# pretend engine file\n", encoding="utf-8")
    (src / "profile").mkdir(parents=True)
    (src / "profile" / "background.md").write_text(
        "Real name: Someone Private. Real email: someone.private@gmail.com\n", encoding="utf-8"
    )
    dst.mkdir()

    sync_sh = os.path.join(REPO_ROOT, "scripts", "sync.sh")
    result = subprocess.run(
        ["bash", sync_sh, "push", "--root", str(src), "--to", str(dst)],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "profile" not in result.stdout
    assert not (dst / "profile").exists()
    assert (dst / "engine" / "dummy_tool.py").exists()


def test_sync_push_aborts_and_writes_nothing_on_a_finding(tmp_path):
    """A leaked email inside an engine-manifest path (not a forbidden prefix, just a file the
    audit's content checks would flag) must block the push entirely — dst stays untouched."""
    src = tmp_path / "src_root"
    dst = tmp_path / "dst_repo"
    (src / "engine").mkdir(parents=True)
    (src / "engine" / "dummy_tool.py").write_text(
        "# TODO: contact real.person@gmail.com about this\n", encoding="utf-8"
    )
    dst.mkdir()

    sync_sh = os.path.join(REPO_ROOT, "scripts", "sync.sh")
    result = subprocess.run(
        ["bash", sync_sh, "push", "--root", str(src), "--to", str(dst)],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )

    assert result.returncode != 0
    assert not (dst / "engine").exists()
