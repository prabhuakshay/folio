# Folio

A single-person finance ledger for Indian markets: what I own, what I owe, what I spend, and whether my money is arranged to meet my Goals.

## Language

**Doctrine**:
The ordered ladder of financial-health Stages Folio holds you to. Folio records everything but endorses only what follows the Doctrine: it flags actions that skip a Stage rather than refusing them. Every threshold has a default and a recommended band; you may set any value, and Folio warns when it sits outside the band.

**Stage**:
One rung of the Doctrine, met or not met, in fixed order: no revolving credit → starter emergency fund → protection (health and term life cover) → high-interest debt cleared → full Emergency Fund → Goals and Retirement. The **current Stage** is the lowest one not met; surplus advice always points there. A Stage judged on declared rather than measured figures is **provisional**.

**Emergency Fund**:
A system Goal, fixed at 100% cash and liquid debt, that must cover the trailing 6 months of outflow: Expense Postings (less tax and employee EPF) plus loan principal repaid. Counts only what is Earmarked to it, and only Emergency-Fund-eligible Accounts and Instruments can be. Cannot be deleted.
_Avoid_: rainy-day fund, buffer

**Take-home**:
Trailing-12-month Income less Taxes and less whatever an Income Transaction puts straight into a retirement Account (employee and employer EPF/NPS, VPF, EPF and PPF interest credited); excludes Realised and Unrealised Gains. The base for the EMI cap, life-cover need and savings rate. Declared by hand until the ledger holds enough history.

**Dependent**:
A person who relies on your income or is under your health cover. Recorded in your profile; never logs in and owns nothing. Every Dependent needs health cover; only one flagged as **relying on your income** creates a need for term life cover.

**Account**:
A node in the Chart of Accounts that Postings hit. Every Account has one Account Type. A bank account, cash, a wallet, a loan, a credit card, a Holding, Groceries, Salary — all are Accounts.
An Account can be **closed** (zero balance required; hidden from pickers, history kept, reopenable; a Holding closes itself when its units reach zero and reopens on its next buy) or **deleted** (its Postings and sub-accounts moved to another Account first).
_Avoid_: ledger, category, head

**Account Role**:
A system purpose an Account serves so Folio can find it — Opening Balances, Realised Gains, Interest, Dividends, Interest paid, Bank charges & fees, Rewards & cashback, Insurance premiums, Taxes, Uncategorised. A role may sit on a group Account, meaning every Account under it (Taxes does). **Uncategorised** is where importers and quick-add put what they can't place, for review. A role-bearing Account can be deleted; Folio recreates it when the role is next needed, or the role is pointed at another Account.

**Account Type**:
One of Asset, Liability, Equity, Income, Expense. Fixes which side of the balance sheet or income statement an Account reports on.

**Chart of Accounts**:
The hierarchy of Accounts, grouped (e.g. Expenses › Food › Groceries, Assets › Bank › HDFC Savings). Postings hit only leaf Accounts; group Accounts only roll up. Folio seeds a default Indian personal Chart of Accounts, which you then edit freely.

**Transaction**:
Something that happened to your money on one day, recorded as two or more Postings that sum to zero — a card bill payment, an EMI split into principal and interest, an MF purchase, a payslip split into gross salary, TDS, EPF and net pay. Dated by when it happened, not when it cleared. A Corporate Action within one Holding is the one Transaction with a single Posting: units at ₹0.
_Avoid_: entry, journal, voucher

**Posting**:
One leg of a Transaction: a signed INR amount (Dr +, Cr −) to one Account. A Transaction's Postings always balance.
_Avoid_: split, line item

**Opening Balance**:
A Transaction on an Account's start date that brings in its balance as of that day, against the Opening Balances Equity Account. Each Account has its own start date. For a Holding it is an opening position of one or more **Opening Lots**.

**Opening Lot**:
Part of a Holding's opening position: units and cost with the date they were originally bought, which may be before the Holding's start date. Posted against Opening Balances on the start date, but its original date is what FIFO and XIRR use. An Opening Lot with units but no cost or date yet is **incomplete**: it counts toward units and value, is left out of XIRR and Realised Gains, and is flagged until completed.

**Realised Gain**:
The difference between a sale's proceeds, net of sell charges, and the FIFO cost of the units sold, posted to an Income Account. A buy's charges are part of its cost.

**Corporate Action**:
An event an issuer or AMC applies on a date to every Holding of one Instrument — split, consolidation, bonus, merger, demerger, segregated portfolio — changing units, cost or Instrument without money moving, so it never creates a Realised Gain. Recorded once per Instrument, it reaches only Holdings with Postings before its date, and lots keep their original dates: a split re-points the Holding to its new ISIN, a bonus adds a ₹0-cost lot on its allotment date, a merger carries every lot into a new Holding, a demerger moves a share of each lot's cost to one. Earmarks follow the units.
_Avoid_: scheme event, adjustment

**Units correction**:
Bringing a ULIP or NPS Holding's units to what its statement shows: units missing were cancelled for charges and post as an expense at the current Price, units extra (loyalty additions) are a ₹0-cost lot. No other Holding can be corrected this way.

**Unrealised Gain**:
The gap between Holdings' market value and their cost. Computed and shown under Equity on the balance sheet; never posted.

**Net Worth**:
Assets at market value minus Liabilities.

**Cash on hand**:
The sum of bank, cash and wallet Account balances — money spendable today without redeeming anything. Card balances are not netted off; Term Deposits and liquid funds are not included, even when Emergency-Fund eligible.
_Avoid_: liquidity, liquid assets

**Loan**:
A Liability Account with an interest rate and optionally EMI terms (EMI amount and EMI day) — a bank loan, a purchase converted to EMI on a Card, money borrowed from family. Each EMI is split into principal (to the Loan) and interest; its end date follows from balance, rate and EMI. An EMI is **overdue** once its EMI day plus a grace period passes with no payment into the Loan since the previous EMI day. A joint Loan is recorded at your share only. A Loan closes itself when its balance reaches zero and reopens on its next Posting.
_Avoid_: debt (means all Liabilities)

**Card**:
A revolving Liability Account with a billing cycle — a statement day, a due day and a credit limit. Credit cards and BNPL accounts are Cards. Its **statement amount due** is computed from the cycle's Postings, overridable per cycle; the Card is **paid in full** when payments into it between the statement day and the due day reach that amount. Closed only by hand.
_Avoid_: credit card (as the term), revolving account

**Term Deposit**:
An Asset Account of one kind — bank FD, post-office TD, RD, NSC, KVP, SCSS, POMIS or corporate FD — with a rate fixed for its term, a compounding frequency, a payout mode (cumulative, or paid out monthly, quarterly or yearly to a payout Account) and a maturity date. Its interest credits are Occurrences from its terms, pre-filled with the computed amount; an RD's monthly instalments are too. Its **maturity instruction** is to pay out (it then closes itself at zero) or renew, principal only or with interest, as the same Account under new terms. Goal projections grow it at its own rate until maturity.
_Avoid_: FD (as the umbrella term), fixed income

**Provident Account**:
A PPF or EPF Account, whose interest rate is set by government notification for the whole scheme and credited once a year, dated 31 March. Its interest credit is an estimated Occurrence, pre-filled with the computed amount at the latest known rate, and not overdue until six months past its date. Goal projections grow it at that rate. A PPF Account is held to its rules: at most ₹1.5L and at least ₹500 deposited per Financial Year, maturity after 15 years, extendable in 5-year blocks.
_Avoid_: retirement account (NPS is a Holding)

**Accrued interest**:
Interest a Term Deposit or Provident Account has earned since its last credit. Computed and shown on the Account; never posted, and counted in neither Net Worth, Goal progress nor the Emergency Fund until credited.

**Schedule**:
A rule that expects a Transaction to repeat — a template Transaction plus a recurrence (every N days, weeks, months or years, ending never, on a date or after N times). It may step up by a percentage or amount at intervals, its amount can be changed from an effective date, and it can be **paused** between two dates. Salary, rent, SIPs, subscriptions and premiums are Schedules. Loan EMIs, Card bills and interest credits are not: their Occurrences come from the Loan's, Card's, Term Deposit's or Provident Account's own terms. A Schedule is **fixed** (its Occurrences may post themselves on their date) or **estimated** (always confirmed, pre-filled with the last actual amount).
_Avoid_: recurring payment, standing instruction, mandate

**Occurrence**:
One dated instance a Schedule, Loan, Card, Term Deposit or Provident Account expects. It is **due** until **fulfilled** — by confirming it (with the date and amount edited if needed) or by linking a Transaction already recorded — or **skipped**; past its date it is **overdue**, and it never expires on its own. It returns to due if its Transaction is unlinked, deleted or undone with its Import; only deleting an auto-posted one skips it. Auto-post holds back, leaving it due, when a Match already exists.

**Budget**:
A monthly pay-yourself-first plan: expected income, less the **savings** reserved (the savings-rate target or the scheduled savings, whichever is larger), less **committed** spend (Occurrences that hit Expense Accounts, and Loan EMIs), leaves **spendable**. Spend not from a fulfilled Occurrence is **discretionary** and draws spendable down. Optional **limits** on any Expense Account, monthly or yearly, apply from the month they are set and never roll over. A Budget month begins on a chosen month-start day.
_Avoid_: envelope, sinking fund (a planned big spend is a Goal)

**Saved**:
Take-home less outflow (as the Emergency Fund counts it), plus what Income Transactions put straight into retirement Accounts. The **savings rate** is saved ÷ Take-home; loan principal repaid is outflow, not saving.

**Surplus to direct**:
Money Folio won't count as spendable — income that arrived without a Schedule (a bonus, a refund) and spendable left at month end — shown with advice pointing at the current Stage. Never moved automatically.
_Avoid_: windfall (as a term), rollover

**Tag**:
A free, flat label on a Transaction for spending that cuts across Accounts — a trip, a wedding. Used to filter and report; never drives the Budget.

**Financial Year**:
April to March — the default reporting period. Periods are never closed or locked; this is a personal finance app, not an accounting package.

**Goal**:
A named future need with a target amount in today's rupees, an inflation rate (general, medical or custom; 0% for a fixed nominal sum) and a target date (e.g. "Vacation 2027", "Retirement"). Each Goal has its own Target Allocation because its horizon sets its risk appetite. Goals sit in a **rank** you set; Retirement is always funded first. A Goal is **on track** when its projection (Earmarked value grown along its Glide Path plus future Occurrences of Schedules naming it) reaches its inflated target, otherwise **behind**; **unfunded** when Surplus runs out before its rank; **out of order** while it sits above the current Stage. You mark a Goal **reached** by hand, which releases its Earmarks; one past its date and not reached is flagged.
_Avoid_: bucket, compartment, envelope

**Asset Class**:
A risk category money sits in — equity, debt, gold & silver, real estate, cash. The unit in which a Target Allocation is expressed; cash counts toward its debt side. Instruments carry a split across Asset Classes; an Asset Account that isn't a Holding carries at most one (none for things like money lent or a car, which count in Net Worth but in no allocation).

**Target Allocation**:
The desired split of a Goal's money across equity, debt and gold & silver (e.g. 20:80 equity:debt for a one-year Goal) — never below Asset Class. Real estate Earmarked to a Goal counts toward its progress but sits outside its Target Allocation. Drift from it is what rebalancing corrects.

**Glide Path**:
How a Goal's default Target Allocation de-risks as its date nears, stepping down at the boundaries of SEBI's Life Cycle Fund equity bands by years-to-goal. An override is an offset from the band midpoint, carried across steps. Retirement switches to a fixed decumulation mix once its date passes.
_Avoid_: ratio, mix

**Instrument**:
One price series you can hold units of — a mutual fund plan and option, a listed stock/ETF/SGB/bond, one NPS scheme in one variant, physical gold, a ULIP fund, a property. Has an **Asset Class split**, usually 100% one class (a hybrid fund spans several). Priced from a Feed where a free one exists, otherwise revalued by hand. An SGB or listed bond carries a **coupon** (rate on its issue price or face value, and frequency). INR only; foreign assets are entered as INR-valued Instruments. The searchable catalogue is made of Instruments; one its Feed has stopped listing is **inactive** — hidden from search unless held, never deleted.

**Holding**:
An Asset Account whose value can differ from its INR balance because it is revalued, by Feed or by hand; every other Asset Account (bank, cash, wallet, FD, RD, EPF, PPF, chit fund, money lent) is valued at its balance. A Holding is your position in one Instrument at one place held (an MF folio, a demat account, an NPS PRAN tier), built from its Postings (buys, sells, SIP instalments, dividends, interest credits); each Posting to a Holding carries units as well as an INR amount at cost. Value is units × latest Price — computed, never posted, so price moves create no Transactions. Return is XIRR.

**Emergency-Fund eligible**:
Whether an Account or Instrument may count toward the Emergency Fund: savings, cash, wallets, liquid and overnight funds, and bank FDs and post-office TDs you mark as breakable. Nothing else can be made eligible.

**Price**:
The value of one unit of an Instrument on a date, from a Feed or entered by hand — one per date, a hand-entered Price outranking an uploaded file and an uploaded file outranking an automatic fetch, and an ETF's exchange close outranking its AMFI NAV. A Holding is valued at its Instrument's latest Price, carried forward, and at cost until its Instrument has one; a Price older than the Instrument's staleness window is **stale** — flagged, never blanked. A transaction's price is not a Price.

**Feed**:
A published file of Prices Folio reads — AMFI, a BSE or NSE bhavcopy, Protean NPS. Fetched automatically once a day, or **upload-only** (NSE always; any Feed switched off); every Feed also accepts its own file uploaded by hand. It prices only Instruments with an open Holding, back-filling past Prices at month-ends, daily for the last 30 days, back to the Instrument's earliest Posting.
_Avoid_: source (reserved for a statement's sources), provider

**Earmark**:
Assignment of part of an Asset Account to a Goal: units of a Holding (so the Goal's share moves with price), a fixed INR amount of a plain Account, or the **whole** Account, following all its future units or balance. A whole Earmark is exclusive; otherwise an Account may be split across several Goals, and its Earmarks never exceed its units or balance, and a Goal whose fixed-INR Earmark outruns the balance is **short**. Earmarks are current-only.
_Avoid_: allocation (reserved for Target Allocation)

**Unallocated**:
The portion of any Asset Account not Earmarked to a Goal. Allowed and visible, never forced.

**Statement Importer**:
A pluggable reader for one institution's statement format. It only reports what the statement says — per source (a bank account, a card, an MF folio's scheme, a demat account's security), dated lines and optionally the opening and closing balance or units — and Folio turns that into Transactions. It recognises its own files and says how their password is formed; the password is never kept. Each bank or card issuer is added as its own Importer. A depository (NSDL/CDSL) CAS yields only a holdings snapshot: its first import seeds demat Holdings with incomplete Opening Lots, and later imports post nothing and only flag Holdings whose units differ.

**Import**:
One run of a Statement Importer over one uploaded statement. It is staged for preview — lines Folio proposes to post, lines it could not read, and any gap against the statement's closing balance or units — and posts only the lines you confirm, all at once. An unconfirmed Import is discarded after a week; a confirmed one is kept as a record and can be **undone**, removing what it posted so a later Import can bring it back.
Folio remembers which Account each source maps to, and every line it has seen: a line already posted is never posted again, however the Transaction was edited since, and a line you unticked or whose Transaction you deleted is **dismissed** — offered again only greyed, for restoring. A line matching a Transaction you entered yourself is **linked** to it instead: the statement corrects its units, price and charges, and your Accounts and Tags stay. Lines dated before their Account's start date are covered by its Opening Balance and never posted. A closing balance or units that differ from the ledger stays flagged on the Account until a later Import agrees or you dismiss it.
_Avoid_: sync, upload (as the term)

**Funding Account**:
The Account a unit source's cash comes from and returns to when the statement doesn't say — the bank Account behind an MF folio. A line dated before the funding Account's start date is funded from Opening Balances instead, since that money predates Folio.

**Match**:
A Transaction Folio proposes as the same money as an import line or a due Occurrence: it hits the other record's **anchor Account** on the same side (the Loan or Card paid into; a Schedule's Expense, Income, Holding or other non-cash Account; an import source's mapped Account), within ±5 days (at most half the recurrence period), at the exact amount — any amount for estimated Schedules and Card bills; amount or units for unit lines. A unique best Match is pre-selected; none is ever accepted without a tap. Each Transaction answers at most one line and fulfils at most one Occurrence.
_Avoid_: reconcile, dedupe (as terms)

**Policy**:
An insurance contract you record: its type, insurer, persons covered (you and/or Dependents), sum assured, cover dates, nominees and riders. Not an Account — cover is a promise, not money you own; a pure-protection premium posts to an Expense Account, while a value-bearing Policy (ULIP, endowment) links to the Holdings that carry its value and its whole premium goes to them at cost. It counts only from its cover start to its **cover until** date — its own, not derived from any premium Schedule, and rolled forward by its **renewal term** when a linked premium Occurrence is fulfilled near it. **Employer-provided** cover is shown but never counted by the Doctrine.
_Avoid_: insurance account, plan (the insurer's product name only)

**Policy Type**:
One of a fixed set, each with a fixed meaning for the Doctrine: term life and endowment/ULIP (life cover, counted only when you are the life assured), health base and health super top-up (health cover, a floater counting its full sum insured for each person covered; a top-up counts only where a person's counted base cover reaches its deductible); personal accident, critical illness, motor, home, travel and other are recorded but never counted.

**Retirement**:
A system Goal like any other whose target is set live by a calculator: Retirement expense ÷ Safe Withdrawal Rate, in today's rupees. Its date is your date of birth plus your **retirement age**; it counts only what is Earmarked to it. Past that date it is in **drawdown**: judged by its **withdrawal rate** (trailing-12-month outflow ÷ Earmarked value) against the Safe Withdrawal Rate instead of on track or behind. Never marked reached; cannot be deleted.

**Retirement expense**:
The yearly spending the Retirement corpus must replace: trailing outflow (as the Emergency Fund counts it) less payments on Loans that end before retirement, unless you declare a monthly figure in today's rupees. Pensions, rent and other retirement income never reduce it.

**Safe Withdrawal Rate**:
The share of the Retirement corpus you can draw in the first year of retirement, then raise with inflation, without running out. A Doctrine threshold.
_Avoid_: SWR (in the UI), 4% rule

**Surplus**:
Trailing monthly Take-home less trailing monthly outflow — the money Doctrine advice directs, to the current Stage and then down the Goal rank.

**Drift**:
How far a Goal's actual mix sits from its Target Allocation, per Asset Class in percentage points. Past the inner band Folio nudges you to rebalance — first by re-earmarking between Goals or from Unallocated, then by steering new money; past the outer band, or at a Glide Path step, it suggests switching or selling. Judged per Goal; Unallocated has no target and never drifts.
_Avoid_: imbalance, deviation

**Preferred Instrument**:
The Instrument a Goal names for one Asset Class, so advice can say where new money goes. Advice only; never a target.

**Expected Return**:
The assumed nominal pre-tax yearly return of an Asset Class, used to project Goals. A Doctrine threshold with a default and a recommended band.

## Relationships

- A **Transaction** has two or more **Postings**, summing to zero
- A **Posting** hits exactly one **Account**
- An **Account** has exactly one **Account Type** and sits in the **Chart of Accounts**
- An **Account** carries zero or more **Account Roles**; each role is held by at most one Account
- A **Liability** Account is a **Loan**, a **Card**, or neither (a bill owed)
- A **Loan** may be owed to a **Card** (a purchase converted to EMI), whose instalments are billed onto that Card
- A **Schedule**, **Loan**, **Card**, **Term Deposit**, **Provident Account** or Holding in a coupon-bearing **Instrument** expects zero or more **Occurrences**; a fulfilled **Occurrence** is linked to exactly one **Transaction**
- A **Budget** limit sits on one Expense **Account**, leaf or group
- A **Goal** has exactly one **Target Allocation**
- A **Target Allocation** is expressed over **Asset Classes**
- An **Instrument** is split across one or more **Asset Classes**, the split summing to 100%
- An Asset **Account** that isn't a **Holding** carries zero or one **Asset Class**
- A **Holding** is in exactly one **Instrument** at one place held; an **Instrument** may have several **Holdings**
- A **Holding**'s **Opening Balance** is made of one or more **Opening Lots**
- A **Corporate Action** belongs to one **Instrument** and posts one **Transaction** per **Holding** it reaches
- An Asset **Account** is split between zero or more **Earmarks** and the **Unallocated** remainder
- An **Earmark** ties one Asset **Account** to one **Goal**
- A **Goal** names zero or one **Preferred Instrument** per **Asset Class**
- An **Import** is made by one **Statement Importer** and posts or links zero or more **Transactions**; an imported **Transaction** may come from several lines (a purchase and its stamp duty, both legs of a switch)
- A **Policy** has exactly one **Policy Type**, covers you and/or one or more **Dependents**, and links to zero or one premium **Schedule** and zero or more **Holdings**

## Flagged ambiguities

- "Account" means any Account in the Chart of Accounts, not just bank/cash. Say "bank Account" when that's meant. "Category" (for income/expense) is retired — those are Income and Expense Accounts.
- "compartmentalization" in the original brief meant earmarking money to **Goals**, each with its own **Target Allocation** — not a single portfolio-level ratio.
