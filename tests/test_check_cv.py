"""Tests for engine/check_cv.py — structure gate + coverage report.

Structure tests work directly on a copy of the demo's rendered cv-minimal.md (not through
build_cv.py) since check_structure() reads output shape, independent of how that output was
produced — the same class of bug (locked-experience entry reordered or a verbatim line quietly
dropped) can happen to a hand-edited file too, and the checker doesn't care which.
"""

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
