"""Claiming the install and signing in."""

from django.apps import AppConfig


class SigninConfig(AppConfig):
    """Sign-in configuration."""

    name = "signin"

    def ready(self) -> None:
        """Connect the security log to sign-in signals."""
        from signin import events  # noqa: F401, PLC0415
