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

### Q-006 — Should there be a way to list every JobHuntKit root on a machine?

**Status:** open

As of v0.1.1 every root carries a `.jobhuntkit` marker containing the constant
`jobhuntkit-root/1` — added so root detection stops relying on the presence of `config.json`,
which is far too common a filename. A constant is also *discoverable* in a way a heuristic never
was: you cannot reliably scan a disk for "directories whose `config.json` has plausible keys," but
you can scan for a file whose first line is a known constant.

That would make a `scripts/find_roots.py` possible, which would answer:

- "Where did I put my CV data?" — the question `.jobhuntkit-root` exists to stop you asking, but
  which still applies on a second machine, or after moving the folder.
- Whether a stale `.jobhuntkit-root` pointer has a real root elsewhere it should be repointed at,
  instead of just reporting a broken path.
- That deliberately-multiple roots exist — your own set plus, say, a copy you scaffolded while
  helping someone else set the toolkit up.

Design notes if it happens: bound the scan to `$HOME` by default with a `--path` override, and
skip `node_modules`, `.git`, and similar, because a full-disk walk is slow (especially on
Windows). A registry file listing known roots is the tempting alternative and is worse — it is
duplicated state that goes stale the moment a folder moves, where a bounded scan always reports
what is true now.

What would settle it: whether anyone actually ends up with more than one root. With a single root
and a remembered pointer, this solves a problem nobody has. It was proposed as a *consequence* of
the marker rather than a motivation for it, and it stays here until someone wants it.

### Q-007 — Should `demo.sh` render every CV style, not just the default?

**Status:** open

`render_cv_minimal.sh` ships four visual styles (`--style a|b|c|z`), but `demo.sh` never passes
`--style`, so it renders whichever one `config.json`'s `render.default_style` names — currently
one of four. Someone running the 60-second demo sees a single look and has no reason to suspect
the others exist; `docs/CUSTOMIZING.md` describes them, which is a weaker signal than seeing them.

Rendering all four for the demo persona would make the choice visible at the moment someone is
deciding whether the output suits them, and would incidentally give CI's `render-matrix` job
coverage of every style path instead of one.

The cost is real though: four more headless-Chrome invocations per run, on a script whose selling
point is in its name and in the README heading. It would also need a story for what the output
folder looks like — four PDFs named per style, or a single contact sheet.

What would settle it: whether anyone actually switches style after trying the demo. If everyone
stays on the default, this is four extra renders to show something nobody chose; if people do
switch, they are currently discovering the option by reading rather than by seeing.

### Q-008 — Does any of this work on Windows without Git Bash?

**Status:** open

Every renderer is a Bash script, and the README's answer for Windows is one line: run it from Git
Bash. That is honest but untested as a boundary — **nobody has established what actually happens
on a stock Windows 10 machine with only `cmd` and PowerShell.**

~~CI does not cover it either~~ — it does now; see the update below.

Three directions, in increasing cost:

1. **Document Git Bash as a hard requirement** and check the failure is legible — a clear "this
   needs Bash" beats a cryptic error from `cmd` trying to run a `.sh` file.
2. **Ship PowerShell equivalents** of the renderers. Duplicates logic that already exists twice
   over (four render scripts share `lib.sh`), so it doubles the surface that can drift.
3. **Move rendering into Python**, which is already a hard dependency, and drop Bash from the
   critical path entirely. Biggest change, and the one that actually removes the question.

#### Update — a first run on Windows, finally

Someone ran a fresh clone on a Windows 11 machine, in Git Bash, and it broke immediately: `bash
demo.sh` died at step 1 of 10 because the script invoked `python3`, which is not a command that
exists on a stock Windows install. The python.org installer provides `python` and `py`; the
`python3` that *is* normally on PATH is Windows' App Execution Alias, a stub that advertises the
Microsoft Store and exits non-zero. Python had also been installed without "Add python.exe to
PATH" ticked, which is a separate and equally common trap.

Three things came out of it:

- **Direction 1 has been taken.** Git Bash is now stated as a requirement in the README rather
  than mentioned in passing, `docs/INSTALL.md` covers it per platform, and
  `scripts/preflight.sh` reports what's missing before anything runs.
- **The interpreter is resolved rather than named** (`python_bin()` in `engine/lib.sh`): it tries
  `python3`, `python`, `py` and the usual install locations, and accepts a candidate only if it
  actually executes and reports Python 3.8+. So the Store stub is skipped rather than picked.
- **`render-matrix` now includes `windows-latest`**, so the Bash render path executes in CI on
  Windows. Worth being precise: that job would *not* have caught this bug, because
  `actions/setup-python` provides `python3` on a Windows runner. `tests/test_python_bin.py`
  guards the interpreter name; the CI job guards the renderers.

**Why this stays open.** All of the above is about Windows *with* Git Bash. The question as asked
is about a machine that has none — and nobody has run that. What would still settle it: a fresh
clone on Windows with only `cmd` and PowerShell, recording where it breaks and whether the failure
is legible enough to act on.

### Q-009 — Should the colour palette be settable without editing engine files?

**Status:** open

The palette lives as hardcoded hex values inside the converters — 13 of them in
`engine/render-support/cv2html-minimal.js` alone — and `docs/CUSTOMIZING.md` correctly tells
people that changing the PDF's look means editing the matching `cv2html*.js`.

That is the wrong seam for something this cosmetic. Those files are **engine**, so editing them
means a user's personal preference lives in a tracked engine file: `sync.sh push` would carry it
back, `git pull` conflicts on it, and the engine/content separation this project is otherwise
strict about is broken for the one change most people will want to make first.

Two shapes worth comparing:

- **A `render.palette` block in `config.json`**, read by the converters and injected as CSS
  custom properties. Consistent with how every other setting works, and config.json is already
  per-root rather than per-checkout.
- **A CSS override file at the root**, appended after the converter's own styles. More expressive
  (it can reach anything, not just named colours) but unbounded, so it can also break the layout
  contract the renderer relies on.

What would settle it: whether the wanted change is genuinely "a different accent colour" or
"a different design". The first is a handful of named tokens and belongs in config; the second is
a new style (Q-007's `--style` mechanism) and belongs in a converter after all.
