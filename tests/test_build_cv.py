"""Golden-file test for engine/build_cv.py.

Rebuilds the demo's cv-minimal.md from master + template + application.md and diffs it
byte-for-byte against examples/demo/expected/cv-minimal.md — the same file a human reads to
judge "did the generator produce the right thing" before this was automated. Mirrors the same
golden-file approach for the full pipeline's cv.md/expected/cv.md.
"""

import os

import pytest

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


def test_legacy_call_defaults_to_minimal_pipeline_unchanged(demo_root):
    """Regression guard: build_company(cfg, company_dir, master, check_only) — the exact
    4-positional-arg call every pre-existing caller (and this file's own tests above) makes —
    must keep behaving as pipeline="minimal" with zero change. This is the concrete proof that
    adding the "pipelines" feature didn't alter the single-pipeline path it grew out of."""
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_path)
    company_dir = os.path.join(demo_root, "applications", "offer-pages", "Orbital Dynamics")

    label, diff, warning = build_cv.build_company(cfg, company_dir, master, check_only=True)
    assert diff == []

    out_path = os.path.join(company_dir, "cv-minimal.md")
    assert os.path.isfile(out_path), "default pipeline must still write cv-minimal.md, not cv.md"


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def test_full_pipeline_matches_golden_file(demo_root):
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_full_path)
    company_dir = os.path.join(demo_root, "applications", "offer-pages", "Orbital Dynamics")

    label, diff, warning = build_cv.build_company(
        cfg, company_dir, master, check_only=True, pipeline="full"
    )

    assert label == "Orbital Dynamics"
    assert warning is None, "the full pipeline has no line-budget warning by design"
    assert diff == [], "generated cv.md differs from the committed copy:\n" + "".join(diff)


def test_full_pipeline_generated_output_matches_expected_golden_file(demo_root):
    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_full_path)
    company_dir = os.path.join(demo_root, "applications", "offer-pages", "Orbital Dynamics")

    build_cv.build_company(cfg, company_dir, master, check_only=False, pipeline="full")

    generated = _read(os.path.join(company_dir, "cv.md"))
    expected = _read(os.path.join(demo_root, "expected", "cv.md"))
    assert generated == expected


def test_both_pipelines_build_from_one_application_md(demo_root):
    """The demo's application.md carries "pipelines: minimal, full" — main()'s own orchestration
    (not build_company() directly) is what reads that key and builds both. Exercise it via
    main() with a patched argv, the same way a real CLI invocation would."""
    import sys

    app_path = os.path.join(
        demo_root, "applications", "offer-pages", "Orbital Dynamics", "application.md"
    )
    app = build_cv.parse_application(app_path)
    assert build_cv.resolve_pipelines_for(app["front_matter"]) == ["minimal", "full"]

    old_argv = sys.argv
    try:
        sys.argv = ["build_cv.py", "--root", demo_root, "--all"]
        exit_code = build_cv.main()
    finally:
        sys.argv = old_argv
    assert exit_code == 0

    company_dir = os.path.join(demo_root, "applications", "offer-pages", "Orbital Dynamics")
    assert os.path.isfile(os.path.join(company_dir, "cv-minimal.md"))
    assert os.path.isfile(os.path.join(company_dir, "cv.md"))


def test_resolve_pipelines_for_absent_key_means_minimal_only():
    """The backward-compatibility guarantee, isolated: no "pipelines:" front-matter key at all
    (every application.md written before this feature existed) resolves to exactly ["minimal"]."""
    assert build_cv.resolve_pipelines_for({"template": "minimal-full"}) == ["minimal"]


def test_resolve_pipelines_for_parses_comma_separated_list():
    assert build_cv.resolve_pipelines_for({"pipelines": "minimal, full"}) == ["minimal", "full"]
    assert build_cv.resolve_pipelines_for({"pipelines": "full"}) == ["full"]


# ---------------------------------------------------------------------------
# Id inheritance — the chain's one enforceable rule
# ---------------------------------------------------------------------------

def test_every_minimal_id_exists_in_the_full_master_demo():
    """The chain's inheritance rule: master_cv_minimal.md is a condensation of master_cv.md, so
    every id the minimal master defines must also exist in the full one. The reverse doesn't
    hold — the full master may carry ids (e.g. exp-first-internship) the condensation skips."""
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "examples", "demo")
    minimal_ids = set(build_cv.parse_master(os.path.join(demo_dir, "master", "master_cv_minimal.md")))
    full_ids = set(build_cv.parse_master(os.path.join(demo_dir, "master", "master_cv.md")))

    missing = minimal_ids - full_ids
    assert missing == set(), f"id(s) in master_cv_minimal.md but not master_cv.md: {missing}"
    assert "exp-first-internship" in full_ids - minimal_ids, (
        "fixture assumption broken: the full-only id was renamed or removed"
    )


def test_every_minimal_id_exists_in_the_full_master_starter():
    """Same rule, for the blank starter templates a fresh root gets from init_workspace.py —
    the property has to hold before anyone's filled in their own content, not just for the demo."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    minimal_ids = set(build_cv.parse_master(os.path.join(repo_root, "templates", "master_cv_minimal.md")))
    full_ids = set(build_cv.parse_master(os.path.join(repo_root, "templates", "master_cv.md")))

    missing = minimal_ids - full_ids
    assert missing == set(), f"id(s) in master_cv_minimal.md but not master_cv.md: {missing}"


def test_duplicate_marker_error_names_the_actual_file(tmp_path):
    """parse_master() runs on both master_cv.md and master_cv_minimal.md — the duplicate-@id
    error must name whichever file was actually being parsed, not hardcode one of the two
    filenames. Regression test for a real bug: the message used to always say
    "master_cv_minimal.md" even when the duplicate was in master_cv.md."""
    fixture = tmp_path / "master_cv.md"
    fixture.write_text(
        "<!-- @exp-role -->\nFirst.\n\n<!-- @exp-role -->\nSecond.\n",
        encoding="utf-8",
    )

    with pytest.raises(build_cv.BuildError) as excinfo:
        build_cv.parse_master(str(fixture))

    assert "master_cv.md" in str(excinfo.value)
    assert "master_cv_minimal.md" not in str(excinfo.value)
