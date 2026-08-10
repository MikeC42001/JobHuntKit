# agents/cv-setup.md — set up and evolve your content layer

Read `agents/CONTEXT.md` first (root-finding, file ownership, never-auto-commit) — this file
assumes you've already done Step 0 there. Everything below is relative to the root you found.

Sets up and evolves the content layer the CV pipeline reads from: `profile/background.md`, the
`@id` scheme across **two masters** (`master/master_cv.md`, the primary/complete inventory, and
`master/master_cv_minimal.md`, its condensation — same ids, terser wording, see `docs/SPEC.md`'s
"The full CV — id-agnostic rendering"), and the render setup (photo + a working
`render_cv_minimal.sh` pass). Two modes, auto-detected — no subcommand keyword needed:

- **Update mode** — `profile/background.md` already exists. File one new fact into it and, if
  it's CV-relevant, into the master `@id` scheme. This is what most people reach for after their
  first setup is done.
- **Bootstrap mode** — `profile/background.md` doesn't exist yet. Build the whole content layer
  from scratch out of CV examples / LinkedIn content / background material the person hands
  over. This is what a brand-new root needs on its first run.

**Argument:** the new fact (Update mode) or bootstrap material (Bootstrap mode). Empty in either
mode → ask for it, per that mode's step 1 below.

---

## Mode detection

    ! test -f profile/background.md && echo EXISTS || echo MISSING

If `EXISTS` → **Update mode** (below). If `MISSING` → **Bootstrap mode** (below).

---

## Update mode

For someone who already has a `profile/background.md` — filing one new fact.

1. Take the fact from the argument, or ask: "What's the new fact?"
2. Record it in `profile/background.md` first — the source of truth — with the existing dated-
   annotation convention (`**Label (added YYYY-MM-DD):**`), in whichever section fits (Skills,
   Current work, Leadership, etc. — read the file first to place it next to related material,
   not just appended at the end).
3. Classify whether it also needs a structural block in the masters:
   - **New project** → new `@proj-<slug>` block, nested under whichever Experience entry
     represents self-directed/independent work, available to any `application.md`'s
     `## Projects` list going forward.
   - **New experience entry** → new `@exp-<slug>` block. Ask: LOCKED (always present on every
     CV, no exceptions) or OPTIONAL (present only when an `application.md` explicitly includes
     it)? Default to OPTIONAL unless told otherwise — LOCKED changes every future CV
     unconditionally.
   - **New skill/tool** → no `@id` needed. Add it to `profile/background.md`'s Skills inventory
     and, if likely to recur, to both masters' example Skills lines.
   - **Interview-only context, not CV material** → step 2 already covered it, stop here.
4. Before assigning any new `@id`, check for collisions in *both* masters — an id must not exist
   in one and not the other, and it must not already be taken in either:
     ! grep -n "<!-- @" master/master_cv.md master/master_cv_minimal.md
   IDs are permanent once referenced from an `application.md` — pick a name that still makes
   sense in six months.
5. **Write the full version first, in `master/master_cv.md`.** This is the primary master — the
   complete record, full wording, no length pressure. Follow its documented convention exactly
   (see its header note, and `docs/SPEC.md`): the `<!-- @id -->` marker on its own line
   immediately before the block, one blank line ends it. Keep any explanatory comment on a
   *separate* line before the marker — never combine explanation and marker on one line (a bare,
   single-line marker is what the parser requires).
6. **Condense the same block into `master/master_cv_minimal.md`, same `@id`.** This is the
   editorial step no script can do — cut it down to the terse, one-line-per-bullet wording a
   one-page CV needs, same id, same content in substance, different length. If the new entry
   only belongs in the complete record (e.g. an older role not worth a tailored CV's space), skip
   this step and say so explicitly — the id-inheritance rule only requires the minimal's ids to
   exist in the full master, never the reverse (see `master/master_cv.md`'s own tailoring notes).
7. If it's a new OPTIONAL entry, add its id to `config.json`'s `spine.optional_ids` and a new
   `{{@id?}}` slot to `templates/minimal-full.md`. A new LOCKED entry needs the same but added to
   `spine.locked_order` and an unconditional `{{@id}}` slot — **flag this explicitly** before
   finishing, since it changes every company's minimal CV on the next build, not just new ones.
   For `templates/full.md`, default to an unconditional `{{@id}}` slot regardless of
   LOCKED/OPTIONAL — the full CV is generous by default (see that template's own header comment)
   — unless told the person wants this entry gated there too.
8. Run:
     ! python engine/check_cv.py --coverage
     ! python engine/check_cv.py --pipeline full --coverage
   Report which existing companies would now show the new id as SILENT — informational only.
   Never edit an existing company's `application.md` here; adopting a new fact is that company's
   own call, made later.
9. Report: what was added, where, the new `@id` if one was created (and whether it landed in
   both masters or only the full one), which companies might want it. No auto-commit.

---

## Bootstrap mode

For a root with no content layer yet.

1. **Confirm before starting.** This creates several files and asks a real judgment question —
   not a quick edit. Ask for whatever material isn't already in the argument: CV examples (old
   CVs already in use — format/content reference), LinkedIn profile content (pasted — exports
   vary too much to parse reliably), any other background material. Pasted text or file paths
   both work.

2. **Draft `profile/background.md`.** Use `templates/background.md`'s section structure as the
   pattern (Personal, Education, Work experience, Volunteering, Current work — portfolio
   projects with a per-project status note and a "what this shows for a CV/application" guidance
   line, Skills, What this shows for a CV/application) — adapted to what this person actually
   has, never copied content from any reference file. Same dated-annotation convention as Update
   mode, for traceability of what came from where.

3. **Guided locked-spine conversation — ask, never infer.** "Which 1–4 experience entries should
   *always* appear on every CV this generates, no exceptions?" This is the single most
   consequential decision in the whole setup — it's what makes every future CV consistent
   instead of drifting the way hand-copied ones do. Don't auto-pick the "most impressive"
   entries from their CV/LinkedIn content; ask directly and let them decide. Record the answer
   in `master/CV_SPEC.md` (start from `templates/CV_SPEC.md`'s skeleton) and mirror it into
   `config.json`'s `spine.locked_order`.

4. **Draft `master/master_cv.md` first** from `templates/master_cv.md`'s skeleton — the primary
   master, `@id`-tagged, full wording, no length pressure: this is the complete record, not the
   tailored pitch. Follow the exact convention documented in its own header comment (marker line
   immediately before its block, one blank line ends the block; full rules in `docs/SPEC.md`).
   Use this person's own descriptive slugs for every `@id` — their own employer/project names,
   never a borrowed or generic id.

5. **Condense it into `master/master_cv_minimal.md`**, from `templates/master_cv_minimal.md`'s
   skeleton — same `@id`s as step 4, terser wording, one-line-per-bullet where the full version
   ran two or three. Every id here must also exist in `master/master_cv.md`; the reverse isn't
   required (the full master can carry entries — an older role, extra bullet detail — the
   condensation leaves out entirely, see `master/master_cv.md`'s own tailoring notes for the
   convention).

6. **Draft `master/CV_SPEC.md`** from `templates/CV_SPEC.md`'s skeleton — locked/optional/
   configurable decisions, entirely this person's own choices from step 3. These decisions apply
   to both masters; `config.json`'s `spine` block isn't per-pipeline.

7. **Adapt `templates/minimal-full.md`/`templates/full.md` if needed.** Both starters already
   have slots for every id the starter masters define — only touch either if the person's locked
   spine needs a structurally different slot (e.g. a third always-present role). Placeholder
   mechanics: `{{@id}}` for locked, `{{@id?}}` for optional, `{{FIELD}}` / `{{FIELD|@id}}` for
   configurable content, `{{PROJECTS}}` for the project list — full grammar in `docs/SPEC.md`.
   `templates/full.md`'s own convention is generous by default (unconditional `{{@id}}` even for
   entries the minimal template gates) — match that unless told otherwise.

8. **Render setup smoke test.** Ask for a photo file path (or confirm one already placed under
   `images/`). Draft one `application.md` for a throwaway/example company (or reuse
   `init_workspace.py`'s placeholder if the root still has one) — leave its front matter at the
   default (no `pipelines:` key, so it builds `minimal` only; the full-CV pipeline is opt-in, see
   `docs/CONFIG.md`'s `pipelines` section, not part of this smoke test). Build it:
     ! python engine/build_cv.py "applications/offer-pages/<example>"
   render it:
     ! bash engine/render_cv_minimal.sh "applications/offer-pages/<example>/cv-minimal.md" --photo images/<photo>
   and verify:
     ! python engine/verify_cvs.py "applications/offer-pages/<example>/generate-pdfs/cv-minimal.pdf"
   This confirms browser detection, `marked` auto-install, and font loading all work on this
   machine, and that the layout fits one page. The renderer/CSS/fonts themselves need zero
   changes — they read everything from the master file's content, nothing is hardcoded to any
   particular person.

9. **Confirm `applications/README.md` exists** (created by `init_workspace.py`; same convention
   if drafted by hand: a table with Company/Role/Remote/Date Applied/Source/Status/Files/Next
   Action columns) and that `applications/offer-pages/` is ready for real postings.

10. **Report.** What was created and where. State explicitly that none of it is final — read it,
    correct it, before it's used for anything real.

No auto-commit in either mode. Git stays manual.
