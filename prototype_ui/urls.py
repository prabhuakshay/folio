from django.urls import path

from prototype_ui import aa, goals, imports, nav, plan, settings, views

urlpatterns = [
    path("", views.home, name="prototype-ui"),
    path("add/", views.add, name="prototype-ui-add"),
    path("nav/", nav.home, name="prototype-nav"),
    path("nav/<slug:key>/", nav.screen, name="prototype-nav-screen"),
    path("aa/", aa.activity, name="prototype-aa-activity"),
    path("aa/txn/<int:tid>/", aa.txn, name="prototype-aa-txn"),
    path("aa/accounts/", aa.accounts, name="prototype-aa-accounts"),
    path("aa/accounts/<slug:key>/", aa.account, name="prototype-aa-account"),
    path("plan/", plan.root, name="prototype-plan"),
    path("plan/budget/", plan.budget, name="prototype-plan-budget"),
    path("plan/recurring/", plan.recurring, name="prototype-plan-recurring"),
    path(
        "plan/occurrence/<slug:key>/", plan.occurrence, name="prototype-plan-occurrence"
    ),
    path("plan/schedule/<slug:key>/", plan.schedule, name="prototype-plan-schedule"),
    path("plan/policies/", plan.policies, name="prototype-plan-policies"),
    path("plan/policies/<slug:key>/", plan.policy, name="prototype-plan-policy"),
    path("goals/<slug:key>/", goals.goal, name="prototype-goal"),
    path("goals/<slug:key>/earmarks/", goals.earmarks, name="prototype-goal-earmarks"),
    path("before-goals/", goals.before_goals, name="prototype-before-goals"),
    path("imports/", imports.index, name="prototype-imports"),
    path("imports/new/", imports.new, name="prototype-imports-new"),
    path("imports/staged/", imports.staged, name="prototype-imports-staged"),
    path("imports/<slug:key>/", imports.detail, name="prototype-import"),
    path("settings/", settings.index, name="prototype-settings"),
    path("settings/<slug:key>/", settings.detail, name="prototype-setting"),
    path("claim/", settings.claim, name="prototype-claim"),
    path("setup/", settings.setup, name="prototype-setup"),
]
