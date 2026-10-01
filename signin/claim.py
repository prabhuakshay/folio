"""The setup code that claims an empty install.

A public URL can't hand the first visitor the keys, so claiming asks for a code
only someone who can read the server's log has seen. The code is derived from
`SECRET_KEY` rather than stored, so every process (the entrypoint that prints
it, each gunicorn worker that checks it) agrees on it without shared state. It
stays the same across restarts; claiming is what makes it one-time, since every
claim route is gone once a login exists.
"""

from django.contrib.auth import get_user_model
from django.utils.crypto import constant_time_compare, salted_hmac

# 12 digits: the claim form is public and not yet rate limited, so the code
# must be too long to guess, yet still easy to type on a phone keypad.
DIGITS = 12


def is_claimed() -> bool:
    """Whether the install already has its one login.

    Returns:
        True once any user exists.
    """
    return get_user_model().objects.exists()


def _digits() -> str:
    digest = salted_hmac("folio.signin.setup_code", "", algorithm="sha256")
    return str(int(digest.hexdigest(), 16) % 10**DIGITS).zfill(DIGITS)


def setup_code() -> str:
    """The code that claims this install, in groups of four for reading aloud.

    Returns:
        The code, such as `0482 9153 7710`.
    """
    digits = _digits()
    return " ".join(digits[i : i + 4] for i in range(0, DIGITS, 4))


def is_setup_code(entered: str) -> bool:
    """Check an entered code, ignoring spaces and other separators.

    Args:
        entered: What was typed.

    Returns:
        True when it is this install's setup code.
    """
    digits = "".join(c for c in entered if c.isdigit())
    return constant_time_compare(digits, _digits())
