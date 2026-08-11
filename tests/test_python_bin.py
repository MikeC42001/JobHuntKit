"""Tests for engine/lib.sh's python_bin() — the interpreter resolver.

`python3` is not a name that can be relied on. On Windows the python.org installer provides
`python` and `py` and no `python3` at all, while a `python3` usually *is* on PATH: Windows' App
Execution Alias, a stub that prints a Store advert and exits non-zero. Every test here builds that
situation with shims and asserts the resolver looks past the name to whether the thing runs.
"""

import os
import shutil
import stat
import subprocess

import pytest
from conftest import bash_executable

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_SH = os.path.join(REPO_ROOT, "engine", "lib.sh")


def _shim(dir_path, name, body):
    """An executable shell shim on PATH. No extension: Git Bash resolves these fine, and a real
    Store alias is likewise something bash finds and then can't usefully run."""
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _store_stub(dir_path, name="python3"):
    """Reproduces the Microsoft Store alias: on PATH, exits non-zero, runs no Python."""
    return _shim(dir_path, name, (
        "#!/usr/bin/env bash\n"
        'echo "Python was not found; run without arguments to install from the '
        'Microsoft Store" >&2\n'
        "exit 9009\n"
    ))


def _working_python(dir_path, name, real_python):
    return _shim(dir_path, name, f'#!/usr/bin/env bash\nexec "{real_python}" "$@"\n')


def _resolve(path_prefix=None, env_extra=None):
    """Source lib.sh and print what python_bin() picks, with PATH under our control."""
    env = dict(os.environ)
    if path_prefix is not None:
        env["PATH"] = path_prefix + os.pathsep + env["PATH"]
    env.pop("PYTHON_BIN", None)
    env.update(env_extra or {})
    return subprocess.run(
        [bash_executable(), "-c", f'source "{LIB_SH}"; python_bin'],
        capture_output=True, text=True, env=env, check=False,
    )


@pytest.fixture
def real_python():
    """A python that genuinely runs, found the way a user's machine would have one."""
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found and subprocess.run(
            [found, "-c", "import sys; sys.exit(0)"], capture_output=True, check=False,
        ).returncode == 0:
            return found
    pytest.skip("no working python on PATH to build a shim from")


def test_store_stub_is_skipped_for_a_working_python(tmp_path, real_python):
    """The PC B failure, reproduced: `python3` exists, is first on PATH, and doesn't work.
    Resolving by name picks it and dies; resolving by execution picks `python` and works."""
    shim_dir = str(tmp_path / "shims")
    _store_stub(shim_dir)
    _working_python(shim_dir, "python", real_python)

    result = _resolve(path_prefix=shim_dir)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "python"


def test_missing_python3_falls_back_to_python(tmp_path, real_python):
    """A stock Windows install: no python3 by any spelling, only python."""
    shim_dir = str(tmp_path / "shims")
    _working_python(shim_dir, "python", real_python)

    # PATH is *only* the shim dir plus what bash itself needs, so the machine's own python3
    # can't quietly satisfy the lookup and make this pass for the wrong reason.
    env = dict(os.environ)
    env["PATH"] = shim_dir
    env.pop("PYTHON_BIN", None)
    result = subprocess.run(
        [bash_executable(), "-c", f'source "{LIB_SH}"; python_bin'],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "python"


def test_a_broken_name_is_never_returned(tmp_path):
    """Every name on PATH is a stub. Returning "python3" anyway is the original bug: a caller then
    runs a command that prints a Store advert and dies mid-pipeline."""
    shim_dir = str(tmp_path / "shims")
    _store_stub(shim_dir)
    _store_stub(shim_dir, "python")
    _store_stub(shim_dir, "py")

    env = dict(os.environ)
    env["PATH"] = shim_dir
    env.pop("PYTHON_BIN", None)
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        [bash_executable(), "-c", f'source "{LIB_SH}"; python_bin'],
        capture_output=True, text=True, env=env, check=False,
    )

    resolved = result.stdout.strip()
    if result.returncode == 0:
        # The machine has a real Python in one of the well-known install locations the resolver
        # falls through to (a python.org install on Windows does exactly this). That's a correct
        # resolution, not a failure — the invariant is only that it isn't one of the stubs. Not
        # asserted as a hard failure precisely because it's machine-dependent, and a test that
        # passes on the author's box and fails on a contributor's is worse than a softer one.
        assert resolved not in ("python3", "python", "py")
        assert os.path.isfile(resolved)
    else:
        assert resolved == ""


def test_python_bin_env_var_overrides_everything(tmp_path, real_python):
    shim_dir = str(tmp_path / "shims")
    _working_python(shim_dir, "python3", real_python)
    override = _working_python(str(tmp_path / "elsewhere"), "my-python", real_python)

    result = _resolve(path_prefix=shim_dir, env_extra={"PYTHON_BIN": override})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == override


def test_python_bin_env_var_that_does_not_work_is_an_error_not_a_fallback(tmp_path, real_python):
    """An explicit override that's wrong should say so, not silently resolve to something else —
    the same contract BROWSER_BIN already has in find_browser()."""
    shim_dir = str(tmp_path / "shims")
    _working_python(shim_dir, "python3", real_python)
    broken = _store_stub(str(tmp_path / "elsewhere"), "my-python")

    result = _resolve(path_prefix=shim_dir, env_extra={"PYTHON_BIN": broken})
    assert result.returncode != 0
    assert "PYTHON_BIN" in result.stderr


# ---------------------------------------------------------------------------
# node_supports_require_esm — the other capability probe in lib.sh
# ---------------------------------------------------------------------------

def _node_available():
    return shutil.which("node") is not None


@pytest.mark.skipif(not _node_available(), reason="no node on PATH")
def test_node_probe_agrees_with_actually_requiring_an_esm_package():
    """The probe writes a two-line ES module and requires it. Its answer has to match what the
    converters will really experience, so this asserts the two agree rather than asserting a
    version number — the whole point of probing is that the version rule has holes (21.x and
    22.0-22.11 lack require(esm) despite being newer than 20.19)."""
    probe = subprocess.run(
        [bash_executable(), "-c", f'source "{LIB_SH}"; node_supports_require_esm'],
        capture_output=True, text=True, check=False,
    )

    marked_dir = os.path.join(REPO_ROOT, "engine", "render-support")
    if not os.path.isdir(os.path.join(marked_dir, "node_modules", "marked")):
        pytest.skip("marked not installed yet — nothing to cross-check the probe against")

    real = subprocess.run(
        ["node", "-e", 'require("marked")'],
        capture_output=True, text=True, cwd=marked_dir, check=False,
    )
    assert (probe.returncode == 0) == (real.returncode == 0), (
        f"probe said {probe.returncode == 0}, requiring marked said {real.returncode == 0}: "
        f"{real.stderr.strip()[:200]}"
    )


@pytest.mark.skipif(not _node_available(), reason="no node on PATH")
def test_preflight_passes_on_a_machine_that_can_run_the_suite():
    """CI and any dev machine able to run the renderers must come back clean — a preflight that
    fails where the pipeline works would be worse than none."""
    result = subprocess.run(
        [bash_executable(), os.path.join(REPO_ROOT, "scripts", "preflight.sh")],
        capture_output=True, text=True, check=False,
    )
    if "MISSING browser" in result.stderr:
        pytest.skip("no browser on this machine — not what this test is about")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "python" in result.stdout and "node" in result.stdout


# ---------------------------------------------------------------------------
# Regression guard on the callers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", ["demo.sh", "scripts/sync.sh"])
def test_no_bare_python3_invocation_survives(rel_path):
    """Both scripts hardcoded `python3` and neither ran on Windows because of it. This is a line
    that gets pasted back in without anyone noticing, so pin it: mentions in comments and docs are
    fine, an actual invocation is not."""
    with open(os.path.join(REPO_ROOT, rel_path), encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not stripped.startswith("python3 "), f"{rel_path}:{lineno}: {stripped}"
            assert " python3 " not in f" {stripped} " or "no_python_error" in stripped, (
                f"{rel_path}:{lineno}: {stripped}"
            )
