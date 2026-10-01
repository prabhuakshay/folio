import pytest
from django.urls import reverse

from signin.tests import add_authenticator, code_for, verify

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(
        EMAIL, EMAIL, PASSWORD, first_name="Akshay", last_name="Prabhu"
    )


def sign_in(client, password=PASSWORD):
    return client.post(reverse("login"), {"username": EMAIL, "password": password})


@pytest.mark.django_db
def test_sign_in_with_email_and_password(client, owner):
    response = sign_in(client)

    assert response["Location"] == reverse("home")
    assert client.session["_auth_user_id"] == str(owner.pk)


@pytest.mark.django_db
def test_wrong_password_is_refused(client, owner):
    response = sign_in(client, "not it")

    assert response.status_code == 200
    assert "don't match" in response.text
    assert client.get(reverse("home")).status_code == 302


@pytest.mark.django_db
def test_admin_login_redirects_to_folio_sign_in(client, owner):
    admin_index = reverse("admin:index")

    response = client.get(admin_index, follow=True)

    assert response.redirect_chain[-1][0] == f"{reverse('login')}?next={admin_index}"
    response = client.post(
        response.redirect_chain[-1][0],
        {"username": EMAIL, "password": PASSWORD, "next": admin_index},
    )
    assert response["Location"] == admin_index
    client.post(reverse("verify"), {"code": code_for(add_authenticator(owner))})
    assert client.get(admin_index).status_code == 200


@pytest.mark.django_db
def test_session_lasts_30_days_from_the_last_visit(client, owner, clock):
    sign_in(client)
    verify(client, add_authenticator(owner))

    clock.advance(days=20)
    assert client.get(reverse("home")).status_code == 200
    clock.advance(days=20)
    assert client.get(reverse("home")).status_code == 200
    clock.advance(days=29)
    assert client.get(reverse("home")).status_code == 200

    clock.advance(days=31)
    assert client.get(reverse("home")).status_code == 302


@pytest.mark.django_db
def test_sign_in_ignores_the_email_case(client, owner):
    client.post(
        reverse("login"), {"username": "Akshay@Example.IN", "password": PASSWORD}
    )

    assert client.session["_auth_user_id"] == str(owner.pk)
