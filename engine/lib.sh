#!/usr/bin/env bash
# lib.sh — shared helpers for every render_*.sh script: browser discovery, file:// URLs, mtime
# checks, and reading config.json. Sourced, never run directly.
#
# Extracted from four copy-pasted blocks (one per renderer) so a fix lands everywhere at once.
# The Windows-only version of this that used to live in each script found Chrome/Edge under
# /c/Program Files/... and nowhere else — this version adds PATH lookups (Linux) and macOS .app
# bundles, and fixes two latent bugs that only showed up off Windows: `stat -c %Y` is GNU-only
# (silently returns nothing on macOS, so the "PDF was not updated" warning fired on every
# render there) and `file:///$path` produces a wrong `file:////` prefix on POSIX.

# ROOT must be set by the caller before sourcing (the data root, for config_get()).

is_windows_shell() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) return 0 ;;
    *) return 1 ;;
  esac
}

# config_get "render.browser_bin" — reads one dotted key out of $ROOT/config.json via node
# (already a hard dependency of every renderer). Prints nothing if the file, key, or value is
# absent — callers should treat empty output as "not set."
#
# ROOT unset is treated as "no config", not as an error: every renderer sets it, but preflight.sh
# has no data root to speak of and still wants find_browser(). Under `set -u` a bare $ROOT would
# abort the caller instead of falling through to the next lookup.
config_get() {
  local key="$1"
  local config_path="${ROOT:-}/config.json"
  [ -f "$config_path" ] || return 0
  local config_path_native
  config_path_native="$(native_path "$config_path")"
  node -e "
    try {
      const cfg = require('$config_path_native');
      const val = '$key'.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : undefined, cfg);
      if (val !== undefined && val !== null) process.stdout.write(String(val));
    } catch (e) {}
  " 2>/dev/null
}

find_browser() {
  # 1. Explicit override always wins.
  if [ -n "${BROWSER_BIN:-}" ]; then
    if [ -x "$BROWSER_BIN" ]; then echo "$BROWSER_BIN"; return 0; fi
    echo "lib: BROWSER_BIN set but not executable: $BROWSER_BIN" >&2
    return 1
  fi

  # 2. config.json.
  local cfg_bin
  cfg_bin="$(config_get render.browser_bin)"
  if [ -n "$cfg_bin" ] && [ -x "$cfg_bin" ]; then echo "$cfg_bin"; return 0; fi

  # 3. PATH — covers Linux installs and anyone who's aliased a browser manually.
  local c
  for c in google-chrome google-chrome-stable chromium chromium-browser \
           microsoft-edge microsoft-edge-stable brave-browser chrome; do
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
  done

  # 4. Well-known install locations — macOS, then Windows (Git Bash /c, WSL /mnt/c).
  local p
  for p in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files/Microsoft/Edge/Application/msedge.exe" \
    "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
    "${LOCALAPPDATA:-}/Google/Chrome/Application/chrome.exe" \
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe"; do
    if [ -n "$p" ] && [ -f "$p" ]; then echo "$p"; return 0; fi
  done

  return 1
}

no_browser_error() {
  echo "$1: no Chrome/Chromium/Edge/Brave install found." >&2
  echo "  Install one, or set BROWSER_BIN=/path/to/browser, or set render.browser_bin in config.json." >&2
}

# python_bin — the interpreter to run engine/*.py with. Same search shape as find_browser above:
# explicit override, then PATH, then well-known install locations.
#
# `python3` is the wrong name to hardcode on Windows, twice over. The python.org installer
# provides `python` and `py` and no `python3` at all — and a `python3` usually IS on PATH anyway:
# Windows' own App Execution Alias, a stub that opens the Microsoft Store instead of running
# anything. So `command -v` finding a candidate proves nothing here, and a candidate is accepted
# only if it actually executes and reports a new enough Python. Do not "simplify" that back into
# an existence check.
python_bin() {
  local c
  if [ -n "${PYTHON_BIN:-}" ]; then
    if _is_usable_python "$PYTHON_BIN"; then echo "$PYTHON_BIN"; return 0; fi
    echo "lib: PYTHON_BIN set but not a working Python 3.8+: $PYTHON_BIN" >&2
    return 1
  fi

  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && _is_usable_python "$c"; then echo "$c"; return 0; fi
  done

  # Installed but not on PATH — the commonest Windows outcome, since "Add python.exe to PATH" is
  # an unticked checkbox in the installer. Globs, because the version is in the directory name.
  # Per-user locations go through $HOME/$LOCALAPPDATA rather than a hardcoded per-user directory,
  # same as find_browser above: no username baked in, and the leak gate rejects the alternative.
  local p
  for p in \
    "$HOME"/AppData/Local/Programs/Python/Python3*/python.exe \
    "${LOCALAPPDATA:-}"/Programs/Python/Python3*/python.exe \
    "/c/Program Files/Python3"*/python.exe \
    /c/Python3*/python.exe; do
    if [ -f "$p" ] && _is_usable_python "$p"; then echo "$p"; return 0; fi
  done

  return 1
}

# Runs the candidate rather than trusting its name. Exit 0 only for a real Python >= 3.8.
_is_usable_python() {
  "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1
}

no_python_error() {
  echo "$1: no Python 3.8+ found." >&2
  if is_windows_shell; then
    echo "  On Windows the command is usually 'python', not 'python3' — and the 'python3' on PATH" >&2
    echo "  is often the Microsoft Store stub, which is why this check runs it instead of looking" >&2
    echo "  it up. Install from https://python.org and tick \"Add python.exe to PATH\"." >&2
  else
    echo "  Install Python 3.8 or newer from your package manager or https://python.org." >&2
  fi
  echo "  Already installed somewhere unusual? Point at it: export PYTHON_BIN=/path/to/python" >&2
  echo "  See docs/INSTALL.md, or run: bash scripts/preflight.sh" >&2
}

# Native filesystem path for handing to a Windows .exe browser from Git Bash; identity on
# every other platform.
native_path() {
  if is_windows_shell; then
    local dir base
    # shellcheck disable=SC2015 # if cd fails the caller already handed us a bad path; falling
    # back to pwd here just means "same wrong path back", not a masked success.
    dir="$(cd "$(dirname "$1")" && pwd -W 2>/dev/null || pwd)"
    base="$(basename "$1")"
    printf '%s/%s' "$dir" "$base"
  else
    printf '%s' "$1"
  fi
}

# file:// URL with the correct slash count on both platforms — file:///C:/... on Windows,
# file:///Users/... (no doubled slash) on POSIX.
file_url() {
  if is_windows_shell; then
    printf 'file:///%s' "$(native_path "$1")"
  else
    printf 'file://%s' "$1"
  fi
}

# GNU `stat -c` vs BSD/macOS `stat -f` — try both, empty string if neither works (caller treats
# that as "couldn't determine, warn").
file_mtime() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo ""
}

# Headless flags, with --no-sandbox added when running as root (Chrome refuses to run sandboxed
# as root, exiting non-zero with no clearer symptom than this script's generic "PDF was NOT
# updated" warning) or under CI ($CI=true, set by GitHub Actions and most other CI providers) —
# GH Actions' ubuntu runners restrict the setuid sandbox helper for non-root users too, which
# crashes headless Chromium outright (SIGABRT) rather than falling back cleanly.
browser_flags() {
  local flags="--headless=new --disable-gpu --print-to-pdf-no-header --no-pdf-header-footer"
  if [ "$(id -u 2>/dev/null || echo 1)" = "0" ] || [ "${CI:-}" = "true" ]; then
    flags="$flags --no-sandbox"
  fi
  printf '%s' "$flags"
}

# node_supports_require_esm — can this Node `require()` an ES module?
#
# The converters are CommonJS and do `require("marked")`, but marked ships ESM-only: its exports
# map has no "require" condition at all. So the real Node floor isn't marked's declared
# `engines: >= 20`, it's whether Node can require ESM — unflagged in 20.19+, 22.12+, and 23+, but
# NOT in 21.x or 22.0–22.11. Too many holes to express as a `>=` comparison.
#
# So don't compare versions: run the thing. Same reasoning as python_bin() above — a capability
# probe stays correct as Node changes, a version table starts rotting the day it's written.
# Relative require on purpose: an absolute POSIX path baked into the file would not resolve for
# a native node.exe under Git Bash.
node_supports_require_esm() {
  local tmp rc=0
  tmp="$(mktemp -d)" || return 1
  printf 'export const ok = 1;\n' > "$tmp/probe.mjs"
  printf 'require("./probe.mjs");\n' > "$tmp/probe.cjs"
  ( cd "$tmp" && node probe.cjs ) >/dev/null 2>&1 || rc=1
  rm -rf "$tmp"
  return "$rc"
}

no_node_esm_error() {
  echo "$1: this Node is too old to load the markdown renderer." >&2
  echo "  Node $(node --version 2>/dev/null || echo '(unknown)') cannot require() an ES module," >&2
  echo "  which is how the converters load 'marked'. Install Node 22 LTS or newer." >&2
  echo "  (20.19+ and 22.12+ also work; 21.x and 22.0-22.11 do not.)" >&2
  echo "  See docs/INSTALL.md — on Debian/Ubuntu the apt package is too old on every current LTS." >&2
}

ensure_marked_installed() {
  local support_dir="$1"
  # Checked here rather than only in preflight.sh: a renderer can be run directly, and the failure
  # it would otherwise produce is a bare ERR_REQUIRE_ESM from inside a converter.
  if ! node_supports_require_esm; then
    no_node_esm_error "lib"
    return 1
  fi
  mkdir -p "$support_dir"
  if [ ! -d "$support_dir/node_modules/marked" ]; then
    ( cd "$support_dir" && npm install >/dev/null 2>&1 )
  fi
}
