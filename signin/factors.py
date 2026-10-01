"""What protects the login beyond its password, and sudo mode.

The owner signs in with a passkey alone, or with their password and a code
from an authenticator app (or, when that's lost, a recovery code). Sudo mode is
a fresh passkey or authenticator check, good for 10 minutes, that guards
changing any of these.
"""

import time
from typing import TYPE_CHECKING

from django.utils import timezone
from django_otp.oath import TOTP
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp_webauthn.models import WebAuthnCredential

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.http import HttpRequest
    from django_otp.models import Device

RECOVERY_CODES = 10
SUDO_SECONDS = 10 * 60
SUDO_UNTIL = "signin.sudo_until"
AUTHENTICATOR_DIGITS = 6


def passkeys(user: AbstractBaseUser) -> list[WebAuthnCredential]:
    """The owner's passkeys, newest first.

    Returns:
        The confirmed passkeys.
    """
    return list(
        WebAuthnCredential.objects.filter(user=user, confirmed=True).order_by(
            "-created_at"
        )
    )


def authenticator(user: AbstractBaseUser) -> TOTPDevice | None:
    """The owner's authenticator app, if one is set up.

    Returns:
        The device, or None.
    """
    return TOTPDevice.objects.filter(user=user, confirmed=True).first()


def ways_to_sign_in(user: AbstractBaseUser) -> int:
    """Count the passkeys and authenticator apps that can complete a sign-in.

    Recovery codes don't count: they are a fallback, not a way to sign in.

    Returns:
        How many there are.
    """
    return len(passkeys(user)) + (authenticator(user) is not None)


def matching_device(
    user: AbstractBaseUser, code: str, *, recovery: bool
) -> Device | None:
    """Check a typed code against the authenticator app and recovery codes.

    A recovery code is used up by matching.

    Args:
        user: Whose devices to check.
        code: What was typed; case, spaces and dashes are ignored.
        recovery: Whether a recovery code may stand in for the authenticator.

    Returns:
        The device the code matched, or None.
    """
    code = "".join(c for c in code.lower() if c.isalnum())
    if code.isdigit() and len(code) == AUTHENTICATOR_DIGITS:
        device = authenticator(user)
        return device if device and device.verify_token(code) else None
    if recovery:
        for device in StaticDevice.objects.filter(user=user, confirmed=True):
            if device.verify_token(code):
                return device
    return None


def new_authenticator(user: AbstractBaseUser, key: str) -> TOTPDevice:
    """An unsaved authenticator app for the key the owner is scanning.

    Returns:
        The device, not yet saved.
    """
    return TOTPDevice(user=user, key=key, name="Authenticator app")


def confirm_authenticator(device: TOTPDevice, code: str) -> bool:
    """Save a new authenticator app once it shows a right code, replacing any old one.

    The check is done by hand rather than with `verify_token`, which would save
    the device on a wrong code too.

    Returns:
        Whether the code was right and the device saved.
    """
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time()
    code = "".join(c for c in code if c.isdigit())
    if not code or not totp.verify(int(code), device.tolerance):
        return False
    # The code just used can't be used again to sign in.
    device.last_t = totp.t()
    TOTPDevice.objects.filter(user=device.user).delete()
    device.save()
    return True


def has_recovery_codes(user: AbstractBaseUser) -> bool:
    """Whether recovery codes were ever issued, used up or not.

    Returns:
        True once they have been.
    """
    return StaticDevice.objects.filter(user=user).exists()


def recovery_codes_left(user: AbstractBaseUser) -> int:
    """Count the recovery codes not yet used.

    Returns:
        How many are left.
    """
    return StaticToken.objects.filter(device__user=user).count()


def issue_recovery_codes(user: AbstractBaseUser) -> list[str]:
    """Replace every recovery code with a new set.

    Returns:
        The new codes, to be shown once.
    """
    device, _ = StaticDevice.objects.get_or_create(
        user=user, defaults={"name": "Recovery codes"}
    )
    device.token_set.all().delete()
    codes = [StaticToken.random_token() for _ in range(RECOVERY_CODES)]
    StaticToken.objects.bulk_create(
        StaticToken(device=device, token=code) for code in codes
    )
    return codes


def start_sudo(request: HttpRequest) -> None:
    """Open sudo mode for the next 10 minutes."""
    request.session[SUDO_UNTIL] = timezone.now().timestamp() + SUDO_SECONDS


def in_sudo(request: HttpRequest) -> bool:
    """Whether the owner confirmed it's them in the last 10 minutes.

    Returns:
        True while sudo mode is open.
    """
    return timezone.now().timestamp() < request.session.get(SUDO_UNTIL, 0)


def may_change_factors(request: HttpRequest) -> bool:
    """Whether this session may add a way to sign in.

    The first is added straight after claiming, on the password alone; after
    that only a verified session in sudo mode may.

    Returns:
        True when it may.
    """
    if not ways_to_sign_in(request.user):
        return True
    return request.user.is_verified() and in_sudo(request)
