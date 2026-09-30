"""PROTOTYPE — Goal detail and Before Goals variants for the wayfinder ticket.

Three takes on a Goal's detail (Retirement's calculator included), changing its
Earmarks, and the Before Goals scorecard, switched with ?variant=U|V|W on
/prototype/ui/goals/<key>/ and /prototype/ui/before-goals/. They sit inside
navigation variant L's tab bar, next to Plan variant T. Never merge to main.
"""

import json

from django.http import Http404
from django.shortcuts import render
from django.template.loader import select_template

from prototype_ui import goals_data as G
from prototype_ui.aa_ledger import _u
from prototype_ui.nav import _nav_context, _url as nav_url
from prototype_ui.views import money

VARIANTS = {
    "U": "One page",
    "V": "Three questions",
    "W": "Worksheet",
}

RULES = {
    "U": "A Goal is one long page: the figure, a projection chart, its Earmarks, its mix against the Glide Path, then its settings. Earmarks change in a bottom sheet. Retirement adds its calculator as worked arithmetic. Before Goals is a vertical ladder; the current Stage opens with its gaps and next actions.",
    "V": "A Goal answers three questions on tabs — Getting there, What's in it, How it's invested. Earmarks are edited in place on their tab. Retirement's Getting there is a live calculator with sliders. Before Goals leads with the one Stage to act on; the rest sit under Done and Ahead.",
    "W": "A Goal opens with what to do next, then a worksheet of figures in rows. Earmarks change on their own screen, from the Account's side: split an Account across Goals and Unallocated. Retirement is a worksheet of inputs and outputs. Before Goals is a table of Stages with each one's measure, ₹ gap and action.",
}

TODAY = (2026, 9)
RATES = {"eq": 0.11, "debt": 0.07, "gold": 0.07}

# Existing contributions naming each Goal: (monthly ₹, yearly step-up), and the Goal's end month.
FLOWS = {
    "retirement": ([(10000, 0.10), (10000, 0), (12600, 0)], (2050, 3)),
    "europe": ([(5000, 0)], (2028, 3)),
    "college": ([], (2038, 6)),
}


def _variant(request):
    v = request.GET.get("variant", "U").upper()
    return v if v in VARIANTS else "U"


def _equity(years):
    for (_, eq), lo in zip(G.BANDS, (15, 10, 5, 3, 1, 0)):
        if years >= lo:
            return eq
    return G.BANDS[-1][1]


def _return(years):
    e = _equity(years) / 100
    g = min(0.05, 1 - e)
    return e * RATES["eq"] + (1 - e - g) * RATES["debt"] + g * RATES["gold"]


def _months_left(end):
    return (end[0] - TODAY[0]) * 12 + end[1] - TODAY[1]


def _series(have, flows, months, extra=0):
    # Month by month along the Glide Path mix; one point per year for the chart.
    v, points = have, [have]
    for i in range(months):
        v *= 1 + _return((months - i) / 12) / 12
        for amount, step in flows:
            v += amount * (1 + step) ** ((i + 6) // 12)
        v += extra
        if (i + 1) % 12 == 0 or i == months - 1:
            points.append(v)
    return points


def _chart(key, g, w=320, h=150):
    flows, end = FLOWS[key]
    months = _months_left(end)
    now = _series(g["have"], flows, months)
    more = _series(g["have"], flows, months, g["sip"]) if g["sip"] else None
    top = max(g["target"], *now, *(more or [0])) * 1.08

    def path(points):
        step = w / (len(points) - 1)
        return "M" + " L".join(f"{i * step:.1f},{h - p / top * h:.1f}" for i, p in enumerate(points))

    return {
        "w": w,
        "h": h,
        "now": path(now),
        "more": path(more) if more else "",
        "target_y": round(h - g["target"] / top * h, 1),
        "end": g["date"],
    }


def _glide(end):
    # Each SEBI band the Goal passes through, from today to its date.
    months = _months_left(end)
    steps, prev = [], None
    for m in range(months + 1):
        eq = _equity((months - m) / 12)
        if eq != prev:
            y, mo = divmod(TODAY[1] - 1 + m, 12)
            when = "Now" if m == 0 else f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][mo]} {TODAY[0] + y}"
            band = next(b for b, e in G.BANDS if e == eq)
            steps.append({"when": when, "band": band, "eq": eq, "gold": min(5, 100 - eq), "debt": 100 - eq - min(5, 100 - eq)})
            prev = eq
    return steps


def _goal(key, variant):
    g = dict(G.GOALS[key])
    label, tone = G.STATUS[g["status"]]
    g.update(
        key=key,
        label=label,
        tone=tone,
        url=_u("prototype-goal", variant, key),
        earmarks_url=_u("prototype-goal-earmarks", variant, key),
        m={k: money(g[k]) for k in ("today", "target", "have", "gap", "sip") if g.get(k) is not None},
        projected_m=money(g["projected"]) if g["projected"] is not None else None,
        pct=min(100, round(g["have"] / g["target"] * 100)),
        proj_pct=min(100, round((g["projected"] or 0) / g["target"] * 100)),
        earmarks=[{**e, "m": money(e["value"])} for e in g["earmarks"]],
        mix=[
            {"cls": c, "target": t, "actual": a, "drift": a - t, "far": abs(a - t) > 10, "off": abs(a - t) > 5}
            for c, t, a in g["mix"]
        ],
        sip_split=[{"cls": c, "inst": i, "m": money(a)} for c, i, a in g.get("sip_split", [])],
    )
    if key in FLOWS:
        g["chart"] = _chart(key, g)
        g["glide"] = _glide(FLOWS[key][1])
        if key == "retirement":
            g["glide"].append({"when": "Mar 2050", "band": "Drawdown", "eq": 45, "gold": 5, "debt": 50})
    if g["calc"]:
        c = dict(g["calc"])
        c["what_if"] = [{"age": a, "target": money(t), "sip": money(s)} for a, t, s in c["what_if"]]
        c["loans"] = [{"name": n, "m": money(a), "ends": e} for n, a, e in c["loans"]]
        c["loans_total"] = money(sum(a for _, a, _ in g["calc"]["loans"]))
        g["calc"] = c
    return g


def _base(request, screen, tab, parent_url, back_to, trail):
    variant = _variant(request)
    ctx = _nav_context("L")
    goals = [_goal(k, variant) for k in G.ORDER]
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
        tab_urls={
            "home": nav_url("home", "L"),
            "activity": _u("prototype-aa-activity", "P"),
            "accounts": _u("prototype-aa-accounts", "P"),
            "plan": _u("prototype-plan", "T"),
        },
        settings_url=nav_url("settings", "L"),
        goals=goals,
        ranked=[g for g in goals if g["rank"]],
        stages=G.STAGES,
        current=next(s for s in G.STAGES if s["state"] == "current"),
        also=G.ALSO,
        unallocated=[{"key": k, "name": n, "units": u, "m": money(v), "cls": c} for k, n, u, v, c in G.UNALLOCATED],
        expected=G.EXPECTED,
        surplus=money(G.SURPLUS),
        surplus_free=money(G.SURPLUS_FREE),
        urls={
            "scorecard": _u("prototype-before-goals", variant),
            "policies": _u("prototype-plan-policies", "T"),
            "plan": _u("prototype-plan", "T"),
            "schedules": _u("prototype-plan-recurring", "T", view="schedules"),
            "goals_home": nav_url("home:3", "L"),
        },
        jump=[
            ("Before Goals", _u("prototype-before-goals", variant)),
            ("Retirement · calculator", _u("prototype-goal", variant, "retirement")),
            ("Emergency Fund", _u("prototype-goal", variant, "ef")),
            ("Europe 2028 · out of order, behind", _u("prototype-goal", variant, "europe")),
            ("Aarav's college · unfunded, empty", _u("prototype-goal", variant, "college")),
            ("Change Earmarks · Retirement", _u("prototype-goal-earmarks", variant, "retirement")),
            ("Change Earmarks · Emergency Fund", _u("prototype-goal-earmarks", variant, "ef")),
        ],
    )
    return variant, ctx


def _render(request, variant, screen, ctx):
    names = [f"prototype_ui/goals/{variant.lower()}_{screen}.html"]
    return render(request, select_template(names).template.name, ctx)


def goal(request, key):
    if key not in G.GOALS:
        raise Http404
    name = G.GOALS[key]["name"]
    variant, ctx = _base(request, "goal", "home", nav_url("home:3", "L"), "Home › Goals", f"Home › Goals › {name}")
    ctx["g"] = next(g for g in ctx["goals"] if g["key"] == key)
    ctx["view"] = request.GET.get("view", "")
    ctx["open"] = request.GET.get("open", "")
    return _render(request, variant, "goal", ctx)


def earmarks(request, key):
    # U and V change Earmarks on the Goal itself; only W gives them a screen.
    if key not in G.GOALS:
        raise Http404
    variant = _variant(request)
    if variant != "W":
        request.GET = request.GET.copy()
        request.GET["open" if variant == "U" else "view"] = "earmarks"
        return goal(request, key)
    name = G.GOALS[key]["name"]
    variant, ctx = _base(
        request, "earmarks", "home", _u("prototype-goal", variant, key), name, f"Home › Goals › {name} › Earmarks"
    )
    ctx["g"] = next(g for g in ctx["goals"] if g["key"] == key)
    ctx["acct"] = request.GET.get("acct", "")
    return _render(request, variant, "earmarks", ctx)


def before_goals(request):
    variant, ctx = _base(
        request, "scorecard", "plan", _u("prototype-plan", "T"), "Plan", "Plan › Before Goals"
    )
    return _render(request, variant, "scorecard", ctx)
