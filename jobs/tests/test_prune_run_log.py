from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from jobs.models import Run

Outcome = Run.Outcome


def logged(command, outcome, days_ago):
    return Run.objects.create(
        command=command,
        outcome=outcome,
        started_at=timezone.now() - timedelta(days=days_ago),
    )


def kept():
    return set(
        Run.objects.exclude(command="prune_run_log").values_list("pk", flat=True)
    )


@pytest.mark.django_db
def test_runs_older_than_90_days_are_removed(clock):
    recent = logged("send_digest", Outcome.FAILED, 89)
    logged("send_digest", Outcome.FAILED, 91)
    latest = logged("send_digest", Outcome.SUCCEEDED, 1)

    call_command("prune_run_log")

    assert kept() == {recent.pk, latest.pk}
    assert Run.objects.get(command="prune_run_log").summary == "Removed 1 run"


@pytest.mark.django_db
def test_a_commands_latest_success_is_kept_however_old(clock):
    logged("fetch_prices", Outcome.SUCCEEDED, 120)
    last_success = logged("fetch_prices", Outcome.SUCCEEDED, 100)
    logged("fetch_prices", Outcome.FAILED, 95)
    failing = logged("fetch_prices", Outcome.FAILED, 10)

    call_command("prune_run_log")

    assert kept() == {last_success.pk, failing.pk}
    assert Run.objects.consecutive_failures("fetch_prices") == 1
