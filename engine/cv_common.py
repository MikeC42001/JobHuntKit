"""cv_common.py — shared helpers for the CV pipeline scripts.

Anything more than one script needs — company-name display formatting, the "sent"/"declined"
state-machine reads, offer-pages folder discovery — lives here so it can't silently drift
between scan_applications.py, collect_cvs.py and collect_letters.py.

The "sent" signal: a company is sent once its rendered PDF has been manually copied into
<root>/produced/sent/<prefix>_<Company>.pdf (see collect_cvs.py's own docstring — that's both
the manual archive and the "stop showing me this" signal). display_name() maps a company's
offer-pages folder name to the clean name used in that filename, via config.json's
display_names map (falls back to the folder name with spaces turned into underscores, so a
brand-new company folder works immediately without editing config.json).
"""

import os


def company_label(path):
    """.../offer-pages/<Company>/... -> <Company>, from any path under a company's folder."""
    parts = os.path.normpath(path).split(os.sep)
    try:
        return parts[parts.index("offer-pages") + 1]
    except (ValueError, IndexError):
        return os.path.basename(os.path.normpath(path))


def display_name(cfg, company):
    return cfg.display_names.get(company, company.replace(" ", "_"))


def to_send_dir(cfg):
    return os.path.join(cfg.produced_dir, "to_send")


def to_send_pdf_path(cfg, company, prefix=None):
    prefix = prefix or cfg.file_prefix
    return os.path.join(to_send_dir(cfg), f"{prefix}_{display_name(cfg, company)}.pdf")


def sent_pdf_path(cfg, company, prefix=None):
    prefix = prefix or cfg.file_prefix
    return os.path.join(cfg.produced_dir, "sent", f"{prefix}_{display_name(cfg, company)}.pdf")


def is_sent(cfg, company, prefix=None):
    return os.path.isfile(sent_pdf_path(cfg, company, prefix))


def declined_pdf_path(cfg, company, prefix=None):
    prefix = prefix or cfg.file_prefix
    return os.path.join(cfg.produced_dir, "not_sent", f"{prefix}_{display_name(cfg, company)}.pdf")


def is_declined(cfg, company, prefix=None):
    """True once the PDF has been manually moved to <root>/produced/not_sent/ — the "decided
    not to apply" signal, same manual-archive pattern as is_sent()/produced/sent/."""
    return os.path.isfile(declined_pdf_path(cfg, company, prefix))


def matches_force_arg(cfg, company, arg):
    """Case-insensitive match against either the folder name or the display name — same
    convention collect_cvs.py's --force COMPANY... has always used."""
    arg_lower = arg.lower()
    return arg_lower == company.lower() or arg_lower == display_name(cfg, company).lower()


def all_company_dirs(cfg):
    offer_pages = cfg.offer_pages_dir
    if not os.path.isdir(offer_pages):
        return []
    return sorted(
        d for d in (os.path.join(offer_pages, name) for name in os.listdir(offer_pages))
        if os.path.isdir(d)
    )
