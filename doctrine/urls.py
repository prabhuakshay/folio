"""Settings > Doctrine thresholds."""

from django.urls import path

from doctrine import views

urlpatterns = [
    path(
        "settings/doctrine-thresholds/",
        views.thresholds_screen,
        name="thresholds",
    ),
    path(
        "settings/doctrine-thresholds/reset/",
        views.reset_all,
        name="thresholds_reset",
    ),
    path("settings/doctrine-thresholds/<str:key>/", views.edit, name="threshold"),
    path(
        "settings/doctrine-thresholds/<str:key>/reset/",
        views.reset,
        name="threshold_reset",
    ),
]
