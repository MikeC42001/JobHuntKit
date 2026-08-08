"""Tests for engine/verify_cvs.py's page-count gate, including the --max-pages override added
alongside the render_cv.sh / render_cv_photo.sh pipeline. The long-form CV those renderers
produce has no fixed page count to gate against by default, unlike cv-minimal.pdf — --max-pages
lets a caller check page counts without touching the global limits.max_pages (which stays 1 and
keeps gating cv-minimal.pdf, unaffected by anything here).
"""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "engine")
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import verify_cvs  # noqa: E402


def _fake_pdf(tmp_path, name, page_count):
    """A byte string verify_cvs.count_pages() reads as having exactly page_count pages — no
    real PDF library involved, matching how verify_cvs.py itself only regex-scans raw bytes for
    "/Type /Page" markers (deliberately excluding "/Type /Pages", the page-tree node, via the
    trailing [^s] in PAGE_MARKER)."""
    path = tmp_path / name
    body = b"%PDF-1.4\n" + b"/Type /Page\n" * page_count + b"/Type /Pages\n"
    path.write_bytes(body)
    return str(path)


def test_count_pages_excludes_the_pages_tree_node(tmp_path):
    pdf = _fake_pdf(tmp_path, "three.pdf", 3)
    assert verify_cvs.count_pages(pdf) == 3


def test_default_gate_still_requires_exactly_one_page(demo_root, tmp_path, monkeypatch, capsys):
    """Regression guard: --max-pages must not change default behaviour when omitted."""
    pdf = _fake_pdf(tmp_path, "cv-minimal.pdf", 1)
    monkeypatch.setattr(sys, "argv", ["verify_cvs.py", "--root", demo_root, pdf])
    assert verify_cvs.main() == 0

    pdf_two = _fake_pdf(tmp_path, "cv-minimal-2.pdf", 2)
    monkeypatch.setattr(sys, "argv", ["verify_cvs.py", "--root", demo_root, pdf_two])
    assert verify_cvs.main() == 1
    assert "NOT 1 PAGE" in capsys.readouterr().out


def test_max_pages_zero_disables_the_gate(demo_root, tmp_path, monkeypatch, capsys):
    """A multi-page artifact (e.g. the full CV) must pass with no pass/fail verdict at all."""
    pdf = _fake_pdf(tmp_path, "cv.pdf", 3)
    monkeypatch.setattr(sys, "argv", ["verify_cvs.py", "--root", demo_root, "--max-pages", "0", pdf])
    assert verify_cvs.main() == 0
    out = capsys.readouterr().out
    assert "3 page(s)" in out
    assert "<--" not in out


def test_max_pages_override_gates_at_the_given_count(demo_root, tmp_path, monkeypatch, capsys):
    pdf = _fake_pdf(tmp_path, "cv.pdf", 3)
    monkeypatch.setattr(sys, "argv", ["verify_cvs.py", "--root", demo_root, "--max-pages", "3", pdf])
    assert verify_cvs.main() == 0

    monkeypatch.setattr(sys, "argv", ["verify_cvs.py", "--root", demo_root, "--max-pages", "2", pdf])
    assert verify_cvs.main() == 1


def test_missing_pdf_still_fails_even_with_gate_disabled(demo_root, tmp_path, monkeypatch, capsys):
    missing = str(tmp_path / "nope.pdf")
    monkeypatch.setattr(sys, "argv", ["verify_cvs.py", "--root", demo_root, "--max-pages", "0", missing])
    assert verify_cvs.main() == 1
    assert "MISSING" in capsys.readouterr().out
