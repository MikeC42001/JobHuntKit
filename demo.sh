#!/usr/bin/env bash
# demo.sh — the 60-second demo. Builds and renders the fictional "Robin Vale" persona in
# examples/demo/, using the exact same scripts a real user would run on their own data (just
# pointed at a different --root). Requires only python3, node, and a Chromium-family browser.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROOT="$SCRIPT_DIR/examples/demo"

echo "== JobHuntKit demo — building Robin Vale's CV for Orbital Dynamics =="
echo

echo "[1/5] Assembling cv-minimal.md from master + template + application.md..."
python3 "$SCRIPT_DIR/engine/build_cv.py" --root "$DEMO_ROOT" --all

echo
echo "[2/5] Checking the locked spine landed correctly..."
python3 "$SCRIPT_DIR/engine/check_cv.py" --root "$DEMO_ROOT"

echo
echo "[3/5] Rendering the CV to PDF..."
bash "$SCRIPT_DIR/engine/render_cv_minimal.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/cv-minimal.md"

echo
echo "[4/5] Verifying the render is exactly one page..."
python3 "$SCRIPT_DIR/engine/verify_cvs.py" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv-minimal.pdf"

echo
echo "[5/5] Rendering the cover letter to PDF..."
bash "$SCRIPT_DIR/engine/render_letter.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/cover_letter.md"

echo
echo "Done. Open the results:"
echo "  $DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv-minimal.pdf"
echo "  $DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cover_letter.pdf"
