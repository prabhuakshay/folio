"""The 12 Doctrine thresholds: each one's default, recommended band and unit.

Read a threshold's current value with `threshold(key)`. Percentages read as
percent (3 for 3%, so divide by 100 for a rate), money in rupees, periods in
days or months, and the life cover multiple as times Take-home.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from doctrine.models import Threshold
from ui.formatting import CRORE, LAKH

Key = Threshold.Key

DASH = "\N{EN DASH}"
TIMES = "\N{MULTIPLICATION SIGN}"


class Unit(StrEnum):
    """How a threshold's value reads."""

    DAYS = "days"
    MONTHS = "months"
    MULTIPLE = f"{TIMES} Take-home"
    RUPEES = "rupees"
    PERCENT = "%"


def number(value: Decimal) -> str:
    """Write a number without trailing zeros, such as `2.5` for 2.5000.

    Returns:
        The number as text.
    """
    return f"{value.normalize():f}"


def _rupees(value: Decimal) -> str:
    if value >= CRORE:
        return f"₹{number(value / CRORE)}Cr"
    if value >= LAKH:
        return f"₹{number(value / LAKH)}L"
    return f"₹{number(value)}"


@dataclass(frozen=True)
class Spec:
    """One threshold as the Doctrine defines it."""

    key: Key
    group: str
    unit: Unit
    default: Decimal
    low: Decimal
    high: Decimal
    about: str

    @property
    def label(self) -> str:
        """The threshold's name."""
        return self.key.label

    def format(self, value: Decimal) -> str:
        """Write a value in this threshold's unit, such as `6 months`.

        Returns:
            The value as text.
        """
        match self.unit:
            case Unit.DAYS:
                return f"{number(value)} day{'' if value == 1 else 's'}"
            case Unit.MONTHS:
                return f"{number(value)} month{'' if value == 1 else 's'}"
            case Unit.MULTIPLE:
                return f"{number(value)}{TIMES}"
            case Unit.RUPEES:
                return _rupees(value)
            case Unit.PERCENT:
                return f"{number(value)}%"

    @property
    def band(self) -> str:
        """The recommended band as text, such as `3-12 months`, with an en dash."""
        if self.unit == Unit.RUPEES:
            return f"{_rupees(self.low)}{DASH}{_rupees(self.high)}"
        return f"{number(self.low)}{DASH}{self.format(self.high)}"

    def within_band(self, value: Decimal) -> bool:
        """Whether a value sits inside the recommended band.

        Returns:
            True from the band's low end to its high end, inclusive.
        """
        return self.low <= value <= self.high


def _spec(key: Key, group: str, unit: Unit, *numbers: int | str, about: str) -> Spec:
    default, low, high = (Decimal(n) for n in numbers)
    return Spec(key, group, unit, default, low, high, about)


SPECS = (
    _spec(
        Key.EMI_GRACE_PERIOD,
        "Stage 1 · No revolving credit",
        Unit.DAYS,
        *(3, 0, 7),
        about="How many days past its EMI day a Loan payment can land before "
        "the EMI counts as overdue and Stage 1 is broken.",
    ),
    _spec(
        Key.STARTER_FUND,
        "Stage 2 · Starter fund",
        Unit.MONTHS,
        *(1, 1, 3),
        about="Months of outflow the Emergency Fund must hold to meet Stage 2: "
        "a first cushion before you buy cover and clear debt.",
    ),
    _spec(
        Key.LIFE_COVER_MULTIPLE,
        "Stage 3 · Protection",
        Unit.MULTIPLE,
        *(10, 7, 20),
        about="The term life cover you need, as a multiple of a year's "
        "Take-home, while a Dependent relies on your income.",
    ),
    _spec(
        Key.HEALTH_COVER_FLOOR,
        "Stage 3 · Protection",
        Unit.RUPEES,
        *(10 * LAKH, 5 * LAKH, CRORE),
        about="The least health cover you and every Dependent should have.",
    ),
    _spec(
        Key.HIGH_INTEREST_RATE,
        "Stage 4 · High-interest debt cleared",
        Unit.PERCENT,
        *(10, 8, 14),
        about="A Loan at or above this rate counts as high-interest. Stage 4 is "
        "met once none is open.",
    ),
    _spec(
        Key.EMERGENCY_FUND,
        "Stage 5 · Full Emergency Fund",
        Unit.MONTHS,
        *(6, 3, 12),
        about="Months of outflow the Emergency Fund must hold to meet Stage 5.",
    ),
    _spec(
        Key.EMI_CAP,
        "Watched · flagged, never holds you on a Stage",
        Unit.PERCENT,
        *(40, 30, 50),
        about="The most of your Take-home that Loan EMIs should take. Folio "
        "warns from 30% and flags anything past this cap.",
    ),
    _spec(
        Key.SAVINGS_RATE_TARGET,
        "Watched · flagged, never holds you on a Stage",
        Unit.PERCENT,
        *(20, 10, 60),
        about="The share of Take-home you aim to save. The Budget sets it aside "
        "before working out what's spendable.",
    ),
    _spec(
        Key.GENERAL_INFLATION,
        "Goals",
        Unit.PERCENT,
        *(6, 4, 9),
        about="How fast a Goal's target grows each year from today's rupees to "
        "its date, Retirement's included.",
    ),
    _spec(
        Key.MEDICAL_INFLATION,
        "Goals",
        Unit.PERCENT,
        *(12, 8, 15),
        about="The yearly growth for Goals set to medical inflation, such as "
        "future health costs.",
    ),
    _spec(
        Key.SAFE_WITHDRAWAL_RATE,
        "Retirement",
        Unit.PERCENT,
        *(3, "2.5", "3.5"),
        about="The share of the Retirement corpus you can draw each year. It "
        "sizes the Retirement target and, once retired, your Planned "
        "withdrawal.",
    ),
    _spec(
        Key.DECUMULATION_EQUITY,
        "Retirement",
        Unit.PERCENT,
        *(45, 30, 60),
        about="The equity share Retirement's money holds once its date passes.",
    ),
)

BY_KEY = {spec.key: spec for spec in SPECS}


def current() -> dict[Key, Decimal]:
    """Every threshold's current value: what you set, else its default.

    Returns:
        The values by key, in the Doctrine's order.
    """
    changed = dict(Threshold.objects.values_list("key", "value"))
    return {spec.key: changed.get(spec.key, spec.default) for spec in SPECS}


def threshold(key: Key) -> Decimal:
    """A threshold's current value: what you set, else its default.

    Args:
        key: Which threshold.

    Returns:
        The value, in the threshold's unit.
    """
    return current()[key]
