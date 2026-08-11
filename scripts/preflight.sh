#!/usr/bin/env bash
# preflight.sh — answers "will this work on this machine?" before you find out the hard way at
# step 3 of 10, halfway through a render.
#
# Checks the three hard requirements (Python 3.8+, Node.js, a Chromium-family browser) and prints
# a concrete fix for each one that's missing, rather than leaving you with `python3: command not
# found` and a search engine.
#
# Usage:
#   bash scripts/preflight.sh            # full report, one line per requirement
#   bash scripts/preflight.sh --quiet    # print only failures — what demo.sh runs
#
# Exit 0 if everything needed is present, 1 otherwise.

set -uo pipefail   # deliberately no -e: the point is to report every problem, not stop at the first

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# shellcheck source=engine/lib.sh
source "$REPO_ROOT/engine/lib.sh"

QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

FAILED=0

ok()   { [ "$QUIET" -eq 1 ] || printf '  ok    %-8s %s\n' "$1" "$2"; }
bad()  { printf '  MISSING %-6s %s\n' "$1" "$2" >&2; FAILED=1; }
note() { [ "$QUIET" -eq 1 ] || printf '        %s\n' "$1"; }

[ "$QUIET" -eq 1 ] || echo "JobHuntKit preflight"

# --- Shell ---------------------------------------------------------------------------------
# Not a check that can fail: if this script is running at all, Bash exists. Worth saying out loud
# on Windows anyway, because "run it from Git Bash" is the single most common thing people miss —
# PowerShell and cmd cannot run any of the renderers.
if is_windows_shell; then
  ok "shell" "$(uname -s) — Git Bash or equivalent (PowerShell/cmd cannot run the renderers)"
else
  ok "shell" "$(uname -s)"
fi

# --- Python --------------------------------------------------------------------------------
if PY="$(python_bin)"; then
  ok "python" "$("$PY" --version 2>&1) — $PY"
  case "$PY" in
    python3|python|py) ;;
    *) note "not on PATH; the scripts found it anyway. To use it directly: export PYTHON_BIN=$PY" ;;
  esac
else
  bad "python" "no Python 3.8+ found"
  no_python_error "preflight"
fi

# --- Node ----------------------------------------------------------------------------------
# The renderers use node for markdown->HTML (marked, installed on first render) and for reading
# config.json, so it's a hard requirement even though nothing here is a Node project.
if command -v node >/dev/null 2>&1 && node --version >/dev/null 2>&1; then
  ok "node" "$(node --version) — $(command -v node)"
else
  bad "node" "no Node.js found"
  echo "  Install from https://nodejs.org (LTS), or: winget install OpenJS.NodeJS.LTS" >&2
  echo "  macOS: brew install node   ·   Debian/Ubuntu: sudo apt install nodejs npm" >&2
fi

# --- Browser -------------------------------------------------------------------------------
# Reuses find_browser() so this reports exactly what the renderers will actually pick, including
# the well-known install locations — not a second, subtly different search.
if BROWSER="$(find_browser)"; then
  ok "browser" "$BROWSER"
else
  bad "browser" "no Chrome/Chromium/Edge/Brave found"
  no_browser_error "preflight"
fi

# --- Verdict -------------------------------------------------------------------------------
if [ "$FAILED" -ne 0 ]; then
  echo "" >&2
  echo "preflight: something's missing — see above, or docs/INSTALL.md for the per-OS walkthrough." >&2
  exit 1
fi

[ "$QUIET" -eq 1 ] || { echo ""; echo "preflight: all good — run 'bash demo.sh'."; }
exit 0
