import importlib
import json
from html.parser import HTMLParser

import pytest
from django.urls import reverse

import config.settings
from signin.tests import add_authenticator, start_sudo, verify

TAB_ROOTS = ["home", "activity", "accounts", "plan"]
STACKED = [
    "settings",
    "security",
    "password",
    "sessions",
    "security_log",
    "thresholds",
    "chart",
    "price_feeds",
    "new",
]


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def tags(response, name, **attrs):
    parser = _Tags()
    parser.feed(response.text)
    return [
        a
        for t, a in parser.tags
        if t == name and all(k in a and a[k] == v for k, v in attrs.items())
    ]


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        "akshay", first_name="Akshay", last_name="Prabhu"
    )


@pytest.fixture
def signed_in(client, user):
    client.force_login(user)
    verify(client, add_authenticator(user))
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("tab", TAB_ROOTS)
def test_tab_root_marks_its_own_tab(signed_in, tab):
    response = signed_in.get(reverse(tab))

    assert response.status_code == 200
    current = tags(response, "a", **{"aria-current": "page"})
    # Once in the phone tab bar, once in the desktop header.
    assert [a["href"] for a in current] == [reverse(tab)] * 2


@pytest.mark.django_db
@pytest.mark.parametrize("tab", TAB_ROOTS)
def test_tab_root_header_has_the_avatar(signed_in, tab):
    response = signed_in.get(reverse(tab))

    (avatar,) = tags(response, "a", href=reverse("settings"))
    assert avatar["aria-label"] == "Settings"
    assert ">AP</a>" in response.text


@pytest.mark.django_db
@pytest.mark.parametrize("tab", TAB_ROOTS)
def test_tab_bar_reaches_every_tab_without_adding_history(signed_in, tab):
    response = signed_in.get(reverse(tab))

    hrefs = {a["href"] for a in tags(response, "a") if "data-tab-link" in a}
    assert hrefs == {reverse(t) for t in TAB_ROOTS}


@pytest.mark.django_db
def test_stacked_screen_has_a_back_arrow(signed_in):
    response = signed_in.get(reverse("settings"))

    assert response.status_code == 200
    (back,) = tags(response, "a", **{"data-back": None})
    assert back["href"] == reverse("home")


@pytest.mark.django_db
@pytest.mark.parametrize("name", STACKED)
def test_stacked_screen_header_has_the_avatar(signed_in, name):
    start_sudo(signed_in)

    response = signed_in.get(reverse(name))

    assert response.status_code == 200
    (avatar,) = tags(response, "a", **{"aria-label": "Settings"})
    assert avatar["href"] == reverse("settings")
    assert ">AP</a>" in response.text
    assert ("aria-current" in avatar) == (name == "settings")


@pytest.mark.django_db
@pytest.mark.parametrize("tab", TAB_ROOTS)
def test_avatar_is_not_current_on_a_tab_root(signed_in, tab):
    (avatar,) = tags(signed_in.get(reverse(tab)), "a", **{"aria-label": "Settings"})

    assert "aria-current" not in avatar


@pytest.mark.django_db
def test_primary_plus_opens_a_new_transaction(signed_in):
    response = signed_in.get(reverse("home"))

    assert len(tags(response, "a", href=reverse("new"))) == 2
    assert signed_in.get(reverse("new")).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("name", [*TAB_ROOTS, "settings", "new"])
def test_every_page_requires_sign_in(client, name):
    response = client.get(reverse(name))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


@pytest.mark.django_db
def test_sign_in_page_is_open(client, user):
    assert client.get(reverse("login")).status_code == 200


@pytest.mark.django_db
def test_sign_out_from_settings(signed_in):
    response = signed_in.get(reverse("settings"))
    assert tags(response, "form", action=reverse("logout"), method="post")

    signed_in.post(reverse("logout"))

    assert signed_in.get(reverse("home")).status_code == 302


@pytest.mark.django_db
def test_strict_csp_with_htmx_and_no_inline_scripts(signed_in):
    response = signed_in.get(reverse("home"))

    csp = response["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "unsafe-inline" not in csp
    scripts = tags(response, "script")
    assert all(s.get("src") for s in scripts)
    assert any("htmx" in s["src"] for s in scripts)


@pytest.mark.django_db
def test_manifest_is_installable_without_sign_in(client):
    response = client.get(reverse("manifest"))

    assert response["Content-Type"] == "application/manifest+json"
    manifest = json.loads(response.content)
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == reverse("home")
    assert {i["sizes"] for i in manifest["icons"]} >= {"192x192", "512x512"}


@pytest.mark.django_db
def test_pages_link_the_manifest(signed_in):
    response = signed_in.get(reverse("home"))

    assert tags(response, "link", rel="manifest", href=reverse("manifest"))


def test_time_zone_ignores_the_environment(monkeypatch):
    monkeypatch.setenv("TIME_ZONE", "UTC")
    try:
        assert importlib.reload(config.settings).TIME_ZONE == "Asia/Kolkata"
    finally:
        monkeypatch.undo()
        importlib.reload(config.settings)
