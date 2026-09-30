"""PROTOTYPE — sample Goals world for the "Goal detail and Before Goals screens" ticket. Never merge to main.

Same person as aa_data and plan_data: Akshay, 36, born 14 Mar 1990, retiring at
60 (14 Mar 2050). Today is Wed 30 Sep 2026. Outflow as the Emergency Fund counts
it is ₹80,000 a month; Take-home ₹1,55,400. The current Stage is 3, Protection.
Figures come from a scratch projection at the default Expected Returns.
"""

OUTFLOW = 80000
TAKE_HOME = 155400
SURPLUS = TAKE_HOME - OUTFLOW  # 75,400
SCHEDULED_SAVINGS = 25000
SURPLUS_FREE = SURPLUS - SCHEDULED_SAVINGS  # 50,400 not yet committed to a Schedule

EXPECTED = [("Equity", "11%", "9–13%"), ("Debt", "7%", "6–8%"), ("Gold & silver", "7%", "5–9%"), ("Cash", "3.5%", "3–5%")]

# SEBI Life Cycle band midpoints by years-to-goal; gold takes up to 5% from the non-equity share.
BANDS = [("15–30 y", 80), ("10–15 y", 72), ("5–10 y", 58), ("3–5 y", 42), ("1–3 y", 28), ("< 1 y", 12)]

# Unallocated money another Goal could take, by Asset Class.
UNALLOCATED = [
    ("ppfas", "Parag Parikh Flexi Cap", "2,412.318 units", 199326, "Equity"),
    ("uti", "UTI Nifty 50 Index", "2,300.004 units", 369818, "Equity"),
    ("sgb", "SGB 2023-24 Series III", "20 units", 142000, "Gold & silver"),
    ("hdfc", "HDFC Savings", "₹64,320", 64320, "Cash · EF eligible"),
    ("sbi", "SBI Salary", "₹42,110", 42110, "Cash · EF eligible"),
    ("cash", "Cash", "₹3,200", 3200, "Cash · EF eligible"),
]

GOALS = {
    "retirement": {
        "name": "Retirement",
        "icon": "sunset",
        "system": True,
        "rank": 1,
        "rank_note": "Always funded first",
        "date": "Mar 2050",
        "date_how": "Born 14 Mar 1990 + retirement age 60",
        "years": "23 y 5 m",
        "inflation": ("General", "6%"),
        "today": 14513200,
        "target": 56937265,
        "have": 1708450,
        "projected": 63728679,
        "gap": 0,
        "sip": 0,
        "status": "on_track",
        "status_line": "On track — projected ₹6.37 Cr against ₹5.69 Cr",
        "flags": [],
        "earmarks": [
            {"acct": "EPF", "key": "epf", "form": "Whole Account", "detail": "Follows every credit", "value": 785300, "cls": "Debt", "locked": True},
            {"acct": "PPF · SBI", "key": "ppf", "form": "Whole Account", "detail": "Follows every deposit", "value": 510000, "cls": "Debt", "locked": True},
            {"acct": "Parag Parikh Flexi Cap", "key": "ppfas", "form": "5,000 units", "detail": "of 7,412.318 · 2,412.318 Unallocated", "value": 413150, "cls": "Equity", "locked": False},
        ],
        "schedules": [
            ("Parag Parikh Flexi Cap SIP", "₹10,000 a month · steps up 10% each April", "sip"),
            ("PPF deposit", "₹10,000 a month", "ppf"),
            ("Salary · EPF leg", "₹12,600 a month into EPF", "salary"),
        ],
        "suggest": "EPF, PPF and NPS are all Earmarked already — nothing to add.",
        # (class, target %, actual %)
        "mix": [("Equity", 80, 24), ("Debt", 15, 76), ("Gold & silver", 5, 0)],
        "band": "15–30 y",
        "offset": 0,
        "step": ("Apr 2035", "72% equity once under 15 years out"),
        "preferred": [("Equity", "Parag Parikh Flexi Cap"), ("Debt", "PPF · SBI"), ("Gold & silver", "SGB, next tranche")],
        "rebalance": [
            ("Re-earmark", "Move Unallocated equity in: 2,412 Parag Parikh units and 2,300 UTI Nifty units (₹5.69 L) lift equity to 43%.", "ready"),
            ("Direct new money", "Keep every new SIP in equity until the gap closes — the PPF and EPF legs already carry the debt side.", "ready"),
            ("Switch or sell", "Past ±10 pp this would switch debt to equity, but the debt is EPF and PPF, which can't be sold.", "blocked"),
        ],
        "calc": {
            "outflow": 80000,
            "loans": [("SBI Home loan", 38500, "ends Mar 2041"), ("iPhone 16 on ICICI", 5217, "ends May 2027")],
            "monthly": 36283,
            "yearly": 435396,
            "declared": None,
            "swr": "3%",
            "swr_band": "2.5–3.5%",
            "dob": "14 Mar 1990",
            "age": 60,
            "earliest": 59,
            "what_if": [(50, 31778037, 45000), (55, 42526182, 14600), (58, 50649363, 1400), (60, 56937265, 0)],
            "nps": None,
        },
    },
    "ef": {
        "name": "Emergency Fund",
        "icon": "life-buoy",
        "system": True,
        "rank": None,
        "rank_note": "Stage 5 — funded before any ranked Goal",
        "date": "Ongoing",
        "date_how": "No date: always 6 months of outflow",
        "years": "",
        "inflation": ("Follows outflow", "—"),
        "today": 480000,
        "target": 480000,
        "have": 327163,
        "projected": None,
        "gap": 152837,
        "sip": 0,
        "status": "behind",
        "status_line": "4.1 of 6 months · ₹1.53 L short",
        "flags": [],
        "earmarks": [
            {"acct": "HDFC FD ··4417", "key": "fd", "form": "Whole Account", "detail": "Breakable · matures 12 Jan 2027", "value": 207163, "cls": "Cash", "locked": False},
            {"acct": "HDFC Savings", "key": "hdfc", "form": "₹1,20,000 fixed", "detail": "of ₹1,84,320 · ₹64,320 Unallocated", "value": 120000, "cls": "Cash", "locked": False},
        ],
        "schedules": [],
        "suggest": "Fill from eligible Unallocated: HDFC Savings ₹64,320, SBI Salary ₹42,110, Cash ₹3,200 → 5.5 months.",
        "mix": [],
        "band": "",
        "offset": 0,
        "step": None,
        "preferred": [("Cash", "HDFC Savings")],
        "rebalance": [],
        "months": 4.1,
        "months_target": 6,
        "calc": None,
    },
    "europe": {
        "name": "Europe 2028",
        "icon": "plane",
        "system": False,
        "rank": 2,
        "rank_note": "After Retirement",
        "date": "Mar 2028",
        "date_how": "",
        "years": "1 y 5 m",
        "inflation": ("General", "6%"),
        "today": 300000,
        "target": 325815,
        "have": 34087,
        "projected": 127423,
        "gap": 198392,
        "sip": 11100,
        "status": "out_of_order",
        "status_line": "Out of order — Stage 3, Protection, comes first",
        "flags": ["Behind by ₹1.98 L at the current SIP"],
        "earmarks": [
            {"acct": "UTI Nifty 50 Index", "key": "uti", "form": "212 units", "detail": "of 2,512.004 · 2,300.004 Unallocated", "value": 34087, "cls": "Equity", "locked": False},
        ],
        "schedules": [("Europe 2028 SIP", "₹5,000 a month · out of order", "europe")],
        "suggest": "",
        "mix": [("Equity", 28, 100), ("Debt", 67, 0), ("Gold & silver", 5, 0)],
        "band": "1–3 y",
        "offset": 0,
        "step": ("Apr 2027", "12% equity once under a year out · in 6 months"),
        "preferred": [("Equity", "UTI Nifty 50 Index"), ("Debt", "not set")],
        "rebalance": [
            ("Re-earmark", "No Unallocated debt to swap in — only cash in spending Accounts.", "blocked"),
            ("Direct new money", "Point the ₹5,000 SIP at a debt fund; name a Preferred debt Instrument first.", "ready"),
            ("Switch or sell", "Past ±10 pp: switch about ₹25,000 of UTI Nifty into debt before the April step.", "ready"),
        ],
        "sip_split": [("Equity 28%", "UTI Nifty 50 Index", 3100), ("Debt 67%", "Pick a debt fund", 7450), ("Gold 5%", "Pick a gold fund", 550)],
        "calc": None,
    },
    "college": {
        "name": "Aarav's college",
        "icon": "graduation-cap",
        "system": False,
        "rank": 3,
        "rank_note": "After Europe 2028",
        "date": "Jun 2038",
        "date_how": "",
        "years": "11 y 8 m",
        "inflation": ("Custom", "10%"),
        "today": 3500000,
        "target": 10683348,
        "have": 0,
        "projected": 0,
        "gap": 10683348,
        "sip": 44500,
        "status": "out_of_order",
        "status_line": "Out of order — Stage 3, Protection, comes first",
        "flags": ["Unfunded: Surplus left after Europe 2028 is ₹39,300 of the ₹44,500 a month it needs"],
        "earmarks": [],
        "schedules": [],
        "suggest": "",
        "mix": [("Equity", 72, 0), ("Debt", 23, 0), ("Gold & silver", 5, 0)],
        "band": "10–15 y",
        "offset": 0,
        "step": ("Jul 2028", "58% equity once under 10 years out"),
        "preferred": [("Equity", "not set"), ("Debt", "not set")],
        "rebalance": [],
        "sip_split": [("Equity 72%", "Pick an equity fund", 32040), ("Debt 23%", "Pick a debt fund", 10235), ("Gold 5%", "Pick a gold fund", 2225)],
        "calc": None,
    },
}

ORDER = ["ef", "retirement", "europe", "college"]

STATUS = {
    "on_track": ("On track", "pos"),
    "behind": ("Behind", "neg"),
    "out_of_order": ("Out of order", "neg"),
}

# ——— Before Goals: the Doctrine ladder ———

STAGES = [
    {
        "n": 1,
        "name": "No revolving credit",
        "state": "met",
        "measure": "Every card paid in full by its due date · no EMI overdue",
        "fact": "ICICI Amazon Pay paid in full 14 cycles running",
        "gap": None,
        "actions": [],
        "watch": "Next bill ₹23,410 due 12 Oct — paying it in full keeps this met",
    },
    {
        "n": 2,
        "name": "Starter emergency fund",
        "state": "met",
        "measure": "1 month of outflow Earmarked to the Emergency Fund",
        "fact": "₹3.27 L covers ₹80,000",
        "gap": None,
        "actions": [],
        "watch": "",
    },
    {
        "n": 3,
        "name": "Protection",
        "state": "current",
        "measure": "Term life to 10× Take-home + Liabilities − unearmarked liquid · ₹10 L health for each person",
        "fact": "Term life ₹1.05 Cr of ₹2.26 Cr · Amma has no counted health cover",
        "gap": "₹1.21 Cr term · ₹10 L health",
        "gaps": [
            ("Term life", "₹1.21 Cr short", "Need ₹2.26 Cr · counted ₹1.05 Cr", 46),
            ("Health · Amma", "₹10 L short", "Employer ₹5 L shown, not counted", 0),
        ],
        "actions": [
            ("Add a term Policy for ₹1.25 Cr", "About ₹18,000 a year at 36"),
            ("Add a ₹10 L health Policy for Amma", "About ₹14,000 a year at 64"),
        ],
        "watch": "",
    },
    {
        "n": 4,
        "name": "High-interest debt cleared",
        "state": "met",
        "measure": "No Loan at 10% p.a. or more",
        "fact": "SBI Home loan 8.5% · iPhone EMI 0%",
        "gap": None,
        "actions": [],
        "watch": "",
    },
    {
        "n": 5,
        "name": "Full Emergency Fund",
        "state": "unmet",
        "measure": "6 months of outflow Earmarked to the Emergency Fund",
        "fact": "₹3.27 L of ₹4.80 L · 4.1 months",
        "gap": "₹1.53 L",
        "gaps": [("Emergency Fund", "₹1.53 L short", "4.1 of 6 months", 68)],
        "actions": [
            ("Fill from eligible Unallocated", "+₹1.10 L from HDFC, SBI and Cash → 5.5 months"),
            ("Then save ₹43,200 more", "Surplus goes here once Protection is met"),
        ],
        "watch": "",
    },
    {
        "n": 6,
        "name": "Goals and Retirement",
        "state": "unmet",
        "measure": "Retirement and each ranked Goal on track, funded from Surplus in rank order",
        "fact": "Retirement on track · Europe 2028 behind · Aarav's college unfunded",
        "gap": "₹55,600 a month of SIPs",
        "actions": [
            ("Europe 2028 needs ₹11,100 a month", "Out of order until Stage 5 is met"),
            ("Aarav's college needs ₹44,500 a month", "Only ₹39,300 of Surplus reaches it"),
        ],
        "watch": "",
    },
]

ALSO = [
    ("EMIs", "28% of Take-home", "Warns at 30%, cap 40%", "warn"),
    ("Savings rate", "22% of Take-home", "Target 20%", "ok"),
    ("Surplus", "₹75,400 a month", "Take-home ₹1,55,400 − outflow ₹80,000", "ok"),
]
