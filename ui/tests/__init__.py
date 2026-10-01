"""Tests for the app shell, and shared helpers."""

import re


def closes_from_its_header(html, dialog_id=None):
    """Whether a sheet's Close button follows its title, with no Cancel or Done.

    Args:
        html: A page, or a sheet's own markup.
        dialog_id: The sheet to check, when `html` is a whole page.

    Returns:
        True when the sheet closes only from its header.
    """
    title = "<h2 "
    if dialog_id:
        html = re.search(rf'<dialog id="{dialog_id}".*?</dialog>', html, re.DOTALL)[0]
        title += f'id="{dialog_id}-title"'
    header = re.search(
        title + r"[^>]*autofocus[^>]*>[^<]*</h2>"
        r'\s*<form method="dialog">\s*<button[^>]*aria-label="Close"',
        html,
    )
    pills = re.search(r">\s*(Cancel|Done)\s*</button>", html)
    return bool(header) and not pills
