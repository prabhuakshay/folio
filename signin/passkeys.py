"""Passkey ceremonies: django-otp-webauthn's JSON views, held to Folio's rules."""

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_not_required
from django.urls import path
from django_otp_webauthn import exceptions, views

from signin.factors import may_change_factors, start_sudo
from signin.middleware import second_factor_not_required

if TYPE_CHECKING:
    from django_otp_webauthn.models import AbstractWebAuthnCredential


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


class CompleteAuthentication(views.CompleteCredentialAuthenticationView):
    """Sign in by passkey, or pass the second factor or sudo check with one."""

    def complete_auth(self, device: AbstractWebAuthnCredential) -> None:
        """Sign in and verify as the library does, and open sudo mode.

        Args:
            device: The passkey just used.
        """
        super().complete_auth(device)
        start_sudo(self.request)


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
