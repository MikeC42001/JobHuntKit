#!/usr/bin/env bash
# community/community.sh — read-only reader for the lifecycle in community/README.md.
#
# Usage: bash community/community.sh <questions|open|resolved|status> [--repo OWNER/REPO]
#
# Read-only by construction: this file contains no `gh issue create`, `gh issue edit`,
# `gh issue close`, or `gh issue comment` call anywhere. It never writes to GitHub — that's what
# makes the two-approval-gate rule in community/README.md structurally safe rather than just a
# promise. --repo defaults to whatever `gh` infers from the current directory's git remote.

set -euo pipefail

REPO_OPT=""
CMD=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)
      REPO_OPT="--repo $2"
      shift 2
      ;;
    questions|open|resolved|status)
      CMD="$1"
      shift
      ;;
    *)
      echo "community.sh: unknown argument '$1'" >&2
      exit 1
      ;;
  esac
done

if [ -z "$CMD" ]; then
  echo "Usage: bash community/community.sh <questions|open|resolved|status> [--repo OWNER/REPO]" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "community.sh: the GitHub CLI ('gh') is required — https://cli.github.com" >&2
  exit 1
fi

print_questions() {
  echo "== Open questions (question-labelled issues, ranked by reactions) =="
  local rows
  # shellcheck disable=SC2086 # REPO_OPT is intentionally unquoted: empty means "pass nothing",
  # non-empty ("--repo owner/repo") is meant to word-split into two argv entries for gh.
  rows="$(gh issue list $REPO_OPT --label question --state open \
    --search "sort:reactions-+1-desc" \
    --json number,title,reactionGroups,comments,url \
    --jq '.[] | "#\(.number)  \(.title)\n    +1 \([.reactionGroups[] | select(.content=="THUMBS_UP") | .users.totalCount] | add // 0)   comments \(.comments | length)   \(.url)"')"
  if [ -z "$rows" ]; then
    echo "  (none open)"
  else
    printf '%s\n' "$rows"
  fi
}

print_open() {
  echo "== Open, approved work (open issues without the 'question' label) =="
  local rows
  # shellcheck disable=SC2086 # see the same note above print_questions().
  rows="$(gh issue list $REPO_OPT --state open \
    --json number,title,labels,url \
    --jq '[.[] | select([.labels[].name] | index("question") | not)] | .[] | "#\(.number)  \(.title)  [\([.labels[].name] | join(", "))]\n    \(.url)"')"
  if [ -z "$rows" ]; then
    echo "  (none open)"
  else
    printf '%s\n' "$rows"
  fi
}

# For each closed issue: find the PR that closed it, that PR's merge commit + base branch, then
# which tag (if any) contains that commit. Three separate lookups because GitHub only records the
# first two directly — the tag is derived locally from git, never hand-maintained.
print_resolved() {
  echo "== Resolved (closed issues -> which release shipped them) =="
  local closed
  # shellcheck disable=SC2086 # see the same note above print_questions().
  closed="$(gh issue list $REPO_OPT --state closed \
    --json number,title,closedByPullRequestsReferences \
    --jq '.[] | "\(.number)\t\(.title)\t\(.closedByPullRequestsReferences[0].number // "")"')"

  if [ -z "$closed" ]; then
    echo "  (none closed)"
    return 0
  fi

  while IFS=$'\t' read -r num title pr; do
    [ -z "$num" ] && continue

    if [ -z "$pr" ]; then
      echo "#$num  $title"
      echo "    closed manually — no linked PR"
      continue
    fi

    local pr_out base merge_sha
    # shellcheck disable=SC2086 # see the same note above print_questions().
    pr_out="$(gh pr view "$pr" $REPO_OPT --json baseRefName,mergeCommit \
      --jq '"\(.baseRefName)\t\(.mergeCommit.oid // "")"' 2>/dev/null || true)"

    if [ -z "$pr_out" ]; then
      echo "#$num  $title"
      echo "    closed by PR #$pr — could not read it (deleted, or a fork PR you can't see)"
      continue
    fi

    IFS=$'\t' read -r base merge_sha <<<"$pr_out"

    if [ -z "$merge_sha" ]; then
      echo "#$num  $title"
      echo "    closed by PR #$pr — not merged (closed without merging)"
      continue
    fi

    if ! git rev-parse --quiet --verify "${merge_sha}^{commit}" >/dev/null 2>&1; then
      echo "#$num  $title"
      echo "    closed by PR #$pr, merge ${merge_sha:0:9} -> $base — commit not found locally, run 'git fetch --tags'"
      continue
    fi

    local tag
    tag="$(git tag --contains "$merge_sha" --sort=v:refname 2>/dev/null | head -1 || true)"
    echo "#$num  $title"
    if [ -n "$tag" ]; then
      echo "    closed by PR #$pr, merge ${merge_sha:0:9} -> $base — shipped in $tag"
    else
      echo "    closed by PR #$pr, merge ${merge_sha:0:9} -> $base — unreleased (no tag contains it yet)"
    fi
  done <<<"$closed"
}

case "$CMD" in
  questions) print_questions ;;
  open) print_open ;;
  resolved) print_resolved ;;
  status)
    print_questions
    echo
    print_open
    echo
    print_resolved
    ;;
esac
