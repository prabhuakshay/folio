import re

import pytest
from django.urls import reverse
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp_webauthn.models import WebAuthnCredential

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
SECURITY = reverse("security")


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


@pytest.fixture
def authenticator(owner):
    return add_authenticator(owner)


@pytest.fixture
def signed_in(client, owner, authenticator):
    """Signed in a while ago: verified, but no longer in sudo mode."""
    client.force_login(owner)
    verify(client, authenticator)
    return client


def secret(response):
    return re.search(r"data-secret[^>]*>([^<]+)<", response.text)[1]


def confirm(client, device, steps_ahead=0):
    return client.post(
        f"{reverse('confirm')}?next={SECURITY}",
        {"code": code_for(device, steps_ahead)},
    )


@pytest.mark.django_db
def test_security_asks_to_confirm_its_you(signed_in):
    response = signed_in.get(SECURITY)

    assert response["Location"] == f"{reverse('confirm')}?next={SECURITY}"
    response = signed_in.get(response["Location"])
    assert "Confirm it&#x27;s you" in response.text


@pytest.mark.django_db
def test_confirming_by_authenticator_opens_security(signed_in, authenticator):
    response = confirm(signed_in, authenticator)

    assert response["Location"] == SECURITY
    assert signed_in.get(SECURITY).status_code == 200


@pytest.mark.django_db
def test_wrong_code_does_not_confirm(signed_in):
    response = signed_in.post(reverse("confirm"), {"code": "000000"})

    assert response.status_code == 200
    assert signed_in.get(SECURITY).status_code == 302


@pytest.mark.django_db
def test_recovery_code_does_not_confirm(signed_in, owner):
    add_recovery_codes(owner, "abcdefgh")

    signed_in.post(reverse("confirm"), {"code": "abcdefgh"})

    assert signed_in.get(SECURITY).status_code == 302


@pytest.mark.django_db
def test_sudo_mode_lasts_10_minutes(signed_in, authenticator, clock):
    confirm(signed_in, authenticator)

    clock.advance(minutes=9)
    assert signed_in.get(SECURITY).status_code == 200
    clock.advance(minutes=2)
    assert signed_in.get(SECURITY).status_code == 302


@pytest.mark.django_db
def test_signing_in_counts_as_confirming(client, owner, authenticator):
    client.post(reverse("login"), {"username": EMAIL, "password": PASSWORD})
    client.post(reverse("verify"), {"code": code_for(authenticator)})

    assert client.get(SECURITY).status_code == 200


@pytest.mark.django_db
def test_settings_links_to_security(signed_in):
    response = signed_in.get(reverse("settings"))

    assert f'href="{SECURITY}"' in response.text


@pytest.mark.django_db
def test_security_lists_what_protects_the_login(signed_in, owner, authenticator):
    add_passkey(owner)
    add_recovery_codes(owner, "abcdefgh", "ijklmnop")
    confirm(signed_in, authenticator)

    response = signed_in.get(SECURITY)

    assert "Passkey" in response.text
    assert "Authenticator app" in response.text
    assert "2 of 10 left" in response.text


@pytest.mark.django_db
def test_change_password(signed_in, owner, authenticator):
    confirm(signed_in, authenticator)

    response = signed_in.post(
        reverse("password"),
        {
            "old_password": PASSWORD,
            "new_password1": "a quiet copper meadow",
            "new_password2": "a quiet copper meadow",
        },
    )

    assert response["Location"] == SECURITY
    owner.refresh_from_db()
    assert owner.check_password("a quiet copper meadow")
    assert signed_in.get(SECURITY).status_code == 200


@pytest.mark.django_db
def test_change_password_needs_sudo(signed_in):
    response = signed_in.get(reverse("password"))

    assert response["Location"].startswith(reverse("confirm"))


@pytest.mark.django_db
def test_regenerate_recovery_codes(signed_in, owner, authenticator):
    add_recovery_codes(owner, "abcdefgh")
    confirm(signed_in, authenticator)

    response = signed_in.post(reverse("recovery_codes_regenerate"))

    assert response["Location"] == reverse("new_recovery_codes")
    response = signed_in.get(response["Location"])
    codes = re.findall(r"data-recovery-code>([a-z0-9]{4} [a-z0-9]{4})<", response.text)
    assert len(set(codes)) == 10
    tokens = set(StaticDevice.objects.get().token_set.values_list("token", flat=True))
    assert tokens == {c.replace(" ", "") for c in codes}


@pytest.mark.django_db
def test_new_recovery_codes_are_shown_once(signed_in, owner, authenticator):
    confirm(signed_in, authenticator)
    signed_in.post(reverse("recovery_codes_regenerate"))
    signed_in.get(reverse("new_recovery_codes"))
    tokens = set(StaticToken.objects.values_list("token", flat=True))

    response = signed_in.get(reverse("new_recovery_codes"))

    assert response["Location"] == SECURITY
    assert set(StaticToken.objects.values_list("token", flat=True)) == tokens


@pytest.mark.django_db
def test_regenerate_recovery_codes_needs_sudo(signed_in, owner):
    add_recovery_codes(owner, "abcdefgh")

    signed_in.post(reverse("recovery_codes_regenerate"))

    assert StaticDevice.objects.get().token_set.count() == 1


@pytest.mark.django_db
def test_replace_the_authenticator(signed_in, authenticator):
    confirm(signed_in, authenticator)
    signed_in.post(reverse("authenticator_start"))
    key = signed_in.session["signin.authenticator_key"]

    response = signed_in.post(
        reverse("authenticator"), {"code": code_for_key(key, steps_ahead=1)}
    )

    assert response["Location"] == SECURITY
    assert TOTPDevice.objects.get().key == key


@pytest.mark.django_db
def test_setting_up_an_authenticator_needs_sudo_once_protected(signed_in):
    response = signed_in.post(reverse("authenticator_start"))

    assert response["Location"].startswith(reverse("confirm"))
    assert "signin.authenticator_key" not in signed_in.session


@pytest.mark.django_db
def test_setting_up_from_security_starts_a_setup(signed_in, authenticator):
    confirm(signed_in, authenticator)

    response = signed_in.post(reverse("authenticator_start"))

    assert response["Location"] == reverse("authenticator")
    response = signed_in.get(reverse("authenticator"))
    assert "data-secret" in response.text


@pytest.mark.django_db
def test_reloading_a_setup_keeps_its_key(signed_in, authenticator):
    confirm(signed_in, authenticator)
    signed_in.post(reverse("authenticator_start"))

    first = signed_in.get(reverse("authenticator"))
    again = signed_in.get(reverse("authenticator"))

    assert secret(first) == secret(again)


@pytest.mark.django_db
def test_a_setup_never_starts_by_opening_its_screen(signed_in, authenticator):
    confirm(signed_in, authenticator)

    response = signed_in.get(reverse("authenticator"))

    assert response["Location"] == SECURITY
    assert "signin.authenticator_key" not in signed_in.session


@pytest.mark.django_db
def test_setup_screen_goes_home_outside_sudo_with_none_in_progress(signed_in):
    response = signed_in.get(reverse("authenticator"))

    assert response["Location"] == reverse("home")


@pytest.mark.django_db
def test_a_setup_left_past_sudo_mode_goes_home(signed_in, authenticator, clock):
    confirm(signed_in, authenticator)
    signed_in.post(reverse("authenticator_start"))
    clock.advance(minutes=11)

    response = signed_in.get(reverse("authenticator"))

    assert response["Location"] == reverse("home")


@pytest.mark.django_db
def test_back_after_replacing_the_authenticator_starts_no_new_setup(
    signed_in, authenticator
):
    confirm(signed_in, authenticator)
    signed_in.post(reverse("authenticator_start"))
    key = signed_in.session["signin.authenticator_key"]
    signed_in.post(reverse("authenticator"), {"code": code_for_key(key, 1)})

    response = signed_in.get(reverse("authenticator"))

    assert response["Location"] == SECURITY
    assert TOTPDevice.objects.get().key == key


@pytest.mark.django_db
def test_confirm_goes_straight_on_while_in_sudo(signed_in, authenticator):
    confirm(signed_in, authenticator)

    response = signed_in.get(f"{reverse('confirm')}?next={SECURITY}")

    assert response["Location"] == SECURITY


@pytest.mark.django_db
def test_confirm_in_sudo_ignores_an_unsafe_next(signed_in, authenticator):
    confirm(signed_in, authenticator)

    response = signed_in.get(f"{reverse('confirm')}?next=https://evil.example/")

    assert response["Location"] == reverse("home")


@pytest.mark.django_db
def test_the_last_way_to_sign_in_cannot_be_removed(signed_in, authenticator):
    confirm(signed_in, authenticator)

    response = signed_in.post(reverse("authenticator_remove"), follow=True)

    assert TOTPDevice.objects.exists()
    assert "Add a passkey first" in response.text


@pytest.mark.django_db
def test_remove_the_authenticator_while_a_passkey_remains(
    signed_in, owner, authenticator
):
    add_passkey(owner)
    confirm(signed_in, authenticator)

    signed_in.post(reverse("authenticator_remove"))

    assert not TOTPDevice.objects.exists()


@pytest.mark.django_db
def test_remove_a_passkey(signed_in, owner, authenticator):
    passkey = add_passkey(owner)
    confirm(signed_in, authenticator)

    signed_in.post(reverse("passkey_remove", args=[passkey.pk]))

    assert not WebAuthnCredential.objects.exists()


@pytest.mark.django_db
def test_removing_needs_sudo(signed_in, owner):
    passkey = add_passkey(owner)

    signed_in.post(reverse("passkey_remove", args=[passkey.pk]))

    assert WebAuthnCredential.objects.exists()


@pytest.mark.django_db
def test_removing_asks_first(signed_in, owner, authenticator):
    add_passkey(owner)
    confirm(signed_in, authenticator)

    response = signed_in.get(SECURITY)

    assert response.text.count('data-confirm-action="Remove"') == 2
    assert '<dialog id="confirm"' in response.text


@pytest.mark.django_db
def test_removing_what_verified_this_session_keeps_it_signed_in(
    signed_in, owner, authenticator
):
    add_passkey(owner)
    confirm(signed_in, authenticator)

    signed_in.post(reverse("authenticator_remove"))

    assert signed_in.get(SECURITY).status_code == 200


@pytest.mark.django_db
def test_replacing_the_authenticator_keeps_this_session_signed_in(
    signed_in, authenticator
):
    confirm(signed_in, authenticator)
    signed_in.post(reverse("authenticator_start"))
    key = signed_in.session["signin.authenticator_key"]

    signed_in.post(reverse("authenticator"), {"code": code_for_key(key)})

    assert signed_in.get(SECURITY).status_code == 200
