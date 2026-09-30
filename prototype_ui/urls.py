from django.urls import path

from prototype_ui import nav, views

urlpatterns = [
    path("", views.home, name="prototype-ui"),
    path("add/", views.add, name="prototype-ui-add"),
    path("nav/", nav.home, name="prototype-nav"),
    path("nav/<slug:key>/", nav.screen, name="prototype-nav-screen"),
]
