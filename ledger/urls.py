"""Settings > Chart of Accounts."""

from django.urls import path

from ledger import views

urlpatterns = [
    path("settings/chart-of-accounts/", views.chart_screen, name="chart"),
    path(
        "settings/chart-of-accounts/new/",
        views.new_account_sheet,
        name="chart_new",
    ),
    path(
        "settings/chart-of-accounts/<int:pk>/",
        views.account_sheet,
        name="chart_account",
    ),
    path(
        "settings/chart-of-accounts/roles/<str:role>/",
        views.repoint_role,
        name="chart_role",
    ),
]
