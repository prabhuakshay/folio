"""Template helpers for Folio's design language."""

from typing import TYPE_CHECKING

from django import template
from django.utils.html import format_html

from ui import formatting

if TYPE_CHECKING:
    from decimal import Decimal

    from django.utils.safestring import SafeString

register = template.Library()

MINUS = "\N{MINUS SIGN}"


@register.simple_tag
def inr(value: Decimal, *, short: bool = False, flow: bool = False) -> SafeString:
    """Render an amount in rupees with a small raised ₹.

    Args:
        value: The amount.
        short: Shorten to lakh and crore, for summaries.
        flow: Show money in or out rather than a balance: income green with a
            plus, expenses plain ink with no minus.

    Returns:
        The amount as HTML.
    """
    digits = formatting.short_indian(value) if short else formatting.group_indian(value)
    amount = format_html('<span class="cur">₹</span>{}', digits)
    if flow:
        if value > 0:
            return format_html('<span class="text-positive">+{}</span>', amount)
        return amount
    return format_html("{}{}", MINUS, amount) if value < 0 else amount


@register.filter(expects_localtime=True)
def indian_date(value, arg: str = "") -> str:  # noqa: ANN001
    """Format a date day first; `'short'` leaves out the year.

    Returns:
        The formatted date, or an empty string for no date.
    """
    if not value:
        return ""
    return formatting.indian_date(value, year=arg != "short")


@register.filter
def initials(user) -> str:  # noqa: ANN001
    """Two letters for the avatar: first and last name, else the username.

    Returns:
        The initials, upper case.
    """
    names = [n for n in (user.first_name, user.last_name) if n]
    return "".join(n[0] for n in names).upper() or user.get_username()[:1].upper()
