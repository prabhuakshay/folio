"""PROTOTYPE — sample data for the "Settings and first-run onboarding" ticket.

Same person as aa_data, plan_data and goals_data: Akshay, born 14 Mar 1990,
retiring at 60, today Wed 30 Sep 2026. Onboarding replays his first evening
with an empty install. Never merge to main.
"""

PROFILE = {
    "name": "Akshay Prabhu",
    "email": "akshay@example.in",
    "dob": "14 Mar 1990",
    "age": 36,
    "retirement_age": 60,
    "retirement_date": "14 Mar 2050",
    "month_start": "1st",
    "started": "1 Apr 2025",
    "declared_expense": "₹80,000",
    "declared_take_home": "₹1,55,000",
}

DEPENDENTS = [
    {"name": "Priya", "rel": "Spouse", "dob": "2 Jul 1992", "age": 34, "relies": True},
    {"name": "Aarav", "rel": "Son", "dob": "19 Jan 2020", "age": 6, "relies": True},
    {"name": "Amma", "rel": "Mother", "dob": "5 Nov 1961", "age": 64, "relies": False},
]

THRESHOLDS = [
    {
        "key": "ef",
        "name": "Emergency Fund",
        "value": "6 months",
        "default": "6 months",
        "band": "3–12 months",
        "say": ("Keep", "of outflow in the Emergency Fund."),
        "stage": "Stage 5",
    },
    {
        "key": "starter",
        "name": "Starter fund",
        "value": "1 month",
        "default": "1 month",
        "band": "1–3 months",
        "say": ("Before anything else, put aside", "of outflow."),
        "stage": "Stage 2",
    },
    {
        "key": "high",
        "name": "High-interest debt",
        "value": "10%",
        "default": "10%",
        "band": "8–14%",
        "say": ("Clear any Loan charging", "a year or more."),
        "stage": "Stage 4",
    },
    {
        "key": "emi",
        "name": "EMI cap",
        "value": "40%",
        "default": "40%",
        "band": "30–50%",
        "say": ("Keep all EMIs under", "of Take-home, warning from 30%."),
        "stage": "Watched",
    },
    {
        "key": "life",
        "name": "Life cover",
        "value": "12×",
        "default": "10×",
        "band": "7–20×",
        "say": ("Hold term life cover of", "Take-home, plus what you owe."),
        "stage": "Stage 3",
        "changed": True,
    },
    {
        "key": "health",
        "name": "Health cover floor",
        "value": "₹10 L",
        "default": "₹10 L",
        "band": "₹5 L–₹1 Cr",
        "say": ("Cover yourself and each Dependent for", "of health."),
        "stage": "Stage 3",
    },
    {
        "key": "savings",
        "name": "Savings rate",
        "value": "20%",
        "default": "20%",
        "band": "10–60%",
        "say": ("Aim to save", "of Take-home."),
        "stage": "Watched",
    },
    {
        "key": "inflation",
        "name": "General inflation",
        "value": "6%",
        "default": "6%",
        "band": "4–9%",
        "say": ("Grow Goal targets by", "a year."),
        "stage": "Goals",
    },
    {
        "key": "medical",
        "name": "Medical inflation",
        "value": "12%",
        "default": "12%",
        "band": "8–15%",
        "say": ("Grow health-related Goals by", "a year."),
        "stage": "Goals",
    },
    {
        "key": "swr",
        "name": "Safe Withdrawal Rate",
        "value": "2.5%",
        "default": "3%",
        "band": "2.5–3.5%",
        "say": ("In retirement, draw", "of the corpus in the first year."),
        "stage": "Retirement",
        "changed": True,
    },
    {
        "key": "decum",
        "name": "Equity in drawdown",
        "value": "45%",
        "default": "45%",
        "band": "30–60%",
        "say": ("Once retired, hold", "in equity."),
        "stage": "Retirement",
    },
]

RETURNS = [
    {"cls": "Equity", "value": "11%", "default": "11%", "band": "9–13%"},
    {"cls": "Debt", "value": "7%", "default": "7%", "band": "6–8%"},
    {"cls": "Gold & silver", "value": "7%", "default": "7%", "band": "5–9%"},
    {"cls": "Cash", "value": "3.5%", "default": "3.5%", "band": "3–5%"},
]

GLIDE = [
    ("15–30 years", "80%"),
    ("10–15 years", "72%"),
    ("5–10 years", "58%"),
    ("3–5 years", "42%"),
    ("1–3 years", "28%"),
    ("Under a year", "12%"),
]

DRIFT = {"inner": "±5 pp", "outer": "±10 pp", "gold": "up to 5%"}

# Income/Expense side only; balance-sheet Accounts live on the Accounts tab.
CHART = [
    (
        "Income",
        [
            ("Salary", [], []),
            ("Employer EPF", [], []),
            ("Interest", [], ["Interest"]),
            ("Dividends", [], ["Dividends"]),
            ("Realised Gains", [], ["Realised Gains"]),
            ("Rewards & cashback", [], ["Rewards & cashback"]),
            ("Other income", [], []),
        ],
    ),
    (
        "Expenses",
        [
            ("Food", ["Groceries", "Dining out", "Ordering in"], []),
            ("Home", ["Rent", "Electricity", "Mobile & internet", "Maid & help"], []),
            ("Transport", ["Fuel", "Cabs", "Metro & bus"], []),
            ("Health", ["Doctor", "Medicines"], []),
            (
                "Finance",
                ["Home loan interest", "Interest paid", "Bank charges & fees"],
                [],
            ),
            ("Insurance premiums", [], ["Insurance premiums"]),
            ("Taxes", ["TDS", "Professional tax", "Advance tax"], ["Taxes"]),
            ("Leisure", ["Travel", "Subscriptions"], []),
            ("Uncategorised", [], ["Uncategorised"]),
        ],
    ),
]

ROLES = [
    ("Opening Balances", "Equity › Opening Balances"),
    ("Realised Gains", "Income › Realised Gains"),
    ("Interest", "Income › Interest"),
    ("Dividends", "Income › Dividends"),
    ("Interest paid", "Expenses › Finance › Interest paid"),
    ("Bank charges & fees", "Expenses › Finance › Bank charges & fees"),
    ("Rewards & cashback", "Income › Rewards & cashback"),
    ("Insurance premiums", "Expenses › Insurance premiums"),
    ("Taxes", "Expenses › Taxes (group)"),
    ("Uncategorised", "Expenses › Uncategorised"),
]

TAGS = [
    ("Goa trip", 23, "₹41,820", "Mar 2026"),
    ("Anniversary", 4, "₹12,600", "Sep 2026"),
    ("Diwali", 17, "₹28,450", "Nov 2025"),
    ("Aarav school", 9, "₹86,000", "Jun 2026"),
    ("Home repairs", 6, "₹19,300", "Aug 2026"),
]

PAYEES = [
    ("Swiggy", "Ordering in", "ICICI Amazon Pay", "swiggy, swig"),
    ("Mr. Rao", "Rent", "HDFC Savings", "landlord, rent"),
    ("BigBasket", "Groceries", "HDFC Savings", "bb"),
    ("Uber", "Cabs", "ICICI Amazon Pay", ""),
    ("HP Petrol", "Fuel", "Cash", "petrol"),
]

FEEDS = [
    {
        "name": "AMFI NAVs",
        "what": "Mutual funds and ETF NAVs",
        "mode": "Fetched daily",
        "on": True,
        "last": "Today 06:10 · 14 Instruments priced",
        "state": "ok",
    },
    {
        "name": "BSE bhavcopy",
        "what": "Stocks, ETFs, SGBs and bonds at the close",
        "mode": "Fetched daily",
        "on": True,
        "last": "Today 18:40 · 3 Instruments priced",
        "state": "ok",
    },
    {
        "name": "Protean NPS",
        "what": "NPS scheme NAVs",
        "mode": "Fetched daily",
        "on": True,
        "last": "Failing since 28 Sep · file not published",
        "state": "fail",
    },
    {
        "name": "NSE bhavcopy",
        "what": "Stocks and ETFs, from a file you download",
        "mode": "Upload only",
        "on": False,
        "last": "Last file 12 Sep",
        "state": "upload",
    },
]

FEED_LOG = [
    ("Today 18:40", "BSE bhavcopy", "3 priced"),
    ("Today 06:10", "AMFI NAVs", "14 priced"),
    ("Today 06:10", "Protean NPS", "No file for 29 Sep · retry next hour"),
    ("29 Sep 18:40", "BSE bhavcopy", "3 priced"),
    ("29 Sep 06:10", "AMFI NAVs", "14 priced"),
    ("28 Sep 07:10", "Protean NPS", "No file for 27 Sep"),
]

MANUAL = [
    ("Physical gold", "₹7,412 /g", "IBJA, entered 25 Sep"),
    ("Flat in Whitefield", "₹1.10 Cr", "Entered 1 Apr"),
]

REMINDERS = [
    ("Card bill not paid in full", "On its due date", True),
    ("Loan EMI ahead", "3 days before", True),
    ("Policy lapsing", "30 days before cover ends", True),
    ("Term Deposit maturing", "7 days before", True),
    ("PPF short of its yearly minimum", "1 March", True),
    ("Occurrence gone overdue", "The day after, then Mondays", True),
    ("A price or interest job failing", "After 3 days running", False),
]

PASSKEYS = [
    ("Pixel 9", "Added 2 Apr 2025 · used today"),
    ("MacBook Air", "Added 2 Apr 2025 · used 26 Sep"),
]

SESSIONS = [
    ("This phone", "Chrome on Android · Bengaluru", "Now"),
    ("MacBook Air", "Safari on macOS · Bengaluru", "26 Sep"),
]

SECURITY_LOG = [
    ("Today 08:12", "Signed in with a passkey", "Pixel 9"),
    ("26 Sep 21:03", "Signed in with a passkey", "MacBook Air"),
    ("14 Sep 10:30", "Export everything", "Pixel 9"),
    ("2 Sep 23:51", "5 failed sign-ins · IP paused for an hour", "103.21.x.x"),
]

# ——— Onboarding ———

START_CHOICES = [
    (
        "sep",
        "1 Sep 2026",
        "This month's start",
        "Enter September's Transactions; everything before is a balance.",
        True,
    ),
    (
        "apr",
        "1 Apr 2026",
        "This Financial Year",
        "Six months to catch up, but reports cover the whole year.",
        False,
    ),
    ("pick", "Pick a date", "", "", False),
]

# Balances on the start date, by the Accounts tab's purposes.
START_ACCOUNTS = [
    (
        "Spend from",
        "Bank, cash and Cards",
        [
            {
                "name": "HDFC Savings",
                "kind": "Bank",
                "amount": "₹1,84,320",
                "how": "Balance on 1 Sep",
            },
            {
                "name": "SBI Salary",
                "kind": "Bank",
                "amount": "₹62,410",
                "how": "Balance on 1 Sep",
            },
            {
                "name": "Cash",
                "kind": "Cash",
                "amount": "₹4,200",
                "how": "Balance on 1 Sep",
            },
            {
                "name": "ICICI Amazon Pay",
                "kind": "Card",
                "amount": "−₹23,410",
                "how": "Statement 12th · due 30th · limit ₹3 L",
                "owe": True,
            },
        ],
    ),
    (
        "Owe",
        "Loans and Card EMIs",
        [
            {
                "name": "SBI Home loan",
                "kind": "Loan",
                "amount": "−₹38,62,500",
                "how": "8.5% · EMI ₹42,800 on 28th",
                "owe": True,
            },
        ],
    ),
    (
        "Grow",
        "Holdings, deposits and provident",
        [
            {
                "name": "Mutual funds",
                "kind": "From your CAS",
                "amount": "₹14,82,100",
                "how": "4 Holdings, full history since 2016",
                "cas": True,
            },
            {
                "name": "EPF",
                "kind": "Provident",
                "amount": "₹8,40,000",
                "how": "Balance on 1 Sep",
            },
            {
                "name": "PPF",
                "kind": "Provident",
                "amount": "₹6,12,000",
                "how": "Balance on 1 Sep · opened 2015",
            },
            {
                "name": "HDFC FD",
                "kind": "Term Deposit",
                "amount": "₹3,00,000",
                "how": "7.1% · matures 14 Jun 2027",
            },
        ],
    ),
    (
        "Own",
        "Property and gold",
        [
            {
                "name": "Flat in Whitefield",
                "kind": "Property",
                "amount": "₹1,10,00,000",
                "how": "Valued by hand",
            },
        ],
    ),
]

# What each onboarding piece unlocks on the Doctrine ladder.
LADDER = [
    ("No revolving credit", "Needs your Cards and Loans", ["cards"]),
    (
        "Starter fund",
        "Needs bank balances and your monthly figures",
        ["bank", "expense"],
    ),
    ("Protection", "Needs your Dependents and Policies", ["you", "policies"]),
    ("High-interest debt", "Needs your Loans", ["cards"]),
    (
        "Emergency Fund",
        "Needs bank balances and your monthly figures",
        ["bank", "expense"],
    ),
    (
        "Goals and Retirement",
        "Needs your date of birth and investments",
        ["you", "grow"],
    ),
]
