"""Every browser signed in as the owner, and signing them out.

Sessions live in the database, and the owner is the only login, so the list is
read straight from the session table.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY

from signin import client

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.http import HttpRequest

IP = "signin.ip"
DEVICE = "signin.device"
SINCE = "signin.since"


@dataclass(frozen=True)
class ActiveSession:
    """One browser signed in as the owner."""

    key: str
    device: str
    ip: str
    since: datetime | None
    last_active: datetime
    verified: bool
    current: bool


def stamp(request: HttpRequest) -> None:
    """Note where and when this session signed in, for the sessions list."""
    request.session[IP] = client.ip_address(request)
    request.session[DEVICE] = client.device(request)
    request.session[SINCE] = timezone.now().timestamp()


def _sessions(user: AbstractBaseUser) -> list[tuple[Session, dict]]:
    sessions = Session.objects.filter(expire_date__gt=timezone.now())
    return [
        (session, data)
        for session in sessions
        if (data := session.get_decoded()).get(SESSION_KEY) == str(user.pk)
    ]


def active(request: HttpRequest) -> list[ActiveSession]:
    """Every session signed in as this request's user, this one first.

    Returns:
        The sessions, then most recently active first.
    """
    age = timedelta(seconds=settings.SESSION_COOKIE_AGE)
    current = request.session.session_key
    found = [
        ActiveSession(
            key=session.session_key,
            device=data.get(DEVICE, "Unknown device"),
            ip=data.get(IP, ""),
            since=(
                datetime.fromtimestamp(data[SINCE], tz=timezone.get_current_timezone())
                if SINCE in data
                else None
            ),
            # Every request pushes the expiry out by the session's age.
            last_active=session.expire_date - age,
            verified=DEVICE_ID_SESSION_KEY in data,
            current=session.session_key == current,
        )
        for session, data in _sessions(request.user)
    ]
    return sorted(found, key=lambda s: (not s.current, -s.last_active.timestamp()))


def sign_out_others(request: HttpRequest) -> None:
    """Sign out every session but this one."""
    keys = [
        session.session_key
        for session, _ in _sessions(request.user)
        if session.session_key != request.session.session_key
    ]
    Session.objects.filter(session_key__in=keys).delete()


def sign_out_everywhere(user: AbstractBaseUser) -> None:
    """Sign out every session."""
    keys = [session.session_key for session, _ in _sessions(user)]
    Session.objects.filter(session_key__in=keys).delete()
