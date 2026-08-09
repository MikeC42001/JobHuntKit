# AGENTS.md

Entry point for any AI coding agent (Cursor, Codex, Copilot, or anything else that reads this
filename convention) working in this repo.

Start at [`agents/CONTEXT.md`](agents/CONTEXT.md) — root-finding, file ownership, and the
never-auto-commit rule shared by every task-specific instruction file. Then:

- [`agents/cv-setup.md`](agents/cv-setup.md) — set up or evolve your CV content layer
  (`profile/background.md`, and two masters: `master/master_cv.md` the primary/complete
  inventory, `master/master_cv_minimal.md` its condensation). Start here on a fresh root.
- [`agents/cv-tailor.md`](agents/cv-tailor.md) — scan for new/stale applications, draft
  `application.md`, build, validate, render, and stage a tailored CV (and optionally a cover
  letter) for one posting.
- [`agents/interview-prep.md`](agents/interview-prep.md) — a live mock-Q&A pass against a
  company's `application.md`, checking for contradictions, factual drift, and vague self-praise.
  Doesn't touch `engine/` at all.

Claude Code users: the same instructions are also available as the `cv-setup`/`cv-tailor`/
`interview-prep` skills/commands — see `.claude/skills/cv-setup/SKILL.md`,
`.claude/skills/cv-tailor/SKILL.md`, and `.claude/skills/interview-prep/SKILL.md`. All of these
are thin pointers to the `agents/` files above, not separate copies.

For the format contract (not agent-specific — anyone can read this), see
[`docs/SPEC.md`](docs/SPEC.md); for `config.json`, see [`docs/CONFIG.md`](docs/CONFIG.md); for
which file to edit — content, structure, or the PDF's visual look — see
[`docs/CUSTOMIZING.md`](docs/CUSTOMIZING.md).

**Working on this repo itself, not a user's CV content?** See
[`community/README.md`](community/README.md) — in particular, never open, label, or close a
GitHub issue without the maintainer's explicit approval first.
