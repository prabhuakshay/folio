# Folio

A single-person finance ledger for Indian markets: what I own, what I owe, what I spend, and whether my money is arranged to meet my Goals.

## Language

**Doctrine**:
The ordered ladder of financial-health Stages Folio holds you to. Folio records everything but endorses only what follows the Doctrine: it flags actions that skip a Stage rather than refusing them. Every threshold has a default and a recommended band; you may set any value, and Folio warns when it sits outside the band.

**Stage**:
One rung of the Doctrine, met or not met, in fixed order: no revolving credit → starter emergency fund → protection (health and term life cover) → high-interest debt cleared → full Emergency Fund → Goals and Retirement. The **current Stage** is the lowest one not met; surplus advice always points there. A Stage judged on declared rather than measured figures is **provisional**.

**Emergency Fund**:
A system Goal, fixed at 100% cash and liquid debt, that must cover the trailing 6 months of outflow: Expense Postings (less tax and employee EPF) plus loan principal repaid. Cannot be deleted.
_Avoid_: rainy-day fund, buffer

**Take-home**:
Trailing-12-month Income less tax and employee EPF; excludes Realised and Unrealised Gains. The base for the EMI cap, life-cover need and savings rate. Declared by hand until the ledger holds enough history.

**Dependent**:
A person who relies on your income or is under your health cover. Recorded in your profile; never logs in and owns nothing.

**Account**:
A node in the Chart of Accounts that Postings hit. Every Account has one Account Type. A bank account, cash, a wallet, a loan, a credit card, a Holding, Groceries, Salary — all are Accounts.
An Account can be **closed** (zero balance required; hidden from pickers, history kept, reopenable) or **deleted** (its Postings and sub-accounts moved to another Account first).
_Avoid_: ledger, category, head

**Account Role**:
A system purpose an Account serves so Folio can find it — Opening Balances, Realised Gains, Interest paid, Insurance premiums. A role-bearing Account can be deleted; Folio recreates it when the role is next needed, or the role is pointed at another Account.

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

**Financial Year**:
April to March — the default reporting period. Periods are never closed or locked; this is a personal finance app, not an accounting package.

**Goal**:
A named future need with a target amount and a target date (e.g. "Vacation 2027", "Retirement"). Each Goal has its own Target Allocation because its horizon sets its risk appetite.
_Avoid_: bucket, compartment, envelope

**Asset Class**:
The risk category an Instrument belongs to — equity, debt, gold, real estate, cash. The unit in which a Target Allocation is expressed.

**Target Allocation**:
The desired split of a Goal's money across Asset Classes (e.g. 20:80 equity:debt for a one-year Goal). Drift from it is what rebalancing corrects.

**Glide Path**:
How a Goal's default Target Allocation de-risks as its date nears, following SEBI's Life Cycle Fund equity bands by years-to-goal. Retirement switches to a fixed decumulation mix once its date passes.
_Avoid_: ratio, mix

**Instrument**:
Something you can hold value in — a mutual fund scheme, a listed stock/ETF/SGB, an FD, PPF, EPF, NPS tier, gold, a property. Belongs to one Asset Class. Priced from a feed where a free one exists, otherwise revalued by hand. INR only; foreign assets are entered as INR-valued Instruments.

**Holding**:
An Asset Account holding your position in one Instrument, built from its Postings (buys, sells, SIP instalments, dividends, interest credits); each Posting to a Holding carries units as well as an INR amount at cost. Value is units × latest price — computed, never posted, so price moves create no Transactions. Return is XIRR.

**Earmark**:
Assignment of some units of a Holding to a Goal. A Holding may be split across several Goals by units, so each Goal's share moves with price.
_Avoid_: allocation (reserved for Target Allocation)

**Unallocated**:
The portion of any Holding not Earmarked to a Goal. Allowed and visible, never forced.

**Statement Importer**:
A pluggable reader that turns one institution's statement format into Transactions. Each bank or card issuer is added as its own Importer.

**Retirement**:
A Goal like any other, with a projection calculator attached — not a separate subsystem.

## Relationships

- A **Transaction** has two or more **Postings**, summing to zero
- A **Posting** hits exactly one **Account**
- An **Account** has exactly one **Account Type** and sits in the **Chart of Accounts**
- An **Account** carries zero or more **Account Roles**; each role is held by at most one Account
- A **Goal** has exactly one **Target Allocation**
- A **Target Allocation** is expressed over **Asset Classes**
- An **Instrument** belongs to exactly one **Asset Class**
- A **Holding** is in exactly one **Instrument**
- A **Holding**'s units are split between zero or more **Earmarks** and the **Unallocated** remainder
- An **Earmark** ties one **Holding** to one **Goal**

## Flagged ambiguities

- "Account" means any Account in the Chart of Accounts, not just bank/cash. Say "bank Account" when that's meant. "Category" (for income/expense) is retired — those are Income and Expense Accounts.
- "compartmentalization" in the original brief meant earmarking money to **Goals**, each with its own **Target Allocation** — not a single portfolio-level ratio.
