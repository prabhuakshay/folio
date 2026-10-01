"""Template helpers for sign-in."""

from typing import TYPE_CHECKING

from django import template

from signin import factors

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser

register = template.Library()


@register.simple_tag
def protection(user: AbstractBaseUser) -> str:
    """What protects the login, for Settings' Security row.

    Returns:
        A line such as `2 passkeys · authenticator app · 8 recovery codes`.
    """
    parts = []
    if count := len(factors.passkeys(user)):
        parts.append(f"{count} passkey{'s' if count > 1 else ''}")
    if factors.authenticator(user):
        parts.append("authenticator app")
    parts.append(f"{factors.recovery_codes_left(user)} recovery codes")
    return " · ".join(parts)
