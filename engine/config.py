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
    3. .jobhuntkit-root in the checkout — the root remembered from an earlier --root
    4. Walk up from the current directory looking for a .jobhuntkit marker file
    5. The repo root (this file's grandparent directory) as a last resort

A root is identified by a constant marker file (.jobhuntkit containing "jobhuntkit-root/1"),
never by the presence of config.json: that filename is far too common, and keying on it meant
any unrelated project containing one was claimed as a root by every engine script.

Every script's argparse.ArgumentParser should include ROOT_ARG as a parent so `--root` behaves
identically everywhere.

config.json is deliberately JSON, not YAML/TOML — see build_cv.py's docstring for why avoiding
a third-party dependency matters here. Missing keys fall back to sensible defaults so a fresh
clone with no config.json still runs (with spine checking disabled — see check_cv.py).
"""

import argparse
import json
import os
import sys

# Every engine script imports this module first, so this is the one place to force UTF-8 output.
# Without it, Python on Windows defaults stdout/stderr to the console's codepage (cp1252, not
# UTF-8) even under Git Bash — any em dash or accented character (a name, a Portuguese heading
# alias) then prints as a mangled replacement character instead of erroring loudly. reconfigure()
# is Python 3.7+; guarded because it's absent when stdout is replaced by a non-TextIOWrapper
# (e.g. under some test runners).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

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
    "pipelines": {
        "minimal": {
            "master": "master/master_cv_minimal.md",
            "template": "minimal-full",
            "out": "cv-minimal.md",
        },
        "full": {
            "master": "master/master_cv.md",
            "template": "full",
            "out": "cv.md",
        },
    },
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
    def locked_order(self):
        return self.get("spine.locked_order", [])

    @property
    def title_markers(self):
        return self.get("spine.title_markers", {})

    @property
    def optional_ids(self):
        return self.get("spine.optional_ids", [])

    @property
    def verbatim_ids(self):
        return self.get("spine.verbatim_ids", [])

    @property
    def education_required_titles(self):
        return self.get("spine.education.required_titles", [])

    @property
    def education_require_detail_for(self):
        return self.get("spine.education.require_detail_for", [])

    @property
    def heading_aliases_extra(self):
        return self.get("spine.heading_aliases", {})

    @property
    def spine_configured(self):
        """False for a fresh clone with no spine set up yet — check_cv.py uses this to print a
        NOT CONFIGURED banner instead of a misleading "all OK" that isn't actually checking
        anything."""
        return bool(self.locked_order or self.education_required_titles or self.verbatim_ids)

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
    def pipelines(self):
        """The "pipelines" config block: {name: {"master": ..., "template": ..., "out": ...}},
        each value still relative to root — see pipeline() for the resolved (absolute-master)
        form callers actually want."""
        return self.get("pipelines", {})

    def pipeline(self, name):
        """Resolved pipeline info for e.g. "minimal" or "full": {"master": <abs path>,
        "template": <name, no .md>, "out": <filename>}. Raises KeyError for an unknown pipeline
        name — every caller passes a name it already knows is valid (a CLI --pipeline choice, or
        one of build_cv's own front-matter-parsed selections)."""
        p = self.pipelines.get(name)
        if p is None:
            raise KeyError(
                f"unknown pipeline: {name!r} (check config.json's \"pipelines\" block)"
            )
        return {
            "master": os.path.join(self.root, p["master"]),
            "template": p["template"],
            "out": p["out"],
        }

    @property
    def master_path(self):
        """The minimal pipeline's master — kept as its own property since most callers only
        ever care about this one; equivalent to pipeline("minimal")["master"]."""
        return self.pipeline("minimal")["master"]

    @property
    def master_full_path(self):
        """The full pipeline's master; equivalent to pipeline("full")["master"]."""
        return self.pipeline("full")["master"]

    @property
    def templates_dir(self):
        return os.path.join(self.root, "templates")

    @property
    def offer_pages_dir(self):
        return os.path.join(self.root, "applications", "offer-pages")

    @property
    def produced_dir(self):
        return os.path.join(self.root, "produced")


MARKER_NAME = ".jobhuntkit"
MARKER_CONSTANT = "jobhuntkit-root/1"
POINTER_NAME = ".jobhuntkit-root"


def is_root(path):
    """True if `path` is a JobHuntKit data root.

    Keyed on a constant marker file, not on the presence of config.json. That filename is one of
    the most common there is, and treating its presence as proof made any unrelated project
    containing one look like a root to every engine script. A constant is exact rather than
    probabilistic, and checking it costs one open with no JSON parsing — cheaper than the old
    check, which matters in a walk-up that runs once per directory level.
    """
    try:
        with open(os.path.join(path, MARKER_NAME), "r", encoding="utf-8") as f:
            return f.readline().strip() == MARKER_CONSTANT
    except (OSError, UnicodeDecodeError):
        return False


def write_marker(path):
    """Idempotent. Returns True only if it actually wrote one, so a caller can report a
    migration rather than claiming one on every run."""
    if is_root(path):
        return False
    with open(os.path.join(path, MARKER_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(MARKER_CONSTANT + "\n")
    return True


def read_pointer():
    """The remembered root, written by init_workspace.py when given an external --root.

    Read relative to the checkout rather than cwd, so it works from any directory — the one
    thing $JOBHUNTKIT_ROOT cannot do, since that only survives inside the shell that set it.
    """
    try:
        with open(os.path.join(REPO_ROOT, POINTER_NAME), "r", encoding="utf-8") as f:
            value = f.readline().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return os.path.abspath(os.path.expanduser(value)) if value else None


def _warn(*lines):
    for line in lines:
        sys.stderr.write("config: " + line + "\n")


def find_root(explicit_root=None, announce=True):
    """Resolve the data root:

        --root  >  $JOBHUNTKIT_ROOT  >  .jobhuntkit-root  >  walk up  >  this checkout

    `announce` prints which rule fired whenever the answer isn't the plain default. An env var
    or a pointer file is invisible at the call site — nothing on the command line says where the
    data came from — and the pointer is the more invisible of the two, because it survives
    reboots.
    """
    # expanduser before abspath: nothing expands a literal "~" for us. A shell does it for an
    # unquoted path, but `export JOBHUNTKIT_ROOT="~/my-cv-data"` (quoted, as anyone in the habit
    # of quoting paths would write) arrives here as a literal tilde and would otherwise resolve
    # to a "~" directory relative to cwd.
    if explicit_root:
        return os.path.abspath(os.path.expanduser(explicit_root))

    env_root = os.environ.get("JOBHUNTKIT_ROOT")
    if env_root:
        root = os.path.abspath(os.path.expanduser(env_root))
        if not is_root(root):
            # A warning, not an error: init_workspace.py legitimately runs before a root exists.
            _warn(
                "JOBHUNTKIT_ROOT is set to " + root,
                "  but that isn't a JobHuntKit root. Every command in this shell will use it.",
                "  If that's not what you meant: unset JOBHUNTKIT_ROOT, or pass --root.",
                '  (A quoted "~" is not expanded by the shell.)',
            )
        elif announce:
            _warn("root: " + root + " (from $JOBHUNTKIT_ROOT)")
        return root

    pointer = read_pointer()
    if pointer:
        if not is_root(pointer):
            _warn(
                POINTER_NAME + " points at " + pointer,
                "  but that isn't a JobHuntKit root any more — moved or deleted?",
                "  Pass --root, or delete " + POINTER_NAME + " to fall back to this checkout.",
            )
        elif announce:
            _warn("root: " + pointer + " (remembered in " + POINTER_NAME + ")")
        return pointer

    probe = os.path.abspath(os.getcwd())
    while True:
        if is_root(probe):
            if announce and os.path.abspath(probe) != os.path.abspath(REPO_ROOT):
                _warn("root: " + probe + " (found above the current directory)")
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
