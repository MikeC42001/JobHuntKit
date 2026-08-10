---
template: minimal-full
company: Example Company
role: Example Role
---

## Tagline

Replace this one-line hook with something specific to the posting — the template already wraps
it in italics, so don't add asterisks here yourself.

## About me

Replace this paragraph with a short pitch tailored to this specific posting — two to four
sentences, written fresh each time, never reused verbatim between applications.

## Contact suffix

(remote)

## Projects

- proj-example

## Skills

**Languages:** replace with your own, comma-separated
**Frameworks/Tools:** replace with your own
**Practices:** replace with your own

## Notes

This is the placeholder example created by `scripts/init_workspace.py` so that a fresh clone has
at least one company to build — otherwise the very first `build_cv.py --all` /
`check_cv.py` would fail with "no companies found."

Once you're ready for your first real application:
1. Rename this folder (`applications/offer-pages/Example Company`) to the real company name.
2. Edit every section above for that posting.
3. `python engine/build_cv.py "applications/offer-pages/<Company>"`
4. `python engine/check_cv.py "applications/offer-pages/<Company>"`

Or delete this folder entirely if you'd rather start from scratch with `python
engine/build_cv.py --all --check` reporting nothing to do.

This `## Notes` section is read by nobody but you — it never reaches the generated CV.

This file has no `pipelines:` front-matter key, which means it builds the tailored one-pager
only (`cv-minimal.md`). Add `pipelines: minimal, full` above to also build the long-form
`cv.md` from `master/master_cv.md` — see `docs/CONFIG.md`'s "pipelines" section.
