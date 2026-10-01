"""Scheduled commands and the run log they keep."""

from django.apps import AppConfig


class JobsConfig(AppConfig):
    """Scheduled-work configuration."""

    name = "jobs"
