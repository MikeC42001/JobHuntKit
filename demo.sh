#!/usr/bin/env bash
# demo.sh — the 60-second demo. Builds and renders the fictional "Robin Vale" persona in
# examples/demo/, using the exact same scripts a real user would run on their own data (just
# pointed at a different --root). Requires only python3, node, and a Chromium-family browser.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROOT="$SCRIPT_DIR/examples/demo"

echo "== JobHuntKit demo — building Robin Vale's CV for Orbital Dynamics =="
echo

echo "[1/3] Assembling cv-minimal.md from master + template + application.md..."
python3 "$SCRIPT_DIR/engine/build_cv.py" --root "$DEMO_ROOT" --all

echo
echo "[2/3] Rendering to PDF..."
bash "$SCRIPT_DIR/engine/render_cv_minimal.sh" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/cv-minimal.md"

echo
echo "[3/3] Verifying the render is exactly one page..."
python3 "$SCRIPT_DIR/engine/verify_cvs.py" --root "$DEMO_ROOT" \
  "$DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv-minimal.pdf"

echo
echo "Done. Open the result:"
echo "  $DEMO_ROOT/applications/offer-pages/Orbital Dynamics/generate-pdfs/cv-minimal.pdf"
