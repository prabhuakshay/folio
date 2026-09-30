# Double-entry ledger with a full Chart of Accounts

Folio's core record is a double-entry ledger: every Transaction is two or more Postings that sum to zero, each hitting one leaf Account in a hierarchical Chart of Accounts typed Asset, Liability, Equity, Income or Expense. Almost everything in personal finance is money moving between two places — card bill payments, EMIs split into principal and interest, MF purchases, payslips, transfers — and a single-sided model needs a special linked-pair case for each, which every report then has to know to skip. Double-entry makes net worth the sum of balances and statement mismatches real, findable differences.

## Considered Options

- **Single-sided transactions with categories** — simpler on day one, but transfers, liabilities and investments each become a special case.
- **Friendly "four kinds of place" (Account / Liability / Holding / Category)** — rejected because the user is an accountant; a real Chart of Accounts is more precise, and "Category" is just an Income/Expense Account.

## Consequences

- Holdings are Asset Accounts whose Postings carry units as well as INR cost. Market value is computed (units × latest price) and never posted; sales book a FIFO Realised Gain. The balance sheet shows Holdings at market value with a computed Unrealised Gain line in Equity.
- Opening balances are ordinary Transactions against an Opening Balances Equity Account, on each Account's own start date — including opening positions for EPF, PPF, NPS, gold and property that no statement import covers.
- It is not an accounting package: Transactions stay freely editable, Accounts can be deleted GnuCash-style, and there are no closing entries or locked periods. Reports default to the Indian financial year (April–March).
