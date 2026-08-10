"""Root resolution — the one piece of the engine every script depends on, and the path least
exercised in normal development (whoever builds the toolkit runs it from the checkout, so
`--root` and $JOBHUNTKIT_ROOT are the branches that rot unwatched).
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "engine"))

import config as cfgmod  # noqa: E402


def _make_root(path):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "config.json"), "w", encoding="utf-8") as f:
        json.dump({}, f)
    return str(path)


def test_explicit_root_expands_a_literal_tilde():
    """Nothing expands "~" for us. A shell does it for an unquoted path, but a quoted
    --root "~/my-cv-data" arrives here literally and would resolve to a "~" directory under cwd."""
    resolved = cfgmod.find_root("~/my-cv-data")
    assert "~" not in resolved
    assert resolved == os.path.abspath(os.path.expanduser("~/my-cv-data"))


def test_env_root_expands_a_literal_tilde(monkeypatch):
    monkeypatch.setenv("JOBHUNTKIT_ROOT", "~/my-cv-data")
    resolved = cfgmod.find_root()
    assert "~" not in resolved
    assert resolved == os.path.abspath(os.path.expanduser("~/my-cv-data"))


def test_env_root_without_config_json_warns(monkeypatch, capsys, tmp_path):
    """An env var is invisible at the call site — unlike --root, nothing on the command line says
    where the data came from. Pointing it somewhere empty must not fail silently."""
    monkeypatch.setenv("JOBHUNTKIT_ROOT", str(tmp_path / "nowhere"))
    cfgmod.find_root()

    err = capsys.readouterr().err
    assert "JOBHUNTKIT_ROOT" in err
    assert "no config.json" in err


def test_env_root_with_config_json_is_silent(monkeypatch, capsys, tmp_path):
    """The warning must not cry wolf on a correctly configured root, or it gets tuned out."""
    monkeypatch.setenv("JOBHUNTKIT_ROOT", _make_root(str(tmp_path / "root")))
    cfgmod.find_root()

    assert capsys.readouterr().err == ""


def test_no_env_var_is_silent(monkeypatch, capsys):
    """The overwhelmingly common case prints nothing at all."""
    monkeypatch.delenv("JOBHUNTKIT_ROOT", raising=False)
    cfgmod.find_root()

    assert capsys.readouterr().err == ""


def test_explicit_root_beats_the_env_var(monkeypatch, tmp_path):
    """--root has to win, so a set-and-forgotten env var can still be overridden per command."""
    monkeypatch.setenv("JOBHUNTKIT_ROOT", str(tmp_path / "from-env"))
    assert cfgmod.find_root(str(tmp_path / "explicit")) == os.path.abspath(
        str(tmp_path / "explicit")
    )
