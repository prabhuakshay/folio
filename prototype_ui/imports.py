"""PROTOTYPE — Import flow variants for the "Import flow screens" wayfinder ticket.

Three takes on bringing a statement in — upload with its password hint, the
staged preview, confirming, flagged mismatches and Import history with undo —
switched with ?variant=X|Y|Z on /prototype/ui/imports/. Imports opens from the
Accounts tab of navigation variant L. Nothing persists. Never merge to main.
"""

import json

from django.http import Http404
from django.shortcuts import render

from prototype_ui import imports_data as D
from prototype_ui.aa_ledger import _u
from prototype_ui.nav import _nav_context, _url as nav_url
from prototype_ui.views import money

VARIANTS = {
    "X": "Steps",
    "Y": "By source",
    "Z": "Exceptions first",
    "YZ": "By source + Needs you",
}

RULES = {
    "X": "A guided run. Imports is a page with one big button; the upload is its own screen. The preview is three steps — Sources (mapping and Funding Account), Lines (a feed with filter chips), Post (the totals and the closing checks) — each confirmed before the next.",
    "Y": "Organised by what the statement is about. Upload opens in a bottom sheet over Imports. The preview is one card per source: its mapping and Funding Account on top, its closing-units check, then its lines. A sticky bar posts everything ticked.",
    "Z": "Only what needs you. The upload is inline at the top of Imports. The preview leads with the figure of what will post, then one decision card per thing only you can settle — a source to map, a tie, a dismissed line, a mismatch, an unreadable line — and folds everything routine away.",
    "YZ": "The chosen mix: Y's screens throughout, but its preview opens with Z's Needs you cards — the new source to map, the tie, the dismissed line behind a mismatch, the unreadable line — and the source cards below hold only the routine lines.",
}


def _variant(request):
    v = request.GET.get("variant", "YZ").upper()
    return v if v in VARIANTS else "YZ"


def _tpl(variant, name):
    # YZ differs from Y only in its preview.
    prefix = "y" if variant == "YZ" and name != "staged" else variant.lower()
    return f"prototype_ui/imports/{prefix}_{name}.html"


def _lines():
    out = []
    for s in D.SOURCES:
        for line in s["lines"]:
            label, icon = D.STATUS[line["status"]]
            out.append(
                {
                    **line,
                    "src": s,
                    "label": label,
                    "icon": icon,
                    "m": money(line["amount"]) if line["amount"] else None,
                    # Ticked by default only where Folio is sure; a tie, a dismissed line and an unmapped source wait for you.
                    "ticked": line["status"] in ("match", "fulfils")
                    or (line["status"] == "new" and s["mapped"]),
                    "blocked": line["status"] == "new" and not s["funding"],
                }
            )
    return out


def _counts(lines):
    seen = sum(s["seen"] for s in D.SOURCES)
    opening = sum(s["opening"] for s in D.SOURCES)
    return {
        "post": sum(1 for l in lines if l["ticked"] and l["status"] != "match"),
        "link": sum(1 for l in lines if l["ticked"] and l["status"] == "match"),
        "seen": seen,
        "opening": opening,
        "total": seen + opening + len(lines),
        "errors": sum(1 for l in lines if l["status"] == "error"),
        "dismissed": sum(1 for l in lines if l["status"] == "dismissed"),
        "decisions": sum(
            1 for l in lines if l["status"] in ("tie", "dismissed", "error")
        )
        + sum(1 for s in D.SOURCES if not s["mapped"] and s["closing"]),
        "new_sources": sum(1 for s in D.SOURCES if not s["mapped"] and s["closing"]),
    }


def _base(request, screen, parent, trail):
    variant = _variant(request)
    ctx = _nav_context("L")
    ctx.update(
        variant=variant,
        variant_name=VARIANTS[variant],
        variants_json=json.dumps(VARIANTS),
        rule=RULES[variant],
        screen=screen,
        tab="accounts",
        root=False,
        parent_url=_u(parent, variant) if parent else _u("prototype-aa-accounts", "P"),
        back_to="Imports" if parent else "Accounts",
        trail=trail,
        tab_urls={
            "home": nav_url("home", "L"),
            "activity": _u("prototype-aa-activity", "P"),
            "accounts": _u("prototype-aa-accounts", "P"),
            "plan": _u("prototype-plan", "T"),
        },
        settings_url=nav_url("settings", "L"),
        urls={
            "index": _u("prototype-imports", variant),
            "new": _u("prototype-imports-new", variant),
            "staged": _u("prototype-imports-staged", variant),
            "posted": _u("prototype-import", variant, "sep30"),
            "uti": _u("prototype-aa-account", "P", "uti"),
            "ppfas": _u("prototype-aa-account", "P", "ppfas"),
        },
        jump=[
            ("Imports", _u("prototype-imports", variant)),
            ("Upload · CAMS CAS", _u("prototype-imports-new", variant, f="cams")),
            (
                "Upload · wrong password",
                _u("prototype-imports-new", variant, f="cams", pw="wrong"),
            ),
            ("Upload · NSDL CAS", _u("prototype-imports-new", variant, f="nsdl")),
            (
                "Upload · no Importer reads it",
                _u("prototype-imports-new", variant, f="hdfc"),
            ),
            ("Staged preview", _u("prototype-imports-staged", variant)),
            ("Just posted", _u("prototype-import", variant, "sep30")),
            ("Past Import · confirmed", _u("prototype-import", variant, "sep12")),
            ("Past Import · undo", _u("prototype-import", variant, "sep12", undo=1)),
            ("Past Import · NSDL snapshot", _u("prototype-import", variant, "sep3")),
            ("Past Import · undone", _u("prototype-import", variant, "aug10")),
        ],
        statement=D.STATEMENT,
        flags=D.FLAGS,
        history=[
            {**h, "url": _u("prototype-import", variant, h["key"])} for h in D.HISTORY
        ],
    )
    return variant, ctx


def _upload(request):
    f = request.GET.get("f", "")
    pw = request.GET.get("pw", "")
    file = D.FILES.get(f)
    return {
        "f": f,
        "file": file,
        "files": [
            (k, v["file"], _u("prototype-imports-new", _variant(request), f=k))
            for k, v in D.FILES.items()
        ],
        "wrong_pw": pw == "wrong",
        "pw": pw,
    }


def index(request):
    variant, ctx = _base(request, "imports", None, "Accounts › Imports")
    lines = _lines()
    ctx.update(counts=_counts(lines), sheet_open=False, **_upload(request))
    return render(request, _tpl(variant, "index"), ctx)


def new(request):
    variant, ctx = _base(
        request,
        "upload",
        "prototype-imports",
        "Accounts › Imports › Import a statement",
    )
    lines = _lines()
    ctx.update(counts=_counts(lines), sheet_open=True, **_upload(request))
    # Y uploads in a sheet over Imports and Z inline at its top; only X gives it a screen.
    name = {"X": "new", "Z": "index"}.get(variant, "index")
    return render(request, _tpl(variant, name), ctx)


def staged(request):
    variant, ctx = _base(
        request, "staged", "prototype-imports", "Accounts › Imports › Preview"
    )
    lines = _lines()
    step = request.GET.get("step", "sources")
    chip = request.GET.get("chip", "")
    sources = []
    for s in D.SOURCES:
        mine = [l for l in lines if l["src"] is s]
        sources.append({**s, "rows": mine, "hidden": s["seen"] + s["opening"]})
    ctx.update(
        lines=lines,
        sources=sources,
        counts=_counts(lines),
        step=step,
        chip=chip,
        steps=[
            (
                "sources",
                "Sources",
                _u("prototype-imports-staged", variant, step="sources"),
            ),
            ("lines", "Lines", _u("prototype-imports-staged", variant, step="lines")),
            ("post", "Post", _u("prototype-imports-staged", variant, step="post")),
        ],
        chips=[
            (
                key,
                label,
                _u("prototype-imports-staged", variant, step="lines", chip=key),
                chip == key,
            )
            for key, label in [
                ("", "All"),
                ("attention", "Needs you"),
                ("new", "New"),
                ("link", "Links"),
                ("off", "Not posting"),
            ]
        ],
        funding_choices=D.FUNDING_CHOICES,
        decisions=[l for l in lines if l["status"] in ("tie", "dismissed", "error")],
        mismatches=[s for s in D.SOURCES if s["closing"] and s["closing"]["gap"]],
        new_sources=[s for s in sources if not s["mapped"] and s["closing"]],
    )
    return render(request, _tpl(variant, "staged"), ctx)


def detail(request, key):
    variant, ctx = _base(
        request, "import", "prototype-imports", "Accounts › Imports › Import"
    )
    if key == "sep30":
        lines = _lines()
        c = _counts(lines)
        h = {
            "key": "sep30",
            "importer": D.STATEMENT["importer"],
            "when": "30 Sep 2026",
            "period": D.STATEMENT["period"],
            "state": "just",
            "line": f"{c['post']} posted · {c['link']} linked",
            "posted": c["post"],
            "linked": c["link"],
            "dismissed": 1,
            "edited": 0,
            "creates": ["HDFC Liquid Fund (Holding)"],
            "returns_due": ["UTI Nifty SIP · 5 Sep"],
            "sources": [
                ("Parag Parikh Flexi Cap", "1 linked", "Closing units agreed"),
                (
                    "UTI Nifty 50 Index",
                    "2 posted · 1 dismissed",
                    "12.001 units short — flagged",
                ),
                ("HDFC Liquid Fund", "2 posted · new Holding", "Closing units agreed"),
                ("Franklin STIP · Segregated 3", "1 line not read", "Enter by hand"),
            ],
            "txns": [
                ("21 Sep", "UTI Nifty 50 Index", "Posted as new", 25000),
                (
                    "18 Sep",
                    "HDFC Liquid Fund redemption",
                    "Posted · Realised Gain ₹1,092",
                    20000,
                ),
                ("5 Sep", "UTI Nifty SIP", "Posted · fulfilled its Occurrence", 5000),
                ("5 Sep", "Parag Parikh SIP", "Linked · your Transaction kept", 10000),
                (
                    "10 Mar 2025",
                    "HDFC Liquid Fund",
                    "Posted · from Opening Balances",
                    50000,
                ),
            ],
        }
    else:
        h = next((h for h in D.HISTORY if h["key"] == key), None)
        if not h:
            raise Http404
    ctx.update(
        h={**h, "txns": [(d, n, note, money(a)) for d, n, note, a in h["txns"]]},
        undo=request.GET.get("undo") == "1",
        undone=request.GET.get("undone") == "1",
        undo_url=_u("prototype-import", variant, key, undo=1),
        undone_url=_u("prototype-import", variant, key, undone=1),
        self_url=_u("prototype-import", variant, key),
        header=h["importer"],
    )
    return render(request, _tpl(variant, "import"), ctx)
