"""Settings > Security and sign-in, every screen of it behind sudo mode."""

from functools import wraps
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.views.decorators.http import require_POST
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import default_key
from django_otp_webauthn.models import WebAuthnCredential

from signin import events, factors, sessions
from signin.models import SecurityEvent
from signin.views import AUTHENTICATOR_KEY

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse
    from django_otp.models import Device

LOG_LENGTH = 100
# Held from issuing to showing, so a reload can't issue another set.
NEW_RECOVERY_CODES = "signin.new_recovery_codes"
SCREEN = {"tab": "home", "back": "settings", "title": "Security and sign-in"}


def sudo_required(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Ask the owner to confirm it's them first, unless they just did.

    Returns:
        The guarded view.
    """

    @wraps(view)
    def guarded(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if factors.in_sudo(request):
            return view(request, *args, **kwargs)
        # A form posted here can't be replayed after confirming; Security can.
        target = (
            request.get_full_path() if request.method == "GET" else reverse("security")
        )
        return redirect_to_login(target, "confirm")

    return guarded


@sudo_required
def security(request: HttpRequest) -> HttpResponse:
    """Passkeys, password, authenticator app, recovery codes, sessions and the log.

    Args:
        request: The incoming request.

    Returns:
        The screen.
    """
    user = request.user
    return render(
        request,
        "signin/security.html",
        {
            **SCREEN,
            "passkeys": factors.passkeys(user),
            "authenticator": factors.authenticator(user),
            "codes_left": factors.recovery_codes_left(user),
            "sessions": len(sessions.active(request)),
        },
    )


@sudo_required
def password(request: HttpRequest) -> HttpResponse:
    """Change the password, keeping this session signed in.

    Args:
        request: The incoming request.

    Returns:
        The form, or a redirect to Security once changed.
    """
    form = PasswordChangeForm(request.user, request.POST or None)
    if form.is_valid():
        update_session_auth_hash(request, form.save())
        sessions.sign_out_others(request)
        events.record(request, events.Kind.PASSWORD_CHANGED)
        messages.success(request, "Password changed.")
        return redirect("security")
    return render(
        request,
        "signin/password.html",
        {**SCREEN, "back": "security", "title": "Password", "form": form},
    )


@require_POST
@sudo_required
def regenerate_recovery_codes(request: HttpRequest) -> HttpResponse:
    """Replace the recovery codes, keeping the new ones to be shown once.

    Args:
        request: The incoming request.

    Returns:
        A redirect to the new codes, so a reload can't issue another set.
    """
    request.session[NEW_RECOVERY_CODES] = factors.issue_recovery_codes(request.user)
    events.record(request, events.Kind.RECOVERY_CODES_ISSUED)
    return redirect("new_recovery_codes")


@sudo_required
def new_recovery_codes(request: HttpRequest) -> HttpResponse:
    """The recovery codes just made, shown this once.

    Args:
        request: The incoming request.

    Returns:
        The codes, or a redirect to Security once they have been shown.
    """
    codes = request.session.pop(NEW_RECOVERY_CODES, None)
    if codes is None:
        return redirect("security")
    return render(
        request,
        "signin/new_recovery_codes.html",
        {**SCREEN, "back": "security", "title": "Recovery codes", "codes": codes},
    )


@require_POST
@sudo_required
def start_authenticator(request: HttpRequest) -> HttpResponse:
    """Begin setting up an authenticator app, new or replacing the one there is.

    Args:
        request: The incoming request.

    Returns:
        A redirect to the setup, with a new key to scan.
    """
    request.session[AUTHENTICATOR_KEY] = default_key()
    return redirect("authenticator")


def _keep_one(request: HttpRequest, other: str) -> bool:
    if factors.ways_to_sign_in(request.user) > 1:
        return True
    messages.error(
        request, f"This is the only way to sign in. Add {other} first, then remove it."
    )
    return False


def _remove(request: HttpRequest, device: Device) -> None:
    verified_by_it = request.user.otp_device == device
    device.delete()
    # The session stays verified by a way to sign in that's still there.
    if verified_by_it:
        remaining = (
            factors.authenticator(request.user) or factors.passkeys(request.user)[0]
        )
        otp_login(request, remaining)


@require_POST
@sudo_required
def remove_authenticator(request: HttpRequest) -> HttpResponse:
    """Remove the authenticator app, unless nothing else would sign in.

    Args:
        request: The incoming request.

    Returns:
        A redirect to Security.
    """
    if _keep_one(request, "a passkey"):
        _remove(request, factors.authenticator(request.user))
        events.record(request, events.Kind.AUTHENTICATOR_REMOVED)
        messages.success(request, "Authenticator app removed.")
    return redirect("security")


@require_POST
@sudo_required
def remove_passkey(request: HttpRequest, pk: int) -> HttpResponse:
    """Remove a passkey, unless nothing else would sign in.

    Args:
        request: The incoming request.
        pk: The passkey.

    Returns:
        A redirect to Security.
    """
    passkey = get_object_or_404(WebAuthnCredential, pk=pk, user=request.user)
    if _keep_one(request, "another passkey or an authenticator app"):
        _remove(request, passkey)
        events.record(request, events.Kind.PASSKEY_REMOVED)
        messages.success(request, "Passkey removed.")
    return redirect("security")


@sudo_required
def signed_in_sessions(request: HttpRequest) -> HttpResponse:
    """Every device signed in, with Sign out everywhere else.

    Args:
        request: The incoming request.

    Returns:
        The screen.
    """
    return render(
        request,
        "signin/sessions.html",
        {
            **SCREEN,
            "back": "security",
            "title": "Sessions",
            "sessions": sessions.active(request),
        },
    )


@require_POST
@sudo_required
def sign_out_others(request: HttpRequest) -> HttpResponse:
    """Sign out every device but this one.

    Args:
        request: The incoming request.

    Returns:
        A redirect to Sessions.
    """
    sessions.sign_out_others(request)
    events.record(request, events.Kind.SIGNED_OUT_ELSEWHERE)
    messages.success(request, "Signed out everywhere else.")
    return redirect("sessions")


@sudo_required
def security_log(request: HttpRequest) -> HttpResponse:
    """The latest entries in the security log, newest first.

    Args:
        request: The incoming request.

    Returns:
        The screen.
    """
    return render(
        request,
        "signin/security_log.html",
        {
            **SCREEN,
            "back": "security",
            "title": "Security log",
            "events": SecurityEvent.objects.all()[:LOG_LENGTH],
        },
    )


urlpatterns = [
    path("", security, name="security"),
    path("password/", password, name="password"),
    path(
        "recovery-codes/",
        regenerate_recovery_codes,
        name="recovery_codes_regenerate",
    ),
    path("recovery-codes/new/", new_recovery_codes, name="new_recovery_codes"),
    path("authenticator/start/", start_authenticator, name="authenticator_start"),
    path(
        "authenticator/remove/",
        remove_authenticator,
        name="authenticator_remove",
    ),
    path("passkeys/<int:pk>/remove/", remove_passkey, name="passkey_remove"),
    path("sessions/", signed_in_sessions, name="sessions"),
    path("sessions/sign-out-others/", sign_out_others, name="sign_out_others"),
    path("log/", security_log, name="security_log"),
]
