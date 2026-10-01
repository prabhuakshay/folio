import re
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from signin.tests import (
    add_authenticator,
    add_passkey,
    add_recovery_codes,
    code_for,
    code_for_key,
)

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


def sign_in(client):
    return client.post(reverse("login"), {"username": EMAIL, "password": PASSWORD})


def claim(client):
    out = StringIO()
    call_command("setup_code", stdout=out)
    code = re.search(r"Setup code: ([\d ]+)", out.getvalue())[1]
    client.post(reverse("claim"), {"code": code})
    return client.post(
        reverse("claim_owner"),
        {"name": "Akshay Prabhu", "email": EMAIL, "password": PASSWORD},
    )


def set_up_authenticator(client, steps_ahead=0):
    client.get(reverse("authenticator"))
    key = client.session["signin.authenticator_key"]
    return client.post(
        reverse("authenticator"), {"code": code_for_key(key, steps_ahead)}
    )


def shown_codes(response):
    return re.findall(r"data-recovery-code>([a-z0-9]{4} [a-z0-9]{4})<", response.text)


@pytest.mark.django_db
def test_claim_continues_to_protect_the_login(client):
    response = claim(client)

    assert response["Location"] == reverse("protect")
    response = client.get(reverse("protect"))
    assert "3 of 4" in response.text
    assert "Add a passkey" in response.text
    assert reverse("authenticator") in response.text


@pytest.mark.django_db
def test_nothing_opens_until_the_login_is_protected(client):
    claim(client)

    assert client.get(reverse("home"))["Location"] == (
        f"{reverse('protect')}?next={reverse('home')}"
    )


@pytest.mark.django_db
def test_claim_with_an_authenticator_app_then_shows_recovery_codes_once(client):
    claim(client)

    response = set_up_authenticator(client)

    assert response["Location"] == reverse("recovery_codes")
    response = client.get(reverse("recovery_codes"))
    assert "4 of 4" in response.text
    assert len(set(shown_codes(response))) == 10
    assert client.get(reverse("recovery_codes"))["Location"] == reverse("home")
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_back_after_the_first_setup_goes_home_not_to_confirm(client):
    claim(client)
    set_up_authenticator(client)
    client.get(reverse("recovery_codes"))

    response = client.get(reverse("authenticator"))

    assert response["Location"] == reverse("home")
    assert TOTPDevice.objects.count() == 1


@pytest.mark.django_db
def test_back_to_a_setup_left_for_a_passkey_goes_home(client, django_user_model):
    claim(client)
    client.get(reverse("authenticator"))
    add_passkey(django_user_model.objects.get())

    response = client.get(reverse("authenticator"))

    assert response["Location"] == reverse("home")


@pytest.mark.django_db
def test_authenticator_shows_a_qr_code_and_the_key_to_type(client):
    claim(client)

    response = client.get(reverse("authenticator"))

    assert "<svg" in response.text
    assert "otpauth" not in response.text
    assert "data-secret" in response.text


@pytest.mark.django_db
def test_wrong_authenticator_code_sets_nothing_up(client):
    claim(client)
    client.get(reverse("authenticator"))

    response = client.post(reverse("authenticator"), {"code": "000000"})

    assert response.status_code == 200
    assert "doesn&#x27;t match" in response.text
    assert not TOTPDevice.objects.exists()


@pytest.mark.django_db
def test_password_alone_does_not_sign_in(client, owner):
    add_authenticator(owner)

    sign_in(client)

    assert client.get(reverse("home"))["Location"] == (
        f"{reverse('verify')}?next={reverse('home')}"
    )


@pytest.mark.django_db
def test_password_and_authenticator_code_sign_in(client, owner):
    device = add_authenticator(owner)
    sign_in(client)

    response = client.post(
        f"{reverse('verify')}?next={reverse('plan')}", {"code": code_for(device)}
    )

    assert response["Location"] == reverse("plan")
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_wrong_code_does_not_sign_in(client, owner):
    add_authenticator(owner)
    sign_in(client)

    response = client.post(reverse("verify"), {"code": "000000"})

    assert response.status_code == 200
    assert "doesn&#x27;t match" in response.text
    assert client.get(reverse("home")).status_code == 302


@pytest.mark.django_db
def test_recovery_code_signs_in_once(client, owner):
    add_authenticator(owner)
    add_recovery_codes(owner, "abcdefgh")
    sign_in(client)

    client.post(reverse("verify"), {"code": "ABCD EFGH"})

    assert client.get(reverse("home")).status_code == 200
    client.logout()
    sign_in(client)
    client.post(reverse("verify"), {"code": "abcdefgh"})
    assert client.get(reverse("home")).status_code == 302


@pytest.mark.django_db
def test_verify_offers_a_passkey_only_to_a_login_that_has_one(client, owner):
    add_authenticator(owner)
    sign_in(client)

    response = client.get(reverse("verify"))

    assert "data-passkey" not in response.text


@pytest.mark.django_db
def test_verify_offers_a_passkey_to_a_login_that_has_one(client, owner):
    add_passkey(owner)
    sign_in(client)

    response = client.get(f"{reverse('verify')}?next={reverse('plan')}")

    assert 'data-passkey="sign-in"' in response.text
    assert f"?next={reverse('plan')}" in response.text


@pytest.mark.django_db
def test_admin_needs_a_verified_session(client, owner):
    device = add_authenticator(owner)
    sign_in(client)

    assert client.get(reverse("admin:index")).status_code == 302

    client.post(reverse("verify"), {"code": code_for(device)})
    assert client.get(reverse("admin:index")).status_code == 200


@pytest.mark.django_db
def test_signing_out_needs_no_second_factor(client, owner):
    add_authenticator(owner)
    sign_in(client)

    client.post(reverse("logout"))

    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_protect_is_only_for_a_login_with_nothing_set_up(client, owner):
    device = add_authenticator(owner)
    sign_in(client)

    assert client.get(reverse("protect"))["Location"].startswith(reverse("verify"))
    client.post(reverse("verify"), {"code": code_for(device)})
    assert client.get(reverse("protect"))["Location"] == reverse("home")


@pytest.mark.django_db
def test_recovery_codes_are_not_shown_again_to_a_returning_login(client, owner):
    device = add_authenticator(owner)
    add_recovery_codes(owner)
    sign_in(client)
    client.post(reverse("verify"), {"code": code_for(device)})

    assert client.get(reverse("recovery_codes"))["Location"] == reverse("home")
    assert StaticDevice.objects.get().token_set.count() == 0
