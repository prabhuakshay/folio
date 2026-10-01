"""PROTOTYPE — Settings and first-run onboarding variants for the
"Settings and first-run onboarding" wayfinder ticket.

Three takes, switched with ?variant=AA|BB|CC on /prototype/ui/settings/ and
/prototype/ui/setup/. Settings opens from the avatar of navigation variant L.
Onboarding starts after the owner claims an empty install. Nothing persists.
Never merge to main.
"""

import json

from django.http import Http404
from django.shortcuts import render

from prototype_ui import settings_data as D
from prototype_ui.aa_ledger import _u
from prototype_ui.nav import _nav_context, _url as nav_url

VARIANTS = {
    "AA": "Index + checklist",
    "BB": "One page + wizard",
    "CC": "Rules first + starting point",
}

RULES = {
    "AA": "Settings is an index like Plan: grouped rows, each showing its current value, each opening its own screen. Thresholds are a table of rows with their band. Onboarding never blocks: an empty Home carries a Set up Folio checklist whose items open the real screens, and Folio is usable from the first tap.",
    "BB": "Settings is one long page you edit in place, with a jump strip of sections; only the Chart of Accounts, Price feeds and Security open screens of their own. Onboarding is a full-screen wizard, one question per step, with Back and Continue, ending on Home.",
    "CC": "Settings is ordered by what each setting changes, and the Doctrine reads as sentences with the value you can tap; anything you changed from the default is marked. Onboarding is one Starting point screen: a balance sheet you fill in any order, with the Stage ladder underneath lighting up as Folio gets what it needs to judge each Stage.",
}

DETAILS = {
    "profile": "Profile and retirement",
    "dependents": "Dependents",
    "rules": "Doctrine thresholds",
    "returns": "Target Allocation and returns",
    "chart": "Chart of Accounts",
    "tags": "Tags",
    "payees": "Payees",
    "feeds": "Price feeds",
    "notifications": "Notifications",
    "security": "Security and sign-in",
    "export": "Export everything",
}

CLAIM_STEPS = ["code", "password", "secure", "codes"]
WIZARD = ["you", "dependents", "start", "balances", "invest", "expense", "done"]
CHECKLIST = [
    (
        "you",
        "About you",
        "Date of birth and retirement age",
        "Dates your Retirement Goal",
        "profile",
    ),
    (
        "dependents",
        "Who relies on you",
        "Spouse, children, parents",
        "Sizes the cover you need",
        "dependents",
    ),
    (
        "start",
        "Pick a start date",
        "The day Folio's books open",
        "Everything before it is a balance",
        "start",
    ),
    (
        "bank",
        "Bank and cash",
        "Balances on the start date",
        "Lets Folio judge your starter fund and Emergency Fund",
        "account",
    ),
    (
        "cards",
        "Cards and Loans",
        "What you owe, with its terms",
        "Lets Folio judge credit and high-interest debt",
        "account",
    ),
    (
        "cas",
        "Import your mutual funds",
        "CAMS + KFintech CAS, full history",
        "Lets Folio project Goals and Retirement",
        "imports",
    ),
    (
        "grow",
        "Other investments",
        "EPF, PPF, deposits, demat, property",
        "Completes your Net Worth",
        "account",
    ),
    (
        "policies",
        "Insurance Policies",
        "Term and health cover",
        "Lets Folio judge Protection",
        "policies",
    ),
    (
        "expense",
        "Your monthly figures",
        "Spending and Take-home, until history builds",
        "Stand in until Folio has a year of history",
        "profile",
    ),
]


def _variant(request):
    v = request.GET.get("variant", "AA").upper()
    return v if v in VARIANTS else "AA"


def _base(request, screen, trail, parent=None, tab="home"):
    variant = _variant(request)
    ctx = _nav_context("L")
    from_setup = request.GET.get("setup") == "1"
    if from_setup:
        done = {d for d in request.GET.get("done", "").split(",") if d} | {
            request.GET.get("item", "")
        }
        parent_url, back_to = (
            _u("prototype-setup", variant, done=",".join(sorted(done - {""}))),
            "Set up Folio",
        )
    elif parent:
        parent_url, back_to = _u(parent, variant), "Settings"
    else:
        parent_url, back_to = nav_url("home", "L"), "Home"
    ctx.update(
        variant=variant,
        variant_name=VARIANTS[variant],
        variants_json=json.dumps(VARIANTS),
        rule=RULES[variant],
        screen=screen,
        tab=tab,
        root=False,
        parent_url=parent_url,
        back_to=back_to,
        trail=trail,
        from_setup=from_setup,
        tab_urls={
            "home": nav_url("home", "L"),
            "activity": _u("prototype-aa-activity", "P"),
            "accounts": _u("prototype-aa-accounts", "P"),
            "plan": _u("prototype-plan", "T"),
        },
        settings_url=_u("prototype-settings", variant),
        profile=D.PROFILE,
        dependents=D.DEPENDENTS,
        thresholds=D.THRESHOLDS,
        changed=[t for t in D.THRESHOLDS if t.get("changed")],
        returns=D.RETURNS,
        glide=D.GLIDE,
        drift=D.DRIFT,
        chart=D.CHART,
        roles=D.ROLES,
        tags=D.TAGS,
        payees=D.PAYEES,
        feeds=D.FEEDS,
        feed_log=D.FEED_LOG,
        manual=D.MANUAL,
        cc_groups=[
            (
                "How your books are kept",
                [
                    (
                        _u("prototype-setting", variant, "chart"),
                        "Chart of Accounts",
                        "41 Income and Expense Accounts · 10 roles",
                        False,
                    ),
                    (_u("prototype-setting", variant, "tags"), "Tags", "5 Tags", False),
                    (
                        _u("prototype-setting", variant, "payees"),
                        "Payees",
                        "212 Payees · 38 you added",
                        False,
                    ),
                ],
            ),
            (
                "Where prices come from",
                [
                    (
                        _u("prototype-setting", variant, "feeds"),
                        "Price feeds",
                        "Protean NPS failing since 28 Sep",
                        True,
                    ),
                ],
            ),
            (
                "How Folio reaches you",
                [
                    (
                        _u("prototype-setting", variant, "notifications"),
                        "Notifications",
                        "Daily Digest at 08:00 · 6 of 7 on",
                        False,
                    ),
                ],
            ),
            (
                "Keeping it yours",
                [
                    (
                        _u("prototype-setting", variant, "security"),
                        "Security and sign-in",
                        "2 passkeys · authenticator app · 8 recovery codes",
                        False,
                    ),
                    (
                        _u("prototype-setting", variant, "export"),
                        "Export everything",
                        "Last exported 14 Sep",
                        False,
                    ),
                ],
            ),
        ],
        bb_jump=[
            ("you", "You"),
            ("rules", "Rules"),
            ("books", "Books"),
            ("feeds", "Prices"),
            ("reminders", "Reminders"),
            ("security", "Security"),
            ("export", "Export"),
        ],
        reminders=D.REMINDERS,
        passkeys=D.PASSKEYS,
        sessions=D.SESSIONS,
        security_log=D.SECURITY_LOG,
        urls={k: _u("prototype-setting", variant, k) for k in DETAILS}
        | {
            "settings": _u("prototype-settings", variant),
            "setup": _u("prototype-setup", variant),
            "claim": _u("prototype-claim", variant),
            "imports": _u("prototype-imports", "YZ"),
            "upload": _u("prototype-imports-new", "YZ", f="cams"),
            "policies": _u("prototype-plan-policies", "Q"),
            "accounts": _u("prototype-aa-accounts", "P"),
        },
        jump=[
            ("Settings", _u("prototype-settings", variant)),
            *[
                (title, _u("prototype-setting", variant, k))
                for k, title in DETAILS.items()
            ],
            ("Claim · setup code", _u("prototype-claim", variant)),
            ("Claim · recovery codes", _u("prototype-claim", variant, step="codes")),
            *_setup_jumps(variant),
        ],
    )
    return variant, ctx


def _setup_jumps(variant):
    if variant == "AA":
        return [
            ("Setup · just claimed", _u("prototype-setup", variant)),
            (
                "Setup · halfway",
                _u("prototype-setup", variant, done="you,dependents,start,bank"),
            ),
            (
                "Setup · add an Account",
                _u(
                    "prototype-setup",
                    variant,
                    step="account",
                    done="you,dependents,start",
                ),
            ),
            (
                "Setup · all done",
                _u("prototype-setup", variant, done=",".join(c[0] for c in CHECKLIST)),
            ),
        ]
    if variant == "BB":
        return [
            (f"Wizard · {s}", _u("prototype-setup", variant, step=s)) for s in WIZARD
        ]
    return [
        ("Starting point · empty", _u("prototype-setup", variant)),
        ("Starting point · halfway", _u("prototype-setup", variant, filled="some")),
        (
            "Starting point · add a bank Account",
            _u("prototype-setup", variant, filled="some", sheet="bank"),
        ),
        ("Starting point · complete", _u("prototype-setup", variant, filled="all")),
    ]


def index(request):
    variant, ctx = _base(request, "settings", "Home › Settings")
    return render(request, f"prototype_ui/settings/{variant.lower()}_index.html", ctx)


def detail(request, key):
    if key not in DETAILS:
        raise Http404
    variant, ctx = _base(
        request, key, f"Home › Settings › {DETAILS[key]}", parent="prototype-settings"
    )
    edit = next((t for t in D.THRESHOLDS if t["key"] == request.GET.get("edit")), None)
    stages = {}
    for t in D.THRESHOLDS:
        stages.setdefault(t["stage"], []).append(t)
    order = [
        "Stage 2",
        "Stage 3",
        "Stage 4",
        "Stage 5",
        "Watched",
        "Goals",
        "Retirement",
    ]
    ctx.update(
        edit=edit, rule_groups=sorted(stages.items(), key=lambda kv: order.index(kv[0]))
    )
    ctx.update(
        title=DETAILS[key],
        sudo=request.GET.get("sudo") == "1",
        sudo_url=_u("prototype-setting", variant, key, sudo=1),
    )
    # Thresholds are where the variants disagree; the other screens are shared.
    name = f"{variant.lower()}_rules" if key == "rules" else key
    return render(request, f"prototype_ui/settings/{name}.html", ctx)


def claim(request):
    variant, ctx = _base(request, "claim", "First visit › Claim this Folio")
    step = request.GET.get("step", "code")
    step = step if step in CLAIM_STEPS else "code"
    i = CLAIM_STEPS.index(step)
    ctx.update(
        step=step,
        step_n=i + 1,
        steps=len(CLAIM_STEPS),
        next_url=_u("prototype-claim", variant, step=CLAIM_STEPS[i + 1])
        if i + 1 < len(CLAIM_STEPS)
        else _u("prototype-setup", variant),
        codes=[
            "k7fq-2m9x",
            "p3vd-8hwe",
            "t6zr-4ncu",
            "b9ma-7yjq",
            "h2xe-5rkp",
            "w8cn-3dtf",
            "q4lu-6gvb",
            "e5sy-9pmh",
            "r3jw-2akd",
            "u7bt-8xne",
        ],
    )
    return render(request, "prototype_ui/settings/claim.html", ctx)


def setup(request):
    variant, ctx = _base(request, "setup", "Home › Set up Folio")
    if variant == "AA":
        done = {d for d in request.GET.get("done", "").split(",") if d}
        items = []
        for key, title, what, unlocks, target in CHECKLIST:
            url = {
                "profile": _u(
                    "prototype-setting",
                    variant,
                    "profile",
                    setup=1,
                    done=",".join(done),
                    item=key,
                ),
                "dependents": _u(
                    "prototype-setting",
                    variant,
                    "dependents",
                    setup=1,
                    done=",".join(done),
                    item=key,
                ),
                "imports": _u("prototype-imports-new", "YZ", f="cams"),
                "policies": _u("prototype-plan-policies", "Q"),
                "start": _u(
                    "prototype-setup", variant, step="start", done=",".join(done)
                ),
                "account": _u(
                    "prototype-setup",
                    variant,
                    step="account",
                    done=",".join(done),
                    kind=key,
                ),
            }[target]
            items.append(
                {
                    "key": key,
                    "title": title,
                    "what": what,
                    "unlocks": unlocks,
                    "url": url,
                    "done": key in done,
                }
            )
        nxt = next((i for i in items if not i["done"]), None)
        ctx.update(
            items=items,
            next_item=nxt,
            done_n=sum(i["done"] for i in items),
            total=len(items),
            step=request.GET.get("step", ""),
            kind=request.GET.get("kind", "bank"),
            done_csv=",".join(done),
            back_url=_u("prototype-setup", variant, done=",".join(done)),
            finish_url=_u(
                "prototype-setup",
                variant,
                done=",".join(sorted(done | {request.GET.get("kind") or "start"})),
            ),
            added=[a for _, _, rows in D.START_ACCOUNTS for a in rows][:2]
            if "bank" in done
            else [],
            start_choices=D.START_CHOICES,
        )
        if not ctx["step"]:
            # The checklist is Home itself, so it has no Back.
            ctx.update(parent_url="", root=True)
        return render(request, "prototype_ui/settings/aa_setup.html", ctx)
    if variant == "BB":
        step = request.GET.get("step", "you")
        step = step if step in WIZARD else "you"
        i = WIZARD.index(step)
        ctx.update(
            step=step,
            step_n=i + 1,
            steps=len(WIZARD) - 1,
            next_url=_u("prototype-setup", variant, step=WIZARD[i + 1])
            if i + 1 < len(WIZARD)
            else nav_url("home", "L"),
            prev_url=_u("prototype-setup", variant, step=WIZARD[i - 1])
            if i
            else _u("prototype-claim", variant, step="codes"),
            skip=step in ("dependents", "invest"),
            start_choices=D.START_CHOICES,
            groups=D.START_ACCOUNTS,
            home_url=nav_url("home", "L"),
        )
        return render(request, "prototype_ui/settings/bb_setup.html", ctx)
    filled = request.GET.get("filled", "")
    have = {
        "": set(),
        "some": {"you", "bank", "cards"},
        "all": {"you", "bank", "cards", "grow", "policies", "expense"},
    }[filled if filled in ("some", "all") else ""]
    groups = []
    for label, hint, rows in D.START_ACCOUNTS:
        key = {"Spend from": "bank", "Owe": "cards", "Grow": "grow", "Own": "grow"}[
            label
        ]
        groups.append(
            {
                "label": label,
                "hint": hint,
                "rows": rows if key in have else [],
                "key": key,
            }
        )
    ladder = []
    for n, (name, needs, keys) in enumerate(D.LADDER, 1):
        ladder.append(
            {"n": n, "name": name, "needs": needs, "judged": set(keys) <= have}
        )
    ctx.update(
        filled=filled,
        have=have,
        groups=groups,
        ladder=ladder,
        judged_n=sum(s["judged"] for s in ladder),
        net="₹1,05,96,220"
        if filled == "all"
        else ("₹2,27,520" if filled == "some" else "₹0"),
        sheet=request.GET.get("sheet", ""),
        close_url=_u("prototype-setup", variant, filled=filled),
        add_url=_u("prototype-setup", variant, filled=filled, sheet="bank"),
        parent_url="",
        root=True,
    )
    return render(request, "prototype_ui/settings/cc_setup.html", ctx)
