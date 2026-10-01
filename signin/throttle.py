"""Wrong codes count toward django-axes' pause on an address, as wrong passwords do."""

from typing import TYPE_CHECKING

from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_lockout_response
from django.contrib.auth.signals import user_login_failed

from signin import events

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.http import HttpRequest, HttpResponse


def paused(request: HttpRequest) -> HttpResponse | None:
    """Refuse a request from an address paused for too many wrong tries.

    Returns:
        The pause page, or None when the address may try.
    """
    if AxesProxyHandler.is_allowed(request):
        return None
    return get_lockout_response(request)


def wrong_code(request: HttpRequest, user: AbstractBaseUser) -> None:
    """Count a wrong authenticator or recovery code against the address."""
    user_login_failed.send(
        sender=__name__,
        credentials={"username": user.get_username()},
        request=request,
    )
    events.failed(request, events.Kind.WRONG_CODE)
