# Contributing

Thanks for considering it. JobHuntKit is a small, opinionated toolkit — most contributions worth
making are either extending the engine (a new posting extractor, a renderer fix) or improving
the docs a stranger's first run depends on.

## The one rule that matters: never commit real CV data

`engine/` is upstream-owned tooling and should never contain a real name, email, phone number,
employer, or any other personal content — that's not a style preference, it's what
`scripts/audit_public.py` (the leak gate) actively enforces in CI and in a pre-commit hook. If
you're testing a change against your own CV data, keep that data at a `--root` outside your
clone, or in the gitignored default-root paths (`config.json`, `master/`, `profile/`,
`applications/`, `produced/`, `images/` — see `.gitignore`), never staged into a commit.

Install the pre-commit hook once per clone (git doesn't track `.git/hooks/`, so this is a manual
step):

```bash
bash scripts/install_hooks.sh
```

It runs `audit_public.py` against your staged files before every commit and refuses to let one
through on any finding — an unexpected binary, an email/phone outside the small allowlist, an
absolute path, or a term from your own gitignored `.private-terms` wordlist (copy
`.private-terms.example` and fill in anything specific to you: your name, employer, an
unreleased product name).

## Before you open a PR

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v          # full suite
ruff check engine scripts tests     # lint — same command CI runs
bash demo.sh                        # the actual end-to-end smoke test
python scripts/audit_public.py      # leak gate, same check the pre-commit hook runs
```

CI (`.github/workflows/ci.yml`) runs lint, the pytest suite on ubuntu/macos/windows, and a
render-matrix job that runs `demo.sh` for real on ubuntu and macOS — all of it needs to be
green before a PR merges.

## The engine/content seam

If you're not familiar with the split yet: `engine/` (this toolkit's code) never contains
personal data; everyone's own CV content lives at a "root" resolved at runtime
(`--root`/`$JOBHUNTKIT_ROOT`/the checkout itself by default — see `engine/config.py`). Keep that
boundary in mind for any change — a new script should take `--root` via
`config.root_parent_parser()` like every existing one does, not hardcode a path.

## What's a good first contribution

- A posting extractor for a job board not yet supported (once `engine/extractors/` lands —
  see the roadmap in `README.md`'s Status section). Small, self-contained, ships with its own
  synthetic fixture.
- A renderer or cross-platform fix — `engine/lib.sh` is the shared cross-platform layer; a bug
  report with the exact OS/browser combination is just as valuable as a fix.
- A docs fix. `docs/GETTING-STARTED.md` is meant to work for a stranger with zero context; if a
  step assumed something the docs didn't explain, that's a real bug.

## License

MIT (`LICENSE`). By contributing, you agree your contribution is licensed under the same terms.
Bundled IBM Plex fonts are SIL OFL 1.1 (`NOTICE` + `engine/render-support/fonts/OFL.txt`) — don't
add new font files without checking their license is compatible and adding a NOTICE entry.
