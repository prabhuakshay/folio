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
Something that happened to your money on one day, recorded as two or more Postings that sum to zero — a card bill payment, an EMI split into principal and interest, an MF purchase, a payslip split into gross salary, TDS, EPF and net pay. Dated by when it happened, not when it cleared.
_Avoid_: entry, journal, voucher

**Posting**:
One leg of a Transaction: a signed INR amount (Dr +, Cr −) to one Account. A Transaction's Postings always balance.
_Avoid_: split, line item

**Opening Balance**:
A Transaction on an Account's start date that brings in its balance as of that day, against the Opening Balances Equity Account. Each Account has its own start date. For a Holding it is an opening position: units and cost.

**Realised Gain**:
The difference between a sale's proceeds and the FIFO cost of the units sold, posted to an Income Account.

**Unrealised Gain**:
The gap between Holdings' market value and their cost. Computed and shown under Equity on the balance sheet; never posted.

**Net Worth**:
Assets at market value minus Liabilities.

**Loan**:
A Liability Account with an interest rate and optionally EMI terms (EMI amount and EMI day) — a bank loan, a purchase converted to EMI on a Card, money borrowed from family. Each EMI is split into principal (to the Loan) and interest; its end date follows from balance, rate and EMI. An EMI is **overdue** once its EMI day plus a grace period passes with no payment into the Loan since the previous EMI day. A joint Loan is recorded at your share only. A Loan closes itself when its balance reaches zero and reopens on its next Posting.
_Avoid_: debt (means all Liabilities)

**Card**:
A revolving Liability Account with a billing cycle — a statement day, a due day and a credit limit. Credit cards and BNPL accounts are Cards. Its **statement amount due** is computed from the cycle's Postings, overridable per cycle; the Card is **paid in full** when payments into it between the statement day and the due day reach that amount. Closed only by hand.
_Avoid_: credit card (as the term), revolving account

**Schedule**:
A rule that expects a Transaction to repeat — a template Transaction plus a recurrence (every N days, weeks, months or years, ending never, on a date or after N times). It may step up by a percentage or amount at intervals, its amount can be changed from an effective date, and it can be **paused** between two dates. Salary, rent, SIPs, subscriptions and premiums are Schedules. Loan EMIs and Card bills are not: their Occurrences come from the Loan's or Card's own terms. A Schedule is **fixed** (its Occurrences may post themselves on their date) or **estimated** (always confirmed, pre-filled with the last actual amount).
_Avoid_: recurring payment, standing instruction, mandate

**Occurrence**:
One dated instance a Schedule, Loan or Card expects. It is **due** until **fulfilled** — by confirming it (with the date and amount edited if needed) or by linking a Transaction already recorded — or **skipped**; past its date it is **overdue**, and it never expires on its own.

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
One price series you can hold units of — a mutual fund plan and option, a listed stock/ETF/SGB/bond, one NPS scheme in one variant, physical gold, a ULIP fund, a property. Has an **Asset Class split**, usually 100% one class (a hybrid fund spans several). Priced from a feed where a free one exists, otherwise revalued by hand. INR only; foreign assets are entered as INR-valued Instruments.

**Holding**:
An Asset Account whose value can differ from its INR balance because it is revalued, by feed or by hand; every other Asset Account (bank, cash, wallet, FD, RD, EPF, PPF, chit fund, money lent) is valued at its balance. A Holding is your position in one Instrument at one place held (an MF folio, a demat account, an NPS PRAN tier), built from its Postings (buys, sells, SIP instalments, dividends, interest credits); each Posting to a Holding carries units as well as an INR amount at cost. Value is units × latest Price — computed, never posted, so price moves create no Transactions. Return is XIRR.

**Emergency-Fund eligible**:
Whether an Account or Instrument may count toward the Emergency Fund: savings, cash, wallets, liquid and overnight funds, and FDs you mark as breakable. Nothing else can be made eligible.

**Price**:
The value of one unit of an Instrument on a date, from a feed or entered by hand. A Holding is valued at its Instrument's latest Price, carried forward; a Price older than the Instrument's staleness window is **stale** — flagged, never blanked.

**Earmark**:
Assignment of part of an Asset Account to a Goal: units of a Holding (so the Goal's share moves with price), a fixed INR amount of a plain Account, or the **whole** Account, following all its future units or balance. A whole Earmark is exclusive; otherwise an Account may be split across several Goals, and its Earmarks never exceed its units or balance, and a Goal whose fixed-INR Earmark outruns the balance is **short**. Earmarks are current-only.
_Avoid_: allocation (reserved for Target Allocation)

**Unallocated**:
The portion of any Asset Account not Earmarked to a Goal. Allowed and visible, never forced.

**Statement Importer**:
A pluggable reader that turns one institution's statement format into Transactions. Each bank or card issuer is added as its own Importer.

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
- A **Schedule**, **Loan** or **Card** expects zero or more **Occurrences**; a fulfilled **Occurrence** is linked to exactly one **Transaction**
- A **Budget** limit sits on one Expense **Account**, leaf or group
- A **Goal** has exactly one **Target Allocation**
- A **Target Allocation** is expressed over **Asset Classes**
- An **Instrument** is split across one or more **Asset Classes**, the split summing to 100%
- An Asset **Account** that isn't a **Holding** carries zero or one **Asset Class**
- A **Holding** is in exactly one **Instrument** at one place held; an **Instrument** may have several **Holdings**
- An Asset **Account** is split between zero or more **Earmarks** and the **Unallocated** remainder
- An **Earmark** ties one Asset **Account** to one **Goal**
- A **Goal** names zero or one **Preferred Instrument** per **Asset Class**
- A **Policy** has exactly one **Policy Type**, covers you and/or one or more **Dependents**, and links to zero or one premium **Schedule** and zero or more **Holdings**

## Flagged ambiguities

- "Account" means any Account in the Chart of Accounts, not just bank/cash. Say "bank Account" when that's meant. "Category" (for income/expense) is retired — those are Income and Expense Accounts.
- "compartmentalization" in the original brief meant earmarking money to **Goals**, each with its own **Target Allocation** — not a single portfolio-level ratio.
