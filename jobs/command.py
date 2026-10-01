"""The base every scheduled command is built on."""

import traceback
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Run

if TYPE_CHECKING:
    from datetime import datetime


class ScheduledCommand(BaseCommand):
    """A management command the scheduler runs, logging each run.

    The scheduler doesn't catch up after downtime and may run a command again
    at any time, so a subclass works out from the database what is due since
    its last success and must be safe to repeat.
    """

    def run(self, since: datetime | None) -> str:
        """Do whatever is due.

        Args:
            since: When the last successful run started, or None if there has
                never been one.

        Returns:
            A one-line summary for the run log.
        """
        raise NotImplementedError

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        """Run, logging its start, end, outcome, summary and any error.

        A failure is raised again once logged, so the scheduler sees it too.
        """
        name = self.__module__.rpartition(".")[2]
        # The scheduler never overlaps a command with itself, so a run still
        # open now was killed before it could log how it ended.
        Run.objects.filter(command=name, outcome=Run.Outcome.RUNNING).update(
            outcome=Run.Outcome.FAILED, error="Stopped before it finished."
        )
        last = Run.objects.last_success(name)
        run = Run.objects.create(command=name, started_at=timezone.now())
        try:
            run.summary = self.run(last.started_at if last else None)
        except BaseException:
            run.outcome = Run.Outcome.FAILED
            run.error = traceback.format_exc()
            raise
        else:
            run.outcome = Run.Outcome.SUCCEEDED
            self.stdout.write(run.summary)
        finally:
            run.finished_at = timezone.now()
            run.save()
