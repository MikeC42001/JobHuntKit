"""Tests for scripts/init_workspace.py — the fresh-root scaffolding script.

Every test works against tmp_path, never the real checkout — init_workspace writes files, and
copying first (or targeting an isolated dir) is what keeps a failing run from dirtying the
working tree. conftest.py already puts scripts/ (and engine/) on sys.path.
"""

import json
import os
import shutil
import subprocess
import sys

import build_cv
import check_cv
import config as cfgmod
import init_workspace

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(REPO_ROOT, "engine")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")


def _init(root, *flags):
    return init_workspace.main(["--root", str(root), *flags])


def test_creates_expected_layout(tmp_path):
    assert _init(tmp_path) == 0

    for d in init_workspace.EMPTY_DIRS:
        assert os.path.isdir(tmp_path / d), f"missing dir: {d}"

    for name in init_workspace.CV_TEMPLATES:
        assert (tmp_path / "templates" / name).is_file()

    for _src, dst in init_workspace.STARTER_FILES:
        assert (tmp_path / dst).is_file(), f"missing starter: {dst}"

    example_app = tmp_path / "applications" / "offer-pages" / init_workspace.EXAMPLE_COMPANY / "application.md"
    assert example_app.is_file()


def test_is_idempotent_and_never_clobbers(tmp_path, capsys):
    assert _init(tmp_path) == 0

    master = tmp_path / "master" / "master_cv_minimal.md"
    master.write_text("MY REAL CV\n", encoding="utf-8")

    assert _init(tmp_path) == 0
    out = capsys.readouterr().out

    assert master.read_text(encoding="utf-8") == "MY REAL CV\n"
    assert "kept" in out
    assert "0 file(s) written" in out


def test_force_never_overwrites_personal_files(tmp_path):
    assert _init(tmp_path) == 0

    personal_paths = [
        tmp_path / "config.json",
        tmp_path / "master" / "master_cv_minimal.md",
        tmp_path / "profile" / "background.md",
        tmp_path / "applications" / "offer-pages" / init_workspace.EXAMPLE_COMPANY / "application.md",
    ]
    for p in personal_paths:
        p.write_text("SENTINEL\n", encoding="utf-8")

    template = tmp_path / "templates" / "minimal-full.md"
    template.write_text("SENTINEL\n", encoding="utf-8")

    assert _init(tmp_path, "--force") == 0

    for p in personal_paths:
        assert p.read_text(encoding="utf-8") == "SENTINEL\n", f"--force touched personal file: {p}"

    restored = template.read_text(encoding="utf-8")
    assert restored != "SENTINEL\n"
    with open(os.path.join(REPO_ROOT, "templates", "minimal-full.md"), "r", encoding="utf-8", newline="") as f:
        expected = f.read().replace("\r\n", "\n")
    assert restored == expected


def test_check_mode_writes_nothing(tmp_path):
    root = tmp_path / "root"
    assert _init(root, "--check") == 0
    assert not root.exists()


def test_written_files_use_lf_endings(tmp_path):
    assert _init(tmp_path) == 0

    for path in tmp_path.rglob("*"):
        if not path.is_file():
            continue
        with open(path, "r", encoding="utf-8", newline="") as f:
            text = f.read()
        assert "\r\n" not in text, f"CRLF found in scaffolded file: {path}"


def test_config_json_matches_the_example_and_is_unconfigured(tmp_path):
    assert _init(tmp_path) == 0

    with open(tmp_path / "config.json", "r", encoding="utf-8") as f:
        written = json.load(f)
    with open(os.path.join(REPO_ROOT, "config.example.json"), "r", encoding="utf-8") as f:
        example = json.load(f)
    assert written == example

    cfg = cfgmod.load_config(str(tmp_path))
    assert cfg.spine_configured is False


def test_every_repo_template_is_classified():
    import glob

    on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(REPO_ROOT, "templates", "*.md"))}
    starter_basenames = {
        os.path.basename(src) for src, _dst in init_workspace.STARTER_FILES if src.startswith("templates/")
    }
    accounted_for = set(init_workspace.CV_TEMPLATES) | starter_basenames | {
        os.path.basename(init_workspace.EXAMPLE_COMPANY_SOURCE)
    }
    assert on_disk == accounted_for, (
        "a templates/*.md file exists that init_workspace.py doesn't know what to do with — "
        "add it to CV_TEMPLATES, STARTER_FILES, or EXAMPLE_COMPANY_SOURCE"
    )


def test_no_example_flag_skips_company_folder(tmp_path):
    assert _init(tmp_path, "--no-example") == 0
    offer_pages = tmp_path / "applications" / "offer-pages"
    assert offer_pages.is_dir()
    assert list(offer_pages.iterdir()) == []


def test_default_root_destinations_are_gitignored():
    if not shutil.which("git"):
        return

    def check_ignored(rel_path):
        result = subprocess.run(
            ["git", "-C", REPO_ROOT, "check-ignore", "-q", rel_path],
            capture_output=True,
        )
        return result.returncode == 0

    for _src, dst in init_workspace.STARTER_FILES:
        assert check_ignored(dst), f"{dst} is not gitignored — a scaffolded root risks leaking it"

    example_dst = os.path.join(
        "applications", "offer-pages", init_workspace.EXAMPLE_COMPANY, "application.md"
    )
    assert check_ignored(example_dst)

    for name in init_workspace.CV_TEMPLATES:
        assert not check_ignored(os.path.join("templates", name)), (
            "templates/ is engine-owned and tracked by design — it should not be gitignored"
        )


def test_fresh_root_builds_and_check_reports_not_configured(tmp_path):
    root = str(tmp_path / "myroot")
    env = dict(os.environ)
    env.pop("JOBHUNTKIT_ROOT", None)

    def run(script, *args):
        return subprocess.run(
            [sys.executable, os.path.join(script), "--root", root, *args],
            cwd=REPO_ROOT, capture_output=True, text=True, env=env,
        )

    r0 = run(os.path.join(SCRIPTS_DIR, "init_workspace.py"))
    assert r0.returncode == 0, r0.stderr

    r1 = run(os.path.join(ENGINE_DIR, "build_cv.py"), "--all")
    assert r1.returncode == 0, r1.stderr
    assert "written" in r1.stdout

    r2 = run(os.path.join(ENGINE_DIR, "check_cv.py"))
    assert r2.returncode == 0, r2.stderr
    assert "NOT CONFIGURED" in r2.stdout
    assert "companies OK" not in r2.stdout


def test_example_company_output_has_no_unresolved_tokens(tmp_path):
    assert _init(tmp_path) == 0

    cfg = cfgmod.resolve(str(tmp_path))
    master = build_cv.parse_master(cfg.master_path)
    company_dir = os.path.join(cfg.offer_pages_dir, init_workspace.EXAMPLE_COMPANY)
    build_cv.build_company(cfg, company_dir, master, check_only=False)

    with open(os.path.join(company_dir, "cv-minimal.md"), "r", encoding="utf-8") as f:
        output = f.read()

    assert "{{" not in output
    assert "<!--" not in output
    assert "-->" not in output

    # check_cv's structure gate should also treat this as a clean (if unconfigured) build.
    failures = check_cv.check_structure(cfg, company_dir, check_cv.alias_to_canon(cfg))
    assert failures == []


def _next_steps(root, capsys):
    """print_report's tail, captured. Called directly rather than through a scaffold so the
    default-root case can be exercised without writing into the checkout."""
    init_workspace.print_report(root, "test", [("wrote", "config.json")], False)
    return capsys.readouterr().out


def test_next_steps_carry_root_when_root_is_external(tmp_path, capsys):
    """A scaffold to a separate root prints commands that must include --root. Without it,
    someone who deliberately chose an external root is told to run engine commands that resolve
    back to the checkout instead — silently building against the wrong data."""
    out = _next_steps(str(tmp_path), capsys)

    assert "build_cv.py --root" in out, (
        "init_workspace scaffolded to an external root but told the user to run build_cv.py "
        "with no --root, which would target the checkout instead"
    )
    assert "check_cv.py --root" in out
    assert "JOBHUNTKIT_ROOT" in out, "the env-var alternative to repeating --root should be offered"
    # The .gitignore reassurance is about *this checkout* and is meaningless for an external root.
    assert ".gitignore already excludes them" not in out


def test_next_steps_stay_flagless_for_the_default_root(capsys):
    """The common case must not grow noise: root == checkout needs no --root anywhere."""
    out = _next_steps(init_workspace.REPO_ROOT, capsys)

    assert "--root" not in out, "default root should not print --root on any command"
    assert "build_cv.py --all" in out
    assert ".gitignore already excludes them" in out
