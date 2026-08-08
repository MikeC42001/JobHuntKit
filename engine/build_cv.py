#!/usr/bin/env python3
"""build_cv.py — assembles a company's cv-minimal.md (and optionally cv.md) from a master +
template + application.md.

Three inputs, one generated output per pipeline (see docs/SPEC.md):

    master/master_cv_minimal.md (what CAN be said, locked wording by @id)  -- minimal pipeline
    master/master_cv.md         (the complete inventory, same ids)         -- full pipeline
    templates/<name>.md         (which slots exist, in what order, which are locked)
    applications/offer-pages/<Company>/application.md
                                 (the pitch: tagline, About me, skills, project selection — the
                                  only file a human should ever hand-edit)
        │
        ▼
    <Company>/cv-minimal.md     (GENERATED — never hand-edit; same status as the rendered PDF)
    <Company>/cv.md             (GENERATED, only if application.md opts in — see "pipelines" below)

Why a generator and not just careful copy-pasting: hand-copying a master into each application
means every wording tweak has to be re-applied by hand everywhere it appears, and it's easy to
miss one. The fix is structural — per-company prose lives in application.md, which this script
reads but never overwrites, so there is nothing left for a re-run to clobber.

No YAML/TOML dependency: application.md uses the same "## Heading" convention as every other
markdown file in this toolkit, parsed with the same split-on-"^## "-pattern the renderers
already use. Front matter (template/company/role) is the one exception — a minimal
"key: value" block between "---" lines, just enough to pick a template.

One application.md, two possible pipelines: an optional "pipelines:" front-matter key
(comma-separated, e.g. "pipelines: minimal, full") selects which of config.json's "pipelines"
entries to build. No such key at all means exactly ["minimal"] — every application.md written
before this key existed builds identically to before. See resolve_pipelines_for() and
config.py's Config.pipeline().

Usage:
    python engine/build_cv.py "applications/offer-pages/Acme"     # one company, writes the file
    python engine/build_cv.py --all                               # every company, writes
    python engine/build_cv.py --all --check                       # dry run: prints diffs, writes nothing
    python engine/build_cv.py "applications/offer-pages/Acme" --check
    python engine/build_cv.py --root path/to/your/data --all      # point at a different root

Exit code 0 on success. Exit 1 if any company fails to build (missing required field, unresolved
locked ID, id in both Include and Omit, etc.) — the whole run's errors are collected and printed
together rather than stopping at the first one, so `--all` reports everything wrong in one pass.
"""

import argparse
import difflib
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod

MARKER_RE = re.compile(r"^<!--\s*@([\w-]+)\s*-->\s*$")
COMMENT_RE = re.compile(r"<!--[\s\S]*?-->\n?")
TOKEN_RE = re.compile(r"\{\{([^}]+)\}\}")


class BuildError(Exception):
    """Raised for a single company's build failure; caught and collected by main()."""


# ---------------------------------------------------------------------------
# Master parsing
# ---------------------------------------------------------------------------

def parse_master(path):
    """Extract every `<!-- @id -->`-marked block: content is all lines immediately following the
    marker, up to (not including) the next blank line or EOF. A stray comment line inside a block
    is skipped defensively, but a well-formed master never has one."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().replace("\r\n", "\n").split("\n")

    blocks = {}
    i = 0
    while i < len(lines):
        m = MARKER_RE.match(lines[i])
        if m:
            block_id = m.group(1)
            i += 1
            content_lines = []
            while i < len(lines) and lines[i].strip() != "":
                if not lines[i].lstrip().startswith("<!--"):
                    content_lines.append(lines[i])
                i += 1
            if block_id in blocks:
                raise BuildError(f"master_cv_minimal.md: duplicate @{block_id} marker")
            blocks[block_id] = "\n".join(content_lines).rstrip()
        else:
            i += 1
    return blocks


# ---------------------------------------------------------------------------
# application.md parsing
# ---------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^---\n([\s\S]*?)\n---\n?", re.MULTILINE)

# application.md "## Heading" -> template FIELD name
FIELD_HEADINGS = {
    "tagline": "TAGLINE",
    "about me": "ABOUT_ME",
    "contact suffix": "CONTACT_SUFFIX",
    "skills": "SKILLS",
    "dissertation depth": "EDU_MSC_DISSERTATION",
}
# Headings handled outside the generic FIELD_HEADINGS map (special parsing, or intentionally
# never reaching the output).
SPECIAL_HEADINGS = {"projects", "include", "omit", "notes"}


def parse_application(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")

    fm_match = FRONT_MATTER_RE.match(text)
    if not fm_match:
        raise BuildError(f"{path}: missing '---' front matter block")
    front_matter = {}
    for line in fm_match.group(1).split("\n"):
        if not line.strip():
            continue
        if ":" not in line:
            raise BuildError(f"{path}: malformed front-matter line: {line!r}")
        key, _, value = line.partition(":")
        front_matter[key.strip()] = value.strip()
    for required in ("template", "company", "role"):
        if required not in front_matter:
            raise BuildError(f"{path}: front matter missing required key '{required}'")

    body = text[fm_match.end():]
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    # parts[0] is anything before the first "## " (should be blank/whitespace only)
    fields = {}
    projects = None
    include_ids = []
    omit = {}  # id -> reason
    for j in range(1, len(parts), 2):
        heading = parts[j].strip()
        section_body = parts[j + 1].strip("\n")
        key = heading.lower()
        if key == "projects":
            projects = _parse_id_list(section_body, allow_override=True)
        elif key == "include":
            include_ids = [pid for pid, _ in _parse_id_list(section_body, allow_override=False)]
        elif key == "omit":
            for pid, reason in _parse_id_list(section_body, allow_override=True):
                omit[pid] = reason or "(no reason given)"
        elif key == "notes":
            continue  # never enters the generated file
        elif key in FIELD_HEADINGS:
            fields[FIELD_HEADINGS[key]] = section_body.strip()
        else:
            raise BuildError(
                f"{path}: unrecognized heading '## {heading}' — not in FIELD_HEADINGS or "
                f"SPECIAL_HEADINGS, check spelling against docs/SPEC.md"
            )

    overlap = set(include_ids) & set(omit)
    if overlap:
        raise BuildError(f"{path}: id(s) in both ## Include and ## Omit: {sorted(overlap)}")

    return {
        "front_matter": front_matter,
        "fields": fields,
        "projects": projects or [],
        "include_ids": include_ids,
        "omit": omit,
    }


def _parse_id_list(text, allow_override):
    """Parses a "- id" or "- id: override text" bullet list into [(id, override_or_None), ...].
    A non-"-" line is treated as a soft-wrap continuation of the previous bullet's override text
    (2-space-indent convention used throughout this toolkit's hand-written CVs), joined with a
    space — so a long override can still be wrapped for readability in application.md."""
    result = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if not line.startswith("-"):
            if not result:
                raise BuildError(f"expected a '- ' bullet, got: {line!r}")
            pid, override = result[-1]
            if override is None:
                raise BuildError(f"continuation line with no override to continue: {line!r}")
            result[-1] = (pid, override + " " + line)
            continue
        line = line[1:].strip()
        if allow_override and ":" in line:
            pid, _, override = line.partition(":")
            result.append((pid.strip(), override.strip()))
        else:
            result.append((line.strip(), None))
    return result


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------

def resolve_token(token, master, app, company_label):
    """Resolves one {{...}} token. Returns the replacement string, or None to signal the
    surrounding line (and one adjacent blank line) should be dropped entirely."""
    token = token.strip()

    if token == "PROJECTS":
        return _resolve_projects(master, app, company_label)

    if "|" in token:
        field_token, _, fallback_token = token.partition("|")
        field_token = field_token.strip()
        fallback_token = fallback_token.strip()
        if field_token in app["fields"]:
            value = app["fields"][field_token]
        elif fallback_token.startswith("@"):
            value = resolve_token(fallback_token, master, app, company_label)
        else:
            # Literal fallback (commonly empty) — e.g. {{CONTACT_SUFFIX|}} for an optional field
            # with no master equivalent.
            value = fallback_token
        if field_token == "CONTACT_SUFFIX" and value:
            # Authored as "(remote)", no surrounding spaces — the template places this
            # immediately after the location with no separator, so add the leading space here
            # rather than asking every application.md to remember it.
            value = " " + value
        return value

    if token.startswith("@"):
        rest = token[1:]
        if "?section:" in rest:
            block_id, _, heading = rest.partition("?section:")
            if block_id in app["include_ids"]:
                content = master.get(block_id)
                if content is None:
                    raise BuildError(f"{company_label}: @{block_id} not found in master")
                return f"## {heading.strip()}\n\n{content}"
            return None
        if rest.endswith("?"):
            block_id = rest[:-1]
            if block_id in app["include_ids"]:
                content = master.get(block_id)
                if content is None:
                    raise BuildError(f"{company_label}: @{block_id} not found in master")
                return content
            return None
        block_id = rest
        content = master.get(block_id)
        if content is None:
            raise BuildError(f"{company_label}: locked @{block_id} not found in master — a "
                              f"locked slot must always resolve")
        return content

    if token in ("COMPANY", "ROLE"):
        value = app["front_matter"].get(token.lower())
        if not value:
            raise BuildError(f"{company_label}: front matter missing '{token.lower()}'")
        return value

    # Plain FIELD token, no fallback — required.
    if token not in app["fields"]:
        raise BuildError(f"{company_label}: application.md has no '## {_field_to_heading(token)}' "
                          f"section, required by the template")
    return app["fields"][token]


def _field_to_heading(field_token):
    for heading, name in FIELD_HEADINGS.items():
        if name == field_token:
            return heading
    return field_token


def _resolve_projects(master, app, company_label):
    if not app["projects"]:
        raise BuildError(f"{company_label}: application.md has no '## Projects' entries")
    lines = []
    for pid, override in app["projects"]:
        if override:
            lines.append(f"- {override}")
        else:
            content = master.get(pid)
            if content is None:
                raise BuildError(f"{company_label}: project @{pid} not found in master")
            lines.append(content)
    return "\n".join(lines)


def build_one(template_text, master, app, company_label):
    # Strip every HTML comment from the template before substitution — these are documentation
    # for whoever edits the template, never meant to reach generated output.
    cleaned = COMMENT_RE.sub("", template_text)

    def _sub(m):
        replacement = resolve_token(m.group(1), master, app, company_label)
        return "" if replacement is None else replacement

    output = TOKEN_RE.sub(_sub, cleaned)

    # Dropped optional slots leave behind runs of blank lines — collapse to at most one.
    output = re.sub(r"\n{3,}", "\n\n", output)
    output = output.strip("\n") + "\n"

    # Defensive: nothing from an @id marker or a stray comment should have survived. Catches, in
    # particular, a template doc-comment that itself contains a literal "-->" (e.g. an example of
    # HTML-comment syntax in prose) — COMMENT_RE is non-greedy and closes at that inner "-->",
    # leaking the rest of the real comment as plain text.
    if "<!--" in output or "-->" in output:
        raise BuildError(
            f"{company_label}: unstripped HTML comment markers in generated output — check the "
            f"template for a doc-comment containing a literal '-->' in its own prose, which "
            f"truncates COMMENT_RE's non-greedy match early"
        )

    return output


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def find_application_dirs(cfg):
    return sorted(
        os.path.dirname(p)
        for p in glob.glob(os.path.join(cfg.offer_pages_dir, "*", "application.md"))
    )


def resolve_pipelines_for(front_matter):
    """Which pipelines to build for one company, from application.md's optional "pipelines:"
    front-matter key (comma-separated, e.g. "minimal, full"). Absent entirely -> exactly
    ["minimal"], so every application.md written before this key existed keeps building
    identically — this is the whole backward-compatibility guarantee in one function."""
    raw = front_matter.get("pipelines")
    if not raw:
        return ["minimal"]
    return [p.strip() for p in raw.split(",") if p.strip()]


def build_company(cfg, company_dir, master, check_only, pipeline="minimal"):
    app_path = os.path.join(company_dir, "application.md")
    app = parse_application(app_path)

    if pipeline == "minimal":
        # Template stays a per-application choice, as it always has been — application.md's own
        # front matter picks it, not config. Every other pipeline's template is a fixed config
        # default (see cfg.pipeline()): there's normally exactly one full-CV template, so there's
        # nothing per-company to choose.
        template_name = app["front_matter"]["template"]
    else:
        template_name = cfg.pipeline(pipeline)["template"]

    template_path = os.path.join(cfg.templates_dir, template_name + ".md")
    if not os.path.isfile(template_path):
        raise BuildError(f"{company_dir}: template '{template_name}' not found at {template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        template_text = f.read().replace("\r\n", "\n")

    company_label = app["front_matter"].get("company", os.path.basename(company_dir))
    output = build_one(template_text, master, app, company_label)

    out_path = os.path.join(company_dir, cfg.pipeline(pipeline)["out"])
    line_count = output.count("\n")
    warning = None
    # The soft line budget is a one-page-fit proxy — meaningless for the full pipeline, which has
    # no page target at all.
    if pipeline == "minimal" and line_count > cfg.soft_line_budget:
        warning = f"{line_count} lines, over the {cfg.soft_line_budget}-line soft budget"

    if check_only:
        old = ""
        if os.path.isfile(out_path):
            with open(out_path, "r", encoding="utf-8", newline="") as f:
                old = f.read().replace("\r\n", "\n")
        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True), output.splitlines(keepends=True),
            fromfile=f"{out_path} (current)", tofile=f"{out_path} (generated)",
        ))
        return company_label, diff, warning

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(output)
    return company_label, None, warning


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[cfgmod.root_parent_parser()],
    )
    parser.add_argument("company_dir", nargs="?", help="path to one applications/offer-pages/<Company> folder")
    parser.add_argument("--all", action="store_true", help="build every company with an application.md")
    parser.add_argument("--check", action="store_true", help="dry run — print diffs, write nothing")
    args = parser.parse_args()

    if not args.all and not args.company_dir:
        parser.error("pass a company_dir or --all")

    cfg = cfgmod.resolve(args.root)

    if not os.path.isfile(cfg.master_path):
        print(f"build_cv: master not found at {cfg.master_path}", file=sys.stderr)
        return 1
    masters = {"minimal": parse_master(cfg.master_path)}
    if os.path.isfile(cfg.master_full_path):
        masters["full"] = parse_master(cfg.master_full_path)

    targets = find_application_dirs(cfg) if args.all else [os.path.abspath(args.company_dir)]
    if not targets:
        print("build_cv: no application.md files found.", file=sys.stderr)
        return 1

    errors = []
    warnings = []
    for company_dir in targets:
        try:
            app_peek = parse_application(os.path.join(company_dir, "application.md"))
        except BuildError as e:
            errors.append(str(e))
            continue
        pipeline_names = resolve_pipelines_for(app_peek["front_matter"])

        for pipeline in pipeline_names:
            if pipeline not in masters:
                errors.append(
                    f"{company_dir}: pipeline '{pipeline}' requested but its master "
                    f"({cfg.pipeline(pipeline)['master']}) doesn't exist"
                )
                continue
            try:
                label, diff, warning = build_company(
                    cfg, company_dir, masters[pipeline], args.check, pipeline=pipeline
                )
            except BuildError as e:
                errors.append(str(e))
                continue
            # No tag for the default (minimal) pipeline — output stays byte-identical to before
            # this feature existed, for the common single-pipeline case.
            tag = "" if pipeline == "minimal" else f" [{pipeline}]"
            if warning:
                warnings.append(f"{label}{tag}: {warning}")
            if args.check:
                if diff:
                    print(f"--- {label}{tag} ---")
                    sys.stdout.writelines(diff)
                    print()
                else:
                    print(f"{label}{tag}: no changes")
            else:
                print(f"{label}{tag}: written")

    if warnings:
        print()
        for w in warnings:
            print(f"WARNING: {w}")

    if errors:
        print()
        print(f"build_cv: {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
        return 1

    print()
    print(f"build_cv: {len(targets)} compan{'y' if len(targets) == 1 else 'ies'} OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
