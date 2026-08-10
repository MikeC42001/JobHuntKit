# Open questions

The queue described in `community/README.md`. Each entry is a genuine open question, not decided
work — see that file for what does and doesn't belong here, and for the approval steps that move
an entry down this list.

Think of this file as a **staging area before an idea becomes a public GitHub issue**, not a
discussion venue itself. The actual back-and-forth — comments, 👍 reactions, "I'd want this
too" — happens on GitHub once an entry is posted; this file just tracks what's worth asking and
why, so posting is a deliberate step rather than every stray idea becoming a notification.

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

### Q-004 — Is a ChatGPT-paste variant of the agent instructions worth generating?

**Status:** open

`agents/cv-setup.md`, `agents/cv-tailor.md`, and `agents/interview-prep.md` are written for an
agentic coding tool (Claude Code, Cursor) that can read files and run shell commands on its own.
A "paste this into ChatGPT" variant was sketched as an M3 item and never built — picking it back
up unexamined would carry the same problem the extractor issues did: assuming the answer before
asking. The hard part is real, not cosmetic: `agents/CONTEXT.md`'s Step 0 is a filesystem
root-probe (find `config.json`, walk up from cwd), and every task file's commands are written as
Claude Code's `! command` syntax — neither means anything in a chat window with no filesystem
and no shell. A generator would have to either rewrite Step 0 into "tell me what's in these
folders" prompts, or accept that the paste variant only works for drafting prose (tailoring
decisions, wording) and hands file operations back to the person by hand.

What would settle it: whether anyone actually wants to run this outside an agentic editor at
all — worth asking before designing around a filesystem-free rewrite of Step 0.

### Q-005 — Does a spine-only `minimal-lean.md` template earn its place?

**Status:** open

`templates/` already has two full-inventory shapes: `minimal-full.md` (gated optional slots,
one-page discipline) and `full.md` (same ids, mostly unconditional, no page budget). A third,
`minimal-lean.md`, was sketched as "the locked spine only, no optional slots, no `{{PROJECTS}}`"
— for someone who wants the one-page pipeline's validation but with even less content than
`minimal-full.md` allows. It needs **no config or code change** to add: the minimal pipeline
reads `template:` from each `application.md`'s own front matter
(`docs/CONFIG.md`'s `minimal.template` is only the fallback), so a user opts in per-application
the same way they'd pick any other template — see `docs/CUSTOMIZING.md` for exactly which files
a new template touches.

What would settle it: whether the one-page budget actually feels tight enough in practice
(too many optional slots to choose from, not too little room) that a leaner starting point would
help — or whether `minimal-full.md`'s own `## Include` mechanism already covers "say less" by
just including fewer optional ids.
