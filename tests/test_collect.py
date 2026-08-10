"""Tests for engine/collect_cvs.py and engine/collect_letters.py — staging rendered PDFs into
produced/to_send/.

No real browser/render involved: a rendered "PDF" is just a small placeholder file written
directly under generate-pdfs/. What's under test is the copy/skip/force/stale logic, not
render_cv_minimal.sh itself.
"""

import os
import sys

import collect_cvs
import collect_letters
import config as cfgmod

ORBITAL = "Orbital Dynamics"


def _run(module, *argv):
    """Run a script's main() with a given argv, restoring sys.argv afterward. Both scripts parse
    sys.argv via argparse rather than taking an argv parameter, so this is the simplest way to
    drive them from a test."""
    old_argv = sys.argv
    sys.argv = [module.__name__ + ".py", *argv]
    try:
        return module.main()
    finally:
        sys.argv = old_argv


def _write_rendered_cv(demo_root, company=ORBITAL, content=b"cv pdf v1"):
    pdf_dir = os.path.join(demo_root, "applications", "offer-pages", company, "generate-pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    path = os.path.join(pdf_dir, "cv-minimal.pdf")
    with open(path, "wb") as f:
        f.write(content)
    return path


def _write_rendered_letter(demo_root, company=ORBITAL, content=b"letter pdf v1"):
    pdf_dir = os.path.join(demo_root, "applications", "offer-pages", company, "generate-pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    path = os.path.join(pdf_dir, "cover_letter.pdf")
    with open(path, "wb") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# collect_cvs.py
# ---------------------------------------------------------------------------

def test_stages_a_rendered_cv(demo_root):
    _write_rendered_cv(demo_root)
    cfg = cfgmod.resolve(demo_root)

    rc = _run(collect_cvs, "--root", demo_root)

    assert rc == 0
    staged = os.path.join(cfg.produced_dir, "to_send", f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    assert os.path.isfile(staged)


def test_missing_source_pdf_exits_1(demo_root):
    rc = _run(collect_cvs, "--root", demo_root)
    assert rc == 1


def test_skips_a_company_already_in_sent(demo_root):
    _write_rendered_cv(demo_root)
    cfg = cfgmod.resolve(demo_root)
    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    sent_path = os.path.join(sent_dir, f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    with open(sent_path, "wb") as f:
        f.write(b"already sent")

    rc = _run(collect_cvs, "--root", demo_root)

    assert rc == 0
    to_send_path = os.path.join(cfg.produced_dir, "to_send", f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    assert not os.path.isfile(to_send_path)  # skipped, never copied


def test_force_recopies_a_sent_company(demo_root):
    _write_rendered_cv(demo_root, content=b"cv pdf v2")
    cfg = cfgmod.resolve(demo_root)
    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    sent_path = os.path.join(sent_dir, f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    with open(sent_path, "wb") as f:
        f.write(b"cv pdf v1")

    rc = _run(collect_cvs, "--root", demo_root, "--force")

    assert rc == 0
    to_send_path = os.path.join(cfg.produced_dir, "to_send", f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    assert os.path.isfile(to_send_path)


def test_force_with_a_name_only_touches_that_company(demo_root):
    _write_rendered_cv(demo_root)
    cfg = cfgmod.resolve(demo_root)
    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    with open(os.path.join(sent_dir, f"{cfg.file_prefix}_Orbital_Dynamics.pdf"), "wb") as f:
        f.write(b"sent")

    rc = _run(collect_cvs, "--root", demo_root, "--force", "orbital dynamics")  # case-insensitive

    assert rc == 0
    to_send_path = os.path.join(cfg.produced_dir, "to_send", f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    assert os.path.isfile(to_send_path)


def test_mtime_stale_report_when_source_newer_than_sent(demo_root, capsys):
    cv_path = _write_rendered_cv(demo_root)
    cfg = cfgmod.resolve(demo_root)
    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    sent_path = os.path.join(sent_dir, f"{cfg.file_prefix}_Orbital_Dynamics.pdf")
    with open(sent_path, "wb") as f:
        f.write(b"older")
    # Make the sent copy strictly older than the freshly-written source.
    old_time = os.path.getmtime(sent_path) - 10
    os.utime(sent_path, (old_time, old_time))
    os.utime(cv_path, None)  # now

    _run(collect_cvs, "--root", demo_root)

    out = capsys.readouterr().out
    assert "STALE" in out
    assert "1 stale" in out


# ---------------------------------------------------------------------------
# collect_letters.py
# ---------------------------------------------------------------------------

def test_stages_a_rendered_letter(demo_root):
    _write_rendered_letter(demo_root)
    cfg = cfgmod.resolve(demo_root)

    rc = _run(collect_letters, "--root", demo_root, ORBITAL)

    assert rc == 0
    staged = os.path.join(cfg.produced_dir, "to_send", f"{cfg.letter_prefix}_Orbital_Dynamics.pdf")
    assert os.path.isfile(staged)


def test_no_rendered_letter_exits_1_with_a_clear_message(demo_root, capsys):
    rc = _run(collect_letters, "--root", demo_root, ORBITAL)

    assert rc == 1
    err = capsys.readouterr().err
    assert "no rendered cover letter" in err
    assert "render_letter.sh" in err


def test_collect_letters_requires_exactly_one_company(demo_root):
    """No --all, no bare invocation — argparse rejects a missing company argument."""
    try:
        _run(collect_letters, "--root", demo_root)
        assert False, "expected argparse to exit on a missing company argument"
    except SystemExit as e:
        assert e.code != 0


def test_letter_force_recopies_a_sent_letter(demo_root):
    _write_rendered_letter(demo_root, content=b"letter v2")
    cfg = cfgmod.resolve(demo_root)
    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    with open(os.path.join(sent_dir, f"{cfg.letter_prefix}_Orbital_Dynamics.pdf"), "wb") as f:
        f.write(b"letter v1")

    rc = _run(collect_letters, "--root", demo_root, "--force", ORBITAL)

    assert rc == 0
    to_send_path = os.path.join(cfg.produced_dir, "to_send", f"{cfg.letter_prefix}_Orbital_Dynamics.pdf")
    assert os.path.isfile(to_send_path)
