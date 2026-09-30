# Indian statement formats and CAS parsing

Research for [#5](https://github.com/prabhuakshay/folio/issues/5) (map [#1](https://github.com/prabhuakshay/folio/issues/1)). Researched 2026-09-30.

Question: which statement formats will Folio's Statement Importers face, and how feasible is it to parse each one?

Each claim is tagged with its source. **[P]** means a primary source: the issuer's or regulator's own page, or source code I read or ran. **[S]** means a secondary source only (a blog, aggregator or search-index snippet), so check it against a real statement before building on it.

## TL;DR

- **The CAMS/KFintech detailed CAS is the key input.** It is a single PDF covering every Mutual Fund folio held in SoA (non-demat) form across both RTAs. Every transaction row has date, amount, units, NAV and a running unit balance, and history can go back to 1990. The investor sets the PDF password when requesting it. `casparser` 1.4.1 parses it well: MIT licence, maintained, and it installs and passes its tests on Python 3.14.
- **Depository CAS (NSDL/CDSL) is the wrong tool for back-filling history.** It is sent monthly, contains only that month's transactions plus a holdings snapshot, and NSDL lets you re-download only the previous 12 months. `casparser` extracts **holdings only** from it, even though the PDF also has transaction sections. The password is the first holder's PAN in capitals.
- **Bank and card statements have no common format.** Each bank uses its own password rule and its own layout. PDF is always available. XLS/CSV are available for accounts at some banks (HDFC, ICICI) but rarely for cards. No maintained, permissively licensed library covers these banks, so each Importer is custom work.

## 1. CAS from the MF RTAs (CAMS and KFintech)

### What it is and who sends it

- SEBI requires AMCs/RTAs to send a CAS to unitholders who have **no demat account**. Investors who have a demat account get a combined CAS from the depositories instead (see §2). This split is by PAN. [P] [SEBI CIR/MRD/DP/31/2014 ¶4](https://www.cdslindia.com/downloads/Publications/Communique/DP-4816-SEBI-Circular-CAS-for-All-Securities-Assets.pdf)
- Separately from those scheduled statements, anyone can request a CAS **on demand** from either RTA. It is delivered by email:
  - CAMS: <https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement> ("mailback"). The page is a JS app I could not scrape, so the CAMS form details below are [S].
  - KFintech: <https://mfs.kfintech.com/investor/General/ConsolidatedAccountStatement> [P]
  - MFCentral (run jointly by CAMS and KFintech): <https://www.mfcentral.com>, linked from [AMFI's download-CAS page](https://www.amfiindia.com/online-center/download-cas) [P]
- **One request covers both RTAs.** The KFintech form says it consolidates holdings for investors with registered emails "across Funds serviced by CAMS and KFintech". [P] KFintech page. casparser's `rta` field accordingly holds either `"CAMS"` or `"KFINTECH"` for schemes within one statement. [P] casparser README
- **MF units held in demat form are not in the RTA CAS.** They appear in the depository CAS. [S] (repeated across broker help pages. Not confirmed on an RTA page.)

### Request options

| Option | KFintech [P] | CAMS [S] |
|---|---|---|
| Statement type | Summary / Detailed | Detailed / Summary |
| Period | Current FY, Previous FY, Specific Period | "Since inception", FY presets, Specific Period |
| Zero-balance folios | "With zero balance folio" checkbox | option present |
| Identifiers | email (required), PAN (optional) | email, PAN |
| Delivery | encrypted PDF to the email registered in the folio | same |

- **How far back history goes.** casparser's test fixtures contain real statements with periods `01-Jan-1990 → 31-Mar-2021` (KFintech) and `01-Jan-2000 → 31-Aug-2023` (CAMS/KFintech). [P] `tests/test_kfin.py:27`, `tests/test_cams.py:37`. In practice this means the full history of every folio.
- AMFI's page says MFCentral limits "Specific Period" to **365 days**. [P] AMFI. So MFCentral cannot replace the mailback form for back-filling.

### Password

- **The investor chooses it on the request form.** It is not derived from PAN or other personal data.
  - KFintech rule: at least 8 characters, with one upper-case letter, one lower-case letter, one digit and one special character. [P]
  - CAMS rule: 8–15 characters, starting with a letter, with at least one upper-case letter, one digit and one of `@ # $ * _`. [S]
- casparser's docstring says "most CAS PDFs are encrypted with the investor's PAN". That holds for NSDL/CDSL but not for mailback requests. [P] `casparser/parsers/__init__.py`
- MFCentral downloads reportedly use the PAN in upper case. [S]

### Detailed vs summary

- **Detailed CAS.** For each folio: AMC, PAN, KYC status and nominees. For each scheme: ISIN, advisor (ARN), opening and closing unit balances, valuation, and every transaction. Each transaction has date, description, amount, units, NAV and running unit balance. Tax rows (STT, stamp duty, TDS) have an amount but no units. [P] casparser README
- **Summary CAS.** Holdings and valuation only, with no transactions. [P] casparser README (`cas_type: SUMMARY`)
- **The running unit balance acts as a checksum.** Since v1.1, casparser reconciles `previous balance + units = printed balance` for every row and puts any mismatch in `parse_warnings`. [P] CHANGELOG 1.1.0

## 2. CAS from the depositories (NSDL and CDSL)

- **Mandate.** CAS started in March 2015, covering February 2015. It consolidates by PAN, or by the first holder's PAN plus holding pattern for joint accounts. It covers demat holdings in both depositories plus MF units in SoA form. **The depository where the investor opened a demat account first** sends it. [P] SEBI CIR/MRD/DP/31/2014 ¶4–6, 10
- **Frequency.** Monthly if there was any transaction in any demat account or MF folio during the month. Otherwise half-yearly, with holdings only. It is sent within 10 days of month end. [P] SEBI circular ¶6, 13; [NSDL CAS FAQ](https://investor.nsdl.com/portal/en/kb/articles/faqs-on-cas-26-10-2023); [CDSL CAS FAQ](https://www.cdslindia.com/cas/FAQ.html)
- **Contents.** "All types of transactions executed in demat mode". MF transactions (purchase, redemption, switch, dividend reinvestment, SIP/SWP/STP) **for the statement period**, plus holdings. [P] NSDL FAQ, CDSL FAQ
- **Password.** The first or sole holder's **PAN in CAPITAL letters**, for both depositories. [P] NSDL FAQ, CDSL FAQ
- **Past statements.** NSDL lets you view previously sent e-CAS for the **last 12 months** only, through IDeAS or <https://nsdlcas.nsdl.com>. [P] NSDL FAQ. CDSL lets you download dispatched CAS from its CAS tab or easi login, and its FAQ does not state a retention window. [P] CDSL FAQ
- **What this means for Folio.** A depository CAS is a monthly snapshot plus that month's movements. It cannot rebuild demat history from before the last 12 months. Full equity trade history must come from elsewhere, such as broker tradebooks or contract notes.
- **CDSL also shows NPS holdings.** casparser extracts them into `NSDLCASData.nps`. [P] CHANGELOG 1.3.0

## 3. `casparser`

| | |
|---|---|
| Repo | <https://github.com/codereverser/casparser> (231★, not archived, last push 2026-09-23) |
| Latest | **1.4.1** (2026-08-30). v1.0 shipped 2026-06-08, followed by 7 releases in 3 months [P] PyPI |
| Licence | **MIT**. Since v1.0 the only PDF backend is pypdfium2 (Apache-2.0/BSD-3). The earlier GPL/AGPL PyMuPDF backend was removed [P] README, CHANGELOG 1.0.0 |
| Dependencies | `casparser-isin` (MIT, a bundled ISIN/AMFI database), `pydantic>=2.3,<3`, `pypdfium2>=5,<7`, `click`, `rich`, `colorama`, `python-dateutil` [P] pyproject.toml |
| Python | `requires-python >=3.11`. Its classifiers claim 3.14, but CI only tests 3.11–3.13 [P] `.github/workflows/run-pytest.yml` |
| Python 3.14 check | **I ran it:** `uv run --python 3.14 pytest` gives 199 passed, 68 skipped. The skipped tests need the maintainer's encrypted sample PDFs, so the real-statement tests did not run on 3.14. With pypdfium2 5.8.0 [P] |
| Maintenance | Effectively one maintainer (codereverser has 328 commits, the next contributor 3). 12 open issues, and the maintainer responds within days (e.g. #150) [P] GitHub |

**Supported inputs** [P] README:

| Issuer | Variants | What is extracted |
|---|---|---|
| CAMS / KFintech | Detailed, Summary | `CASData`: folios → schemes → transactions |
| NSDL / CDSL | Demat consolidated | `NSDLCASData`: accounts → equities / mutual_funds / bonds, plus `nps`. **Holdings only, no transactions** |

**Output shape.** `read_cas_pdf(path_or_filelike, password, output="dict"|"json"|"csv")` returns pydantic models. JSON Schemas are committed under `schema/`. Decimal fields serialise as strings and dates as ISO strings, except `statement_period`, which stays `DD-MMM-YYYY`. [P] README

- **Transaction types:** `PURCHASE`, `PURCHASE_SIP`, `REDEMPTION`, `SWITCH_IN[_MERGER]`, `SWITCH_OUT[_MERGER]`, `DIVIDEND_PAYOUT`, `DIVIDEND_REINVEST`, `STT_TAX`, `STAMP_DUTY_TAX`, `TDS_TAX`, `SEGREGATION`, `GIFT_IN`/`GIFT_OUT`, `REVERSAL`, `MISC`, `UNKNOWN`.
- **Identifiers:** each scheme carries `isin`, `amfi` and `rta_code`, looked up from casparser-isin. Folios are keyed by `(amc, folio)` because folio numbers are unique only within an RTA. [P] CHANGELOG 1.1.0
- Errors are raised as `IncorrectPasswordError` and `CASParseError`. [P] `parsers/detect.py`

**Limitations and caveats** [P] README, source:

- **Only original issuer PDFs are accepted.** Detection relies on the watermark text `CAMSCASWS` / `KFINCASWS`, or on header strings for NSDL/CDSL. A CAS that has been re-printed, "saved as PDF" or re-rendered by a broker portal is rejected. MFCentral CAS is out of scope.
- Output changes between minor versions. For example, 1.4.0 added `MISC` marker rows and reclassified some `PURCHASE` rows as `PURCHASE_SIP`. Pin the version, and diff output when upgrading.
- Some CDSL PDFs have a Hindi-font overlay that makes cells unreadable. This is only partly recovered. [P] `parsers/cdsl.py` docstring
- There are open issues about bonus and merger handling (#88, #49), and 1.4.x emits a U+FFFE glyph in some `MISC` rows (#150, fix promised for 1.4.2).
- Bundled extras that Folio may or may not want: capital-gains and Schedule 112A reports, and Cost Inflation Index tables.

**Alternatives.** I found no other maintained, permissively licensed CAS parser. [casparser-web](https://github.com/codereverser/casparser-web) and [folioman](https://github.com/codereverser/folioman) are built on casparser.

## 4. Bank and credit-card statements

Banks publish very little about their export formats. Where a detail is marked [S], treat it as a hypothesis to check against a real statement.

### Password conventions

| Issuer | Product | PDF password | Source |
|---|---|---|---|
| HDFC Bank | Account (NetBanking download / email) | numeric **Customer ID** | [P] [hdfc.bank.in blog, 2026-06-18](https://www.hdfc.bank.in/blogs/digital-banking/download-account-statement-via-netbanking) |
| HDFC Bank | Credit card (email) | first 4 letters of name in UPPER CASE + last 4 digits of card. Some cards reportedly use name + DDMM | [S] |
| ICICI Bank | Account (email) | first 4 letters of account title, **lower case**, + DDMM of birth (or of incorporation for current accounts). Joint accounts use the first holder | [P] help.icicibank.com FAQ "What is the password to open my e-statement?" (seen via search index; the host did not resolve from here) |
| ICICI Bank | Credit card (email) | first 4 letters of name as on card + DDMM of birth | [P] same, plus "How do I open my Credit Card e-statement?" |
| SBI | Account (email / YONO) | last 5 digits of registered mobile + DOB as DDMMYY | [S]. SBI's [e-statement page](https://sbi.bank.in/web/customer-care/e-statement) does not state it |
| SBI Card | Credit card | DOB as DDMMYYYY + last 4 digits of card | [S]. The [SBI Card FAQ](https://www.sbicard.com/en/faq/statement-billing-related.page) does not state it |
| Axis Bank | Account and credit card | first 4 letters of name in UPPER CASE (ignoring spaces and dots) + DDMM of birth, **or** those 4 letters + 9-digit Customer ID | [P] [Axis support](https://application.axis.bank.in/webforms/axis-support/sub-issues/Cards-Credit-statement-5.aspx) |
| Kotak | Account | CRN (Customer Relationship Number) | [S] |
| Kotak | Credit card | unclear: sources disagree (DOB-based vs name + DDMM) | [S] |

Passwords come in three kinds:

- a static customer identifier (HDFC Customer ID, Kotak CRN)
- personal data (name prefix + DOB, mobile digits, card digits)
- one the user chose (CAMS/KFintech CAS)

The rules differ by issuer, and also by product and delivery channel at the same issuer.

### Export formats

| Issuer | Account statement | Card statement |
|---|---|---|
| HDFC Bank | NetBanking: choose period or custom range, and the file is password-protected [P]. Formats reportedly PDF, Excel, Text, Delimited, MS Money, with email in PDF only [S] | Monthly email PDF [S]. Community parsers exist (e.g. [xaneem/hdfc-credit-card-statement-parser](https://github.com/xaneem/hdfc-credit-card-statement-parser), MIT) |
| ICICI Bank | Email e-statement PDF [P]. NetBanking "View Detailed Statement" exports **XLS** (`OpTransactionHistory<date>.xls`, 12 header rows, columns `Transaction Date`, `Transaction Remarks`, …) and **CSV** [P via importer source] | Monthly **CSV**, yearly **XLS**, email PDF [P via importer source] |
| SBI | OnlineSBI can generate a statement for any date range with opening and closing balances [S]. Email PDF has columns `Date`, `Transaction Reference`, `Ref.No./Chq.No.`, `Debit`, `Credit`, `Balance` [P via importer source] | SBI Card: **PDF only**, last **24 months** downloadable [P] SBI Card FAQ |
| Axis Bank | NetBanking: "View detailed statement → select duration → **select format**" [P] [Axis support](https://application.axis.bank.in/webforms/axis-support/sub-issues/Bank-SB-statement-1.aspx). 3 years available online [S] | Email PDF [P via importer source] |
| Kotak | Kotak says banks "allow … PDF, CSV, or Excel" in general terms [P, non-specific] | Download via NetBanking or pre-login page, format unstated [P] |

"P via importer source" means the fact comes from parser code written against real statements. The source is [dumbPy/beancount-importers-india](https://github.com/dumbPy/beancount-importers-india), which is **GPL-3.0**, so it is useful only as a reference for layouts and not as a dependency. It uses camelot, tabula (Java) and pdfminer against fixed column x-coordinates, which shows how fragile PDF table extraction is for these statements.

### How hard each format is to parse

- **XLS/CSV** (ICICI accounts and cards; HDFC Delimited/Excel if confirmed): straightforward. The files have banner or header rows, footer rows, Indian-grouped numbers and DD/MM/YYYY dates. Each is a small, issuer-specific mapping.
- **PDF** (every issuer, and the only format for most cards): feasible with pypdfium2 or pdfplumber text-with-coordinates, but it breaks when the layout changes. Cards add extra complications: reward-point and cashback columns, "Cr"/"Dr" suffixes, EMI conversions, add-on card-holder sections, and international transactions with foreign-currency amounts.
- **No shared vocabulary.** Every bank uses its own column names and narration conventions.

## 5. Adjacent fact: Account Aggregator

RBI's Account Aggregator network delivers bank, MF and demat data as structured, consented JSON. However, the receiving party (a Financial Information User) must be registered with RBI, SEBI, IRDAI or PFRDA. [P] [Sahamati FIU](https://sahamati.org.in/financial-information-user-fiu/). A self-hosted personal app cannot join directly, so statements remain the realistic input.

## Open questions this raises

1. Folio's `Holding` is defined as "built from its transactions", but casparser gives **holdings only** for NSDL/CDSL. Demat equity history needs a different source (broker tradebook or contract-note Importers?), or Folio needs its own parser for the transaction section of depository CAS.
2. Investors with a demat account receive depository CAS by default. The RTA mailback CAS still works for them, but it leaves out MF units held in demat form. Are those units in scope for v1?
3. Password handling: should Folio store per-Importer password recipes (e.g. PAN, name + DOB, Customer ID), or prompt for the password on every import?
4. casparser relies on one maintainer and rejects re-printed PDFs. Pin the version and vendor it, or depend on it directly?
