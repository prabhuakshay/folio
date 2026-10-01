from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from jobs.models import Run
from signin.tests import add_authenticator, verify

Outcome = Run.Outcome


@pytest.fixture
def signed_in(client, django_user_model):
    owner = django_user_model.objects.create_user("akshay")
    client.force_login(owner)
    verify(client, add_authenticator(owner))
    return client


def logged(command, outcome, minutes_ago, **fields):
    started_at = timezone.now() - timedelta(minutes=minutes_ago)
    return Run.objects.create(
        command=command,
        outcome=outcome,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=4),
        **fields,
    )


@pytest.mark.django_db
def test_settings_leads_to_price_feeds(signed_in):
    response = signed_in.get(reverse("settings"))

    assert f'href="{reverse("price_feeds")}"' in response.text


@pytest.mark.django_db
def test_the_run_log_is_shown_newest_first(signed_in):
    logged("prune_run_log", Outcome.SUCCEEDED, 30, summary="Removed 3 runs")
    logged(
        "fetch_prices",
        Outcome.FAILED,
        5,
        error="Traceback …\nConnectionError: AMFI is down",
    )

    response = signed_in.get(reverse("price_feeds"))

    text = response.text
    assert response.status_code == 200
    assert text.index("Fetch prices") < text.index("Prune run log")
    assert "Removed 3 runs" in text
    assert "ConnectionError: AMFI is down" in text


@pytest.mark.django_db
def test_the_run_log_says_when_nothing_has_run(signed_in):
    response = signed_in.get(reverse("price_feeds"))

    assert "Nothing has run yet." in response.text
