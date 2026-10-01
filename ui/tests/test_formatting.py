import datetime as dt
from decimal import Decimal

import pytest
from django.template import Context, Template

from ui.formatting import group_indian, indian_date, short_indian

CUR = '<span class="cur">₹</span>'


def render(source, **context):
    return Template("{% load folio %}" + source).render(Context(context))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0"),
        (7, "7"),
        (999, "999"),
        (1000, "1,000"),
        (123456, "1,23,456"),
        (1234567, "12,34,567"),
        (123456789, "12,34,56,789"),
        (Decimal("123456.50"), "1,23,456.50"),
        (Decimal("123456.00"), "1,23,456"),
        (Decimal("0.05"), "0.05"),
        (Decimal(-123456), "1,23,456"),
    ],
)
def test_group_indian(value, expected):
    assert group_indian(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("7480.40"), "7,480"),
        (Decimal("99999.49"), "99,999"),
        (100000, "1.00 L"),
        (5885000, "58.85 L"),
        (Decimal(9999999), "1.00 Cr"),
        (10000000, "1.00 Cr"),
        (54000000, "5.40 Cr"),
        (1234500000, "123.45 Cr"),
        (-5885000, "58.85 L"),
    ],
)
def test_short_indian(value, expected):
    assert short_indian(value) == expected


def test_amount_shows_a_small_rupee_and_indian_grouping():
    assert render("{% inr v %}", v=Decimal(123456)) == f"{CUR}1,23,456"


def test_negative_balance_keeps_its_minus():
    assert render("{% inr v %}", v=Decimal(-5000)) == f"\N{MINUS SIGN}{CUR}5,000"


def test_summary_amount_uses_lakh_and_crore():
    assert render("{% inr v short=True %}", v=Decimal(5885000)) == f"{CUR}58.85 L"


def test_expense_is_plain_ink_without_minus():
    assert render("{% inr v flow=True %}", v=Decimal(-450)) == f"{CUR}450"


def test_income_is_green_with_plus():
    assert (
        render("{% inr v flow=True %}", v=Decimal(85000))
        == f'<span class="text-positive">+{CUR}85,000</span>'
    )


def test_indian_date():
    assert indian_date(dt.date(2026, 10, 1)) == "1 Oct 2026"


def test_indian_date_without_year():
    assert indian_date(dt.date(2026, 3, 14), year=False) == "14 Mar"


def test_indian_date_reads_datetimes_in_india():
    late_utc = dt.datetime(2026, 9, 30, 20, 0, tzinfo=dt.UTC)
    assert indian_date(late_utc) == "1 Oct 2026"


def test_indian_date_filter():
    day = dt.date(2026, 3, 14)
    assert render("{{ d|indian_date }}", d=day) == "14 Mar 2026"
    assert render("{{ d|indian_date:'short' }}", d=day) == "14 Mar"
