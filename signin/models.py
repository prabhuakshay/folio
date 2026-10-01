"""The security log."""

from django.db import models
from django.utils import timezone


class SecurityEvent(models.Model):
    """Something that happened to how Folio is signed in to, kept forever.

    Addresses are kept as text: behind a proxy they come from a header, and an
    odd one mustn't stop a sign-in being logged.
    """

    class Kind(models.TextChoices):
        SIGNED_IN = "signed_in", "Signed in"
        WRONG_PASSWORD = "wrong_password", "Wrong email or password"
        WRONG_CODE = "wrong_code", "Wrong code"
        PAUSED = "paused", "Signing in paused for an hour"
        PASSKEY_ADDED = "passkey_added", "Passkey added"
        PASSKEY_REMOVED = "passkey_removed", "Passkey removed"
        AUTHENTICATOR_SET_UP = "authenticator_set_up", "Authenticator app set up"
        AUTHENTICATOR_REMOVED = "authenticator_removed", "Authenticator app removed"
        RECOVERY_CODES_ISSUED = "recovery_codes_issued", "New recovery codes"
        PASSWORD_CHANGED = "password_changed", "Password changed"
        SIGNED_OUT_ELSEWHERE = "signed_out_elsewhere", "Signed out everywhere else"
        RESET_ON_SERVER = "reset_on_server", "Reset on the server"
        EXPORTED = "exported", "Everything exported"

    at = models.DateTimeField(default=timezone.now, db_index=True)
    kind = models.CharField(max_length=32, choices=Kind)
    detail = models.CharField(max_length=100, blank=True)
    ip = models.CharField(max_length=64, blank=True)
    device = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-at", "-pk"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} at {self.at:%Y-%m-%d %H:%M}"
