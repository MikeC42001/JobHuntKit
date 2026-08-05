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
