"""Remove run-log entries older than 90 days."""

from datetime import datetime, timedelta

from django.utils import timezone

from jobs.command import ScheduledCommand
from jobs.models import Run

KEEP_FOR = timedelta(days=90)


class Command(ScheduledCommand):
    """Remove run-log entries older than 90 days."""

    help = "Remove run-log entries older than 90 days."

    def run(self, since: datetime | None) -> str:  # noqa: ARG002
        """Remove them, keeping each command's latest success.

        A command works out what is due from its latest success, so losing it
        would make the command start over as if it had never run.

        Returns:
            How many were removed.
        """
        commands = Run.objects.values_list("command", flat=True).distinct()
        latest = [Run.objects.last_success(command) for command in commands]
        removed, _ = (
            Run.objects.filter(started_at__lt=timezone.now() - KEEP_FOR)
            .exclude(pk__in=[run.pk for run in latest if run])
            .delete()
        )
        return f"Removed {removed} run{'' if removed == 1 else 's'}"
