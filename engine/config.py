"""config.py — root resolution and config.json loading, shared by every engine script.

The engine (this folder) never contains personal data. Everything a person writes — their
name, contact details, master CV, per-company applications — lives at a "root" directory that
is resolved at runtime, not hard-coded. This is what lets the same clone serve three purposes
with zero code changes: a 60-second demo (root = examples/demo/), your own real data (root =
this repo checkout itself, or anywhere else via --root), and a private data directory kept
entirely outside this repo.

Root resolution order:
    1. --root <path> on the command line
    2. $JOBHUNTKIT_ROOT environment variable
    3. Walk up from the current directory looking for a config.json
    4. The repo root (this file's grandparent directory) as a last resort

Every script's argparse.ArgumentParser should include ROOT_ARG as a parent so `--root` behaves
identically everywhere.

config.json is deliberately JSON, not YAML/TOML — see build_cv.py's docstring for why avoiding
a third-party dependency matters here. Missing keys fall back to sensible defaults so a fresh
clone with no config.json still runs (with spine checking disabled — see check_cv.py).
"""

import argparse
import json
import os

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(ENGINE_DIR)

DEFAULT_CONFIG = {
    "person": {
        "name": "",
        "file_prefix": "CV",
        "letter_prefix": None,  # None -> "CoverLetter_" + file_prefix
    },
    "render": {
        "default_photo": None,  # None -> --photo required on the CLI
        "default_style": "a",
        "browser_bin": None,  # None -> auto-detect
    },
    "spine": {
        "locked_order": [],
        "title_markers": {},
        "optional_ids": [],
        "verbatim_ids": [],
        "education": {"required_titles": [], "require_detail_for": []},
        "heading_aliases": {},
    },
    "limits": {"soft_line_budget": 57, "max_pages": 1},
    "display_names": {},
}


def _deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    """Resolved root + loaded config.json, as attribute access over nested dicts."""

    def __init__(self, root, data):
        self.root = root
        self._data = data

    def get(self, dotted_path, default=None):
        node = self._data
        for part in dotted_path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    @property
    def person_name(self):
        return self.get("person.name", "")

    @property
    def file_prefix(self):
        return self.get("person.file_prefix", "CV")

    @property
    def letter_prefix(self):
        return self.get("person.letter_prefix") or f"CoverLetter_{self.file_prefix}"

    @property
    def default_photo(self):
        photo = self.get("render.default_photo")
        return os.path.join(self.root, photo) if photo else None

    @property
    def default_style(self):
        return self.get("render.default_style", "a")

    @property
    def browser_bin(self):
        return self.get("render.browser_bin")

    @property
    def display_names(self):
        return self.get("display_names", {})

    @property
    def soft_line_budget(self):
        return self.get("limits.soft_line_budget", 57)

    @property
    def max_pages(self):
        return self.get("limits.max_pages", 1)

    # -- paths, all relative to root --
    @property
    def master_dir(self):
        return os.path.join(self.root, "master")

    @property
    def master_path(self):
        return os.path.join(self.master_dir, "master_cv_minimal.md")

    @property
    def templates_dir(self):
        return os.path.join(self.root, "templates")

    @property
    def offer_pages_dir(self):
        return os.path.join(self.root, "applications", "offer-pages")

    @property
    def produced_dir(self):
        return os.path.join(self.root, "produced")


def find_root(explicit_root=None):
    if explicit_root:
        return os.path.abspath(explicit_root)

    env_root = os.environ.get("JOBHUNTKIT_ROOT")
    if env_root:
        return os.path.abspath(env_root)

    probe = os.path.abspath(os.getcwd())
    while True:
        if os.path.isfile(os.path.join(probe, "config.json")):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent

    return REPO_ROOT


def load_config(root):
    config_path = os.path.join(root, "config.json")
    data = DEFAULT_CONFIG
    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        data = _deep_merge(DEFAULT_CONFIG, user_data)
    return Config(root, data)


def resolve(explicit_root=None):
    """One-call convenience: find the root, load its config.json (or defaults), return a Config."""
    root = find_root(explicit_root)
    return load_config(root)


def add_root_arg(parser):
    """Adds --root to an argparse.ArgumentParser. Call before parser.parse_args()."""
    parser.add_argument(
        "--root",
        default=None,
        help="data root directory (default: $JOBHUNTKIT_ROOT, or walk up from cwd for "
        "config.json, or this repo checkout)",
    )
    return parser


def root_parent_parser():
    """A parent parser carrying just --root, for scripts that want `parents=[...]`."""
    parent = argparse.ArgumentParser(add_help=False)
    add_root_arg(parent)
    return parent
