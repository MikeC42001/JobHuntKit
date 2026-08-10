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
    """A real root: the constant marker is what identifies one, config.json is just its config."""
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "config.json"), "w", encoding="utf-8") as f:
        json.dump({}, f)
    cfgmod.write_marker(path)
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


def test_env_root_that_isnt_a_root_warns(monkeypatch, capsys, tmp_path):
    """An env var is invisible at the call site — unlike --root, nothing on the command line says
    where the data came from. Pointing it somewhere empty must not fail silently."""
    monkeypatch.setenv("JOBHUNTKIT_ROOT", str(tmp_path / "nowhere"))
    cfgmod.find_root()

    err = capsys.readouterr().err
    assert "JOBHUNTKIT_ROOT" in err
    assert "isn't a JobHuntKit root" in err


def test_env_root_that_is_a_root_does_not_warn(monkeypatch, capsys, tmp_path):
    """The warning must not cry wolf on a correctly configured root, or it gets tuned out. The
    announce line is a different thing and is expected — it's what makes an invisible env var
    visible at the call site."""
    monkeypatch.setenv("JOBHUNTKIT_ROOT", _make_root(str(tmp_path / "root")))
    cfgmod.find_root()

    err = capsys.readouterr().err
    assert "isn't a JobHuntKit root" not in err
    assert "from $JOBHUNTKIT_ROOT" in err, "the rule that fired should be announced"


def test_announce_can_be_silenced(monkeypatch, capsys, tmp_path):
    """Callers that resolve a root for their own bookkeeping shouldn't print anything."""
    monkeypatch.setenv("JOBHUNTKIT_ROOT", _make_root(str(tmp_path / "root")))
    cfgmod.find_root(announce=False)

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


# --- root identification: a constant marker, never the presence of config.json ---


def test_foreign_config_json_is_not_a_root(tmp_path, monkeypatch):
    """The bug this replaced: config.json is one of the most common filenames there is, and
    treating its presence as proof meant any unrelated project containing one was claimed as the
    root by every engine script."""
    foreign = tmp_path / "some-other-project"
    (foreign / "src").mkdir(parents=True)
    (foreign / "config.json").write_text('{"name": "unrelated", "port": 8080}', encoding="utf-8")

    assert not cfgmod.is_root(str(foreign))

    monkeypatch.delenv("JOBHUNTKIT_ROOT", raising=False)
    monkeypatch.chdir(foreign / "src")
    assert cfgmod.find_root(announce=False) == cfgmod.REPO_ROOT


def test_foreign_config_json_sharing_our_key_names_is_still_not_a_root(tmp_path):
    """Specifically the case a key-based heuristic would have failed: "render" and "limits" are
    generic enough for a game or build config to carry them."""
    foreign = tmp_path / "renderer"
    foreign.mkdir()
    (foreign / "config.json").write_text(
        '{"render": {"fps": 60}, "limits": {"mem": 512}}', encoding="utf-8"
    )
    assert not cfgmod.is_root(str(foreign))


def test_marker_with_wrong_contents_is_not_a_root(tmp_path):
    """Guards against an empty or unrelated dotfile another tool happened to leave behind."""
    d = tmp_path / "root"
    d.mkdir()
    (d / cfgmod.MARKER_NAME).write_text("something else\n", encoding="utf-8")
    assert not cfgmod.is_root(str(d))

    (d / cfgmod.MARKER_NAME).write_text("", encoding="utf-8")
    assert not cfgmod.is_root(str(d))


def test_write_marker_is_idempotent_and_reports_only_real_writes(tmp_path):
    d = tmp_path / "root"
    d.mkdir()
    assert cfgmod.write_marker(str(d)) is True
    assert cfgmod.is_root(str(d))
    assert cfgmod.write_marker(str(d)) is False, "a second call must not claim it wrote one"


def test_walk_up_finds_a_real_root_from_a_subdirectory(tmp_path, monkeypatch):
    root = tmp_path / "my-cv-data"
    (root / "deep" / "deeper").mkdir(parents=True)
    cfgmod.write_marker(str(root))

    monkeypatch.delenv("JOBHUNTKIT_ROOT", raising=False)
    monkeypatch.chdir(root / "deep" / "deeper")
    assert cfgmod.find_root(announce=False) == str(root)


def test_the_shipped_demo_is_a_marked_root():
    """examples/demo is a real root and is tracked as one, so demo.sh and CI exercise the marker
    path rather than a synthetic fixture."""
    assert cfgmod.is_root(os.path.join(REPO_ROOT, "examples", "demo"))
