"""App shell URLs: the four tab roots, the screens stacked on them."""

from typing import TYPE_CHECKING

from django.urls import path
from django.views.generic import TemplateView

from ui import views

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpResponse


def screen(template: str, **context: str) -> Callable[..., HttpResponse]:
    """Serve a template with the shell's navigation context.

    Args:
        template: Template name under `ui/`.
        **context: `tab` marks the active tab; `back` names the URL a stacked
            screen's back arrow returns to, and `title` heads that screen.

    Returns:
        The view.
    """
    return TemplateView.as_view(template_name=f"ui/{template}", extra_context=context)


urlpatterns = [
    path("", screen("home.html", tab="home"), name="home"),
    path("activity/", screen("activity.html", tab="activity"), name="activity"),
    path("accounts/", screen("accounts.html", tab="accounts"), name="accounts"),
    path("plan/", screen("plan.html", tab="plan"), name="plan"),
    path(
        "settings/",
        screen("settings.html", tab="home", back="home", title="Settings"),
        name="settings",
    ),
    path(
        "new/",
        screen("new.html", back="home", title="New transaction"),
        name="new",
    ),
    path("manifest.webmanifest", views.manifest, name="manifest"),
]
