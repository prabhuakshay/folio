"""Passkey ceremonies: django-otp-webauthn's JSON views, held to Folio's rules."""

from typing import TYPE_CHECKING

from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.urls import path
from django_otp_webauthn import exceptions, views

from signin import events
from signin.factors import may_change_factors, start_sudo
from signin.middleware import second_factor_not_required

if TYPE_CHECKING:
    from django.http import JsonResponse
    from django_otp_webauthn.models import AbstractWebAuthnCredential

PASSKEY_BACKEND = "django_otp_webauthn.backends.WebAuthnBackend"


class SudoRequired(exceptions.OTPWebAuthnApiError):
    """Adding a passkey to a protected login needs a fresh check."""

    status_code = 403
    default_detail = "Confirm it's you before adding a passkey."
    default_code = "sudo_required"


class RegistrationRules:
    """The first passkey is added on the password alone; later ones need sudo mode.

    The library already refuses an unverified session once anything protects
    the login.
    """

    def check_can_register(self) -> None:
        """Refuse a protected login outside sudo mode.

        Raises:
            SudoRequired: The session isn't in sudo mode.
        """
        if not may_change_factors(self.request):
            raise SudoRequired


class BeginRegistration(RegistrationRules, views.BeginCredentialRegistrationView):
    """Start adding a passkey."""


class CompleteRegistration(RegistrationRules, views.CompleteCredentialRegistrationView):
    """Save the new passkey; the first one also verifies the session."""

    def post(self, *args: object, **kwargs: object) -> JsonResponse:
        """Save the passkey as the library does, and log it.

        Returns:
            The new passkey's id.
        """
        response = super().post(*args, **kwargs)
        events.record(self.request, events.Kind.PASSKEY_ADDED)
        return response


class CompleteAuthentication(views.CompleteCredentialAuthenticationView):
    """Sign in by passkey, or pass the second factor or sudo check with one."""

    def complete_auth(self, device: AbstractWebAuthnCredential) -> None:
        """Sign in and verify as the library does, and open sudo mode.

        The library signs in through `authenticate`, which django-axes refuses
        on a paused address. A passkey can't be guessed, so it isn't held to
        the pause.

        Args:
            device: The passkey just used.
        """
        user = self.request.user
        # Already verified, it's confirming it's them, not signing in.
        how = None if user.is_verified() else "Password and passkey"
        if not user.is_authenticated:
            how = "Passkey"
            login(self.request, device.user, backend=PASSKEY_BACKEND)
        super().complete_auth(device)
        start_sudo(self.request)
        if how:
            events.signed_in(self.request, how)


def _ceremony(view: type[views.BaseWebAuthnView], *, public: bool = False):  # noqa: ANN202
    func = second_factor_not_required(view.as_view())
    return login_not_required(func) if public else func


urlpatterns = [
    path(
        "register/begin/",
        _ceremony(BeginRegistration),
        name="passkey_register_begin",
    ),
    path(
        "register/complete/",
        _ceremony(CompleteRegistration),
        name="passkey_register_complete",
    ),
    path(
        "sign-in/begin/",
        _ceremony(views.BeginCredentialAuthenticationView, public=True),
        name="passkey_auth_begin",
    ),
    path(
        "sign-in/complete/",
        _ceremony(CompleteAuthentication, public=True),
        name="passkey_auth_complete",
    ),
]
