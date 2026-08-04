#!/usr/bin/env bash
# sync.sh — copy exactly the paths listed in engine.manifest between a canonical JobHuntKit
# checkout and your own root, in either direction. This is the mechanism that lets you improve
# the engine from wherever's convenient (your own private data root, a fork, a scratch clone)
# and get those changes into a canonical repo — or the reverse — without ever risking your
# personal content crossing the boundary, because content paths simply aren't on the list.
#
# Usage:
#   sync.sh pull [--from <repo>] [--root <dir>] [--dry-run]
#     Copies manifest paths FROM <repo> (default: this script's own repo) INTO <root> (default:
#     cwd). Use this to refresh your own root's copy of the engine with upstream changes.
#
#   sync.sh push [--to <repo>] [--root <dir>] [--dry-run]
#     Copies manifest paths FROM <root> (default: cwd) INTO <repo> (default: this script's own
#     repo). Runs scripts/audit_public.py against exactly the files about to be copied FIRST —
#     on any finding, aborts with nothing written. Use this to contribute engine improvements
#     made while working inside your own root back to the canonical repo.
#
# Neither direction ever touches a path outside engine.manifest, and push refuses to write
# anything at all if the audit fails — there is no partial-write failure mode to worry about.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DEFAULT="$(dirname "$SCRIPT_DIR")"
MANIFEST="$REPO_DEFAULT/engine.manifest"

usage() {
  echo "Usage:" >&2
  echo "  sync.sh pull [--from <repo>] [--root <dir>] [--dry-run]" >&2
  echo "  sync.sh push [--to <repo>]   [--root <dir>] [--dry-run]" >&2
}

MODE="${1:-}"
if [ "$MODE" != "pull" ] && [ "$MODE" != "push" ]; then
  usage
  exit 1
fi
shift

FROM=""
TO=""
ROOT=""
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --from) FROM="$2"; shift 2 ;;
    --to) TO="$2"; shift 2 ;;
    --root) ROOT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "sync.sh: unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [ ! -f "$MANIFEST" ]; then
  echo "sync.sh: no engine.manifest found at $MANIFEST" >&2
  exit 1
fi

if [ "$MODE" = "pull" ]; then
  SRC="${FROM:-$REPO_DEFAULT}"
  DST="${ROOT:-$(pwd)}"
else
  SRC="${ROOT:-$(pwd)}"
  DST="${TO:-$REPO_DEFAULT}"
fi

SRC="$(cd "$SRC" && pwd)"
mkdir -p "$DST"
DST="$(cd "$DST" && pwd)"

if [ "$SRC" = "$DST" ]; then
  echo "sync.sh: source and destination are the same directory ($SRC) — nothing to do." >&2
  exit 1
fi

# Expand engine.manifest into an actual file list under SRC — used both to audit (push only)
# and to drive the copy loop below, so the two never see a different file set.
manifest_files_under() {
  local base="$1"
  while IFS= read -r rel || [ -n "$rel" ]; do
    rel="$(printf '%s' "$rel" | sed 's/\r$//')"
    [ -z "$rel" ] && continue
    case "$rel" in \#*) continue ;; esac
    local p="$base/$rel"
    if [ -d "$p" ]; then
      find "$p" -type f
    elif [ -f "$p" ]; then
      printf '%s\n' "$p"
    fi
    # Missing path: not an error — it's a future-milestone path not built yet, skip quietly.
  done < "$MANIFEST"
}

if [ "$MODE" = "push" ]; then
  echo "sync.sh: auditing $SRC before push..."
  mapfile -t AUDIT_FILES < <(manifest_files_under "$SRC")
  if [ "${#AUDIT_FILES[@]}" -eq 0 ]; then
    echo "sync.sh: no manifest paths found under $SRC — nothing to push." >&2
    exit 1
  fi
  if ! python3 "$REPO_DEFAULT/scripts/audit_public.py" --root "$SRC" "${AUDIT_FILES[@]}"; then
    echo "" >&2
    echo "sync.sh: audit FAILED — push aborted, nothing written to $DST." >&2
    exit 1
  fi
  echo ""
fi

echo "sync.sh: $MODE  $SRC  ->  $DST"
COUNT=0
while IFS= read -r rel || [ -n "$rel" ]; do
  rel="$(printf '%s' "$rel" | sed 's/\r$//')"
  [ -z "$rel" ] && continue
  case "$rel" in \#*) continue ;; esac

  src_path="$SRC/$rel"
  dst_path="$DST/$rel"
  [ -e "$src_path" ] || continue

  if [ "$DRY_RUN" = "1" ]; then
    echo "  would copy: $rel"
    COUNT=$((COUNT + 1))
    continue
  fi

  if [ -d "$src_path" ]; then
    mkdir -p "$dst_path"
    cp -r "$src_path/." "$dst_path/"
  else
    mkdir -p "$(dirname "$dst_path")"
    cp "$src_path" "$dst_path"
  fi
  COUNT=$((COUNT + 1))
done < "$MANIFEST"

if [ "$DRY_RUN" = "1" ]; then
  echo "sync.sh: dry run — $COUNT manifest path(s) would be synced."
else
  echo "sync.sh: $COUNT manifest path(s) synced."
fi
