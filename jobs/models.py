"""The run log."""

from django.db import models


class RunQuerySet(models.QuerySet):
    """Queries over the run log."""

    def last_success(self, command: str) -> Run | None:
        """The command's latest run that succeeded.

        Returns:
            The run, or None if it has never succeeded.
        """
        return (
            self.filter(command=command, outcome=Run.Outcome.SUCCEEDED)
            .order_by("-started_at", "-pk")
            .first()
        )

    def consecutive_failures(self, command: str) -> int:
        """How many times running the command has failed since it last succeeded.

        Returns:
            The count; 0 if its latest finished run succeeded.
        """
        failures = self.filter(command=command, outcome=Run.Outcome.FAILED)
        if last := self.last_success(command):
            failures = failures.filter(started_at__gt=last.started_at)
        return failures.count()


class Run(models.Model):
    """One run of a scheduled command."""

    class Outcome(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    command = models.CharField(max_length=64)
    started_at = models.DateTimeField(db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=16, choices=Outcome, default=Outcome.RUNNING)
    summary = models.CharField(max_length=200, blank=True)
    error = models.TextField(blank=True)

    objects = RunQuerySet.as_manager()

    class Meta:
        ordering = ["-started_at", "-pk"]
        indexes = [models.Index(fields=["command", "-started_at"])]

    def __str__(self) -> str:
        return f"{self.command} at {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def label(self) -> str:
        """The command's name as words, such as `Fetch prices`."""
        return self.command.replace("_", " ").capitalize()
