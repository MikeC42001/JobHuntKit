"""Shared pytest fixtures for the JobHuntKit test suite.

Every test that needs a data root works on a *copy* under tmp_path, never the real
examples/demo/ or the repo itself — build_cv.py and sync.sh both write files, and the point of
copying first is that a failing test run never leaves the working tree dirty.
"""

import os
import shutil
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
ENGINE_DIR = os.path.join(REPO_ROOT, "engine")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
DEMO_ROOT = os.path.join(REPO_ROOT, "examples", "demo")
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")

for _p in (ENGINE_DIR, SCRIPTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture
def demo_root(tmp_path):
    """A writable copy of examples/demo/, isolated per test."""
    dest = tmp_path / "demo"
    shutil.copytree(DEMO_ROOT, dest)
    return str(dest)


def bash_executable():
    """Path to a real bash for tests that shell out to a .sh script. On Windows, "bash" on PATH
    can resolve to the WSL launcher stub Windows itself ships (which errors out if no WSL distro
    is installed, as on a stock GitHub Actions windows-latest runner) instead of Git for
    Windows' own bash.exe, which every dev machine and that same runner both also ship.
    A real end user never hits this: they already run these scripts from inside Git Bash, so
    there's no new "bash" process to resolve; this only matters for spawning one from Python."""
    if sys.platform == "win32":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ):
            if os.path.isfile(candidate):
                return candidate
    return "bash"
