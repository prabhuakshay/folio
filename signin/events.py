"""The security log, and the email a sign-in from somewhere new sends."""

import logging
from typing import TYPE_CHECKING

from axes.signals import user_locked_out
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from signin import client, sessions
from signin.models import SecurityEvent

if TYPE_CHECKING:
    from django.http import HttpRequest

Kind = SecurityEvent.Kind
logger = logging.getLogger(__name__)


def record(
    request: HttpRequest | None, kind: SecurityEvent.Kind, detail: str = ""
) -> SecurityEvent:
    """Add an entry to the security log.

    Args:
        request: The request it happened in, for its address and device; None
            for what happens on the server.
        kind: What happened.
        detail: More about it, such as how a sign-in was made.

    Returns:
        The entry.
    """
    return SecurityEvent.objects.create(
        kind=kind,
        detail=detail,
        ip=client.ip_address(request)[:64] if request else "",
        device=client.device(request) if request else "",
    )


def failed(request: HttpRequest, kind: SecurityEvent.Kind) -> None:
    """Log a wrong password or code, unless it paused the address.

    The pause has its own entry, which says as much.
    """
    if not getattr(request, "axes_locked_out", False):
        record(request, kind)


def signed_in(request: HttpRequest, how: str) -> None:
    """Log a finished sign-in, and email the owner if it's from somewhere new.

    Somewhere new is an address or a device no earlier sign-in came from.

    Args:
        request: The request that finished signing in.
        how: Such as `Passkey`.
    """
    earlier = SecurityEvent.objects.filter(kind=Kind.SIGNED_IN)
    new = (
        not earlier.filter(ip=client.ip_address(request)).exists()
        or not earlier.filter(device=client.device(request)).exists()
    )
    event = record(request, Kind.SIGNED_IN, how)
    if new:
        _email_new_sign_in(request, event)


def _email_new_sign_in(request: HttpRequest, event: SecurityEvent) -> None:
    body = render_to_string(
        "signin/new_sign_in_email.txt",
        {
            "event": event,
            "sessions_url": request.build_absolute_uri(reverse("sessions")),
        },
    )
    try:
        send_mail("New sign-in to Folio", body, None, [request.user.email])
    except OSError:
        # The owner is signed in either way; a mail outage mustn't stop that.
        logger.exception("Couldn't send the new sign-in email")


@receiver(user_logged_in)
def _stamp_session(request: HttpRequest, **_: object) -> None:
    sessions.stamp(request)


@receiver(user_locked_out)
def _log_pause(request: HttpRequest, **_: object) -> None:
    # Axes signals again on every try refused during the pause.
    pause_began = timezone.now() - settings.AXES_COOLOFF_TIME
    if not SecurityEvent.objects.filter(
        kind=Kind.PAUSED, ip=client.ip_address(request), at__gt=pause_began
    ).exists():
        record(request, Kind.PAUSED)
