import pytest
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse

from signin.models import SecurityEvent
from signin.tests import add_authenticator, code_for

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105
FIREFOX_ON_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"
)
SAFARI_ON_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1"
)


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


@pytest.fixture
def authenticator(owner):
    return add_authenticator(owner)


@pytest.fixture
def steps():
    return iter(range(100))


def signed_in(authenticator, steps, user_agent, ip):
    """A fresh browser, signed in and so in sudo mode."""
    client = Client(headers={"user-agent": user_agent}, REMOTE_ADDR=ip)
    client.post(reverse("login"), {"username": EMAIL, "password": PASSWORD})
    client.post(reverse("verify"), {"code": code_for(authenticator, next(steps))})
    return client


@pytest.fixture
def phone(authenticator, steps):
    return signed_in(authenticator, steps, SAFARI_ON_IPHONE, "198.51.100.7")


@pytest.fixture
def laptop(authenticator, steps):
    return signed_in(authenticator, steps, FIREFOX_ON_WINDOWS, "203.0.113.9")


@pytest.mark.django_db
def test_sessions_lists_every_signed_in_device(phone, laptop):
    response = phone.get(reverse("sessions"))

    text = response.text
    assert "Safari on iPhone" in text
    assert "Firefox on Windows" in text
    assert "203.0.113.9" in text
    assert "This device" in text


@pytest.mark.django_db
def test_a_session_past_only_the_password_is_listed_as_such(owner, phone):
    stranger = Client(headers={"user-agent": FIREFOX_ON_WINDOWS})
    stranger.post(reverse("login"), {"username": EMAIL, "password": PASSWORD})

    assert "Password only" in phone.get(reverse("sessions")).text


@pytest.mark.django_db
def test_sign_out_everywhere_else(phone, laptop):
    response = phone.post(reverse("sign_out_others"))

    assert response["Location"] == reverse("sessions")
    assert Session.objects.count() == 1
    assert laptop.get(reverse("home")).status_code == 302
    assert phone.get(reverse("home")).status_code == 200
    assert SecurityEvent.objects.filter(
        kind=SecurityEvent.Kind.SIGNED_OUT_ELSEWHERE
    ).exists()


@pytest.mark.django_db
def test_changing_the_password_signs_out_everywhere_else(phone, laptop):
    phone.post(
        reverse("password"),
        {
            "old_password": PASSWORD,
            "new_password1": "a quieter ferry at dawn",
            "new_password2": "a quieter ferry at dawn",
        },
    )

    assert Session.objects.count() == 1
    assert phone.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_sessions_need_sudo(phone, clock):
    clock.advance(minutes=11)

    assert phone.get(reverse("sessions"))["Location"].startswith(reverse("confirm"))
    assert phone.post(reverse("sign_out_others"))["Location"].startswith(
        reverse("confirm")
    )
    assert Session.objects.count() == 1
