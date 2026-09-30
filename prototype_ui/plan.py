"""PROTOTYPE — Plan tab variants for the wayfinder ticket.

Three takes on what the Plan tab shows — its root, the Budget, Recurring and
Policies — switched with ?variant=Q|R|S on /prototype/ui/plan/. They sit inside
navigation variant L's tab bar, next to Activity and Accounts variant P. Never
merge to main.
"""

import json

from django.http import Http404
from django.shortcuts import render
from django.template.loader import select_template

from prototype_ui import plan_data as B
from prototype_ui.aa_ledger import _u
from prototype_ui.nav import _nav_context, _url as nav_url
from prototype_ui.plan_policies import FLOOR, LIFE, PEOPLE, POLICIES
from prototype_ui.plan_recurring import DONE, OCCURRENCES
from prototype_ui.plan_schedules import FROM_TERMS, MONTHLY, SCHEDULES
from prototype_ui.views import money

VARIANTS = {
    "Q": "Rooms",
    "R": "The month",
    "S": "What needs you",
    "T": "Chosen",
}

RULES = {
    "Q": "Plan is an index of four rooms, each with one live line. Budget is a top-down waterfall to spendable, then limits, then surplus. Recurring splits Due and Schedules; confirming or linking happens in a bottom sheet. Policies are grouped by what they count toward; a Policy is a plain record.",
    "R": "Plan is this Budget month on one page. Budget is one sentence of arithmetic and a burn-down of spendable. Recurring is a timeline through the month; each Occurrence opens in place to confirm or link, and Schedules group by the Account they leave. Policies are cover per person against the floor and the life need.",
    "T": "The picks so far: Q everywhere, with a Budget that mixes Q's waterfall bars and S's itemised ledger, limits table and surplus decision. Recurring is still to choose.",
    "S": "Plan opens with a queue of what needs a decision, then quiet links. Budget is an itemised ledger — every Occurrence behind every line — with limits as a table. Confirming an Occurrence is its own screen that shows the Match. Policies open with the Doctrine's verdict and gaps; a Policy leads with whether it counts.",
}

CLASS_NAMES = {
    "income": "Expected income",
    "savings": "Savings",
    "committed": "Committed",
    "excluded": "Excluded from the Budget",
}

CASH_SIDE = ("HDFC Savings", "SBI Salary", "Cash", "ICICI Amazon Pay")

STATUS_NAMES = {
    "overdue": "Overdue",
    "today": "Due today",
    "soon": "Next 7 days",
    "later": "Later in October",
}


def _variant(request):
    v = request.GET.get("variant", "Q").upper()
    return v if v in VARIANTS else "Q"


def _base(request, screen, parent=None, back_to="— (tab root)", trail="Plan"):
    variant = _variant(request)
    ctx = _nav_context("L")
    ctx.update(
        variant=variant,
        variant_name=VARIANTS[variant],
        variants_json=json.dumps(VARIANTS),
        rule=RULES[variant],
        screen=screen,
        tab="plan",
        root=parent is None,
        parent_url=_u(parent, variant) if parent else "",
        back_to=back_to,
        trail=trail,
        tab_urls={
            "home": nav_url("home", "L"),
            "activity": _u("prototype-aa-activity", "P"),
            "accounts": _u("prototype-aa-accounts", "P"),
            "plan": _u("prototype-plan", variant),
        },
        settings_url=nav_url("settings", "L"),
        urls={
            "plan": _u("prototype-plan", variant),
            "budget": _u("prototype-plan-budget", variant),
            "recurring": _u("prototype-plan-recurring", variant),
            "schedules": _u("prototype-plan-recurring", variant, view="schedules"),
            "policies": _u("prototype-plan-policies", variant),
            "scorecard": _u("prototype-before-goals", "U"),
            "activity": _u("prototype-aa-activity", "P"),
            "uncategorised": _u("prototype-aa-activity", "P", type="uncategorised"),
            "hdfc": _u("prototype-aa-account", "P", "hdfc"),
            "icici": _u("prototype-aa-account", "P", "icici"),
            "epf": _u("prototype-aa-account", "P", "epf"),
        },
        jump=[
            ("Plan", _u("prototype-plan", variant)),
            ("Budget", _u("prototype-plan-budget", variant)),
            ("Recurring · Due", _u("prototype-plan-recurring", variant)),
            ("Recurring · Schedules", _u("prototype-plan-recurring", variant, view="schedules")),
            ("Occurrence · overdue with a Match", _u("prototype-plan-occurrence", variant, "bescom")),
            ("Occurrence · EPF interest", _u("prototype-plan-occurrence", variant, "epf")),
            ("Schedule · out of order", _u("prototype-plan-schedule", variant, "europe")),
            ("Schedule · paused", _u("prototype-plan-schedule", variant, "cult")),
            ("Policies", _u("prototype-plan-policies", variant)),
            ("Policy · renews soon", _u("prototype-plan-policy", variant, "star")),
            ("Policy · endowment", _u("prototype-plan-policy", variant, "endow")),
            ("Policy · employer", _u("prototype-plan-policy", variant, "acme")),
        ],
    )
    ctx.update(_budget(variant), **_recurring(variant), **_policies(variant))
    return variant, ctx


def _budget(variant):
    spend = [
        {
            "name": n,
            "spent": money(s),
            "limit": money(lim) if lim else None,
            "pct": min(100, round(s / lim * 100)) if lim else None,
            "over": money(s - lim) if lim and s > lim else None,
            "left": money(lim - s) if lim and s <= lim else None,
            "share": round(s / B.SPENT * 100),
            "color": c,
            "icon": i,
        }
        for n, s, lim, c, i in B.SPEND
    ]
    yearly = [
        {
            "name": n,
            "spent": money(s),
            "limit": money(lim),
            "pct": round(s / lim * 100),
            "left": money(lim - s),
            "color": c,
            "icon": i,
        }
        for n, s, lim, c, i in B.YEARLY_LIMITS
    ]
    target = B.INCOME * B.SAVINGS_RATE
    return {
        "month": B.MONTH,
        "b": {
            "income": money(B.INCOME),
            "savings": money(B.SAVINGS),
            "target": money(target),
            "rate": round(B.SAVINGS_RATE * 100),
            "scheduled": money(B.SCHEDULED_SAVINGS),
            "unscheduled": money(target - B.SCHEDULED_SAVINGS),
            "committed": money(B.COMMITTED),
            "spendable": money(B.SPENDABLE),
            "spent": money(B.SPENT),
            "left": money(B.LEFT),
            "spent_pct": round(B.SPENT / B.SPENDABLE * 100),
            "card_bill": money(B.CARD_BILL_EXCLUDED),
            # Widths of each waterfall step as a share of income.
            "w_savings": round(B.SAVINGS / B.INCOME * 100, 1),
            "w_committed": round(B.COMMITTED / B.INCOME * 100, 1),
            "w_spent": round(B.SPENT / B.INCOME * 100, 1),
            "w_left": round(B.LEFT / B.INCOME * 100, 1),
        },
        "savings_lines": [
            {"name": n, "amount": money(a), "note": note, "url": _u("prototype-plan-schedule", variant, k)}
            for n, a, note, k in B.SAVINGS_LINES
        ],
        "committed_lines": [
            {"name": n, "amount": money(a), "note": note, "url": _u("prototype-plan-occurrence", variant, k)}
            for n, a, note, k in B.COMMITTED_LINES
        ],
        "spend": spend,
        "limits": [s for s in spend if s["limit"]],
        "yearly": yearly,
        "over_limits": [s for s in spend if s["over"]],
        "pace": [
            {"day": d, "spent": money(s), "pct": round(s / B.SPENDABLE * 100), "x": round(d / 30 * 100, 1)}
            for d, s in B.PACE
        ],
        "stage": B.STAGE,
        "ladder": B.LADDER,
        "surplus": [{"name": n, "amount": money(a), "note": note} for n, a, note in B.SURPLUS],
        "surplus_total": money(sum(a for _, a, _ in B.SURPLUS)),
    }


def _occ(o, variant):
    return {
        **o,
        "money": money(o["amount"]),
        "tilde": "~" if o["estimated"] else "",
        "class_name": CLASS_NAMES[o["cls"]],
        "url": _u("prototype-plan-occurrence", variant, o["key"]),
        "schedule_url": _u("prototype-plan-schedule", variant, o["schedule"]) if o["schedule"] else "",
        "match_money": money(o["match"]["amount"]) if o["match"] else None,
    }


def _sched(key, s, variant):
    return {
        **s,
        "key": key,
        "money": money(s["amount"]),
        "tilde": "~" if s["estimated"] else "",
        "class_name": CLASS_NAMES[s["cls"]],
        "paused": s.get("paused", ""),
        "url": _u("prototype-plan-schedule", variant, key),
    }


def _recurring(variant):
    occs = [_occ(o, variant) for o in OCCURRENCES]
    scheds = [_sched(k, s, variant) for k, s in SCHEDULES.items()]
    by_from = {}
    for s in scheds:
        leg = next(n for n, _ in s["template"] if n in CASH_SIDE)
        by_from.setdefault(leg, []).append(s)
    return {
        "occurrences": occs,
        "occ_groups": [
            {"key": k, "name": n, "items": [o for o in occs if o["status"] == k]}
            for k, n in STATUS_NAMES.items()
        ],
        "needs_you": [o for o in occs if o["status"] in ("overdue", "today")],
        "done": [
            {"name": n, "date": d, "money": money(a), "how": how, "cls": c}
            for n, d, a, how, c in DONE
        ],
        "schedules": scheds,
        "sched_groups": [
            {
                "name": CLASS_NAMES[c],
                "items": [s for s in scheds if s["cls"] == c],
                "total": money(sum(s["amount"] for s in scheds if s["cls"] == c and "Monthly" in s["every"] and not s["paused"])),
            }
            for c in ("income", "savings", "committed")
        ],
        "sched_by_from": [{"name": n, "items": items} for n, items in by_from.items()],
        "from_terms": FROM_TERMS,
        "monthly": {k: money(v) for k, v in MONTHLY.items()},
    }


def _policies(variant):
    pols = [
        {**p, "key": k, "url": _u("prototype-plan-policy", variant, k)}
        for k, p in POLICIES.items()
    ]
    return {
        "policies": pols,
        "policy_groups": [
            ("Life cover", "Counted when you're the life assured", [p for p in pols if p["counts"] == "life"]),
            ("Health cover", "Counted toward each person's ₹10 L floor", [p for p in pols if p["counts"] == "health"]),
            ("Recorded only", "Shown, never counted", [p for p in pols if p["counts"] == "none"]),
        ],
        "people": [
            {
                **person,
                "pct": min(100, round(person["health"] / FLOOR * 100)),
                "policies": [p for p in pols if person["name"] in p["persons"]],
            }
            for person in PEOPLE
        ],
        "floor": money(FLOOR),
        "life": LIFE,
        "renewing": [p for p in pols if p["status"] == "soon"],
    }


def _render(request, variant, screen, ctx):
    # T holds only the screens that differ from the Q it was picked from.
    names = [f"prototype_ui/plan/{variant.lower()}_{screen}.html"]
    if variant == "T":
        names.append(f"prototype_ui/plan/q_{screen}.html")
    return render(request, select_template(names).template.name, ctx)


def root(request):
    variant, ctx = _base(request, "plan")
    return _render(request, variant, "root", ctx)


def budget(request):
    variant, ctx = _base(request, "budget", "prototype-plan", "Plan", "Plan › Budget")
    return _render(request, variant, "budget", ctx)


def recurring(request):
    variant, ctx = _base(request, "recurring", "prototype-plan", "Plan", "Plan › Recurring")
    ctx["view"] = request.GET.get("view", "due")
    ctx["open"] = request.GET.get("open", "")
    return _render(request, variant, "recurring", ctx)


def occurrence(request, key):
    o = next((o for o in OCCURRENCES if o["key"] == key), None)
    if not o:
        raise Http404
    variant, ctx = _base(
        request, "occurrence", "prototype-plan-recurring", "Recurring", f"Plan › Recurring › {o['name']}"
    )
    ctx["o"] = _occ(o, variant)
    return _render(request, variant, "occurrence", ctx)


def schedule(request, key):
    if key not in SCHEDULES:
        raise Http404
    variant, ctx = _base(
        request, "schedule", "prototype-plan-recurring", "Recurring", f"Plan › Recurring › {SCHEDULES[key]['name']}"
    )
    ctx["parent_url"] = _u("prototype-plan-recurring", variant, view="schedules")
    ctx["s"] = _sched(key, SCHEDULES[key], variant)
    ctx["s_occurrences"] = [o for o in ctx["occurrences"] if o["schedule"] == key]
    ctx["s_done"] = [d for d in ctx["done"] if d["name"] == SCHEDULES[key]["name"]]
    return _render(request, variant, "schedule", ctx)


def policies(request):
    variant, ctx = _base(request, "policies", "prototype-plan", "Plan", "Plan › Policies")
    return _render(request, variant, "policies", ctx)


def policy(request, key):
    if key not in POLICIES:
        raise Http404
    variant, ctx = _base(
        request, "policy", "prototype-plan-policies", "Policies", f"Plan › Policies › {POLICIES[key]['name']}"
    )
    p = next(p for p in ctx["policies"] if p["key"] == key)
    if p["premium"]:
        p = {**p, "premium_url": _u("prototype-plan-schedule", variant, p["premium"][2])}
    ctx["p"] = p
    return _render(request, variant, "policy", ctx)
