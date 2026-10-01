"""Claiming the install, signing in and out."""

from django.contrib.auth import views as auth_views
from django.urls import path

from signin import views

urlpatterns = [
    path("claim/", views.claim, name="claim"),
    path("claim/owner/", views.claim_owner, name="claim_owner"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
