# Free Indian price and NAV data sources

Research for [#4](https://github.com/prabhuakshay/folio/issues/4) (map: [#1](https://github.com/prabhuakshay/folio/issues/1)).
Every URL below was fetched with `curl` on **2026-09-30** unless marked otherwise. "UA" means the HTTP `User-Agent` header.

This note records facts only. It does not design the fetch pipeline.

## Summary

| Instrument | Source | Format | Key | Free history | Access notes |
|---|---|---|---|---|---|
| Mutual funds (incl. ETF NAVs) | AMFI `NAVAll.txt` + NAV history report | `;`-delimited text | AMFI scheme code (ISIN also given) | 2006 onwards | No UA filtering. ToS says "personal and non-commercial use only" |
| Listed stocks, ETFs, SGBs | NSE / BSE UDiFF CM bhavcopy | CSV (NSE zipped) | ISIN, NSE symbol, BSE scrip code | UDiFF from 2024-01-01. Older days only in the legacy format | Needs a browser UA. NSE ToS bans automated collection |
| Physical gold (and silver) | IBJA `ibjarates.com` | HTML only | purity (999, 995, 916, ...) | about 30 days (HTML table) | History only through a **paid** API |
| NPS schemes | Protean CRA `NAV_File_DDMMYYYY.zip` | CSV | NPS scheme code `SMxxxyyy` | mid-2014 onwards | Since 2026-04-01 one scheme has **several NAVs** (POP / Direct) |
| EPF, PPF, FD, real estate, chit funds, endowment policies | none | n/a | n/a | n/a | No price feed. Only rate notices or statements |

## 1. Mutual funds: AMFI

### Daily NAV: `NAVAll.txt`

- URL: `https://www.amfiindia.com/spages/NAVAll.txt`. It returns a **302 redirect** to `https://portal.amfiindia.com/spages/NAVAll.txt`, so use the portal URL. It returned 200, 1.52 MB, `text/plain`, UTF-8 with CRLF line endings, 18,141 lines.
- `Last-Modified` was `Wed, 30 Sep 2026 04:09:58 GMT` (09:39 IST). The file held NAVs dated 29-Sep-2026, so treat it as a T+1-morning file. `ETag` and `Last-Modified` headers are present, so conditional GETs are possible.
- The header now has **8 columns** (the older 6-column layout, still used by many third-party parsers, had no Plan and Option columns):
  ```
  Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date
  135762;INF846K01WO1;-;Axis Children's Fund;Direct Plan;Growth Option;29.2283;29-Sep-2026
  ```
  Non-data lines are interleaved: blank lines (a single space), category headings such as `Open Ended Schemes(Equity Scheme - Large Cap Fund)`, and fund-house names. Fund-house names can start with a digit (e.g. "360 ONE"), so "starts with a digit" does not reliably mark a data row.
- The date format is `DD-Mon-YYYY`. A missing ISIN is written `-`.
- Observed data quality:
  - 14,418 data rows, but only **8,695** carried the latest date. The rest are stale (matured or wound-up schemes). Their last NAV dates go back to 2018, e.g. 113 rows dated `02-Jul-2018`. Some show NAV `0`.
  - Among the current rows, **639** have no ISIN and **533** have empty Plan and Option fields. ETFs typically fall in this group, e.g. `115127;INF209KB18D3;-;Aditya Birla Sun Life Gold ETF;;;128.6205;29-Sep-2026`.
  - 5 ISINs appear on more than one scheme code. Scheme Name + Plan + Option is **not unique**: Axis Children's Fund has two "Direct Plan / Growth Option" rows (135762 and 135764) with different NAVs.
- It covers ETFs: 349 of the 351 ISINs in NSE's ETF list (`eq_etfseclist.csv`) appear in `NAVAll.txt`. An ETF therefore has both an AMFI NAV and an exchange close.

### Historical NAV

- URL: `https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=DD-Mon-YYYY&todt=DD-Mon-YYYY`, with an optional `mf=<AMC id>` (e.g. `mf=3` gave Aditya Birla SL only). An invalid `mf` returns an **HTML page with HTTP 200** instead of an error.
- It has a different 8-column layout:
  ```
  Scheme Code;NAV Name;Plan;Option;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Date
  ```
  The column order differs from `NAVAll.txt`: ISIN comes after Plan and Option.
- History: `frmdt=01-Apr-2006` returned data (2,276 rows for 3 days). No range cap was hit. A 4-month all-AMC request (Jan to Apr 2026) returned **94 MB and 711k rows in 73 s**. A 5-day request returned 4.7 MB in 3.5 s.
- No rate limit is documented, and none was hit.

### Scheme master

- URL: `https://portal.amfiindia.com/DownloadSchemeData_Po.aspx?mf=0`. It returns CSV, 4.1 MB, 16,493 schemes. It includes the AMC, code, category, launch and closure dates, and the minimum amount.
- **Gotcha:** the last column header is `ISIN Div Payout/ ISIN GrowthISIN Div Reinvestment`. Two ISINs are concatenated with no separator, e.g. `INF209K01157INF209K01CE5`, so split every 12 characters.

### Terms

- [AMFI Terms of Use](https://www.amfiindia.com/terms-of-use) grant a "non-exclusive, personal, non-transferable ... right to access, use and display this Site ... for your personal and non-commercial use only". They say nothing specific about automated download. Folio (self-hosted, single-user) fits "personal, non-commercial". [robots.txt](https://www.amfiindia.com/robots.txt) disallows only `/admin/`, `/login/` and `/search/`.
- No UA filtering: plain `curl` and `python-requests` UAs both got 200.

### Unofficial mirror (secondary, for reference)

- `https://api.mfapi.in/mf/<scheme code>` returns JSON with the full history for one scheme (e.g. 135762: 2,668 points back to 14-12-2015, `DD-MM-YYYY`). It is convenient for single-scheme backfill, but it is third-party and has no SLA.

## 2. Listed stocks, ETFs and SGBs: NSE and BSE bhavcopy

### The 2024 format change

Under **NSE circular 62424 (12-Jun-2024)**, the old CM bhavcopy was replaced by the **UDiFF** (Unified Distilled File Format) file from **08-Jul-2024**. The old files ran in parallel until **05-Jul-2024**. BSE made the matching UDiFF change. ([NSE circular](https://nsearchives.nseindia.com/content/circulars/INVG61787.pdf), [TeamLease summary, NSE](https://teamleaseregtech.com/updates/article/30936/nse-issued-regarding-the-discontinuation-date-for-old-formats-for-the/), [TeamLease summary, BSE](https://teamleaseregtech.com/updates/article/32519/bse-notified-regarding-the-standardization-of-exchange-to-member-inter/).) Both exchanges now publish the **same column schema**.

### NSE

- **Current (UDiFF):** `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip` (also served on `archives.nseindia.com`).
  - 29-Sep-2026: 200, 207 KB zip, 3,688 rows. `Last-Modified` was 11:09 GMT (16:39 IST, same day).
  - The archive starts at **2024-01-01**: 2024-01-02 returned 200, while every 2023 date tried returned 404. NSE back-converted history only to January 2024.
  - A missing day, such as a holiday or a date not yet published, returns a real **404**.
- **Legacy format** (needed for pre-2024 history): `https://nsearchives.nseindia.com/content/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip`, e.g. `2024/JUL/cm05JUL2024bhav.csv.zip`.
  - It exists from 1994 (`cm03NOV1994` returned 200) through **05-Jul-2024**. `cm08JUL2024` and later return 404.
  - The ISIN column is present from 2011 (present on 01-Dec-2011, absent on 03-Jan-2011). Earlier files are symbol-only.
  - Columns: `SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,`.
- Also available: `https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv`. It includes delivery data but **no ISIN**, and it goes back only to about 2020 (2020-01-03 returned 200, 2019 returned 404).
- **Masters:**
  - `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv`: symbol, name, series, listing date, **ISIN**, face value.
  - `https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv`: ETF symbol, underlying, **ISIN**.

### BSE

- **Current (UDiFF):** `https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_YYYYMMDD_F_0000.CSV`. It is a **plain CSV, not zipped**.
  - 29-Sep-2026: 864 KB, `Last-Modified` 10:59 GMT (16:29 IST).
  - It starts at **2024-01-01**; 2023-12-29 was not available.
- **Legacy format:** `https://www.bseindia.com/download/BhavCopy/Equity/EQ_ISINCODE_DDMMYY.zip`. It worked for 2023 and 2024 dates up to 05-Jul-2024, but was **not available for 2007, 2010 and 2015** dates, so BSE's free legacy archive is shallower than NSE's.
  - Columns: `SC_CODE,SC_NAME,SC_GROUP,SC_TYPE,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,NO_TRADES,NO_OF_SHRS,NET_TURNOV,TDCLOINDI,ISIN_CODE,TRADING_DATE,...`
- **Gotcha:** BSE returns **HTTP 200 with a 14 KB HTML page** (`text/html`) for any missing file (soft 404). Detect a miss by `Content-Type` or body, not by status code.

### UDiFF schema (both exchanges)

```
TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,
OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,
TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4
2026-09-29,2026-09-29,CM,NSE,STK,19078,IN0020200104,SGBJUN28,GB,,,,,2.5%GOLDBONDS2028SR-III,14700.00,...,14700.00,...
2026-09-29,2026-09-29,CM,BSE,STK,500002,INE117A01022,ABB,A,,,,,ABB INDIA LIMITED,6967.95,...,6845.00,...
```

- Dates are ISO `YYYY-MM-DD`. `ClsPric` is the close.
- `FinInstrmId` means different things on each exchange: the NSE token on NSE, the **BSE scrip code** on BSE (e.g. 500002). `TckrSymb` is the NSE symbol or the BSE short name.
- `SctySrs` on NSE is the series: `EQ` (2,671 rows), `BE`, `SM`, `ST`, `GS` (G-secs), **`GB` (SGBs, 44 rows)**, `TB`, `N*` (bonds), and so on. On BSE it holds the group (`A`, `B`, `X`, `T`, `M`, ...).
- **ETFs** sit in NSE series `EQ` (e.g. `INF204KB17I5,GOLDBEES,EQ,120.64`). **SGBs** are ISIN `IN0020...`, series `GB`, with symbols such as `SGBJUN28` and `SGBN28VIII`. BSE listed 28 SGB rows that day.
- **Only traded securities appear.** No row had `TtlTradgVol = 0` on either exchange. An illiquid SGB or small-cap therefore has **no row** on days it did not trade.
- **ISIN is not unique within one NSE file.** The same ISIN can appear under several series, e.g. `INE555B01013` as both `AXISCADES,BL` (block deal) and `AXISCADES,EQ`.

### Access and terms

- **UA filtering:**
  - NSE (Akamai) resets the connection (`HTTP/2 stream ... INTERNAL_ERROR`) for no UA, `curl/*` and `python-requests/*`. It served files to a browser-like UA with no cookies or referer.
  - BSE returned **403** to `python-requests/*` but served no-UA `curl` and browser UAs.
- **Rate limits:** neither exchange publishes any. NSE's [robots.txt](https://www.nseindia.com/robots.txt) allows `/`.
- **NSE Terms of Use** ([static/nse-terms-of-use](https://www.nseindia.com/static/nse-terms-of-use)): "User is prohibited to conduct any systematic or automated data collection activities (including scraping, data mining, data extraction and data harvesting) on or in relation to our Website". The bhavcopy is published for public download, but fetching it automatically technically falls under this clause. NSE's licensed alternative is paid (NSE Data / [dotexdata](https://dotexdata.nseindia.com/TermsAndConditions/TermsofUse.pdf)).
- **BSE Terms of Use** could not be read: the site is a JS app, and the terms page returned 403 to WebFetch. **Unverified.**

## 3. Gold: IBJA

- `https://ibjarates.com/` (no official free file or API) publishes the daily **AM (opening) and PM (closing)** rates for gold purities 999, 995, 916, 750 and 585, plus silver 999 and platinum 999. The site states: "*Gold rates per 10gm & Silver rate per 1kg*", "*without 3% GST and Making Charges*".
  - The headline tiles show **per-gram** values (e.g. `GoldRatesCompare999 = 14767`), while the tables are per 10 g (29/09/2026, 999: 147400 AM).
  - Only **HTML** is available: a "Previous 30 Days" table, a hidden JSON chart field (`HdnGold`, about 4 months of 999 and 916 closing values), and a "30 Days PDF" under `/UploadedFiles/30DaysPdf/`.
- Publishing calendar (from the IBJA Terms popup on the site): no rates on Saturdays, Sundays or Central Government holidays.
- **No free history:** longer history is available only through the **paid** "IBJA Rates API" ([indiagoldratesapi.com](https://www.indiagoldratesapi.com/)): "Is IBJA rates API free? No, It is a paid subscription." IBJA also says "*Any party using the IBJA Gold Price for valuation and pricing activities ... are advised to subscribe IBJA rates only through OFFICIAL IBJA API*".
- The disclaimer allows fair use only. Anything "beyond fair use" needs permission. No UA filtering was seen.
- **IBJA is the benchmark for SGBs:** RBI and the Ministry of Finance use the IBJA 999 closing price for SGB issue and redemption prices. The site hosts the RBI premature-redemption notices.
- **Free proxies** for gold history, if IBJA's history is out of reach:
  - Gold ETF NAVs in AMFI history back to 2006, though each ETF's NAV reflects a fraction of a gram less expenses.
  - Exchange closes for `GOLDBEES` and SGBs from the bhavcopy.

## 4. NPS: Protean CRA NAV file

- URL: `https://www.npscra.proteantech.in/download/NAV_File_DDMMYYYY.zip`. It is linked from the [PFM-wise NAV search](https://www.npscra.proteantech.in/nav-search.php) page. The old domain `npscra.nsdl.co.in` **no longer resolves**; the site says it has "migrated ... to https://www.npscra.proteantech.in".
- The zip contains `NAV_File_DDMMYYYY.out`, a header-less CSV (plus a stray `__MACOSX/` entry):
  ```
  09/28/2026,PFM001,SBI PENSION FUNDS PRIVATE LIMITED,SM001001,SBI PENSION FUND SCHEME - CENTRAL GOVT,49.8745
  ```
  Fields: date (**`MM/DD/YYYY`**, US order), PFM code, PFM name, **scheme code `SMxxxyyy`**, scheme name, NAV.
- Timing: the 28-Sep-2026 file was stamped 29-Sep 10:47 local time, and the 29-Sep file still returned 404 on the morning of 30-Sep. So NAV for day T lands around mid-morning of T+1. Missing days return a real 404.
- History: files exist back to **mid-2014**. 01-Jul-2014 and 02-Jan-2015 returned 200; 02-Jan-2014 and earlier returned 404. Longer per-scheme history is on each PFM's own site (SBI, HDFC, ICICI, Axis, Tata, ABSL, ...), which are linked from the same page but not probed here.
- **2026 change, multiple NAVs per scheme:** from **01-Apr-2026**, under PFRDA circular PFRDA/2026/15/REG-PF/04 (06-Mar-2026) and PFRDA/2026/16–17/REG-POP, each scheme has separate NAVs for Government, **POP** and **Direct/e-NPS** subscribers. This implements differentiated investment management fees and POP charges ([Public Notice, 24-Mar-2026](https://www.npscra.proteantech.in/download/Public%20Notice%20-%20Implementation%20of%20multiple%20NAVs%20framework%20wef%2001.04.2026.pdf)).
  - The file grew from about **104 rows (Jan 2023) to 273 rows (Sep 2026)**.
  - Names now end in `TIER I POP`, `TIER I DIRECT`, `TIER I GS`, `TIER II POP`, `TIER II DIRECT`, `VATSALYA SCHEME POP/DIRECT`, `LITE ... POP/DIRECT`, `UPS CG SCHEME`, and so on.
  - Existing codes were **renamed in place**: `SM001003` was "SCHEME E - TIER I" in 2023 and is "SCHEME E - TIER I POP" now, while the Direct variant got a new code (`SM001025`).
- Terms: the [Protean disclaimer](https://www.npscra.proteantech.in/disclaimer.php) disclaims accuracy and says access "may be monitored". It has no scraping clause. No UA filtering was seen (a `python-requests` UA got 200).

## 5. Identifier mapping

| Identifier | Where it lives | Notes |
|---|---|---|
| **AMFI scheme code** (integer, e.g. 135762) | `NAVAll.txt`, NAV history, scheme master | The only key for MF NAVs. One code is one plan and option. |
| **ISIN** (12 chars) | AMFI (per plan and option, two columns: growth/payout and reinvestment); UDiFF `ISIN`; `EQUITY_L.csv`; `eq_etfseclist.csv` | The only key shared by AMFI, NSE and BSE. It is what CAS and contract notes carry. ISIN to AMFI code is not always 1:1 (5 duplicates, 639 current rows missing ISIN). ISIN is not unique per exchange file (multiple series). Prefixes: `INE` equity/corporate, `INF` MF/ETF units, `IN00` government securities including SGBs. |
| **NSE symbol + series** | UDiFF `TckrSymb` + `SctySrs`; `EQUITY_L.csv` | Symbols change on renames and mergers. The ISIN is more stable. |
| **BSE scrip code** (6 digits) | BSE UDiFF `FinInstrmId` | BSE's primary key. |
| **NPS scheme code** (`SMxxxyyy`) | Protean NAV file | No ISIN. PFM code `PFMxxx` is the second field. |
| **Gold purity** | IBJA | 999, 995, 916 (22k), 750 (18k), 585 (14k). No other identifier. |

## 6. Instruments with no price feed

None of these has a public end-of-day price. Their value comes from contract terms, declared rates or statements:

- **EPF:** the interest rate is declared once a year by EPFO/CBT, and the balance comes from the member passbook. No daily feed.
- **PPF:** the rate is notified quarterly by the Ministry of Finance (DEA) in its small-savings notification. No price. The balance follows from contributions, the rate and PPF's monthly-minimum-balance rule.
- **Fixed deposits:** bank-specific contracted rate and compounding. No feed.
- **Real estate:** no market feed. State circle and guidance rates exist but are not market prices. Value is manual.
- **Chit funds:** no feed. Value comes from the foreman's statements and auction dividends.
- **Endowment policies:** no feed. Insurers declare reversionary bonuses once a year, and surrender value is on request.

(These are domain facts, not probed sources. No URL was checked for this section.)

## Open points surfaced

1. **Terms:** NSE's ToS literally bans automated collection. AMFI's allows personal, non-commercial use. IBJA wants valuation users on its paid API. Whether a single-user self-hosted app fetching one file a day is acceptable is a judgement call for the project, not something this research can settle.
2. **Pre-2024 equity history** needs a second parser (legacy NSE format), and NSE files before 2011 lack ISIN.
3. **Missing rows:** instruments that did not trade that day have no bhavcopy row, so a "last available close" rule is needed. Matured MF schemes stay in `NAVAll.txt` with stale dates.
4. **NPS multiple-NAV split:** a holding must record which variant it is in (POP, Direct, Govt). Pre-April-2026 history lives under a code whose name has since changed.
5. **ETFs** are priced by both AMFI (NAV) and the exchanges (close). Choose one deliberately.
6. **Free gold history** is limited to about 30 days from IBJA. Anything longer means a paid API or a proxy.
