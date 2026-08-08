#!/usr/bin/env bash
# render_letter.sh — convert a cover_letter.md file into a clean, prose-only PDF (no CV-style
# section headers — just readable paragraphs and a right-formatted signature block).
#
# Usage:
#   engine/render_letter.sh applications/offer-pages/<Company>/cover_letter.md
#   engine/render_letter.sh --root path/to/data applications/<company>/cover_letter.md
#
# Output: <dir of source>/generate-pdfs/cover_letter.pdf (+ intermediate .html). Strips any lines
# starting with "> " (internal tailoring notes) and everything from a lone "---" line onward
# (internal draft/review footer) before rendering — see render-support/letter2html.js.
#
# No --photo, no --style — a letter has neither a photo nor style variants.
#
# Requires: node/npm on PATH, and a Chromium-family browser installed (Chrome, Edge, Chromium,
# or Brave — see lib.sh's find_browser for the search order, or set BROWSER_BIN to override).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPPORT_DIR="$SCRIPT_DIR/render-support"

ROOT=""
FILES=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

# Root resolution mirrors render_cv_minimal.sh: --root, else $JOBHUNTKIT_ROOT, else the repo
# checkout (this script's grandparent directory). No cwd walk-up — that's config.py's job, not
# a shell script's.
if [ -z "$ROOT" ]; then
  ROOT="${JOBHUNTKIT_ROOT:-$(dirname "$SCRIPT_DIR")}"
fi
ROOT="$(cd "$ROOT" && pwd)"

# shellcheck source=engine/lib.sh
source "$SCRIPT_DIR/lib.sh"

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "Usage: render_letter.sh [--root <dir>] file1.md [file2.md ...]" >&2
  exit 1
fi

BROWSER="$(find_browser)" || { no_browser_error "render_letter"; exit 1; }

ensure_marked_installed "$SUPPORT_DIR"

for src in "${FILES[@]}"; do
  if [ ! -f "$src" ]; then
    echo "render_letter: skipping, not found: $src" >&2
    continue
  fi

  src_dir="$(cd "$(dirname "$src")" && pwd)"
  out_dir="$src_dir/generate-pdfs"
  mkdir -p "$out_dir"

  html_path="$out_dir/cover_letter.html"
  pdf_path="$out_dir/cover_letter.pdf"

  node "$SUPPORT_DIR/letter2html.js" "$src" "$html_path" "cover_letter"

  # mtime before, so a silent write failure (e.g. the PDF is locked open in a viewer) can be
  # detected below instead of always printing "wrote" regardless of whether it actually did.
  mtime_before="$(file_mtime "$pdf_path")"

  # shellcheck disable=SC2046 # browser_flags() intentionally returns multiple
  # space-separated flags meant to word-split into separate argv entries.
  "$BROWSER" $(browser_flags) \
    --print-to-pdf="$(native_path "$pdf_path")" \
    "$(file_url "$html_path")" >/dev/null 2>&1

  mtime_after="$(file_mtime "$pdf_path")"

  if [ -z "$mtime_after" ] || [ "$mtime_before" = "$mtime_after" ]; then
    echo "render_letter: WARNING — $pdf_path was NOT updated (still has old content)." >&2
    echo "  Likely cause: the file is open in a PDF viewer/browser tab and the browser" >&2
    echo "  couldn't overwrite it. Close it and re-run." >&2
  else
    echo "render_letter: wrote $pdf_path"
  fi
done
