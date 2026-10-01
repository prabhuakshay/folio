"""Indian formatting for amounts and dates.

Amounts group the Indian way (1,23,456) and summaries shorten to lakh and
crore. Dates read day first (1 Oct 2026), in India's time zone.
"""

import datetime as dt
import re
from decimal import ROUND_HALF_UP, Decimal

from django.utils import dateformat, timezone

LAKH = Decimal(1_00_000)
CRORE = Decimal(1_00_00_000)
_PAISE = Decimal("0.01")


def group_indian(value: Decimal | int) -> str:
    """Group an amount's digits the Indian way, without sign or symbol.

    Args:
        value: The amount; its sign is dropped.

    Returns:
        Digits grouped as 1,23,456, with paise only when there are some.
    """
    value = abs(Decimal(value)).quantize(_PAISE, ROUND_HALF_UP)
    whole, paise = f"{value:f}".split(".")
    head, tail = whole[:-3], whole[-3:]
    head = re.sub(r"(\d)(?=(\d{2})+$)", r"\1,", head)
    grouped = f"{head},{tail}" if head else tail
    return grouped if paise == "00" else f"{grouped}.{paise}"


def short_indian(value: Decimal | int) -> str:
    """Shorten an amount for a summary, without sign or symbol.

    Args:
        value: The amount; its sign is dropped.

    Returns:
        Crores or lakhs to two places (58.85 L, 1.00 Cr), or whole rupees
        grouped the Indian way below a lakh.
    """
    value = abs(Decimal(value))
    if value < LAKH:
        return group_indian(value.quantize(Decimal(1), ROUND_HALF_UP))
    lakhs = (value / LAKH).quantize(_PAISE, ROUND_HALF_UP)
    # Rounding can carry 99.995 L up to 100.00 L, which reads as 1.00 Cr.
    if lakhs * LAKH < CRORE:
        return f"{lakhs} L"
    return f"{(value / CRORE).quantize(_PAISE, ROUND_HALF_UP)} Cr"


def indian_date(value: dt.date, *, year: bool = True) -> str:
    """Format a date day first, as India writes it.

    Args:
        value: A date, or a datetime, which is read in India's time zone.
        year: Whether to include the year.

    Returns:
        The date as 1 Oct 2026, or 1 Oct without the year.
    """
    if isinstance(value, dt.datetime) and timezone.is_aware(value):
        value = timezone.localtime(value)
    return dateformat.format(value, "j M Y" if year else "j M")
