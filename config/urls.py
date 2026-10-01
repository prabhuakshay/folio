"""Root URL configuration.

https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from config.crawlers import robots_txt
from config.health import healthz
from signin.views import admin_login

urlpatterns = [
    # Ahead of the admin's own login, so it has only one way in: Folio's.
    path(f"{settings.ADMIN_URL}login/", admin_login, name="admin_login"),
    path(settings.ADMIN_URL, admin.site.urls),
    # No trailing slash: probes hit the exact path by convention.
    path("healthz", healthz, name="healthz"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("", include("signin.urls")),
    path("", include("ui.urls")),
    path("", include("jobs.urls")),
    path("", include("doctrine.urls")),
    path("", include("ledger.urls")),
]
