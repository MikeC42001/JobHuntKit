"""Tests for engine/check_cv.py — structure gate + coverage report.

Structure tests work directly on a copy of the demo's rendered cv-minimal.md (not through
build_cv.py) since check_structure() reads output shape, independent of how that output was
produced — the same class of bug (locked-experience entry reordered or a verbatim line quietly
dropped) can happen to a hand-edited file too, and the checker doesn't care which.
"""

import json
import os

import check_cv
import config as cfgmod

ORBITAL_CV = os.path.join("applications", "offer-pages", "Orbital Dynamics", "cv-minimal.md")

SKILL_NOTE_LINE = "*Main technologies for this role — full list on request.*"


def _cv_path(demo_root):
    return os.path.join(demo_root, ORBITAL_CV)


def _company_dir(demo_root):
    return os.path.dirname(_cv_path(demo_root))


def _cfg_and_alias(demo_root):
    cfg = cfgmod.resolve(demo_root)
    return cfg, check_cv.alias_to_canon(cfg)


def test_unmodified_demo_has_no_structure_failures(demo_root):
    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)
    assert failures == []


def test_reordered_experience_entries_are_caught(demo_root):
    """Swap the two locked Experience entries — config.json's locked_order is
    [exp-self-directed, exp-current-role], so Meridian Systems (current role) landing before
    Independent Projects (self-directed) must fail."""
    cv_path = _cv_path(demo_root)
    with open(cv_path, "r", encoding="utf-8") as f:
        text = f.read()

    self_directed_start = text.index("**Independent Projects")
    current_role_start = text.index("**Software Engineer")
    skills_start = text.index("## Skills")

    header = text[:self_directed_start]
    self_directed_block = text[self_directed_start:current_role_start]
    current_role_block = text[current_role_start:skills_start]
    footer = text[skills_start:]

    reordered = header + current_role_block + self_directed_block + footer
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(reordered)

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)

    assert any("order wrong" in f for f in failures), failures


def test_dropped_verbatim_line_is_caught(demo_root):
    """Delete the @skill-note verbatim line — config.json's verbatim_ids includes it, so the
    checker must notice it's no longer present byte-for-byte."""
    cv_path = _cv_path(demo_root)
    with open(cv_path, "r", encoding="utf-8") as f:
        text = f.read()

    assert SKILL_NOTE_LINE in text, "fixture assumption broken: skill-note line text changed"
    text = text.replace(SKILL_NOTE_LINE + "\n", "")
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(text)

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)

    assert any("skill-note" in f and "dropped or altered" in f for f in failures), failures


def test_missing_locked_experience_entry_is_caught(demo_root):
    """Delete the current-role entry outright — locked_order requires both entries to be
    present, not just correctly ordered."""
    cv_path = _cv_path(demo_root)
    with open(cv_path, "r", encoding="utf-8") as f:
        text = f.read()

    current_role_start = text.index("**Software Engineer")
    skills_start = text.index("## Skills")
    text = text[:current_role_start] + text[skills_start:]
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(text)

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)

    assert any("current role" in f and "missing" in f for f in failures), failures


# ---------------------------------------------------------------------------
# --pipeline full
# ---------------------------------------------------------------------------

ORBITAL_CV_FULL = os.path.join("applications", "offer-pages", "Orbital Dynamics", "cv.md")


def _cv_full_path(demo_root):
    return os.path.join(demo_root, ORBITAL_CV_FULL)


def _build_full(demo_root):
    """The full pipeline's cv.md isn't in the demo_root fixture until built — build it once,
    same as a real check_cv.py run would expect after build_cv.py --all."""
    import build_cv

    cfg = cfgmod.resolve(demo_root)
    master = build_cv.parse_master(cfg.master_full_path)
    company_dir = os.path.dirname(_cv_full_path(demo_root))
    build_cv.build_company(cfg, company_dir, master, check_only=False, pipeline="full")


def test_full_pipeline_unmodified_demo_has_no_structure_failures(demo_root):
    _build_full(demo_root)
    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map, pipeline="full")
    assert failures == []


def test_full_pipeline_reordered_experience_entries_are_caught(demo_root):
    """Same fixture-mutation approach as the minimal pipeline's equivalent test, applied to
    cv.md instead — proves --pipeline full checks against its own master (full wording), not the
    minimal one."""
    _build_full(demo_root)
    cv_path = _cv_full_path(demo_root)
    with open(cv_path, "r", encoding="utf-8") as f:
        text = f.read()

    self_directed_start = text.index("**Independent Projects")
    current_role_start = text.index("**Software Engineer")
    skills_start = text.index("## Skills")

    header = text[:self_directed_start]
    self_directed_block = text[self_directed_start:current_role_start]
    current_role_block = text[current_role_start:skills_start]
    footer = text[skills_start:]

    reordered = header + current_role_block + self_directed_block + footer
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(reordered)

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map, pipeline="full")

    assert any("order wrong" in f for f in failures), failures


def test_full_pipeline_coverage_totals(demo_root, capsys):
    """Regression test for a real bug caught during development: templates/full.md makes
    exp-course-tutor and vol-community unconditional (not gated by ## Include/## Omit), but
    config.json's spine.optional_ids still lists them (shared with the minimal pipeline, which
    *does* gate them). Coverage must not report an unconditionally-present id as DELIBERATE or
    SILENT just because it's in that shared list — it must check whether *this* pipeline's own
    template actually gates it."""
    _build_full(demo_root)
    cfg = cfgmod.resolve(demo_root)
    company_dir = _company_dir(demo_root)

    check_cv.run_coverage(cfg, [company_dir], pipeline="full")

    out = capsys.readouterr().out
    assert "15 of 15 master items present" in out
    assert "exp-course-tutor" not in out, (
        "unconditional in templates/full.md — must not appear as DELIBERATE/SILENT"
    )
    assert "DELIBERATE" not in out
    assert "SILENT" not in out


def test_gated_optional_ids_only_returns_ids_the_template_actually_gates():
    template_text = "{{@exp-course-tutor}}\n\n{{@vol-community?section:Volunteer work}}\n"
    result = check_cv.gated_optional_ids(template_text, ["exp-course-tutor", "vol-community"])
    assert result == ["vol-community"]


def test_not_configured_banner_when_spine_unset(tmp_path):
    """A fresh root with no spine configured must not silently report OK — it should say
    NOT CONFIGURED and no-op (exit 0), per Config.spine_configured."""
    cfg = cfgmod.load_config(str(tmp_path))  # no config.json at all -> DEFAULT_CONFIG
    assert cfg.spine_configured is False


# ---------------------------------------------------------------------------
# Coverage math
# ---------------------------------------------------------------------------

def test_count_locked_slots_matches_template_unconditional_ids(demo_root):
    template_path = os.path.join(demo_root, "templates", "minimal-full.md")
    with open(template_path, "r", encoding="utf-8") as f:
        template_text = f.read()

    # The template has 10 unconditional {{@id}} slots: header-name, header-location,
    # header-phone, header-email, header-linkedin, edu-bsc, exp-self-directed, exp-current-role,
    # skill-note, languages-line. exp-course-tutor and vol-community are both optional
    # ({{@id?}} / {{@id?section:H}}) and must not be counted.
    assert check_cv.count_locked_slots(template_text) == 10


def test_coverage_denominator_is_not_hardcoded(demo_root):
    """The whole point of deriving TOTAL from the template is that adding a new unconditional
    locked slot changes the denominator without touching check_cv.py — prove that by adding one
    and checking the count moves."""
    template_path = os.path.join(demo_root, "templates", "minimal-full.md")
    with open(template_path, "r", encoding="utf-8") as f:
        template_text = f.read()

    before = check_cv.count_locked_slots(template_text)
    augmented = template_text + "\n{{@edu-bsc}}\n"  # a second unconditional slot, any @id works
    after = check_cv.count_locked_slots(augmented)

    assert after == before + 1


def test_coverage_totals_for_demo_application(demo_root, capsys):
    """13 of 14: 3 PRESENT rows (vol-community included, both proj-* used) out of 4 optional/
    proj rows, plus the template's 10 unconditional locked slots -> 13 of 14."""
    cfg = cfgmod.resolve(demo_root)
    company_dir = _company_dir(demo_root)

    check_cv.run_coverage(cfg, [company_dir])

    out = capsys.readouterr().out
    assert "13 of 14 master items present" in out
    assert "exp-course-tutor" in out  # DELIBERATE, declared in ## Omit
    assert "SILENT" not in out  # nothing undeclared for this fully-migrated application


# ---------------------------------------------------------------------------
# An unconfigured spine must diagnose itself, not blame the content
# ---------------------------------------------------------------------------

def _rewrite_spine(demo_root, mutate):
    """Edit config.json's spine block in the throwaway demo copy."""
    path = os.path.join(demo_root, "config.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    mutate(data["spine"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_empty_title_markers_reports_the_config_gap_not_missing_entries(demo_root):
    """The first-real-build failure found in field testing: a user fills locked_order (which the
    walkthrough tells them to) and leaves title_markers at its scaffolded {} (which it didn't).
    identify() then matches nothing, so every locked entry reports as missing — while sitting
    correctly in the rendered CV. The content is fine; the config can't see it. Say so."""
    _rewrite_spine(demo_root, lambda spine: spine.update({"title_markers": {}}))

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)

    assert len(failures) == 1, f"expected one diagnosis, not a pile of blame: {failures}"
    assert "title_markers" in failures[0]
    assert "missing" not in failures[0], "must not read as though content were dropped"


def test_a_locked_id_with_no_marker_is_named_as_such(demo_root):
    """Partial version of the same gap: title_markers exists but doesn't cover every locked id.
    That id can never be found no matter what the CV says, so it's a config fault, not content."""
    _rewrite_spine(demo_root, lambda spine: spine["title_markers"].pop("exp-current-role"))

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)

    joined = " ".join(failures)
    assert "title_markers" in joined and "exp-current-role" in joined, failures
    assert not any("'current role' entry missing" in f for f in failures), (
        "the unmatchable id must be reported once, with its real cause, not also as missing"
    )


def test_a_configured_spine_still_catches_genuinely_missing_content(demo_root):
    """Guard on the guard: the new short-circuit must not swallow real failures when
    title_markers IS configured."""
    cv_path = _cv_path(demo_root)
    with open(cv_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text[:text.index("**Software Engineer")] + text[text.index("## Skills"):]
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(text)

    cfg, alias_map = _cfg_and_alias(demo_root)
    failures = check_cv.check_structure(cfg, _company_dir(demo_root), alias_map)

    assert any("current role" in f and "missing" in f for f in failures), failures
