"""Golden-file test for engine/build_cv.py.

Rebuilds the demo's cv-minimal.md from master + template + application.md and diffs it
byte-for-byte against examples/demo/expected/cv-minimal.md — the same file a human reads to
judge "did the generator produce the right thing" before this was automated.
"""

import os

import build_cv
import config as cfgmod


def _read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def test_demo_matches_golden_file(demo_root):
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    company_dir = os.path.join(demo_root, "applications", "offer-pages", "Orbital Dynamics")

    label, diff, warning = build_cv.build_company(cfg, company_dir, master, check_only=True)

    assert label == "Orbital Dynamics"
    assert warning is None
    assert diff == [], "generated cv-minimal.md differs from the committed copy:\n" + "".join(diff)


def test_generated_output_matches_expected_golden_file(demo_root):
    """Belt-and-suspenders: build_company's --check diff only proves "matches the tracked
    cv-minimal.md" — this proves that tracked file is itself still what expected/ says it
    should be, so the two can't silently drift apart."""
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    company_dir = os.path.join(demo_root, "applications", "offer-pages", "Orbital Dynamics")

    build_cv.build_company(cfg, company_dir, master, check_only=False)

    generated = _read(os.path.join(company_dir, "cv-minimal.md"))
    expected = _read(os.path.join(demo_root, "expected", "cv-minimal.md"))
    assert generated == expected
