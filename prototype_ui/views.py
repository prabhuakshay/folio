"""PROTOTYPE — throwaway UI variants for the "UI look and feel" wayfinder ticket.

Three variants of the home screen and quick-add expense flow on one route,
switched with ?variant=A|B|C. In-memory state only; never merge to main.
"""

import json
import re
from datetime import date

from django.shortcuts import render
from django.views.decorators.http import require_POST

from prototype_ui.data import (
    ACCOUNTS,
    BUDGETS,
    CATEGORIES,
    EXPENSE_ACCOUNTS,
    PAID_FROM,
    SEPTEMBER_SPEND,
    TOKENS,
    UPCOMING,
    VARIANTS,
)

ADDED = []

# D reuses B's layout with light tokens.
TEMPLATE_OF = {
    "A": "a",
    "B": "b",
    "C": "c",
    "D": "b",
    "E": "e",
    "F": "f",
    "G": "g",
    "H": "h",
    "I": "i",
    "J": "j",
}


def group_inr(n):
    # Indian grouping: last three digits, then pairs (1,23,45,678).
    whole = f"{abs(int(n))}"
    head, tail = whole[:-3], whole[-3:]
    head = re.sub(r"(\d)(?=(\d{2})+$)", r"\1,", head)
    return f"{head},{tail}" if head else tail


def short_inr(n):
    v = abs(n)
    if v >= 1_00_00_000:
        return f"{v / 1_00_00_000:.2f} Cr"
    if v >= 1_00_000:
        return f"{v / 1_00_000:.2f} L"
    return group_inr(v)


def money(n, signed=False):
    paise = f"{round(abs(n) * 100) % 100:02d}"
    sign = "−" if n < 0 else ("+" if signed and n > 0 else "")
    return {
        "sign": sign,
        "whole": group_inr(abs(n)),
        "paise": paise,
        "short": short_inr(n),
        "text": f"{sign}₹{group_inr(abs(n))}",
        "neg": n < 0,
        "pos": n > 0,
    }


def smooth_path(values, width, height, pad=6):
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = width / (len(values) - 1)
    pts = [
        (i * step, pad + (height - 2 * pad) * (1 - (v - lo) / span))
        for i, v in enumerate(values)
    ]
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += (
            f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
        )
    area = f"{d} L{width},{height} L0,{height} Z"
    return {
        "line": d,
        "area": area,
        "end_x": pts[-1][0],
        "end_y": pts[-1][1],
        "w": width,
        "h": height,
    }


def _accounts():
    groups = []
    for name, rows in ACCOUNTS:
        groups.append(
            {
                "name": name,
                "total": money(sum(r[3] for r in rows)),
                "rows": [
                    {"name": n, "mark": m, "color": c, "balance": money(b)}
                    for n, m, c, b in rows
                ],
            }
        )
    net = sum(r[3] for _, rows in ACCOUNTS for r in rows)
    assets = sum(r[3] for _, rows in ACCOUNTS for r in rows if r[3] > 0)
    return groups, net, assets, net - assets


def _txn(payee, category, amount, paid_from, day, time, new=False):
    icon, color = CATEGORIES.get(category, ("receipt", "#5B6475"))
    return {
        "payee": payee,
        "initial": payee[0],
        "category": category,
        "icon": icon,
        "color": color,
        "amount": money(amount, signed=True),
        "raw": amount,
        "paid_from": paid_from,
        "day": day,
        "time": time,
        "new": new,
    }


def _transactions():
    seeded = [
        _txn("Swiggy", "Dining out", -486, "ICICI Amazon Pay", "Today", "9:14 pm"),
        _txn("BigBasket", "Groceries", -2134.50, "HDFC Savings", "Today", "6:02 pm"),
        _txn("Uber", "Transport", -312, "ICICI Amazon Pay", "Today", "9:40 am"),
        _txn(
            "HP Petrol, Indiranagar",
            "Fuel",
            -1500,
            "ICICI Amazon Pay",
            "Yesterday",
            "7:48 pm",
        ),
        _txn("BESCOM", "Utilities", -1860, "HDFC Savings", "Yesterday", "11:20 am"),
        _txn("Zepto", "Groceries", -643, "HDFC Savings", "Yesterday", "8:05 am"),
        _txn(
            "Acme Technologies",
            "Salary",
            142800,
            "SBI Salary",
            "Mon, 28 Sep",
            "10:00 am",
        ),
        _txn(
            "SBI Home loan EMI",
            "Home loan",
            -38500,
            "SBI Salary",
            "Mon, 28 Sep",
            "10:02 am",
        ),
        _txn(
            "Parag Parikh SIP",
            "Investments",
            -10000,
            "SBI Salary",
            "Mon, 28 Sep",
            "10:05 am",
        ),
    ]
    return ADDED[::-1] + seeded


def _context(variant):
    groups, net, assets, liabilities = _accounts()
    transactions = _transactions()
    weeks, today_cell = _calendar(transactions)
    history = [
        52.4,
        53.1,
        52.8,
        54.2,
        55.0,
        54.6,
        56.9,
        57.4,
        57.1,
        58.3,
        59.2,
        net / 1_00_000,
    ]
    spent = sum(s for s, _ in BUDGETS.values())
    budget = sum(b for _, b in BUDGETS.values())
    stages = [
        {
            "name": "No revolving credit",
            "short": "Credit",
            "met": True,
            "detail": "Card paid in full for 14 months",
        },
        {
            "name": "Starter emergency fund",
            "short": "Starter fund",
            "met": True,
            "detail": "₹58,000 set aside — one month of outflow",
        },
        {
            "name": "Protection",
            "short": "Protection",
            "met": False,
            "current": True,
            "detail": "Term cover ₹1.00 Cr against a need of ₹2.10 Cr",
        },
        {
            "name": "High-interest debt cleared",
            "short": "Debt",
            "met": True,
            "detail": "No loan above 10%",
        },
        {
            "name": "Full Emergency Fund",
            "short": "Emergency Fund",
            "met": False,
            "detail": "4.2 of 6 months covered",
        },
        {
            "name": "Goals and Retirement",
            "short": "Goals",
            "met": False,
            "detail": "Unlocks once the stages above are met",
        },
    ]
    return {
        "variant": variant,
        "variant_name": VARIANTS[variant],
        "variants_json": json.dumps(VARIANTS),
        "tokens": TOKENS[variant],
        "today": date.today(),
        "net_worth": money(net),
        "net_worth_raw": round(net),
        "assets": money(assets),
        "liabilities": money(liabilities),
        "nw_change": money(net - 59.2 * 1_00_000, signed=True),
        "nw_change_pct": f"{(net / (59.2 * 1_00_000) - 1) * 100:.1f}",
        "nw_year_pct": f"{(net / (52.4 * 1_00_000) - 1) * 100:.1f}",
        "chart": smooth_path(history, 640, 180),
        "chart_sm": smooth_path(history, 340, 96),
        "chart_months": ["Oct", "Dec", "Feb", "Apr", "Jun", "Aug", "Sep"],
        "account_groups": groups,
        "transactions": transactions,
        "weeks": weeks,
        "today_cell": today_cell,
        "month": {
            "name": "September",
            "income": money(142800),
            "spent": money(spent),
            "budget": money(budget),
            "left": money(budget - spent),
            "pct": round(spent / budget * 100),
            "days_left": 1,
            "savings_rate": 34,
        },
        "cashflow": [
            {
                "m": m,
                "inc": i,
                "out": o,
                "inc_pct": round(i / 1.5 * 100),
                "out_pct": round(o / 1.5 * 100),
                "rate": r,
                "rate_h": r * 2 + 20,
            }
            for m, i, o, r in [
                ("Apr", 1.38, 0.61, 31),
                ("May", 1.38, 0.72, 26),
                ("Jun", 1.42, 0.58, 35),
                ("Jul", 1.42, 0.66, 29),
                ("Aug", 1.42, 0.69, 28),
                ("Sep", 1.43, 0.48, 34),
            ]
        ],
        "budgets": [
            {
                "name": n,
                "icon": CATEGORIES[n][0],
                "color": CATEGORIES[n][1],
                "spent": money(s),
                "budget": money(b),
                "left": money(b - s),
                "pct": min(100, round(s / b * 100)),
                "pct_raw": round(s / b * 100),
                "over": s > b,
            }
            for n, (s, b) in sorted(BUDGETS.items(), key=lambda kv: -kv[1][0])[:5]
        ],
        "stages": stages,
        "stage_index": 3,
        "current_stage": stages[2],
        "goals": [
            {
                "name": "Emergency Fund",
                "icon": "life-buoy",
                "pct": 70,
                "have": "₹2.44 L",
                "target": "₹3.48 L",
                "date": "Ongoing",
                "note": "4.2 of 6 months",
            },
            {
                "name": "Europe trip",
                "icon": "plane",
                "pct": 38,
                "have": "₹1.14 L",
                "target": "₹3.00 L",
                "date": "May 2027",
                "note": "₹15,700 a month to stay on track",
            },
            {
                "name": "Retirement",
                "icon": "sunset",
                "pct": 12,
                "have": "₹19.02 L",
                "target": "₹5.40 Cr",
                "date": "2051",
                "note": "On track at current SIPs",
            },
        ],
        "categories": [
            {"name": n, "icon": CATEGORIES[n][0], "color": CATEGORIES[n][1]}
            for n in EXPENSE_ACCOUNTS
        ],
        "categories_json": json.dumps({n: CATEGORIES[n] for n in EXPENSE_ACCOUNTS}),
        "budgets_json": json.dumps(BUDGETS),
        "paid_from": PAID_FROM,
        "donut": _donut(),
        "upcoming": [{**u, "money": money(u["amount"])} for u in UPCOMING],
        "upcoming_total": money(sum(u["amount"] for u in UPCOMING)),
        "cards": CARDS,
    }


def _donut(r=42, gap=2.5):
    total = sum(sp for sp, _ in BUDGETS.values())
    budget = sum(b for _, b in BUDGETS.values())
    circ = 2 * 3.14159 * r
    at, out = 0, []
    for name, (spent, _) in sorted(BUDGETS.items(), key=lambda kv: -kv[1][0]):
        length = spent / total * circ
        out.append(
            {
                "name": name,
                "color": CATEGORIES[name][1],
                "dash": f"{max(length - gap, 0):.2f} {circ:.2f}",
                "offset": f"{-at:.2f}",
                "amount": money(spent),
                "pct": round(spent / total * 100),
                "of_budget": f"{spent / budget * 100:.2f}",
            }
        )
        at += length
    return out


CARDS = [
    {
        "name": "HDFC Savings",
        "kind": "Savings · XX4821",
        "balance": money(184320.45),
        "from": "#0B2E6B",
        "to": "#2563D8",
        "icon": "landmark",
        "foot": "Updated today",
    },
    {
        "name": "Investments",
        "kind": "7 Holdings",
        "balance": money(2453650.80),
        "from": "#2A1659",
        "to": "#7B4FD0",
        "icon": "chart-line",
        "foot": "+14.8% in 1 year",
    },
    {
        "name": "ICICI Amazon Pay",
        "kind": "Credit card · XX9043",
        "balance": money(-23410),
        "from": "#4A0D18",
        "to": "#C0353C",
        "icon": "credit-card",
        "foot": "Due 12 Oct",
    },
    {
        "name": "SBI Home loan",
        "kind": "8.40% · 186 EMIs left",
        "balance": money(-3842000),
        "from": "#1B2433",
        "to": "#4A5872",
        "icon": "house",
        "foot": "Next EMI 28 Oct",
    },
]


DAY_OF = {"Today": 30, "Yesterday": 29, "Mon, 28 Sep": 28}
NOT_SPENDING = {"Salary", "Home loan", "Investments"}


def _calendar(transactions):
    days = {
        n: [_txn(p, c, -a, "", "", "") for p, c, a in rows]
        for n, rows in SEPTEMBER_SPEND.items()
    }
    for t in transactions:
        days.setdefault(DAY_OF.get(t["day"], 30), []).append(t)
    cells = [{"n": 31, "out": True}]
    for n in range(1, 31):
        rows = days.get(n, [])
        spent = -sum(t["raw"] for t in rows if t["category"] not in NOT_SPENDING)
        level = (
            0
            if spent <= 0
            else 1
            if spent < 700
            else 2
            if spent < 1500
            else 3
            if spent < 2800
            else 4
        )
        cells.append(
            {
                "n": n,
                "level": level,
                "spent": money(spent),
                "short": ""
                if spent <= 0
                else (
                    f"{spent / 1000:.1f}k".replace(".0k", "k")
                    if spent >= 1000
                    else str(round(spent))
                ),
                "today": n == 30,
                "income": any(t["category"] == "Salary" for t in rows),
                "rows": rows,
                "count": len(rows),
                "weekday": date(2026, 9, n).strftime("%A"),
            }
        )
    cells += [{"n": n, "out": True, "due": n == 2} for n in range(1, 5)]
    return [cells[i : i + 7] for i in range(0, len(cells), 7)], cells[30]


def home(request):
    variant = request.GET.get("variant", "A").upper()
    if variant not in VARIANTS:
        variant = "A"
    return render(
        request, f"prototype_ui/variant_{TEMPLATE_OF[variant]}.html", _context(variant)
    )


@require_POST
def add(request):
    variant = request.POST.get("variant", "A")
    if variant not in TEMPLATE_OF:
        variant = "A"
    amount = float(request.POST.get("amount") or 0)
    category = request.POST.get("account") or "Groceries"
    paid_from = request.POST.get("paid_from") or "HDFC Savings"
    payee = request.POST.get("payee") or category
    day = request.POST.get("day") or "Today"
    txn = _txn(
        payee,
        category,
        -amount,
        paid_from,
        "Today",
        "Just now" if day == "Today" else day,
        new=True,
    )
    ADDED.append({**txn, "new": False})
    postings = [
        {
            "account": f"Expenses › {category}",
            "amount": money(amount, signed=True)["text"],
        },
        {"account": paid_from, "amount": money(-amount)["text"]},
    ]
    response = render(
        request, f"prototype_ui/partials/row_{TEMPLATE_OF[variant]}.html", {"t": txn}
    )
    response["HX-Trigger"] = json.dumps(
        {
            "txnAdded": {
                "payee": payee,
                "category": category,
                "amount": money(amount)["text"],
                "postings": postings,
            }
        }
    )
    return response
