# Folio

A single-person finance ledger for Indian markets: what I own, what I owe, what I spend, and whether my money is arranged to meet my Goals.

## Language

**Doctrine**:
The ordered set of financial-health rules Folio holds you to (emergency fund, insurance cover, debt limits, allocation by horizon). Folio is opinionated: it advises and enforces against the Doctrine, not just records.

**Goal**:
A named future need with a target amount and a target date (e.g. "Vacation 2027", "Retirement"). Each Goal has its own Target Allocation because its horizon sets its risk appetite.
_Avoid_: bucket, compartment, envelope

**Asset Class**:
The risk category an Instrument belongs to — equity, debt, gold, real estate, cash. The unit in which a Target Allocation is expressed.

**Target Allocation**:
The desired split of a Goal's money across Asset Classes (e.g. 20:80 equity:debt for a one-year Goal). Drift from it is what rebalancing corrects.
_Avoid_: ratio, mix

**Instrument**:
Something you can hold value in — a mutual fund scheme, a listed stock/ETF/SGB, an FD, PPF, EPF, NPS tier, gold, a property. Belongs to one Asset Class. Priced from a feed where a free one exists, otherwise revalued by hand. INR only; foreign assets are entered as INR-valued Instruments.

**Holding**:
Your position in one Instrument, built from its transactions (buys, sells, SIP instalments, dividends, interest credits). Value is units × price; return is XIRR.

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

- A **Goal** has exactly one **Target Allocation**
- A **Target Allocation** is expressed over **Asset Classes**
- An **Instrument** belongs to exactly one **Asset Class**
- A **Holding** is in exactly one **Instrument**
- A **Holding**'s units are split between zero or more **Earmarks** and the **Unallocated** remainder
- An **Earmark** ties one **Holding** to one **Goal**

## Flagged ambiguities

- "compartmentalization" in the original brief meant earmarking money to **Goals**, each with its own **Target Allocation** — not a single portfolio-level ratio.
