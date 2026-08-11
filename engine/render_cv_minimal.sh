#!/usr/bin/env bash
# render_cv_minimal.sh — convert a cv-minimal.md file into a one-column, minimalist PDF with a
# circular photo in the header and right-aligned dates/durations per entry. Reads a cv-minimal.md
# written against the pipe-delimited entry convention documented in docs/SPEC.md.
#
# Usage:
#   engine/render_cv_minimal.sh applications/offer-pages/<Company>/cv-minimal.md
#   engine/render_cv_minimal.sh --photo images/me.png --style a applications/<company>/cv-minimal.md
#   engine/render_cv_minimal.sh --root path/to/data applications/<company>/cv-minimal.md
#
# --photo <path> — optional. Falls back to config.json's render.default_photo if set; otherwise
#   required. Casual vs. formal photo is a per-application call some people like to make — no
#   forced single default.
# --style a|b|c|z — optional, falls back to config.json's render.default_style, then "a" (the
#   default "graph spine" style). z is a plain baseline kept as a permanent fallback; b/c are
#   alternate directions. See render-support/cv2html-minimal.js's header comment for what each
#   looks like.
#
# Output: <dir of source>/generate-pdfs/cv-minimal.pdf (+ intermediate .html) when --style is
# "a" — the default style gets the plain filename. With any other --style, output is
# cv-minimal-<style>.pdf instead, so comparison renders never clobber the default file.
# Strips any lines starting with "> " (internal tailoring notes) before rendering.
#
# Requires: Node.js 22+ (20.19+ works) and npm on PATH, and a Chromium-family browser (Chrome, Edge, Chromium,
# or Brave — see lib.sh's find_browser for the search order, or set BROWSER_BIN to override).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPPORT_DIR="$SCRIPT_DIR/render-support"

ROOT=""
PHOTO=""
STYLE=""
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
    --style)
      STYLE="$2"
      shift 2
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

# Root resolution mirrors config.py: --root, else $JOBHUNTKIT_ROOT, else the repo checkout
# (this script's grandparent directory).
if [ -z "$ROOT" ]; then
  ROOT="${JOBHUNTKIT_ROOT:-$(dirname "$SCRIPT_DIR")}"
fi
ROOT="$(cd "$ROOT" && pwd)"

# shellcheck source=engine/lib.sh
source "$SCRIPT_DIR/lib.sh"

if [ -z "$STYLE" ]; then
  STYLE="$(config_get render.default_style)"
  STYLE="${STYLE:-a}"
fi

case "$STYLE" in
  a|b|c|z) ;;
  *)
    echo "render_cv_minimal: --style must be a, b, c, or z (got: $STYLE)" >&2
    exit 1
    ;;
esac

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
  echo "render_cv_minimal: --photo <path> is required (no render.default_photo set in" >&2
  echo "  config.json either). Point it at any image, e.g. images/me.png." >&2
  exit 1
fi

if [ ! -f "$PHOTO" ]; then
  echo "render_cv_minimal: photo not found: $PHOTO" >&2
  exit 1
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "Usage: render_cv_minimal.sh [--photo <image>] [--style a|b|c|z] [--root <dir>] file1.md [file2.md ...]" >&2
  exit 1
fi

BROWSER="$(find_browser)" || { no_browser_error "render_cv_minimal"; exit 1; }

ensure_marked_installed "$SUPPORT_DIR"

PHOTO_ABS="$(native_path "$PHOTO")"

for src in "${FILES[@]}"; do
  if [ ! -f "$src" ]; then
    echo "render_cv_minimal: skipping, not found: $src" >&2
    continue
  fi

  src_dir="$(cd "$(dirname "$src")" && pwd)"
  out_dir="$src_dir/generate-pdfs"
  mkdir -p "$out_dir"

  if [ "$STYLE" = "a" ]; then
    out_name="cv-minimal"
  else
    out_name="cv-minimal-$STYLE"
  fi
  html_path="$out_dir/$out_name.html"
  pdf_path="$out_dir/$out_name.pdf"

  node "$SUPPORT_DIR/cv2html-minimal.js" "$src" "$html_path" "$PHOTO_ABS" "$STYLE"

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
    echo "render_cv_minimal: WARNING — $pdf_path was NOT updated (still has old content)." >&2
    echo "  Likely cause: the file is open in a PDF viewer/browser tab and the browser" >&2
    echo "  couldn't overwrite it. Close it and re-run." >&2
  else
    echo "render_cv_minimal: wrote $pdf_path"
  fi
done
