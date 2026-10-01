"""Settings > Price feeds."""

from django.urls import path

from jobs import views

urlpatterns = [
    path("settings/price-feeds/", views.price_feeds, name="price_feeds"),
]
