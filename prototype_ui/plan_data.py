"""PROTOTYPE — sample Plan-tab world for the Plan tab screens ticket. Never merge to main.

Same person as aa_data: today is Wed 30 Sep 2026, the last day of the September
Budget month (month-start day 1). Salary lands in SBI Salary on the 28th.
"""

# ——— Budget: September's pay-yourself-first waterfall ———

INCOME = 155400.00  # Salary Occurrence, net of TDS and EPF
SAVINGS_RATE = 0.20
SCHEDULED_SAVINGS = 25000.00  # SIP + PPF + Europe SIP
SAVINGS = max(INCOME * SAVINGS_RATE, SCHEDULED_SAVINGS)  # 31,080
COMMITTED = 80668.00
SPENDABLE = INCOME - SAVINGS - COMMITTED  # 43,652
SPENT = 36172.00
LEFT = SPENDABLE - SPENT  # 7,480
UNSCHEDULED_INCOME = 18200.00  # income tax refund, 14 Sep
CARD_BILL_EXCLUDED = 23410.00

MONTH = {
    "name": "September",
    "span": "1–30 Sep",
    "day": 30,
    "days": 30,
    "ends": "today",
    "next": "October",
}

SAVINGS_LINES = [
    ("Parag Parikh Flexi Cap SIP", 10000, "5 Sep · fulfilled", "sip"),
    ("PPF deposit", 10000, "5 Sep · fulfilled", "ppf"),
    ("Europe 2028 SIP", 5000, "10 Sep · fulfilled", "europe"),
]

COMMITTED_LINES = [
    ("SBI Home loan EMI", 38500, "28 Sep · fulfilled", "emi"),
    ("Rent to Mr. Rao", 32000, "1 Sep · auto-posted", "rent"),
    ("Domestic help · Sunita", 6000, "25 Sep · overdue", "help"),
    ("BESCOM electricity", 2340, "22 Sep · overdue · ~estimate", "bescom"),
    ("Airtel broadband", 1179, "2 Sep · fulfilled", "airtel"),
    ("Netflix", 649, "14 Sep · auto-posted", "netflix"),
]

# (Expense Account, spent this month, monthly limit or None, colour, icon)
SPEND = [
    ("Groceries", 9840, 12000, "#0B9B6A", "shopping-basket"),
    ("Dining out", 7770, 6000, "#E0662B", "utensils"),
    ("Shopping", 5200, 8000, "#8E44AD", "shopping-bag"),
    ("Transport", 4310, None, "#2A6FDB", "car"),
    ("Uncategorised", 3402, None, "#8D8D97", "circle-help"),
    ("Food delivery", 2600, 3000, "#D4418E", "bike"),
    ("Health", 1850, None, "#C0392B", "heart-pulse"),
    ("Leisure", 1200, None, "#6C5CE7", "clapperboard"),
]

# Yearly limits run over the Financial Year.
YEARLY_LIMITS = [
    ("Travel & holidays", 64000, 120000, "#0E7C86", "plane"),
]

# Weekly discretionary spend, for a pace line (week ending, cumulative spend).
PACE = [(7, 9200), (14, 17850), (21, 26400), (28, 33010), (30, 36172)]

# ——— Doctrine: where surplus goes ———

STAGE = {
    "n": 3,
    "of": 6,
    "name": "Protection",
    "gaps": [
        ("Term life", "₹1.21 Cr short", "Need ₹2.26 Cr · counted ₹1.05 Cr"),
        ("Health · Amma", "₹10 L short", "No counted cover; employer ₹5 L not counted"),
    ],
    "advice": "Protection comes first, and money alone can't close it — cover does. Buy the ₹1.21 Cr of term cover and a ₹10 L policy for Amma; this surplus can pay their first premiums (about ₹32,000 a year together). The rest waits for Stage 5, the Emergency Fund, now 4.1 of 6 months.",
    "next": "Stage 5 · Emergency Fund · ₹1.52 L to 6 months",
}

LADDER = [
    (1, "No revolving credit", "met", "Card paid in full 14 months running"),
    (2, "Starter emergency fund", "met", "1 month covered"),
    (3, "Protection", "current", "Term life ₹1.21 Cr short · Amma uncovered"),
    (4, "High-interest debt cleared", "met", "No loan at 10% or more"),
    (5, "Full Emergency Fund", "unmet", "4.1 of 6 months"),
    (6, "Goals and Retirement", "unmet", "Retirement on track · Europe 2028 out of order"),
]

SURPLUS = [
    ("Income tax refund", UNSCHEDULED_INCOME, "14 Sep · arrived without a Schedule"),
    ("September left to spend", LEFT, "Carried to surplus tomorrow"),
]
