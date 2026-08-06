"""Tests for engine/scan_applications.py — the NEW/INCOMPLETE/CURRENT/STALE/ERROR classifier.

Every test works on a copy of examples/demo/ (the demo_root fixture) so mutations never touch
the tracked demo files.
"""

import os

import build_cv
import config as cfgmod
import scan_applications

ORBITAL = "Orbital Dynamics"


def _company_dir(demo_root, company=ORBITAL):
    return os.path.join(demo_root, "applications", "offer-pages", company)


def _build(demo_root):
    """Ensure cv-minimal.md reflects the current application.md/master before classifying —
    scan_applications.py itself never writes, it only diffs against what's on disk."""
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    build_cv.build_company(cfg, _company_dir(demo_root), master, check_only=False)


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------

def test_unmodified_demo_is_current(demo_root):
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    status, detail = scan_applications.classify(cfg, _company_dir(demo_root), master)
    assert status == "CURRENT"
    assert detail is None


def test_editing_application_md_marks_stale(demo_root):
    _build(demo_root)
    app_path = os.path.join(_company_dir(demo_root), "application.md")
    with open(app_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.replace(
        "React and Node.js, with a habit of adding the tests a codebase never had",
        "React and Node.js, with a habit of adding the tests a codebase never had (edited)",
    )
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(text)

    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    status, _ = scan_applications.classify(cfg, _company_dir(demo_root), master)
    assert status == "STALE"


def test_editing_master_marks_every_dependent_company_stale(demo_root):
    """The case the whole script exists for: application.md is untouched, but the master
    changed, so the built output would now differ from what's on disk."""
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    with open(cfg.master_path, "r", encoding="utf-8") as f:
        master_text = f.read()
    master_text = master_text.replace(
        "*Main technologies for this role — full list on request.*",
        "*Main technologies for this role — updated wording.*",
    )
    with open(cfg.master_path, "w", encoding="utf-8") as f:
        f.write(master_text)

    master = build_cv.parse_master(cfg.master_path)
    status, _ = scan_applications.classify(cfg, _company_dir(demo_root), master)
    assert status == "STALE"


def test_folder_with_only_posting_is_new(demo_root):
    cfg = cfgmod.resolve(demo_root)
    company_dir = os.path.join(cfg.offer_pages_dir, "Fresh Co")
    os.makedirs(company_dir)
    with open(os.path.join(company_dir, "posting.md"), "w", encoding="utf-8") as f:
        f.write("# Some Role — Fresh Co\n")

    master = build_cv.parse_master(cfg.master_path)
    status, detail = scan_applications.classify(cfg, company_dir, master)
    assert status == "NEW"
    assert detail is None


def test_empty_company_folder_is_incomplete(demo_root):
    cfg = cfgmod.resolve(demo_root)
    company_dir = os.path.join(cfg.offer_pages_dir, "Empty Co")
    os.makedirs(company_dir)

    master = build_cv.parse_master(cfg.master_path)
    status, detail = scan_applications.classify(cfg, company_dir, master)
    assert status == "INCOMPLETE"
    assert "no application.md" in detail


def test_malformed_application_is_error(demo_root):
    app_path = os.path.join(_company_dir(demo_root), "application.md")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write("not even front matter\n")

    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    status, detail = scan_applications.classify(cfg, _company_dir(demo_root), master)
    assert status == "ERROR"
    assert detail


# ---------------------------------------------------------------------------
# scan_all() / sent+declined state, tracked independently for CV and letter
# ---------------------------------------------------------------------------

def test_sent_state_read_from_produced_sent(demo_root):
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    open(os.path.join(sent_dir, f"{cfg.file_prefix}_{ORBITAL.replace(' ', '_')}.pdf"), "w").close()

    rows = scan_applications.scan_all(cfg)
    row = next(r for r in rows if r["company"] == ORBITAL)
    assert row["cv_state"] == "SENT"
    assert row["letter_state"] is None  # no cover_letter.pdf ever rendered


def test_declined_state_read_from_produced_not_sent(demo_root):
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    not_sent_dir = os.path.join(cfg.produced_dir, "not_sent")
    os.makedirs(not_sent_dir, exist_ok=True)
    open(os.path.join(not_sent_dir, f"{cfg.file_prefix}_{ORBITAL.replace(' ', '_')}.pdf"), "w").close()

    rows = scan_applications.scan_all(cfg)
    row = next(r for r in rows if r["company"] == ORBITAL)
    assert row["cv_state"] == "DECLINED"


def test_letter_state_tracked_independently_of_cv_state(demo_root):
    """A company can have its CV sent but its letter still pending, or vice versa."""
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    company_dir = _company_dir(demo_root)
    pdf_dir = os.path.join(company_dir, "generate-pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    open(os.path.join(pdf_dir, "cover_letter.pdf"), "w").close()

    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    open(os.path.join(sent_dir, f"{cfg.file_prefix}_{ORBITAL.replace(' ', '_')}.pdf"), "w").close()

    rows = scan_applications.scan_all(cfg)
    row = next(r for r in rows if r["company"] == ORBITAL)
    assert row["cv_state"] == "SENT"
    assert row["letter_state"] == "pending"


# ---------------------------------------------------------------------------
# --target resolution
# ---------------------------------------------------------------------------

def test_target_new_lists_only_new_companies(demo_root):
    cfg = cfgmod.resolve(demo_root)
    new_dir = os.path.join(cfg.offer_pages_dir, "Fresh Co")
    os.makedirs(new_dir)
    open(os.path.join(new_dir, "posting.md"), "w").close()

    _build(demo_root)
    rows = scan_applications.scan_all(cfg)
    targets = scan_applications.resolve_target(cfg, rows, "new")
    assert [r["company"] for r in targets] == ["Fresh Co"]


def test_target_all_includes_current_and_stale(demo_root):
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    rows = scan_applications.scan_all(cfg)
    targets = scan_applications.resolve_target(cfg, rows, "all")
    assert [r["company"] for r in targets] == [ORBITAL]


def test_target_stale_and_not_sent_exclude_sent_company(demo_root):
    """A SENT+STALE company is reported but never auto-targeted by --target stale/not-sent."""
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)

    # Tweak a locked, always-rendered line so the build diff is genuine.
    with open(cfg.master_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.replace(
        "English (native) · Spanish (B1)", "English (native) · Spanish (B1) · French (A2)"
    )
    with open(cfg.master_path, "w", encoding="utf-8") as f:
        f.write(text)

    sent_dir = os.path.join(cfg.produced_dir, "sent")
    os.makedirs(sent_dir, exist_ok=True)
    open(os.path.join(sent_dir, f"{cfg.file_prefix}_{ORBITAL.replace(' ', '_')}.pdf"), "w").close()

    rows = scan_applications.scan_all(cfg)
    row = next(r for r in rows if r["company"] == ORBITAL)
    assert row["status"] == "STALE"
    assert row["cv_state"] == "SENT"

    assert scan_applications.resolve_target(cfg, rows, "stale") == []
    assert scan_applications.resolve_target(cfg, rows, "not-sent") == []
    # Naming it directly still works.
    assert [r["company"] for r in scan_applications.resolve_target(cfg, rows, ORBITAL)] == [ORBITAL]


def test_target_by_display_name(demo_root):
    _build(demo_root)
    cfg = cfgmod.resolve(demo_root)
    rows = scan_applications.scan_all(cfg)
    # No display_names configured for the demo, so display name == folder name with spaces
    # turned into underscores.
    targets = scan_applications.resolve_target(cfg, rows, "Orbital_Dynamics")
    assert [r["company"] for r in targets] == [ORBITAL]
