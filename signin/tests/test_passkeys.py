import json
import re
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django_otp_webauthn.helpers import WebAuthnHelper

from signin.tests import add_authenticator, add_passkey, code_for, verify

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


def post_json(client, name, data=None, query=""):
    return client.post(
        reverse(name) + query, json.dumps(data or {}), content_type="application/json"
    )


@pytest.fixture
def authenticator_accepts(monkeypatch):
    """Stand in for a browser and authenticator that make a new passkey, or
    answer for `device`."""

    def accept(device=None):
        monkeypatch.setattr(
            WebAuthnHelper,
            "register_complete",
            lambda self, user, **kw: add_passkey(user),
        )
        monkeypatch.setattr(
            WebAuthnHelper, "authenticate_complete", lambda self, **kw: device
        )

    return accept


@pytest.mark.django_db
def test_claim_with_a_passkey(client, authenticator_accepts):
    out = StringIO()
    call_command("setup_code", stdout=out)
    client.post(reverse("claim"), {"code": re.search(r": ([\d ]+)", out.getvalue())[1]})
    client.post(
        reverse("claim_owner"),
        {"name": "Akshay Prabhu", "email": EMAIL, "password": PASSWORD},
    )

    begin = post_json(client, "passkey_register_begin")
    assert begin.status_code == 200
    assert "challenge" in begin.json()
    authenticator_accepts()
    assert post_json(client, "passkey_register_complete").status_code == 200

    assert client.get(reverse("recovery_codes")).status_code == 200
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_a_passkey_alone_signs_in(client, owner, authenticator_accepts):
    authenticator_accepts(add_passkey(owner))

    post_json(client, "passkey_auth_begin")
    response = post_json(
        client, "passkey_auth_complete", query=f"?next={reverse('plan')}"
    )

    assert response.json()["redirect_url"] == reverse("plan")
    assert client.get(reverse("home")).status_code == 200
    assert client.get(reverse("security")).status_code == 200


@pytest.mark.django_db
def test_sign_in_page_offers_a_passkey(client, owner):
    response = client.get(reverse("login"))

    assert "data-passkey" in response.text


@pytest.mark.django_db
def test_registering_another_passkey_needs_sudo(client, owner, authenticator_accepts):
    device = add_authenticator(owner)
    client.force_login(owner)
    verify(client, device)

    assert post_json(client, "passkey_register_begin").status_code == 403

    client.post(reverse("confirm"), {"code": code_for(device)})
    assert post_json(client, "passkey_register_begin").status_code == 200


@pytest.mark.django_db
def test_registering_a_passkey_needs_a_verified_session(client, owner):
    add_authenticator(owner)
    client.force_login(owner)

    assert post_json(client, "passkey_register_begin").status_code == 403


@pytest.mark.django_db
def test_confirming_by_passkey_opens_security(client, owner, authenticator_accepts):
    passkey = add_passkey(owner)
    client.force_login(owner)
    verify(client, passkey)
    authenticator_accepts(passkey)

    post_json(client, "passkey_auth_begin")
    response = post_json(
        client, "passkey_auth_complete", query=f"?next={reverse('security')}"
    )

    assert response.json()["redirect_url"] == reverse("security")
    assert client.get(reverse("security")).status_code == 200
