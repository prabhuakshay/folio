from django.urls import path

from prototype_ui import views

urlpatterns = [
    path("", views.home, name="prototype-ui"),
    path("add/", views.add, name="prototype-ui-add"),
]
