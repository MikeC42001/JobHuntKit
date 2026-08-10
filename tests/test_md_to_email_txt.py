"""Tests for engine/md_to_email_txt.py — flattening a hand-wrapped markdown draft into
paste-ready email text. Pure-Python, no browser needed.
"""

import md_to_email_txt as m2e


def test_wrapped_lines_within_a_paragraph_join():
    text = (
        "This is a long deliberately-wrapped line that is well past the sixty character "
        "threshold on its own,\nand this continuation line joins onto it."
    )
    out = m2e.flatten(text)
    assert "\n" not in out.strip()  # the two lines became one


def test_short_standalone_lines_do_not_join():
    """Greeting, sign-off, and signature fields are short deliberate lines — they must stay
    one-per-line, not get joined into the paragraph above them."""
    # Built via "\n".join rather than one literal string with an escaped newline right before the
    # email — that raw source text would glue the backslash-n's "n" onto the email as one token,
    # which audit_public.py's regex reads as a different (non-allowlisted) local part.
    text = "\n".join(["Best,", "Robin Vale", "robin.vale@example.com"])
    out = m2e.flatten(text).strip()
    assert out.splitlines() == ["Best,", "Robin Vale", "robin.vale@example.com"]


def test_everything_from_a_lone_dash_divider_onward_is_dropped():
    text = "Dear team,\n\nI'd love to work here.\n\n---\nDraft notes: not for sending.\n"
    out = m2e.flatten(text)
    assert "Draft notes" not in out
    assert "---" not in out
    assert "I'd love to work here." in out


def test_emphasis_markers_are_stripped():
    text = "This has **bold** and *italic* text in it, long enough to count as a real line."
    out = m2e.flatten(text)
    assert "**" not in out
    assert "*italic*" not in out
    assert "bold" in out
    assert "italic" in out


def test_paragraphs_stay_separated_by_a_blank_line():
    text = "First paragraph, short.\n\nSecond paragraph, also short."
    out = m2e.flatten(text)
    assert "\n\n" in out


def test_convert_writes_stem_email_txt_beside_the_input(tmp_path):
    src = tmp_path / "cover_letter.md"
    src.write_text("Dear team,\n\nBest,\nRobin Vale\n", encoding="utf-8")

    out_path = m2e.convert(src)

    assert out_path == tmp_path / "cover_letter_email.txt"
    assert out_path.is_file()
    assert "Dear team," in out_path.read_text(encoding="utf-8")


def test_main_reports_a_missing_file(capsys):
    import sys
    old_argv = sys.argv
    sys.argv = ["md_to_email_txt.py", "does/not/exist.md"]
    try:
        rc = m2e.main()
    finally:
        sys.argv = old_argv
    assert rc == 1
    assert "not a file" in capsys.readouterr().err
