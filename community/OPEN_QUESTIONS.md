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

### Q-003 — Do the extractor `good first issue`s stay open indefinitely, or get built in-house?

**Status:** open

Greenhouse, Lever, Workday, and Indeed (#3–#6) are filed as `good first issue`s and explicitly
parked until after M4. If nobody claims them once the repo goes public, is that fine indefinitely
(the point of a `good first issue` is that it's fine to wait), or is there a point past which the
maintainer should just build them?

What would settle it: revisit after the public flip and see if there's any outside interest at
all before deciding either way.
