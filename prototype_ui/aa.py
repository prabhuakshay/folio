"""PROTOTYPE — Activity and Accounts tab variants for the wayfinder ticket.

Three takes on what the Activity and Accounts tabs show, switched with
?variant=N|O|P on /prototype/ui/aa/. They sit inside navigation variant L's
tab bar; Home and Plan lead back to that prototype. Never merge to main.
"""

import json
from collections import defaultdict

from django.http import Http404
from django.shortcuts import render

from prototype_ui.aa_data import (
    ACCTS,
    ASSET_GROUPS,
    GROUPS,
    LEAVES,
    LIABILITY_GROUPS,
    PURPOSES,
    TAGS,
    TODAY,
)
from prototype_ui.aa_ledger import (
    KIND_NAMES,
    _acct_name,
    _matches,
    _row,
    _summary,
    _txns,
    _u,
    _variant,
)
from prototype_ui.nav import _nav_context, _url as nav_url
from prototype_ui.views import money

VARIANTS = {
    "N": "Plain",
    "O": "Ledger",
    "P": "Kind-first",
}

RULES = {
    "N": "Plain money, postings hidden. Activity is a day feed with type chips and a filter sheet. A Transaction reads as a sentence with fields; its Postings sit behind a disclosure. Accounts follow the Chart of Accounts groups; every Account detail is the same frame — figure, sentence, four tiles, tabs.",
    "O": "Double-entry up front. Activity is a register by month with In/Out totals and a filter bar. A Transaction is its Postings table. Accounts is the balance sheet, with Income & Expenses one toggle away. Account detail is a register with a running balance under a one-line terms strip.",
    "P": "Each kind gets its own screen. Activity has lenses — by day, by Payee, by Tag — and a review queue on top. A Transaction is edited as the quick-add sentence. Accounts are grouped by what they're for, each row showing its kind's one key fact; Account detail leads with that kind's hero.",
}

TYPE_CHIPS = [
    ("", "All"),
    ("spending", "Spending"),
    ("income", "Income"),
    ("transfer", "Transfers"),
    ("investment", "Investments"),
    ("uncategorised", "Uncategorised"),
]


def _base(request, screen, tab):
    variant = _variant(request)
    ctx = _nav_context("L")
    ctx.update(
        variant=variant,
        variant_name=VARIANTS[variant],
        variants_json=json.dumps(VARIANTS),
        rule=RULES[variant],
        screen=screen,
        tab=tab,
        root=screen in ("activity", "accounts"),
        tab_urls={
            "home": nav_url("home", "L"),
            "activity": _u("prototype-aa-activity", variant),
            "accounts": _u("prototype-aa-accounts", variant),
            "plan": nav_url("plan", "L"),
        },
        settings_url=nav_url("settings", "L"),
        imports_url=nav_url("imports", "L"),
        accounts_url=_u("prototype-aa-accounts", variant),
        activity_url=_u("prototype-aa-activity", variant),
        kind_links=[
            (KIND_NAMES[a["kind"]], a["name"], _u("prototype-aa-account", variant, k))
            for k, a in ACCTS.items()
            if k in ("hdfc", "icici", "homeloan", "ppfas", "sgb", "fd", "ppf", "epf")
        ],
    )
    return variant, ctx


def activity(request):
    variant, ctx = _base(request, "activity", "activity")
    f = {k: request.GET.get(k, "") for k in ("type", "tag", "payee", "account", "q")}
    lens = request.GET.get("lens", "days")
    txns = _txns(variant)
    shown = [t for t in txns if _matches(t, f)]

    def link(**changes):
        return _u("prototype-aa-activity", variant, **{**f, "lens": lens, **changes})

    months = defaultdict(list)
    for t in shown:
        months[t["month"]].append(t)
    payees = defaultdict(list)
    for t in shown:
        payees[t["payee"]].append(t)
    tags = defaultdict(list)
    for t in txns:
        for tag in t["tags"]:
            tags[tag].append(t)
    ctx.update(
        f=f,
        lens=lens,
        filtered=any(f.values()),
        txns=shown,
        clear_url=_u("prototype-aa-activity", variant, lens=lens),
        chips=[(label, link(type=key), f["type"] == key) for key, label in TYPE_CHIPS],
        lenses=[
            (label, link(lens=key), lens == key)
            for key, label in [
                ("days", "By day"),
                ("payees", "By Payee"),
                ("tags", "By Tag"),
            ]
        ],
        tag_links=[(t, link(tag=t, lens="days"), f["tag"] == t) for t in TAGS],
        account_links=[
            (a["name"], link(account=k), f["account"] == k) for k, a in ACCTS.items()
        ],
        account_label=_acct_name(f["account"]) if f["account"] else "",
        account_known=f["account"] in ACCTS,
        months=[{"name": m, "txns": ts, **_summary(ts)} for m, ts in months.items()],
        payee_rows=sorted(
            [
                {
                    "name": p,
                    "count": len(ts),
                    "total": money(sum(t["raw"] for t in ts), signed=True),
                    "icon": ts[0]["icon"],
                    "color": ts[0]["color"],
                    "last": ts[0]["day"],
                    "url": link(payee=p, lens="days"),
                }
                for p, ts in payees.items()
            ],
            key=lambda r: -r["count"],
        ),
        tag_rows=[
            {
                "name": tag,
                "count": len(ts),
                "total": money(-sum(t["raw"] for t in ts)),
                "span": f"{ts[-1]['date']:%-d %b} – {ts[0]['date']:%-d %b}",
                "url": link(tag=tag, lens="days"),
            }
            for tag, ts in tags.items()
        ],
        review=[t for t in txns if t["flag"]],
        review_url=link(type="uncategorised", lens="days"),
        month_summary=_summary([t for t in txns if t["date"].month == TODAY.month]),
        select_accounts=[(k, a["name"]) for k, a in ACCTS.items()],
        select_tags=TAGS,
        select_payees=sorted({t["payee"] for t in txns}),
        trail="Activity",
        back_to="— (tab root)",
    )
    return render(request, f"prototype_ui/aa/{variant.lower()}_activity.html", ctx)


def txn(request, tid):
    variant, ctx = _base(request, "txn", "activity")
    t = next((t for t in _txns(variant) if t["id"] == tid), None)
    if not t:
        raise Http404
    ctx.update(
        t=t,
        parent_url=_u("prototype-aa-activity", variant),
        trail=f"Activity › {t['payee']}",
        back_to="Activity",
        balanced=sum(p["raw"] for p in t["postings"]) == 0,
        dr=money(sum(p["raw"] for p in t["postings"] if p["raw"] > 0)),
        leaves=[
            (k, v[1], v[2]) for k, v in LEAVES.items() if v[0].startswith("Expenses")
        ],
    )
    return render(request, f"prototype_ui/aa/{variant.lower()}_txn.html", ctx)


def accounts(request):
    variant, ctx = _base(request, "accounts", "accounts")
    view = request.GET.get("view", "bs")
    rows = {k: _row(k, variant) for k in ACCTS}

    def group(names):
        out = []
        for g in names:
            rs = [r for r in rows.values() if r["group"] == g]
            out.append(
                {"name": g, "rows": rs, "total": money(sum(r["value_raw"] for r in rs))}
            )
        return out

    assets = sum(r["value_raw"] for r in rows.values() if r["value_raw"] > 0)
    liabilities = sum(r["value_raw"] for r in rows.values() if r["value_raw"] < 0)
    cost = sum(r["balance"] for r in rows.values() if r["kind"] == "holding")
    held = sum(r["value_raw"] for r in rows.values() if r["kind"] == "holding")
    month = [t for t in _txns(variant) if t["date"].month == TODAY.month]
    ie = defaultdict(float)
    for t in month:
        for p in t["postings"]:
            if p["path"].startswith(("Income", "Expenses")):
                ie[p["path"]] += p["raw"]
    ctx.update(
        view=view,
        count=len(rows),
        net=money(assets + liabilities),
        assets=money(assets),
        liabilities=money(liabilities),
        unrealised=money(held - cost, signed=True),
        groups=group(GROUPS),
        asset_groups=group(ASSET_GROUPS),
        liability_groups=group(LIABILITY_GROUPS),
        sections=[
            ("Assets", group(ASSET_GROUPS)),
            ("Liabilities", group(LIABILITY_GROUPS)),
        ],
        purposes=[
            {
                "name": n,
                "hint": h,
                "rows": [rows[k] for k in keys],
                "total": money(sum(rows[k]["value_raw"] for k in keys)),
            }
            for n, h, keys in PURPOSES
        ],
        view_links=[
            ("Balance sheet", _u("prototype-aa-accounts", variant), view == "bs"),
            (
                "Income & Expenses",
                _u("prototype-aa-accounts", variant, view="ie"),
                view == "ie",
            ),
        ],
        ie_rows=[
            {
                "path": path,
                "leaf": path.rsplit(" › ", 1)[1],
                "parent": path.rsplit(" › ", 1)[0],
                "total": money(abs(v)),
                "income": path.startswith("Income"),
                "url": _u(
                    "prototype-aa-activity", variant, account=path.rsplit(" › ", 1)[1]
                ),
            }
            for path, v in sorted(ie.items())
        ],
        ie_income=money(-sum(v for p, v in ie.items() if p.startswith("Income"))),
        ie_expense=money(sum(v for p, v in ie.items() if p.startswith("Expenses"))),
        trail="Accounts",
        back_to="— (tab root)",
    )
    return render(request, f"prototype_ui/aa/{variant.lower()}_accounts.html", ctx)


def account(request, key):
    if key not in ACCTS:
        raise Http404
    variant, ctx = _base(request, "account", "accounts")
    row = _row(key, variant)
    tab = request.GET.get("tab", "activity")
    # Walk back from today's balance so the register shows a running balance.
    running = row["balance"]
    register = []
    for t in _txns(variant):
        mine = [p for k, p in zip(t["keys"], t["postings"]) if k == key]
        if not mine:
            continue
        p = mine[0]
        register.append({**t, "mine": p, "after": money(running)})
        running -= p["raw"]
    ctx.update(
        a=row,
        tab_links=[
            (label, _u("prototype-aa-account", variant, key, tab=k), tab == k)
            for k, label in [
                ("activity", "Activity"),
                ("upcoming", "Upcoming"),
                ("earmarks", "Earmarks"),
                ("terms", "Terms"),
            ]
        ],
        register=register,
        upcoming=[
            {
                "when": w,
                "name": n,
                "amount": money(v, signed=True) if v is not None else None,
                "note": note,
            }
            for w, n, v, note in row["upcoming"]
        ],
        unallocated=100 - sum(e[2] for e in row["earmarks"]),
        all_url=_u("prototype-aa-activity", variant, account=key),
        parent_url=_u("prototype-aa-accounts", variant),
        trail=f"Accounts › {row['name']}",
        back_to="Accounts",
        kind_name=KIND_NAMES[row["kind"]],
    )
    # The tab bar owns this screen's tab; keep the page's own tab separate.
    ctx["tab"] = "accounts"
    ctx["page_tab"] = tab
    return render(request, f"prototype_ui/aa/{variant.lower()}_account.html", ctx)
