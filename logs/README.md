# logs/

Development logs, one file per month: `YYYY_MM_log.md`. Oldest entry first, newest appended at
the bottom.

## What goes here vs. in the changelog

| | [`CHANGELOG.md`](../CHANGELOG.md) | `logs/YYYY_MM_log.md` |
|---|---|---|
| Written for | people **using** the toolkit | whoever **picks the work back up** |
| Unit | one entry per released tag | one entry per working session |
| Contains | what changed, grouped by capability | what was built, what broke, what was tried and rejected, and why |
| Length | short by design | as long as the reasoning needs |

The changelog answers "what's in `v0.1.0`?". These files answer "why is it built like that, and
what already didn't work?" — the part that's expensive to reconstruct and cheap to write down at
the time.

## Why it isn't in `CLAUDE.md`

It used to be. By 2026-08-10 that file was 468 lines, 341 of them a dated history sitting under a
heading called "Current state" — which is precisely what a history is not. It loaded into context
every session, went stale the moment anything shipped, and buried the ~100 lines of actual
orientation that a reader (human or agent) needs first.

So `CLAUDE.md` keeps the standing facts: architecture, conventions, what exists right now, open
follow-ups. The narrative lives here, and both are linked from there.

## Conventions

- **Append, don't rewrite.** A log entry describes what was true that day. Later corrections go in
  a later entry rather than being edited into an earlier one, so the record stays honest about
  what was believed when.
- **New month, new file.** No index to maintain — the filenames sort themselves.
- **Keep the dead ends.** An approach that was tried and abandoned is often more useful than the
  one that worked, and it's the first thing lost if only the outcome is recorded.
- **Same leak rules as every tracked file.** These are scanned by `scripts/audit_public.py` like
  anything else: no real names, no personal data, no absolute paths.
