import json

import pytest
from django.urls import reverse
from django_otp_webauthn.helpers import WebAuthnHelper
from django_otp_webauthn.models import WebAuthnCredential

from signin.models import SecurityEvent
from signin.tests import (
    add_authenticator,
    add_passkey,
    add_recovery_codes,
    code_for,
    code_for_key,
    verify,
)

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105
CHROME_ON_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
Kind = SecurityEvent.Kind


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


@pytest.fixture
def authenticator(owner):
    return add_authenticator(owner)


@pytest.fixture
def in_sudo(client, owner, authenticator):
    client.force_login(owner)
    verify(client, authenticator)
    client.post(reverse("confirm"), {"code": code_for(authenticator)})
    return client


@pytest.fixture
def passkey_accepts(monkeypatch):
    def accept(device):
        monkeypatch.setattr(
            WebAuthnHelper, "authenticate_complete", lambda self, **kw: device
        )
        monkeypatch.setattr(
            WebAuthnHelper,
            "register_complete",
            lambda self, user, **kw: add_passkey(user),
        )

    return accept


def post_json(client, name):
    return client.post(reverse(name), json.dumps({}), content_type="application/json")


@pytest.fixture(autouse=True)
def _from_a_mac(client):
    client.defaults.update(HTTP_USER_AGENT=CHROME_ON_MAC, REMOTE_ADDR="198.51.100.7")


def sign_in(client, password=PASSWORD):
    return client.post(reverse("login"), {"username": EMAIL, "password": password})


def kinds():
    return list(
        SecurityEvent.objects.order_by("at", "pk").values_list("kind", flat=True)
    )


@pytest.mark.django_db
def test_signing_in_by_password_and_code_is_logged(client, owner, authenticator):
    sign_in(client)
    client.post(reverse("verify"), {"code": code_for(authenticator)})

    event = SecurityEvent.objects.get()
    assert event.kind == Kind.SIGNED_IN
    assert event.detail == "Password and authenticator code"
    assert event.ip == "198.51.100.7"
    assert event.device == "Chrome on Mac"


@pytest.mark.django_db
def test_signing_in_by_recovery_code_is_logged(client, owner, authenticator):
    add_recovery_codes(owner, "abcd1234")
    sign_in(client)
    client.post(reverse("verify"), {"code": "abcd1234"})

    assert SecurityEvent.objects.get().detail == "Password and recovery code"


@pytest.mark.django_db
def test_signing_in_by_passkey_is_logged(client, owner, passkey_accepts):
    passkey_accepts(add_passkey(owner))

    post_json(client, "passkey_auth_begin")
    post_json(client, "passkey_auth_complete")

    event = SecurityEvent.objects.get()
    assert (event.kind, event.detail) == (Kind.SIGNED_IN, "Passkey")


@pytest.mark.django_db
def test_a_passkey_after_the_password_is_logged(client, owner, passkey_accepts):
    passkey_accepts(add_passkey(owner))
    sign_in(client)

    post_json(client, "passkey_auth_begin")
    post_json(client, "passkey_auth_complete")

    assert SecurityEvent.objects.get().detail == "Password and passkey"


@pytest.mark.django_db
def test_confirming_its_you_by_passkey_isnt_a_sign_in(client, owner, passkey_accepts):
    passkey = add_passkey(owner)
    passkey_accepts(passkey)
    client.force_login(owner)
    verify(client, passkey)

    post_json(client, "passkey_auth_begin")
    post_json(client, "passkey_auth_complete")

    assert not SecurityEvent.objects.exists()


@pytest.mark.django_db
def test_failures_and_the_pause_are_logged(client, owner, authenticator):
    sign_in(client, "not it")
    sign_in(client)
    client.post(reverse("verify"), {"code": "000000"})
    for _ in range(3):
        sign_in(client, "not it")

    assert kinds() == [
        Kind.WRONG_PASSWORD,
        Kind.WRONG_CODE,
        Kind.WRONG_PASSWORD,
        Kind.WRONG_PASSWORD,
        Kind.PAUSED,
    ]


@pytest.mark.django_db
def test_changing_the_password_is_logged(in_sudo):
    in_sudo.post(
        reverse("password"),
        {
            "old_password": PASSWORD,
            "new_password1": "a quieter ferry at dawn",
            "new_password2": "a quieter ferry at dawn",
        },
    )

    assert kinds() == [Kind.PASSWORD_CHANGED]


@pytest.mark.django_db
def test_changing_second_factors_is_logged(in_sudo, owner, passkey_accepts):
    passkey_accepts(None)

    def add_a_passkey():
        post_json(in_sudo, "passkey_register_begin")
        post_json(in_sudo, "passkey_register_complete")

    add_a_passkey()
    passkey = WebAuthnCredential.objects.get(user=owner)
    in_sudo.post(reverse("passkey_remove", args=[passkey.pk]))
    in_sudo.post(reverse("recovery_codes_regenerate"))
    add_a_passkey()
    in_sudo.post(reverse("authenticator_remove"))

    assert kinds() == [
        Kind.PASSKEY_ADDED,
        Kind.PASSKEY_REMOVED,
        Kind.RECOVERY_CODES_ISSUED,
        Kind.PASSKEY_ADDED,
        Kind.AUTHENTICATOR_REMOVED,
    ]


@pytest.mark.django_db
def test_setting_up_an_authenticator_is_logged(in_sudo):
    in_sudo.get(reverse("authenticator"))
    key = in_sudo.session["signin.authenticator_key"]

    in_sudo.post(reverse("authenticator"), {"code": code_for_key(key, 1)})

    assert kinds() == [Kind.AUTHENTICATOR_SET_UP]


@pytest.mark.django_db
def test_the_log_is_shown_newest_first(in_sudo):
    SecurityEvent.objects.create(kind=Kind.WRONG_PASSWORD, ip="203.0.113.9")
    SecurityEvent.objects.create(
        kind=Kind.SIGNED_IN, detail="Passkey", device="Safari on iPhone"
    )

    response = in_sudo.get(reverse("security_log"))

    text = response.text
    assert text.index("Signed in") < text.index("Wrong email or password")
    assert "Safari on iPhone" in text
    assert "203.0.113.9" in text


@pytest.mark.django_db
def test_the_log_needs_sudo(client, owner, authenticator):
    client.force_login(owner)
    verify(client, authenticator)

    assert client.get(reverse("security_log"))["Location"].startswith(
        reverse("confirm")
    )


@pytest.mark.django_db
def test_signing_in_by_password_alone_is_logged(client, owner):
    sign_in(client)

    event = SecurityEvent.objects.get()
    assert (event.kind, event.detail) == (Kind.SIGNED_IN, "Password")


@pytest.mark.django_db
def test_tries_during_a_pause_dont_repeat_it(client, owner):
    for _ in range(8):
        sign_in(client, "not it")

    assert kinds().count(Kind.PAUSED) == 1
