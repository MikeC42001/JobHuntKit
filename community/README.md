# community/ — how an idea becomes shipped work

This folder is the queue between "someone wondered aloud" and "this is approved work". It exists
because those are genuinely different states, and collapsing them — filing a GitHub issue for
every idea the moment it's typed — makes the issue tracker noisy and implies a commitment nobody
actually made yet.

## The lifecycle

```
community/OPEN_QUESTIONS.md          hand-written. The only file in this folder that's a source
        │                            of truth rather than a read-back of GitHub.
        │
        │   ── maintainer approves ──▶   gh issue create --label question
        ▼
GitHub issue, `question` label       public. gathers 👍 reactions and comments.
        │                            demand is a number — GitHub sorts by it server-side.
        │
        │   ── maintainer approves ──▶   gh issue edit --add-label enhancement \
        │                                              --remove-label question
        ▼
GitHub issue, scoped work            approved. gets built on a branch, closed by a PR.
        │
        ▼
closing PR → merge commit → `git tag --contains` → "shipped in v0.2.0" (or "unreleased" if no
                                                      tag contains it yet)
```

**GitHub is the source of truth for issue state.** Nothing in this folder duplicates it —
`community.sh` (below) only ever *reads* GitHub back into a terminal, never writes a report file
that could drift out of sync with reality. The one exception is `OPEN_QUESTIONS.md`, because a
pre-issue idea exists nowhere else yet.

## Two approval gates — both explicit, both the maintainer's

1. **Opening the question as an issue.** An open question in `OPEN_QUESTIONS.md` is not itself
   public and commits nobody. It only becomes a GitHub issue — public, permanent, and something
   that notifies watchers — once the maintainer explicitly says so.
2. **Promoting a question into scoped work.** A `question`-labelled issue gathering reactions is
   still just a question. Relabelling it `enhancement` (or closing it, or turning it into a real
   task) is a second, separate approval — high demand on a question is a signal, not a decision.

Nothing in this repo's tooling opens, edits, or closes a GitHub issue on its own. If you're an
agent working in this repo: draft the issue body, show it, and wait for a yes before running
`gh issue create` (or `--add-label` / `close`). Reading issues (`gh issue list`, `gh issue view`)
is unrestricted — the rule is about writes that reach GitHub, not about looking.

## What belongs in `OPEN_QUESTIONS.md`

A genuine open question — something the maintainer hasn't decided and where community input would
actually change the answer. "Should extractors be plugins?" "Is this the right default template?"

## What does **not** belong here

The project's own roadmap. Milestone items in `CLAUDE.md` (M4's `CHANGELOG.md`, the `v0.1.0` tag,
`build_paste_prompts.py`, and so on) are decided work, not things the community is being asked
about — they stay in `CLAUDE.md`, not here. If everything lands in this folder it turns into a
second backlog competing with the real one.

## `community.sh` — reading GitHub back

Read-only. Never creates, edits, or closes anything — it can't, structurally, which is what makes
the approval rule above safe rather than just a promise.

```bash
bash community/community.sh questions   # open `question`-labelled issues, ranked by reactions
bash community/community.sh open        # approved work: open issues without the `question` label
bash community/community.sh resolved    # closed issues -> which release actually shipped them
bash community/community.sh status      # all three
```

## The raw `gh`/`git` commands, if you'd rather not go through the script

```bash
# Open questions, most-wanted first (GitHub sorts by reaction count server-side):
gh issue list --label question --state open --search "sort:reactions-+1-desc" \
  --json number,title,reactionGroups,comments,url

# Approved work — everything open that isn't a bare question:
gh issue list --state open --json number,title,labels,url \
  --jq '[.[] | select([.labels[].name] | index("question") | not)]'

# Post an approved question as an issue (only after the maintainer says yes):
gh issue create --title "..." --body "..." --label question

# Promote a question into scoped work (only after the maintainer says yes):
gh issue edit <N> --add-label enhancement --remove-label question

# Which release closed issue #N — three steps, since GitHub only tells you the closing PR:
gh issue view <N> --json closedByPullRequestsReferences   # -> the PR number
gh pr view <PR>    --json mergeCommit,baseRefName          # -> the merge commit + branch
git tag --contains <merge-commit-sha> --sort=v:refname     # -> earliest release, or nothing yet
```

## Why not GitHub Discussions?

Considered and rejected for now. Reactions — the actual demand signal — are native to ordinary
issues; a normal issue can carry 👍/👎/🎉/❤️/🚀/👀 same as any other. Discussions would add
threading and a separate upvote counter, but `gh` (as of 2.78.0) has no `discussion` subcommand at
all — every read would be a hand-written GraphQL query instead of the one-liners above — and
Discussions isn't enabled on this repo. If a real community outgrows plain issues, Discussions is
still there to turn on later.

## Why not GitHub Milestones?

Also considered and rejected for now. `git tag --contains` already answers "which release shipped this"
as a fact derived from git, with no upkeep. A milestone records *intent* ahead of time and then
needs someone to keep it current — one more thing to go stale. `README.md`'s roadmap paragraph
points here instead.
