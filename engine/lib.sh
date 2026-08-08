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
config_get() {
  local key="$1"
  local config_path="$ROOT/config.json"
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

ensure_marked_installed() {
  local support_dir="$1"
  mkdir -p "$support_dir"
  if [ ! -d "$support_dir/node_modules/marked" ]; then
    ( cd "$support_dir" && npm install >/dev/null 2>&1 )
  fi
}
