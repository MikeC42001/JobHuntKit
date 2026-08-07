# agents/interview-prep.md — build an interview prep doc, then rehearse it live

Read `agents/CONTEXT.md` first (root-finding, file ownership, never-auto-commit) — this file
assumes you've already done Step 0 there. Every path below is relative to the root you found
there.

Unlike `cv-tailor`/`cv-setup`, this doesn't touch `engine/` at all — it's pure conversational
coaching grounded in files already on disk, not a build pipeline.

**Argument:** which company (must already have an `applications/offer-pages/<Company>/` folder
with at least `posting.md`; `application.md`/`cover_letter.md` if they exist, read them too). If
ambiguous or missing, ask rather than guess.

## Step 0 — Ask which stage

Interview processes are rarely one call — ask which stage this is (intro/screening call,
technical/coding round, culture/values round, final, etc.) before building anything. Prep content
differs enough by stage that guessing wastes the rest of the run. If the person doesn't know, ask
if the posting names a process (many do) and default to the first unstarted stage.

## Step 1 — Read everything already on record for this company

- `applications/offer-pages/<Company>/posting.md` — the role itself.
- `application.md` and `cover_letter.md`, if they exist — **this is what the person already told
  the company in writing.** Any prep must stay consistent with it, not contradict or soften it.
- `profile/background.md` — the actual source of truth on what's true. Cross-check every claim the
  application/cover letter makes against it; note anything the application implied that
  `background.md` doesn't actually support (this is a real failure mode: application copy drifting
  from the underlying facts under the pressure of trying to sound qualified).
- Any target-roles/preferences file the root has, for location/comp/seniority framing.

Light web research on the company (product, leadership, recent news) is worth doing if it'll
plausibly come up ("why us specifically" questions are common and generic answers are weak) — but
keep it to what's actually useful for the stage identified in Step 0, not a general company
dossier.

## Step 2 — Write the prep doc

Save as `applications/offer-pages/<Company>/interview_prep_<stage>.md`. Structure:

- **Company snapshot** — what they actually do, who's who if relevant, source links.
- **What you already told them** — the exact framing/claims from the cover letter and
  application, especially any deliberately-honest gap admissions. State plainly: getting an
  interview means someone read this and is fine with it — the job in the interview is to stay
  consistent with it, not to re-litigate or backpedal on it.
- **Likely topics for this stage** — grounded in the posting's actual requirements vs. the
  person's actual background, not generic interview advice.
- **Redlines** — specific claims the background doesn't support and shouldn't be made, however
  the conversation goes.
- **Questions worth asking them** — specific to what's actually unclear about the role/company,
  not stock questions.
- **Logistics** — application date/channel, what stage comes next.

## Step 3 — Mock Q&A, one question at a time

Offer this after the doc exists. Ask one realistic question, wait for the person's actual spoken/
typed answer, then give direct feedback before moving to the next question. Don't front-load a
list of questions and answers — the value is in reacting to what they actually say, including
their filler, tangents, and unscripted mistakes, not in producing a clean transcript.

**What to check every answer against, in priority order:**

1. **Consistency with what's already in writing.** If the cover letter admitted a gap, the live
   answer must not claim the gap doesn't exist or downplay it — that reads as either the letter
   being wrong or the person backpedaling under pressure, both worse than the gap itself. Flag any
   answer that contradicts or walks back a written claim.
2. **Factual accuracy against `background.md`.** Watch for real-time embellishment — a role or
   skill described more impressively live than it's documented. If the person surfaces a genuinely
   new fact not yet in `background.md` (e.g. more detail about a past project), that's worth
   capturing back into `background.md` after the session (dated note, per that file's existing
   convention) — don't just let it evaporate into the mock transcript.
3. **Evidence over assertion.** Vague self-praise ("I'm the best candidate," "I know it all,"
   "everyone says I'm great at X") is unfalsifiable and undercuts credibility, especially paired
   with an admitted gap. Redirect every instance to the specific, checkable fact the person
   actually has on record (a named project, a dated role, a concrete outcome) instead of a
   superlative. If this pattern repeats across multiple answers, say so explicitly — it's usually
   a live-pressure habit, not a one-off, and naming the pattern helps more than fixing each
   instance separately.
4. **Never badmouth a former employer, colleague, or generalize negatively about a group**
   (a nationality, a company culture, "people like X") to make a contrast. If a draft answer heads
   this direction, stop it immediately and offer a scope-based contrast instead ("that role was
   about Y, this one is about Z") rather than a character judgment.
5. **Concede real gaps rather than arguing the interviewer's stated requirement is wrong.** "If you
   need someone with X from day one, that's a fair reason to pick someone else" lands better than
   telling a company their own job requirement is mistaken.
6. **Length and structure.** Live answers tend to run long and lose their thread under pressure.
   For any "tell me about yourself / your background" style question, coach toward a small number
   of ordered beats (what's most relevant first) rather than a chronological life story.

Give feedback as: what's wrong and *why it matters* (the concrete mechanism — what a follow-up
question or a re-read of their own cover letter would expose), not just a corrected version to
recite. Offer a rewritten version only after the diagnosis, and frame it as beats to internalize,
not a script to memorize verbatim — reciting a memorized paragraph reads as stiff as the problems
it's fixing.

## Step 4 — Update the prep doc

On request (or once a question's answer has stabilized through a few iterations), fold the fixed
version and the specific mistake it fixes back into the prep doc — both the working answer and the
failure mode it corrects, so the doc is useful read cold before the real call, not just a log of
the practice session. If new facts about the person's background surfaced during practice, update
`profile/background.md` too, with a dated note per its existing convention — don't leave a fact
that only exists in the mock-interview transcript.

## Step 5 — Report

No auto-commit — this is personal/sensitive content, leave committing to the person (same rule as
every other agent-driven flow in this toolkit — see `agents/CONTEXT.md`). Summarize what's in the
prep doc and flag anything still weak after practice (a question that never landed solidly) rather
than declaring the person fully ready if they aren't.
