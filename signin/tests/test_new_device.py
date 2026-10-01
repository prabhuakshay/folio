import smtplib

import pytest
from django.core import mail
from django.urls import reverse

from signin.tests import add_authenticator, code_for

EMAIL = "akshay@example.in"
PASSWORD = "a long harbour lantern"  # noqa: S105
CHROME_ON_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
SAFARI_ON_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1"
)
HOME_IP = "198.51.100.7"


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser(EMAIL, EMAIL, PASSWORD)


@pytest.fixture
def authenticator(owner):
    return add_authenticator(owner)


@pytest.fixture
def sign_in(client, authenticator):
    steps = iter(range(100))

    def sign_in(ip=HOME_IP, user_agent=CHROME_ON_MAC):
        client.logout()
        meta = {"REMOTE_ADDR": ip, "HTTP_USER_AGENT": user_agent}
        client.post(reverse("login"), {"username": EMAIL, "password": PASSWORD}, **meta)
        code = code_for(authenticator, next(steps))
        return client.post(reverse("verify"), {"code": code}, **meta)

    return sign_in


@pytest.mark.django_db
def test_the_first_sign_in_is_emailed(sign_in):
    sign_in()

    [message] = mail.outbox
    assert message.to == [EMAIL]
    assert message.subject == "New sign-in to Folio"
    assert "Chrome on Mac" in message.body
    assert HOME_IP in message.body
    assert "/settings/security/sessions/" in message.body


@pytest.mark.django_db
def test_the_same_address_and_device_arent_emailed_again(sign_in):
    sign_in()
    sign_in()

    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_a_new_address_is_emailed(sign_in):
    sign_in()
    sign_in(ip="203.0.113.9")

    assert len(mail.outbox) == 2
    assert "203.0.113.9" in mail.outbox[1].body


@pytest.mark.django_db
def test_a_new_device_is_emailed(sign_in):
    sign_in()
    sign_in(user_agent=SAFARI_ON_IPHONE)

    assert len(mail.outbox) == 2
    assert "Safari on iPhone" in mail.outbox[1].body


@pytest.mark.django_db
def test_a_failing_mailer_doesnt_stop_the_sign_in(sign_in, monkeypatch, client):
    def refuse(*args, **kwargs):
        raise smtplib.SMTPServerDisconnected

    monkeypatch.setattr("django.core.mail.message.EmailMessage.send", refuse)

    response = sign_in()

    assert response["Location"] == reverse("home")
    assert client.get(reverse("home")).status_code == 200
