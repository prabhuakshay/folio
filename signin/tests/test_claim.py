import re
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

DETAILS = {
    "name": "Akshay Prabhu",
    "email": "akshay@example.in",
    "password": "a long harbour lantern",
}


def printed_code():
    out = StringIO()
    call_command("setup_code", stdout=out)
    return re.search(r"Setup code: ([\d ]+)", out.getvalue())[1].strip()


def claim(client, code=None):
    client.post(reverse("claim"), {"code": code or printed_code()})
    return client.post(reverse("claim_owner"), DETAILS)


@pytest.mark.django_db
def test_claim_creates_the_login_and_signs_in(client):
    response = claim(client)

    assert response.status_code == 302
    assert response["Location"] == reverse("protect")
    (owner,) = get_user_model().objects.all()
    assert client.session["_auth_user_id"] == str(owner.pk)
    assert owner.get_full_name() == "Akshay Prabhu"
    assert owner.email == "akshay@example.in"


@pytest.mark.django_db
def test_wrong_setup_code_is_refused(client):
    response = client.post(reverse("claim"), {"code": "1234 5678 9012"})

    assert response.status_code == 200
    assert "isn&#x27;t the setup code" in response.text
    assert client.get(reverse("claim_owner"))["Location"] == reverse("claim")
    assert client.post(reverse("claim_owner"), DETAILS).status_code == 302
    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_setup_code_may_be_typed_without_spaces(client):
    response = client.post(reverse("claim"), {"code": printed_code().replace(" ", "")})

    assert response["Location"] == reverse("claim_owner")


@pytest.mark.django_db
def test_second_claim_is_refused(client):
    code = printed_code()
    claim(client, code)
    client.logout()

    assert client.get(reverse("claim")).status_code == 404
    assert client.post(reverse("claim"), {"code": code}).status_code == 404
    assert client.post(reverse("claim_owner"), DETAILS).status_code == 404
    assert get_user_model().objects.count() == 1


@pytest.mark.django_db
def test_claim_mid_way_is_refused_once_claimed(client, django_user_model):
    client.post(reverse("claim"), {"code": printed_code()})
    django_user_model.objects.create_user("someone@example.in")

    assert client.post(reverse("claim_owner"), DETAILS).status_code == 404
    assert get_user_model().objects.count() == 1


@pytest.mark.django_db
def test_no_setup_code_once_claimed(client):
    claim(client)
    out = StringIO()

    call_command("setup_code", stdout=out)

    assert "Setup code" not in out.getvalue()


@pytest.mark.django_db
def test_weak_password_is_refused(client):
    client.post(reverse("claim"), {"code": printed_code()})

    response = client.post(reverse("claim_owner"), {**DETAILS, "password": "akshay"})

    assert response.status_code == 200
    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_unclaimed_install_sends_sign_in_to_claim(client):
    assert client.get(reverse("login"))["Location"] == reverse("claim")


@pytest.mark.django_db
def test_owner_signs_in_with_their_email_whatever_its_case(client):
    client.post(reverse("claim"), {"code": printed_code()})
    client.post(reverse("claim_owner"), {**DETAILS, "email": "Akshay@Example.in"})
    client.logout()

    client.post(
        reverse("login"),
        {"username": "akshay@example.in", "password": DETAILS["password"]},
    )

    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_email_too_long_for_a_login_is_refused(client):
    client.post(reverse("claim"), {"code": printed_code()})

    response = client.post(
        reverse("claim_owner"), {**DETAILS, "email": "a" * 140 + "@example.in"}
    )

    assert response.status_code == 200
    assert not get_user_model().objects.exists()
