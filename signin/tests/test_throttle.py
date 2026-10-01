from datetime import timedelta

import pytest
from axes.models import AccessAttempt
from django.db.models import F
from django.urls import reverse
from django_otp_webauthn.helpers import WebAuthnHelper

from signin.tests import add_authenticator, add_passkey, code_for, verify

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105
WRONG_CODE = "000000"


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


def sign_in(client, password=PASSWORD, **extra):
    return client.post(
        reverse("login"), {"username": EMAIL, "password": password}, **extra
    )


def fail_password(client, times, **extra):
    for _ in range(times):
        sign_in(client, "not it", **extra)


@pytest.mark.django_db
def test_five_wrong_passwords_pause_sign_in_for_an_hour(client, owner):
    fail_password(client, 4)
    response = sign_in(client, "not it")

    assert response.status_code == 429
    assert "an hour" in response.text
    response = sign_in(client)
    assert response.status_code == 429
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_the_pause_lifts_after_an_hour(client, owner):
    fail_password(client, 5)

    AccessAttempt.objects.update(
        attempt_time=F("attempt_time") - timedelta(hours=1, minutes=1)
    )

    assert sign_in(client).status_code == 302


@pytest.mark.django_db
def test_the_account_is_never_locked_only_the_address(client, owner):
    fail_password(client, 5)

    assert sign_in(client, REMOTE_ADDR="203.0.113.9").status_code == 302


@pytest.mark.django_db
def test_wrong_authenticator_codes_count_with_wrong_passwords(client, owner):
    device = add_authenticator(owner)
    fail_password(client, 3)
    sign_in(client)

    assert client.post(reverse("verify"), {"code": WRONG_CODE}).status_code == 200
    assert client.post(reverse("verify"), {"code": WRONG_CODE}).status_code == 429
    response = client.post(reverse("verify"), {"code": code_for(device)})
    assert response.status_code == 429
    assert client.get(reverse("home")).status_code == 302


@pytest.mark.django_db
def test_wrong_codes_confirming_its_you_count(client, owner):
    device = add_authenticator(owner)
    client.force_login(owner)
    verify(client, device)

    for _ in range(4):
        client.post(reverse("confirm"), {"code": WRONG_CODE})
    assert client.post(reverse("confirm"), {"code": WRONG_CODE}).status_code == 429
    assert (
        client.post(reverse("confirm"), {"code": code_for(device)}).status_code == 429
    )


@pytest.mark.django_db
def test_behind_the_proxy_the_forwarded_address_is_paused(settings, client, owner):
    settings.USE_X_FORWARDED_FOR = True
    fail_password(client, 5, HTTP_X_FORWARDED_FOR="198.51.100.7")

    assert sign_in(client, HTTP_X_FORWARDED_FOR="198.51.100.7").status_code == 429
    assert sign_in(client, HTTP_X_FORWARDED_FOR="203.0.113.9").status_code == 302


@pytest.mark.django_db
def test_a_spoofed_forwarded_address_doesnt_escape_the_pause(settings, client, owner):
    settings.USE_X_FORWARDED_FOR = True
    fail_password(client, 5, HTTP_X_FORWARDED_FOR="198.51.100.7")

    response = sign_in(client, HTTP_X_FORWARDED_FOR="203.0.113.9, 198.51.100.7")

    assert response.status_code == 429


@pytest.mark.django_db
def test_a_passkey_still_signs_in_from_a_paused_address(client, owner, monkeypatch):
    passkey = add_passkey(owner)
    monkeypatch.setattr(
        WebAuthnHelper, "authenticate_complete", lambda self, **kw: passkey
    )
    fail_password(client, 5)

    client.post(reverse("passkey_auth_begin"), "{}", content_type="application/json")
    response = client.post(
        reverse("passkey_auth_complete"), "{}", content_type="application/json"
    )

    assert response.status_code == 200
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_tries_during_the_pause_dont_extend_it(client, owner):
    fail_password(client, 5)
    AccessAttempt.objects.update(attempt_time=F("attempt_time") - timedelta(minutes=50))

    fail_password(client, 3)
    AccessAttempt.objects.update(attempt_time=F("attempt_time") - timedelta(minutes=11))

    assert sign_in(client).status_code == 302
