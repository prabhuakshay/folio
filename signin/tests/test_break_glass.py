import re
from io import StringIO

import pytest
from axes.models import AccessAttempt
from django.contrib.sessions.models import Session
from django.core.management import CommandError, call_command
from django.urls import reverse
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp_webauthn.models import WebAuthnCredential

from signin.models import SecurityEvent
from signin.tests import add_authenticator, add_passkey, add_recovery_codes, verify

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105


@pytest.fixture
def owner(django_user_model):
    owner = django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)
    add_authenticator(owner)
    add_passkey(owner)
    add_recovery_codes(owner, "abcd1234")
    return owner


@pytest.fixture
def signed_in(client, owner):
    client.force_login(owner)
    verify(client, owner.totpdevice_set.get())
    return client


def break_glass(*args):
    out = StringIO()
    call_command("break_glass", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_resetting_two_factor_removes_every_second_step(client, owner):
    break_glass("--two-factor")

    assert not TOTPDevice.objects.exists()
    assert not WebAuthnCredential.objects.exists()
    assert not StaticDevice.objects.exists()
    client.post(reverse("login"), {"username": EMAIL, "password": PASSWORD})
    assert client.get(reverse("home"))["Location"].startswith(reverse("protect"))


@pytest.mark.django_db
def test_resetting_the_password_prints_a_new_one(client, owner):
    out = break_glass("--password")

    new_password = re.search(r"New password: (\S+)", out)[1]
    owner.refresh_from_db()
    assert owner.check_password(new_password)
    assert TOTPDevice.objects.exists()


@pytest.mark.django_db
def test_a_reset_signs_out_everywhere_and_lifts_every_pause(signed_in, owner):
    AccessAttempt.objects.create(
        ip_address="198.51.100.7", failures_since_start=5, user_agent="", username=""
    )

    break_glass("--two-factor")

    assert not Session.objects.exists()
    assert not AccessAttempt.objects.exists()
    event = SecurityEvent.objects.get()
    assert event.kind == SecurityEvent.Kind.RESET_ON_SERVER
    assert event.detail == "Two-factor"


@pytest.mark.django_db
def test_both_can_be_reset_at_once(owner):
    break_glass("--two-factor", "--password")

    assert not TOTPDevice.objects.exists()
    assert SecurityEvent.objects.get().detail == "Two-factor and password"


@pytest.mark.django_db
def test_something_must_be_chosen(owner):
    with pytest.raises(CommandError, match="--two-factor"):
        break_glass()


@pytest.mark.django_db
def test_an_unclaimed_install_has_nothing_to_reset():
    with pytest.raises(CommandError, match="claimed"):
        break_glass("--password")
