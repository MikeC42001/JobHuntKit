# AGENTS.md

Entry point for any AI coding agent (Cursor, Codex, Copilot, or anything else that reads this
filename convention) working in this repo.

Start at [`agents/CONTEXT.md`](agents/CONTEXT.md) — root-finding, file ownership, and the
never-auto-commit rule shared by every task-specific instruction file. Then:

- [`agents/cv-setup.md`](agents/cv-setup.md) — set up or evolve your CV content layer
  (`profile/background.md`, `master/master_cv_minimal.md`). Start here on a fresh root.
- [`agents/cv-tailor.md`](agents/cv-tailor.md) — scan for new/stale applications, draft
  `application.md`, build, validate, render, and stage a tailored CV (and optionally a cover
  letter) for one posting.

Claude Code users: the same instructions are also available as the `cv-setup`/`cv-tailor`
skills/commands — see `.claude/skills/cv-setup/SKILL.md` and `.claude/skills/cv-tailor/SKILL.md`.
All of these are thin pointers to the `agents/` files above, not separate copies.

For the format contract (not agent-specific — anyone can read this), see
[`docs/SPEC.md`](docs/SPEC.md); for `config.json`, see [`docs/CONFIG.md`](docs/CONFIG.md).
