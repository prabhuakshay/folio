import contextlib

import pytest
from django.core.management import call_command

from jobs.command import ScheduledCommand
from jobs.models import Run

Outcome = Run.Outcome


class Tidy(ScheduledCommand):
    def run(self, since):
        return "Tidied 3 things"


@pytest.mark.django_db
def test_a_run_is_logged_with_its_summary(clock):
    started = clock.now

    call_command(Tidy())

    run = Run.objects.get()
    assert run.command == "test_scheduled_command"
    assert run.outcome == Outcome.SUCCEEDED
    assert run.summary == "Tidied 3 things"
    assert run.started_at == started
    assert run.finished_at == started
    assert run.error == ""


class Broken(ScheduledCommand):
    def run(self, since):
        msg = "the feed is down"
        raise ConnectionError(msg)


class Remembers(ScheduledCommand):
    def __init__(self, *, fails=False):
        super().__init__()
        self.fails = fails
        self.since = "never asked"

    def run(self, since):
        self.since = since
        if self.fails:
            raise RuntimeError
        return ""


@pytest.mark.django_db
def test_a_failed_run_is_logged_with_its_error_and_still_fails(clock):
    started = clock.now

    with pytest.raises(ConnectionError):
        call_command(Broken())

    run = Run.objects.get()
    assert run.outcome == Outcome.FAILED
    assert run.finished_at == started
    assert "ConnectionError: the feed is down" in run.error


@pytest.mark.django_db
def test_a_first_run_has_nothing_to_count_from():
    command = Remembers()

    call_command(command)

    assert command.since is None


@pytest.mark.django_db
def test_a_run_counts_from_when_the_last_success_started(clock):
    succeeded_at = clock.now
    call_command(Remembers())
    clock.advance(hours=1)
    with pytest.raises(RuntimeError):
        call_command(Remembers(fails=True))
    clock.advance(hours=1)

    command = Remembers()
    call_command(command)

    assert command.since == succeeded_at


def run_as(name, command):
    command.__module__ = f"jobs.management.commands.{name}"
    with contextlib.suppress(RuntimeError):
        call_command(command)


@pytest.mark.django_db
def test_failures_are_counted_since_the_last_success(clock):
    for fails in [True, False, True, True]:
        clock.advance(minutes=1)
        run_as("fetch_prices", Remembers(fails=fails))
    run_as("send_digest", Remembers(fails=True))

    assert Run.objects.consecutive_failures("fetch_prices") == 2


@pytest.mark.django_db
def test_failures_are_counted_from_the_start_when_nothing_succeeded(clock):
    for _ in range(3):
        clock.advance(minutes=1)
        run_as("fetch_prices", Remembers(fails=True))

    assert Run.objects.consecutive_failures("fetch_prices") == 3


@pytest.mark.django_db
def test_a_success_clears_the_failures(clock):
    for fails in [True, True, False]:
        clock.advance(minutes=1)
        run_as("fetch_prices", Remembers(fails=fails))

    assert Run.objects.consecutive_failures("fetch_prices") == 0


@pytest.mark.django_db
def test_a_run_killed_before_it_finished_is_failed_by_the_next(clock):
    killed = Run.objects.create(command="fetch_prices", started_at=clock.now)
    clock.advance(hours=1)

    run_as("fetch_prices", Remembers(fails=True))

    killed.refresh_from_db()
    assert killed.outcome == Outcome.FAILED
    assert killed.error == "Stopped before it finished."
    assert Run.objects.consecutive_failures("fetch_prices") == 2
