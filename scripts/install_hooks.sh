#!/usr/bin/env bash
# install_hooks.sh — installs the pre-commit leak-gate hook. One-time, per-clone (git doesn't
# track .git/hooks/, so this has to be run manually after cloning — not automatic).
#
# Usage: bash scripts/install_hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$REPO_ROOT/.git" ]; then
  echo "install_hooks: $REPO_ROOT is not a git repo — nothing to install into." >&2
  exit 1
fi

mkdir -p "$HOOKS_DIR"
cp "$SCRIPT_DIR/hooks/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "install_hooks: pre-commit hook installed — every commit now runs scripts/audit_public.py"
echo "  against staged files first. Copy .private-terms.example to .private-terms and fill in"
echo "  your own wordlist (name, employer, unreleased product names) for it to catch those too."
