# Open questions

The queue described in `community/README.md`. Each entry is a genuine open question, not decided
work — see that file for what does and doesn't belong here, and for the approval steps that move
an entry down this list.

**Status values:** `open` (not yet posted anywhere) · `posted (#N)` (a `question`-labelled issue
exists, gathering reactions) · `promoted (#N)` (relabelled `enhancement`, now scoped work) ·
`dropped (reason)`.

---

### Q-001 — Does `interview-prep` need test coverage?

**Status:** open

Every other agent-driven flow (`cv-setup`, `cv-tailor`) has a pytest suite behind it, because each
has an `engine/` script doing real work that can regress. `interview-prep` is pure conversational
guidance — no `engine/` backing, nothing to golden-file. Open since 2026-08-07, never revisited.

What would settle it: whether `interview-prep`'s prompt/instructions are stable enough that a
regression would be visible without a test, or whether it's grown enough branching logic that a
prompt change could silently break a case nobody's eyeballing anymore.

### Q-002 — Should saved postings support change detection?

**Status:** open

A saved `posting.md` is a point-in-time snapshot. If the live posting changes after you've already
tailored a CV against it (role requirements edited, deadline moved), nothing today re-fetches or
diffs it — you'd only notice by chance. Scoped to no milestone yet.

What would settle it: whether this folds into M4 as-is, waits for a later milestone, or turns out
to be low-value because postings rarely change after being saved in practice.

### Q-003 — Which posting-board extractors are actually worth building?

**Status:** open

Greenhouse, Lever, Workday, and Indeed were briefly filed as `good first issue`s (#3–#6, then
deleted 2026-08-08) — filing them assumed the answer (all four, in that order) before actually
asking anyone. The real open question: which of these, if any, are worth building at all, and is
there real demand from someone who'd use them, versus guessing based on which boards seemed
popular.

What would settle it: post this as a `question`-labelled issue after the public flip, see which
boards people actually ask for (or none), and only scope approved extractor work off real
reactions/comments — not before.
