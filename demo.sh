#!/usr/bin/env bash
# demo.sh — the 60-second demo. Builds and renders the fictional "Robin Vale" persona in
# examples/demo/, using the exact same scripts a real user would run on their own data (just
# pointed at a different --root). Requires only python3, node, and a Chromium-family browser.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROOT="$SCRIPT_DIR/examples/demo"

echo "== JobHuntKit demo — building Robin Vale's CV for Orbital Dynamics =="
echo

echo "[1/10] Assembling cv-minimal.md AND cv.md (application.md opts into both pipelines)..."
python3 "$SCRIPT_DIR/engine/build_cv.py" --root "$DEMO_ROOT" --all

echo
echo "[2/10] Checking the locked spine landed correctly (minimal pipeline)..."
python3 "$SCRIPT_DIR/engine/check_cv.py" --root "$DEMO_ROOT"

echo
echo "[3/10] Rendering the tailored CV to PDF..."
bash "$SCRIPT_DIR/engine/render_cv_minimal.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/cv-minimal.md"

echo
echo "[4/10] Verifying the render is exactly one page..."
python3 "$SCRIPT_DIR/engine/verify_cvs.py" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv-minimal.pdf"

echo
echo "[5/10] Rendering the cover letter to PDF..."
bash "$SCRIPT_DIR/engine/render_letter.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/cover_letter.md"

echo
echo "[6/10] Checking the locked spine landed correctly (full pipeline)..."
python3 "$SCRIPT_DIR/engine/check_cv.py" --root "$DEMO_ROOT" --pipeline full

echo
echo "[7/10] Rendering the built full CV (same per-company selections as cv-minimal.md)..."
bash "$SCRIPT_DIR/engine/render_cv.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/cv.md"

echo
echo "[8/10] Reporting its page count (no gate — the full CV has no page budget)..."
python3 "$SCRIPT_DIR/engine/verify_cvs.py" --root "$DEMO_ROOT" --max-pages 0 \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv.pdf"

echo
echo "[9/10] Rendering the primary master directly (no build step — id-agnostic)..."
bash "$SCRIPT_DIR/engine/render_cv.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/master/master_cv.md"

echo
echo "[10/10] Rendering the primary master with a photo, two-column..."
bash "$SCRIPT_DIR/engine/render_cv_photo.sh" --root "$DEMO_ROOT" \
  --photo "$DEMO_ROOT/images/avatar.png" \
  "$DEMO_ROOT/master/master_cv.md"

echo
echo "Done. Open the results:"
echo "  $DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv-minimal.pdf"
echo "  $DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cover_letter.pdf"
echo "  $DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv.pdf"
echo "  $DEMO_ROOT/master/generate-pdfs/cv.pdf"
echo "  $DEMO_ROOT/master/generate-pdfs/cv-photo.pdf"
