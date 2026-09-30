from django.urls import path

from prototype_ui import aa, nav, views

urlpatterns = [
    path("", views.home, name="prototype-ui"),
    path("add/", views.add, name="prototype-ui-add"),
    path("nav/", nav.home, name="prototype-nav"),
    path("nav/<slug:key>/", nav.screen, name="prototype-nav-screen"),
    path("aa/", aa.activity, name="prototype-aa-activity"),
    path("aa/txn/<int:tid>/", aa.txn, name="prototype-aa-txn"),
    path("aa/accounts/", aa.accounts, name="prototype-aa-accounts"),
    path("aa/accounts/<slug:key>/", aa.account, name="prototype-aa-account"),
]
