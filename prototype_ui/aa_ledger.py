"""PROTOTYPE — turns aa_data's sample ledger into rows the Activity and Accounts variants render. Never merge to main."""

from datetime import timedelta
from urllib.parse import urlencode

from django.urls import reverse

from prototype_ui.aa_data import ACCTS, LEAVES, TODAY, TXNS
from prototype_ui.views import money

KIND_NAMES = {
    "bank": "Bank or cash",
    "card": "Card",
    "loan": "Loan",
    "holding": "Holding",
    "deposit": "Term Deposit",
    "provident": "Provident Account",
}


def _variant(request):
    v = request.GET.get("variant", "N").upper()
    return v if v in ("N", "O", "P") else "N"


def _u(name, variant, *args, **params):
    params = {k: v for k, v in params.items() if v}
    return f"{reverse(name, args=args)}?{urlencode({'variant': variant, **params})}"


def _acct_name(key):
    return ACCTS[key]["name"] if key in ACCTS else key


def _value(a):
    h = a.get("holding")
    return h["units"] * h["price"] if h else a["balance"]


def _posting(key, amount, units, variant):
    if key in ACCTS:
        a = ACCTS[key]
        return {
            "name": a["name"],
            "path": f"{'Liabilities' if a['balance'] < 0 else 'Assets'} › {a['group']} › {a['name']}",
            "url": _u("prototype-aa-account", variant, key),
            "amount": money(amount, signed=True),
            "raw": amount,
            "units": f"{units:,.3f}" if units else "",
            "icon": "wallet",
            "color": a["color"],
        }
    path, icon, color = LEAVES[key]
    return {
        "name": key,
        "path": path,
        "url": _u("prototype-aa-activity", variant, account=key),
        "amount": money(amount, signed=True),
        "raw": amount,
        "units": "",
        "icon": icon,
        "color": color,
    }


def _day_label(d):
    if d == TODAY:
        return "Today"
    if d == TODAY - timedelta(days=1):
        return "Yesterday"
    return d.strftime("%a, %-d %b")


def _txn(row, variant):
    tid, d, time, payee, kind, amount, postings, extra = row
    ps = [_posting(k, a, u, variant) for k, a, u in postings]
    split = len(ps) > 2
    # The feed names a Transaction by where the money went (or, for income, came from).
    pos = next(p for p in ps if p["raw"] > 0)
    neg = next(p for p in ps if p["raw"] < 0)
    lead, source = (neg, pos) if amount > 0 else (pos, neg)
    if split:
        cash = [
            p
            for k, p in zip((k for k, _, _ in postings), ps)
            if k in ("hdfc", "sbi", "cash", "icici")
        ]
        source = cash[0] if cash else source
    return {
        "id": tid,
        "date": d,
        "day": _day_label(d),
        "month": d.strftime("%B %Y"),
        "dnum": d.day,
        "dow": d.strftime("%a"),
        "time": time,
        "payee": payee,
        "kind": kind,
        "amount": money(amount, signed=True),
        "raw": amount,
        "category": f"Split · {len(ps)} Postings" if split else lead["name"],
        "paid_from": source["name"],
        "icon": "split" if split else lead["icon"],
        "color": lead["color"],
        "postings": ps,
        "keys": [k for k, _, _ in postings],
        "tags": extra.get("tags", []),
        "note": extra.get("note", ""),
        "source": extra.get("source", ""),
        "fulfils": extra.get("fulfils", ""),
        "flag": extra.get("flag", ""),
        "split": split,
        "url": _u("prototype-aa-txn", variant, tid),
    }


def _txns(variant):
    return [_txn(r, variant) for r in TXNS]


def _matches(t, f):
    if f["type"] == "uncategorised":
        if t["flag"] != "Uncategorised":
            return False
    elif f["type"] and t["kind"] != f["type"]:
        return False
    if f["tag"] and f["tag"] not in t["tags"]:
        return False
    if f["payee"] and t["payee"] != f["payee"]:
        return False
    if f["account"] and f["account"] not in t["keys"]:
        return False
    if f["q"]:
        hay = " ".join(
            [t["payee"], t["note"], t["amount"]["whole"], *t["tags"]]
            + [p["name"] for p in t["postings"]]
        ).lower()
        return f["q"].lower() in hay
    return True


def _summary(txns):
    spent = earned = saved = 0
    for t in txns:
        for p in t["postings"]:
            if p["path"].startswith("Expenses") and not p["path"].endswith(
                ("TDS", "Professional tax")
            ):
                spent += p["raw"]
            elif p["path"].startswith("Income"):
                earned -= p["raw"]
            elif p["raw"] > 0 and any(
                p["name"] == ACCTS[k]["name"]
                for k in ("ppfas", "uti", "sgb", "fd", "ppf", "epf")
            ):
                saved += p["raw"]
    return {"spent": money(spent), "earned": money(earned), "saved": money(saved)}


def _row(key, variant):
    a = ACCTS[key]
    h = a.get("holding")
    value = _value(a)
    return {
        "key": key,
        **a,
        "value": money(value),
        "value_raw": value,
        "url": _u("prototype-aa-account", variant, key),
        "gain": money(value - h["cost"], signed=True) if h else None,
        "gain_pct": f"{(value / h['cost'] - 1) * 100:+.1f}%" if h else "",
        "stale": bool(h and h["stale"]),
        "kind_name": KIND_NAMES[a["kind"]],
        # Pre-formatted with Indian grouping for the templates.
        "m": {
            "cost": money(a["balance"]),
            "due": money(a["card"]["due"]) if "card" in a else None,
            "unbilled": money(a["card"]["unbilled"]) if "card" in a else None,
            "limit": money(a["card"]["limit"]) if "card" in a else None,
            "accrued": money(
                (a.get("deposit") or a.get("provident") or {}).get("accrued", 0)
            ),
            "emi": money(a["loan"]["emi"]) if "loan" in a else None,
            "sanctioned": money(a["loan"]["sanctioned"]) if "loan" in a else None,
            "paid": money(a["loan"]["sanctioned"] + a["balance"])
            if "loan" in a
            else None,
            "price": money(h["price"]) if h else None,
        },
    }
