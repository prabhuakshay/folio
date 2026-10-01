from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils.html import escape

from doctrine.models import Threshold
from doctrine.thresholds import SPECS, Key, threshold
from signin.tests import add_authenticator, verify
from ui.tests import closes_from_its_header


@pytest.fixture
def signed_in(client, django_user_model):
    owner = django_user_model.objects.create_user("akshay")
    client.force_login(owner)
    verify(client, add_authenticator(owner))
    return client


def edit(client, key, value):
    return client.post(reverse("threshold", args=[key]), {"value": value})


def test_twelve_thresholds_in_the_spec_order():
    assert [s.label for s in SPECS] == [
        "EMI grace period",
        "Starter fund",
        "Life cover multiple",
        "Health cover floor",
        "High-interest rate",
        "Emergency Fund",
        "EMI cap",
        "Savings-rate target",
        "General inflation",
        "Medical inflation",
        "Safe Withdrawal Rate",
        "Decumulation equity",
    ]


@pytest.mark.django_db
def test_every_threshold_says_what_it_does(signed_in):
    text = signed_in.get(reverse("thresholds")).text

    for spec in SPECS:
        assert spec.about
        assert text.count(escape(spec.about)) == 2  # on its row and in its sheet


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("key", "default"),
    [
        (Key.EMI_GRACE_PERIOD, Decimal(3)),
        (Key.HEALTH_COVER_FLOOR, Decimal(10_00_000)),
        (Key.SAFE_WITHDRAWAL_RATE, Decimal(3)),
    ],
)
def test_an_untouched_threshold_reads_its_default(key, default):
    assert threshold(key) == default


@pytest.mark.django_db
def test_settings_shows_the_thresholds_row(signed_in):
    response = signed_in.get(reverse("settings"))

    assert f'href="{reverse("thresholds")}"' in response.text
    assert "All at default" in response.text


@pytest.mark.django_db
def test_the_screen_lists_every_threshold_with_its_value(signed_in):
    response = signed_in.get(reverse("thresholds"))

    text = response.text
    assert response.status_code == 200
    assert text.index("Stage 1 · No revolving credit") < text.index("EMI grace period")
    assert text.index("Retirement") < text.index("Decumulation equity")
    assert "3 days" in text
    assert "₹10L" in text
    assert "2.5\N{EN DASH}3.5%" in text
    assert "Outside the recommended" not in text


@pytest.mark.django_db
def test_editing_a_threshold_changes_what_it_reads(signed_in):
    response = edit(signed_in, Key.EMERGENCY_FUND, "9")

    assert response.status_code == 302
    assert threshold(Key.EMERGENCY_FUND) == Decimal(9)
    page = signed_in.get(reverse("thresholds")).text
    assert "9 months" in page
    assert "Outside the recommended" not in page
    assert "1 changed" in signed_in.get(reverse("settings")).text


@pytest.mark.django_db
def test_a_value_outside_the_band_is_kept_with_a_warning(signed_in):
    edit(signed_in, Key.SAFE_WITHDRAWAL_RATE, "5")

    assert threshold(Key.SAFE_WITHDRAWAL_RATE) == Decimal(5)
    page = signed_in.get(reverse("thresholds")).text
    assert "Outside the recommended 2.5\N{EN DASH}3.5%" in page


@pytest.mark.django_db
def test_any_number_is_kept_even_a_negative_one(signed_in):
    edit(signed_in, Key.EMI_GRACE_PERIOD, "-1")

    assert threshold(Key.EMI_GRACE_PERIOD) == Decimal(-1)
    assert "Outside the recommended" in signed_in.get(reverse("thresholds")).text


@pytest.mark.django_db
def test_the_sheet_shows_a_saved_value_without_trailing_zeros(signed_in):
    edit(signed_in, Key.SAFE_WITHDRAWAL_RATE, "2.50")

    assert 'value="2.5"' in signed_in.get(reverse("thresholds")).text


@pytest.mark.django_db
def test_setting_the_default_again_counts_as_unchanged(signed_in):
    edit(signed_in, Key.EMERGENCY_FUND, "9")
    edit(signed_in, Key.EMERGENCY_FUND, "6")

    assert not Threshold.objects.exists()
    assert "All at default" in signed_in.get(reverse("settings")).text


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["", "lots"])
def test_a_value_that_isnt_a_number_is_refused(signed_in, value):
    response = edit(signed_in, Key.STARTER_FUND, value)

    assert response.status_code == 200
    assert threshold(Key.STARTER_FUND) == Decimal(1)
    assert "data-open" in response.text
    assert f'value="{value}"' in response.text


@pytest.mark.django_db
def test_an_unknown_threshold_is_not_found(signed_in):
    assert edit(signed_in, "nonsense", "1").status_code == 404


@pytest.mark.django_db
def test_reset_to_default(signed_in):
    edit(signed_in, Key.GENERAL_INFLATION, "7")
    edit(signed_in, Key.MEDICAL_INFLATION, "14")

    signed_in.post(reverse("threshold_reset", args=[Key.GENERAL_INFLATION]))

    assert threshold(Key.GENERAL_INFLATION) == Decimal(6)
    assert threshold(Key.MEDICAL_INFLATION) == Decimal(14)


@pytest.mark.django_db
def test_reset_all(signed_in):
    edit(signed_in, Key.GENERAL_INFLATION, "7")
    edit(signed_in, Key.EMI_CAP, "45")

    signed_in.post(reverse("thresholds_reset"))

    assert threshold(Key.GENERAL_INFLATION) == Decimal(6)
    assert threshold(Key.EMI_CAP) == Decimal(40)


@pytest.mark.django_db
def test_changes_are_audited(signed_in):
    edit(signed_in, Key.HIGH_INTEREST_RATE, "12")
    edit(signed_in, Key.HIGH_INTEREST_RATE, "11")
    signed_in.post(reverse("thresholds_reset"))

    history = Threshold.history.filter(key=Key.HIGH_INTEREST_RATE).order_by(
        "history_date"
    )
    assert [(h.history_type, h.value) for h in history] == [
        ("+", Decimal(12)),
        ("~", Decimal(11)),
        ("-", Decimal(11)),
    ]
    assert all(h.history_user is not None for h in history)


@pytest.mark.django_db
def test_every_sheet_closes_from_its_header(signed_in):
    edit(signed_in, Key.EMERGENCY_FUND, "9")
    page = signed_in.get(reverse("thresholds")).text

    for spec in SPECS:
        assert closes_from_its_header(page, f"sheet-{spec.key}")
