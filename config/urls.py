"""Root URL configuration.

https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from config.health import healthz

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # No trailing slash: probes hit the exact path by convention.
    path("healthz", healthz, name="healthz"),
]

# PROTOTYPE — throwaway UI variants, never served in production.
if settings.DEBUG:
    urlpatterns += [path("prototype/ui/", include("prototype_ui.urls"))]
