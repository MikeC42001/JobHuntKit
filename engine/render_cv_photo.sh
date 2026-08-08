#!/usr/bin/env bash
# render_cv_photo.sh — convert any CV markdown file into a modern, two-column PDF with a
# circular photo in the header band. Id-agnostic, same as render_cv.sh: works on a built cv.md,
# a master file pointed at directly, or a hand-written file with no @id scheme — see
# cv2html-photo.js's header comment for how it cleans its own input. Companion to render_cv.sh
# (which stays the plain/ATS-safe, no-photo, single-column renderer) — this one trades some
# ATS-parsing safety for a more attractive human-facing layout. Use per application based on
# the hiring company's culture and how strict/legacy their ATS is likely to be.
#
# Usage:
#   engine/render_cv_photo.sh applications/offer-pages/<Company>/cv.md
#   engine/render_cv_photo.sh --photo images/me.png master/master_cv.md
#   engine/render_cv_photo.sh --root path/to/data applications/<company>/cv.md
#
# --photo <path> — optional. Falls back to config.json's render.default_photo if set (same
#   fallback render_cv_minimal.sh already has); otherwise required. Casual vs. formal photo is
#   a per-application call some people like to make — no forced single default.
#
# Output: <dir of source>/generate-pdfs/cv-photo.pdf (+ intermediate .html) — a distinct
# filename from render_cv.sh's cv.pdf, so both can exist side by side per application. Strips
# any lines starting with "> " (internal tailoring notes) before rendering, same as render_cv.sh.
#
# Requires: node/npm on PATH, and a Chromium-family browser installed (Chrome, Edge, Chromium,
# or Brave — see lib.sh's find_browser for the search order, or set BROWSER_BIN to override).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPPORT_DIR="$SCRIPT_DIR/render-support"

ROOT=""
PHOTO=""
FILES=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --photo)
      PHOTO="$2"
      shift 2
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

# Root resolution mirrors render_cv.sh / render_cv_minimal.sh: --root, else $JOBHUNTKIT_ROOT,
# else the repo checkout (this script's grandparent directory).
if [ -z "$ROOT" ]; then
  ROOT="${JOBHUNTKIT_ROOT:-$(dirname "$SCRIPT_DIR")}"
fi
ROOT="$(cd "$ROOT" && pwd)"

source "$SCRIPT_DIR/lib.sh"

if [ -z "$PHOTO" ]; then
  cfg_photo="$(config_get render.default_photo)"
  if [ -n "$cfg_photo" ]; then
    case "$cfg_photo" in
      /*) PHOTO="$cfg_photo" ;;
      *) PHOTO="$ROOT/$cfg_photo" ;;
    esac
  fi
fi

if [ -z "$PHOTO" ]; then
  echo "render_cv_photo: --photo <path> is required (no render.default_photo set in" >&2
  echo "  config.json either). Point it at any image, e.g. images/me.png." >&2
  exit 1
fi

if [ ! -f "$PHOTO" ]; then
  echo "render_cv_photo: photo not found: $PHOTO" >&2
  exit 1
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "Usage: render_cv_photo.sh [--photo <image>] [--root <dir>] file1.md [file2.md ...]" >&2
  exit 1
fi

BROWSER="$(find_browser)" || { no_browser_error "render_cv_photo"; exit 1; }

ensure_marked_installed "$SUPPORT_DIR"

PHOTO_ABS="$(native_path "$PHOTO")"

for src in "${FILES[@]}"; do
  if [ ! -f "$src" ]; then
    echo "render_cv_photo: skipping, not found: $src" >&2
    continue
  fi

  src_dir="$(cd "$(dirname "$src")" && pwd)"
  out_dir="$src_dir/generate-pdfs"
  mkdir -p "$out_dir"

  html_path="$out_dir/cv-photo.html"
  pdf_path="$out_dir/cv-photo.pdf"

  node "$SUPPORT_DIR/cv2html-photo.js" "$src" "$html_path" "$PHOTO_ABS" "cv-photo"

  # mtime before, so a silent write failure (e.g. the PDF is locked open in a viewer) can be
  # detected below instead of always printing "wrote" regardless of whether it actually did.
  mtime_before="$(file_mtime "$pdf_path")"

  "$BROWSER" $(browser_flags) \
    --print-to-pdf="$(native_path "$pdf_path")" \
    "$(file_url "$html_path")" >/dev/null 2>&1

  mtime_after="$(file_mtime "$pdf_path")"

  if [ -z "$mtime_after" ] || [ "$mtime_before" = "$mtime_after" ]; then
    echo "render_cv_photo: WARNING — $pdf_path was NOT updated (still has old content)." >&2
    echo "  Likely cause: the file is open in a PDF viewer/browser tab and the browser" >&2
    echo "  couldn't overwrite it. Close it and re-run." >&2
  else
    echo "render_cv_photo: wrote $pdf_path"
  fi
done
