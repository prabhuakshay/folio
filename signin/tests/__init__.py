"""Sign-in tests, and helpers that give a test login its second factor."""

import time

from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.oath import TOTP
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp_webauthn.models import WebAuthnCredential


def add_authenticator(user):
    return TOTPDevice.objects.create(user=user, name="Authenticator app")


def add_passkey(user):
    return WebAuthnCredential.objects.create(
        user=user,
        name="Passkey",
        credential_id=b"credential-id",
        public_key=b"public-key",
        sign_count=0,
    )


def add_recovery_codes(user, *codes):
    device = StaticDevice.objects.create(user=user, name="Recovery codes")
    for code in codes:
        device.token_set.create(token=code)
    return device


def code_for(device, steps_ahead=0):
    """The authenticator's code now, or a later step's, which is still accepted.

    A code is accepted once, so a test signing in twice uses the next step's.
    """
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time() + steps_ahead * device.step
    return f"{totp.token():06d}"


def code_for_key(hex_key, steps_ahead=0):
    return code_for(TOTPDevice(key=hex_key), steps_ahead)


def verify(client, device):
    """Mark the client's signed-in session as having passed its second factor."""
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
