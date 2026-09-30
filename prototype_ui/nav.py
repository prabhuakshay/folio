"""PROTOTYPE — navigation variants for the "App navigation beyond home" ticket.

Three ways to reach everything beyond J's four home pages, switched with
?variant=K|L|M on /prototype/ui/nav/. Screens are stubs: they settle where
things sit and how you get there, not what they show. Never merge to main.
"""

import json
from urllib.parse import quote

from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from prototype_ui.data import ACCOUNTS, UPCOMING
from prototype_ui.views import _context, money

NAV_VARIANTS = {
    "K": "Drill + More sheet",
    "L": "Tab bar",
    "M": "Find anywhere",
}

RULES = {
    "K": "Home stays the hub. Anything a home page owns is reached by tapping it; the rest sits in a More sheet on the bar. Every other screen is pushed with a back arrow.",
    "L": "Four persistent tabs — Home, Activity, Accounts, Plan — with + in the middle. Screens stack inside their tab; the bar never leaves.",
    "M": "No menu. Home drills as in K; everything else is one search away — the magnifier on the bar (or / on desktop) opens Find, which lists every place and every Account, Goal, Policy and payee.",
}

# key: (title, parent in K/M, parent in L, L tab). Parent "home:N" is home page N.
SCREENS = {
    "transactions": ("Transactions", "home:1", None, "activity"),
    "accounts": ("Accounts", "home:0", None, "accounts"),
    "account": ("Account", "accounts", "accounts", "accounts"),
    "imports": ("Imports", "home:0", "accounts", "accounts"),
    "plan": ("Plan", "home:0", None, "plan"),
    "budget": ("Budget", "home:1", "plan", "plan"),
    "recurring": ("Recurring", "home:0", "plan", "plan"),
    "policies": ("Policies", "scorecard", "plan", "plan"),
    "policy": ("Policy", "policies", "policies", "plan"),
    "goal": ("Goal", "home:3", "home:3", "home"),
    "scorecard": ("Before Goals", "home:3", "home:3", "home"),
    "report": ("Report", "home:0", "home:0", "home"),
    "settings": ("Settings", "home:0", "home:0", "home"),
    "setting": ("Setting", "settings", "settings", "home"),
}

PLACES = [
    (
        "Money",
        [
            ("transactions", "Transactions", "list", "128 in September"),
            ("accounts", "Accounts", "wallet", "11 open · ₹58.85 L net"),
            ("recurring", "Recurring", "repeat", "2 due this week"),
        ],
    ),
    (
        "Plan",
        [
            ("budget", "Budget", "gauge", "₹7,480 left in September"),
            ("scorecard", "Before Goals", "list-checks", "Step 3 of 6 · Protection"),
            ("policies", "Policies", "shield", "4 policies · 1 renews in 18 days"),
        ],
    ),
    (
        "Folio",
        [
            ("imports", "Imports", "file-down", "Last CAS 12 Sep"),
            ("settings", "Settings", "settings", "Profile, feeds, security, export"),
        ],
    ),
]

POLICIES = [
    ("HDFC Click 2 Protect", "Term life", "₹1.00 Cr", "Renews 14 Mar", False),
    ("Star Health Family Floater", "Health · base", "₹10 L", "Renews 18 Oct", True),
    (
        "Care Supreme top-up",
        "Health · top-up",
        "₹25 L over ₹10 L",
        "Renews 2 Jan",
        False,
    ),
    ("Acme group health", "Employer", "₹5 L", "Shown, not counted", False),
]

SETTINGS = [
    ("You", ["Profile and retirement", "Dependents"]),
    (
        "Money",
        [
            "Chart of Accounts",
            "Tags",
            "Target Allocation and returns",
            "Doctrine thresholds",
            "Price feeds",
        ],
    ),
    ("Folio", ["Notifications", "Security and sign-in", "Export everything"]),
]

SCHEDULES = [
    ("Rent to Mr. Rao", "Monthly · 1st · ₹32,000", "house"),
    ("Parag Parikh SIP", "Monthly · 5th · ₹10,000 · Retirement", "chart-line"),
    ("Airtel broadband", "Monthly · 2nd · about ₹1,179", "wifi"),
    ("SBI Home loan EMI", "From the Loan's terms · 28th", "house"),
    ("ICICI card bill", "From the Card's cycle · 12th", "credit-card"),
    ("PPF top-up", "Yearly · 1 Apr · ₹1,50,000", "piggy-bank"),
]

IMPORTS = [
    ("CAMS + KFintech CAS", "12 Sep · 214 lines posted", False),
    ("NSDL CAS", "3 Sep · 2 unit mismatches flagged", True),
    ("CAMS + KFintech CAS", "10 Aug · undone", False),
]

PAYEES = ["Swiggy", "Zepto", "BigBasket", "Uber", "HP Petrol", "Apollo Pharmacy"]


def _variant(request):
    variant = request.GET.get("variant", "K").upper()
    return variant if variant in NAV_VARIANTS else "K"


def _url(key, variant, name=None):
    if key.startswith("home"):
        page = key.partition(":")[2] or "0"
        return f"{reverse('prototype-nav')}?variant={variant}&page={page}"
    url = f"{reverse('prototype-nav-screen', args=[key])}?variant={variant}"
    return f"{url}&name={quote(name)}" if name else url


def _parent(key, variant):
    _, parent_km, parent_l, _ = SCREENS[key]
    return parent_l if variant == "L" else parent_km


def _trail(key, variant, name):
    # Walk parents up to home so the state panel shows where Back leads.
    trail = [name or SCREENS[key][0]]
    parent = _parent(key, variant)
    while parent and not parent.startswith("home"):
        trail.append(SCREENS[parent][0])
        parent = _parent(parent, variant)
    if parent:
        trail.append(
            ["Overview", "Spend", "Invest", "Goals"][int(parent.partition(":")[2])]
        )
    return " › ".join(reversed(trail))


def _back_label(parent):
    if not parent:
        return "— (tab root)"
    if parent.startswith("home"):
        return "Home › " + ["Overview", "Spend", "Invest", "Goals"][int(parent[5:])]
    return SCREENS[parent][0]


def _nav_context(variant):
    ctx = _context("J")
    places = [
        (group, [(k, t, i, h, _url(k, variant)) for k, t, i, h in rows])
        for group, rows in PLACES
    ]
    find = [
        {"title": t, "hint": h, "icon": i, "url": u, "group": "Places"}
        for _, rows in places
        for k, t, i, h, u in rows
    ]
    find += [
        {
            "title": n,
            "hint": f"{group} · {money(b)['text']}",
            "icon": "wallet",
            "url": _url("account", variant, n),
            "group": "Accounts",
        }
        for group, rows in ACCOUNTS
        for n, _, _, b in rows
    ]
    find += [
        {
            "title": g["name"],
            "hint": f"{g['have']} of {g['target']}",
            "icon": g["icon"],
            "url": _url("goal", variant, g["name"]),
            "group": "Goals",
        }
        for g in ctx["goals"]
    ]
    find += [
        {
            "title": n,
            "hint": f"{kind} · {cover}",
            "icon": "shield",
            "url": _url("policy", variant, n),
            "group": "Policies",
        }
        for n, kind, cover, _, _ in POLICIES
    ]
    find += [
        {
            "title": s,
            "hint": f"Settings › {group}",
            "icon": "settings",
            "url": _url("setting", variant, s),
            "group": "Settings",
        }
        for group, rows in SETTINGS
        for s in rows
    ]
    find += [
        {
            "title": p,
            "hint": "Payee · transactions",
            "icon": "receipt",
            "url": _url("transactions", variant, p),
            "group": "Payees",
        }
        for p in PAYEES
    ]
    ctx.update(
        variant=variant,
        variant_name=NAV_VARIANTS[variant],
        variants_json=json.dumps(NAV_VARIANTS),
        rule=RULES[variant],
        q=f"?variant={variant}",
        places=places,
        find=find,
        home_url=_url("home", variant),
        tab_urls={
            "home": _url("home", variant),
            "activity": _url("transactions", variant),
            "accounts": _url("accounts", variant),
            "plan": _url("plan", variant),
        },
        settings_url=_url("settings", variant),
        tabs_left=[("home", "Home", "house"), ("activity", "Activity", "list")],
        tabs_right=[("accounts", "Accounts", "wallet"), ("plan", "Plan", "compass")],
    )
    return ctx


def home(request):
    variant = _variant(request)
    ctx = _nav_context(variant)
    ctx.update(screen="home", tab="home", trail="Home", back_to="—")
    return render(request, "prototype_ui/nav_home.html", ctx)


def screen(request, key):
    if key not in SCREENS:
        raise Http404
    variant = _variant(request)
    name = request.GET.get("name", "")
    parent = _parent(key, variant)
    ctx = _nav_context(variant)
    ctx.update(
        screen=key,
        title=name or SCREENS[key][0],
        name=name,
        tab=SCREENS[key][3],
        parent_url=_url(parent, variant) if parent else "",
        trail=_trail(key, variant, name),
        back_to=_back_label(parent),
        policies=[
            {
                "name": n,
                "kind": k,
                "cover": c,
                "when": w,
                "soon": s,
                "url": _url("policy", variant, n),
            }
            for n, k, c, w, s in POLICIES
        ],
        settings_groups=[
            (g, [(s, _url("setting", variant, s)) for s in rows])
            for g, rows in SETTINGS
        ],
        schedules=SCHEDULES,
        imports=IMPORTS,
        accounts_url=_url("accounts", variant),
        policies_url=_url("policies", variant),
        imports_url=_url("imports", variant),
        account_rows=[
            (
                group,
                money(sum(r[3] for r in rows)),
                [
                    (n, mark, color, money(b), _url("account", variant, n))
                    for n, mark, color, b in rows
                ],
            )
            for group, rows in ACCOUNTS
        ],
        upcoming_rows=[{**u, "money": money(u["amount"])} for u in UPCOMING],
        txns=[
            t
            for t in ctx["transactions"]
            if key != "transactions" or not name or t["payee"] == name
        ],
        root=not parent,
        balance=money(
            next(
                (b for _, rows in ACCOUNTS for n, _, _, b in rows if n == name),
                184320.45,
            )
        ),
        plan_places=[
            (group, [p for p in rows if p[0] in keys])
            for group, keys in [
                ("This month", {"budget", "recurring"}),
                ("Before Goals", {"scorecard", "policies"}),
            ]
            for rows in [[r for _, rs in ctx["places"] for r in rs]]
        ],
    )
    return render(request, "prototype_ui/nav_screen.html", ctx)
