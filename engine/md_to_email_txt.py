#!/usr/bin/env python3
"""md_to_email_txt.py — flatten a markdown draft into paste-ready email text.

Cover letters and similar drafts are written as hand-wrapped markdown: prose paragraphs
soft-wrapped at a fixed column, a blank line between them, and often a trailing "---" section
with draft/review notes that isn't meant to be sent. Pasted as-is into an email client, the wrap
points become hard line breaks mid-sentence.

This joins each paragraph's wrapped prose lines into one line, while leaving short deliberate
lines alone (greeting, sign-off, signature block: name, phone, email, LinkedIn — those are meant
to stay one-per-line). The rule: a line only gets joined to the next if it's long enough to have
been a wrapped line (>= LONG_LINE chars) rather than a short standalone field. It also strips
inline **bold**/*italic* markers (meaningless in plain email text) and drops everything from a
lone "---" divider onward.

Usage:
    python engine/md_to_email_txt.py path/to/cover_letter.md [more.md ...]

Writes <name>_email.txt next to each input file. Always check the output before pasting — this
is a mechanical wrap-joiner, not a content edit.

No --root: unlike every other engine script, this one takes explicit file paths and never
resolves anything root-relative, so it deliberately doesn't take config.root_parent_parser().
"""

import re
import sys
from pathlib import Path

EMPHASIS = re.compile(r'(\*\*|\*)(.+?)\1')
LONG_LINE = 60  # below this, a line is treated as a deliberate standalone line, not a wrap


def flatten(text):
    lines = text.splitlines()

    # Drop everything from a lone "---" divider onward (draft/review notes).
    for i, line in enumerate(lines):
        if line.strip() == "---":
            lines = lines[:i]
            break

    text = "\n".join(lines).strip("\n")

    paragraphs = re.split(r'\n\s*\n', text)
    out_paragraphs = []
    for para in paragraphs:
        para_lines = [line.strip() for line in para.splitlines() if line.strip()]
        joined_lines = []
        for line in para_lines:
            if joined_lines and len(joined_lines[-1]) >= LONG_LINE:
                joined_lines[-1] = joined_lines[-1] + " " + line
            else:
                joined_lines.append(line)
        out_paragraphs.append("\n".join(EMPHASIS.sub(r'\2', ln) for ln in joined_lines))

    return "\n\n".join(out_paragraphs) + "\n"


def convert(md_path):
    md_path = Path(md_path)
    out_path = md_path.with_name(md_path.stem + "_email.txt")
    out_path.write_text(flatten(md_path.read_text(encoding="utf-8")), encoding="utf-8")
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: md_to_email_txt.py path/to/file.md [more.md ...]", file=sys.stderr)
        return 1
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.is_file():
            print(f"md_to_email_txt: not a file -- {arg}", file=sys.stderr)
            return 1
        out = convert(path)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
