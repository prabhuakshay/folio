"""PROTOTYPE — a staged CAMS + KFintech CAS, past Imports and standing flags for the Import flow ticket.

The staged Import re-reads a statement Folio has mostly seen, so every line
status the contract names turns up: already imported, covered by Opening
Balance, a Match to link, a new line fulfilling a due Occurrence, a tie to
pick, a dismissed line, a new source to map, and an unsupported line.
Today is Wed 30 Sep 2026. Never merge to main.
"""

FILES = {
    "cams": {
        "file": "CAS_01012023-29092026_CP123456789.pdf",
        "importer": "CAMS + KFintech CAS",
        "hint": "The password you set when you requested the statement.",
        "size": "412 KB",
    },
    "nsdl": {
        "file": "NSDL_CAS_AUG2026_AB12345678.pdf",
        "importer": "NSDL CAS",
        "hint": "Your PAN in capitals, e.g. ABCDE1234F.",
        "size": "188 KB",
    },
    "hdfc": {
        "file": "Acct_Statement_XX4417_30092026.pdf",
        "importer": None,
        "hint": "",
        "size": "96 KB",
    },
}

STATEMENT = {
    "importer": "CAMS + KFintech CAS",
    "period": "1 Jan 2023 – 29 Sep 2026",
    "staged": "Staged today, 11:42",
    "expires": "Discarded 7 Oct unless you confirm it",
}

FUNDING_CHOICES = ["HDFC Savings", "SBI Salary", "Cash"]

# status: match | fulfils | tie | new | dismissed | error
SOURCES = [
    {
        "key": "ppfas",
        "name": "Parag Parikh Flexi Cap – Direct Growth",
        "short": "Parag Parikh Flexi Cap",
        "folio": "Folio 1234567/89",
        "isin": "INF879O01027",
        "mark": "PP",
        "color": "#6B3FA0",
        "mapped": True,
        "account": "Parag Parikh Flexi Cap",
        "account_key": "ppfas",
        "funding": "SBI Salary",
        "seen": 18,
        "opening": 27,
        "start": "1 Apr 2025",
        "closing": {"statement": "7,412.318", "after": "7,412.318", "gap": None},
        "lines": [
            {
                "id": 1,
                "date": "5 Sep",
                "type": "SIP purchase",
                "amount": 10000.00,
                "detail": "121.019 units @ ₹82.63 · stamp duty ₹0.50",
                "status": "match",
                "match": "Parag Parikh SIP · 5 Sep · ₹10,000 from SBI Salary",
                "match_note": "You confirmed it from its Occurrence. Linking sets units, price and stamp duty from the statement; your Accounts and Tags stay.",
            },
        ],
    },
    {
        "key": "uti",
        "name": "UTI Nifty 50 Index – Direct Growth",
        "short": "UTI Nifty 50 Index",
        "folio": "Folio 5501234/12",
        "isin": "INF789F01XA0",
        "mark": "UTI",
        "color": "#E35205",
        "mapped": True,
        "account": "UTI Nifty 50 Index",
        "account_key": "uti",
        "funding": "HDFC Savings",
        "seen": 16,
        "opening": 12,
        "start": "1 Apr 2025",
        "closing": {
            "statement": "2,142.338",
            "after": "2,130.337",
            "gap": "12.001 units short",
            "why": "The same as the 14 Aug purchase you dismissed. Restore it and they agree.",
        },
        "lines": [
            {
                "id": 2,
                "date": "5 Sep",
                "type": "SIP purchase",
                "amount": 5000.00,
                "detail": "29.874 units @ ₹167.36 · stamp duty ₹0.25",
                "status": "fulfils",
                "fulfils": "UTI Nifty SIP · due 5 Sep",
                "posting": "UTI Nifty 50 Index ← HDFC Savings",
            },
            {
                "id": 3,
                "date": "21 Sep",
                "type": "Purchase",
                "amount": 25000.00,
                "detail": "148.812 units @ ₹167.99 · stamp duty ₹1.25",
                "status": "tie",
                "candidates": [
                    (
                        "19 Sep",
                        "UTI top-up · ₹25,000 from HDFC Savings",
                        "2 days before",
                    ),
                    (
                        "23 Sep",
                        "UTI top-up · ₹25,000 from HDFC Savings",
                        "2 days after",
                    ),
                ],
                "posting": "UTI Nifty 50 Index ← HDFC Savings",
            },
            {
                "id": 4,
                "date": "14 Aug",
                "type": "Purchase",
                "amount": 2000.00,
                "detail": "12.001 units @ ₹166.65",
                "status": "dismissed",
                "dismissed": "You unticked it on the 12 Sep Import",
                "posting": "UTI Nifty 50 Index ← HDFC Savings",
            },
        ],
    },
    {
        "key": "hdfcliq",
        "name": "HDFC Liquid Fund – Direct Growth",
        "short": "HDFC Liquid Fund",
        "folio": "Folio 88776655/01",
        "isin": "INF179KB1HK0",
        "mark": "HL",
        "color": "#0B6E4F",
        "mapped": False,
        "proposal": "New Holding under Mutual Funds",
        "instrument": "Found by ISIN · Debt 100% (Liquid) · Emergency-Fund eligible · AMFI NAV",
        "account": "HDFC Liquid Fund",
        "account_key": "",
        "funding": "",
        "seen": 0,
        "opening": 0,
        "start": "1 Jan 2023 (statement start)",
        "closing": {"statement": "6.351", "after": "6.351", "gap": None},
        "lines": [
            {
                "id": 5,
                "date": "10 Mar 2025",
                "type": "Purchase",
                "amount": 50000.00,
                "detail": "10.213 units @ ₹4,895.72",
                "status": "new",
                "posting": "HDFC Liquid Fund ← funding Account",
                "note": "Before HDFC Savings' start date (1 Apr 2025): funded from Opening Balances.",
            },
            {
                "id": 6,
                "date": "18 Sep",
                "type": "Redemption",
                "amount": 20000.00,
                "detail": "3.862 units @ ₹5,178.66 · Realised Gain ₹1,092",
                "status": "new",
                "posting": "funding Account ← HDFC Liquid Fund",
            },
        ],
    },
    {
        "key": "franklin",
        "name": "Franklin India Short Term Income – Segregated Portfolio 3",
        "short": "Franklin STIP · Segregated 3",
        "folio": "Folio 20411987",
        "isin": "INF090I01TJ9",
        "mark": "FT",
        "color": "#1F3B73",
        "mapped": False,
        "proposal": "Nothing to map — its only line can't be read",
        "account": "",
        "account_key": "",
        "funding": "",
        "seen": 0,
        "opening": 0,
        "start": "",
        "closing": None,
        "lines": [
            {
                "id": 7,
                "date": "24 Apr 2020",
                "type": "Segregated portfolio",
                "amount": 0,
                "detail": "Allotment of 94.113 units",
                "status": "error",
                "raw": "24-Apr-2020  *** Segregated Portfolio units allotted ***  94.113",
                "reason": "Not supported yet: enter it by hand as a Corporate Action.",
            },
        ],
    },
]

STATUS = {
    "match": ("Links to yours", "link"),
    "fulfils": ("New · fulfils an Occurrence", "repeat"),
    "tie": ("Pick a match or post as new", "git-compare"),
    "new": ("New", "plus"),
    "dismissed": ("Dismissed", "eye-off"),
    "error": ("Can't read", "circle-alert"),
}

HISTORY = [
    {
        "key": "sep12",
        "importer": "CAMS + KFintech CAS",
        "when": "12 Sep 2026",
        "period": "1 Jan 2023 – 10 Sep 2026",
        "posted": 34,
        "linked": 2,
        "dismissed": 1,
        "state": "confirmed",
        "line": "34 posted · 2 linked · 1 dismissed",
        "edited": 2,
        "creates": ["No Holdings or Instruments"],
        "returns_due": ["UTI Nifty SIP · 5 Aug", "Parag Parikh SIP · 5 Aug"],
        "sources": [
            ("Parag Parikh Flexi Cap", "18 posted · 1 linked", "Closing units agreed"),
            (
                "UTI Nifty 50 Index",
                "16 posted · 1 linked · 1 dismissed",
                "Closing units agreed",
            ),
        ],
        "txns": [
            ("5 Aug", "Parag Parikh SIP", "Linked · your Transaction kept", 10000),
            ("5 Aug", "UTI Nifty SIP", "Posted · fulfilled its Occurrence", 5000),
            ("5 Jul", "Parag Parikh SIP", "Posted", 10000),
            ("5 Jul", "UTI Nifty SIP", "Posted · edited since", 5000),
            ("5 Jun", "Parag Parikh SIP", "Posted", 10000),
        ],
    },
    {
        "key": "sep3",
        "importer": "NSDL CAS",
        "when": "3 Sep 2026",
        "period": "Holdings on 31 Aug 2026",
        "posted": 0,
        "linked": 0,
        "dismissed": 0,
        "state": "flagged",
        "line": "Snapshot · posted nothing · 1 mismatch flagged",
        "edited": 0,
        "creates": [],
        "returns_due": [],
        "sources": [
            ("SGB 2023-24 Series III", "20 units", "Agreed"),
            ("Nippon India ETF Nifty BeES", "125 units", "Folio has 120 — flagged"),
        ],
        "txns": [],
    },
    {
        "key": "aug10",
        "importer": "CAMS + KFintech CAS",
        "when": "10 Aug 2026",
        "period": "1 Jan 2023 – 8 Aug 2026",
        "posted": 0,
        "linked": 0,
        "dismissed": 0,
        "state": "undone",
        "line": "Undone 11 Aug · its lines came back on 12 Sep",
        "edited": 0,
        "creates": [],
        "returns_due": [],
        "sources": [],
        "txns": [],
    },
]

# Mismatches that outlive their Import: flagged on the Account until a later Import agrees or you dismiss.
FLAGS = [
    {
        "account": "Nippon India ETF Nifty BeES",
        "place": "Demat ··4411 · Zerodha",
        "statement": "125 units",
        "folio": "120 units",
        "gap": "5 units more on the statement",
        "from": "NSDL CAS · 3 Sep",
        "hint": "A buy missing from Folio, or a bonus. Add it, or dismiss if the statement is behind.",
    },
]
