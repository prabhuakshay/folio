"""Claiming the install, signing in and out, and Security and sign-in."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from signin import passkeys, security, views
from signin.middleware import second_factor_not_required

urlpatterns = [
    path("claim/", views.claim, name="claim"),
    path("claim/owner/", views.claim_owner, name="claim_owner"),
    path("protect/", views.protect, name="protect"),
    path("protect/authenticator/", views.authenticator, name="authenticator"),
    path("protect/recovery-codes/", views.recovery_codes, name="recovery_codes"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("login/verify/", views.verify, name="verify"),
    path("confirm/", views.confirm, name="confirm"),
    path(
        "logout/",
        second_factor_not_required(auth_views.LogoutView.as_view()),
        name="logout",
    ),
    path("passkeys/", include(passkeys)),
    path("settings/security/", include(security)),
]
