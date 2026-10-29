# Project Charter — Retail Demand & Profitability Diagnostic

## Project title
Local Retail Demand and Profitability Diagnostic
A 24-month, 30-store POS profitability audit ending in a one-page decision memo.

## Business question
Which SKUs, categories, and discount tiers are growing revenue but destroying
contribution margin — and what three pricing, promotional, and operational
changes should the owner implement next month?

## Stakeholder persona
Owner-operator of a 30-store regional U.S. retail chain. Time-poor. Numbers-
literate but not SQL-literate. Reads memos on Sunday evening. Will not read a
dashboard with more than six visuals. Will act on a recommendation only if it
names a dollar value, a specific action, and an owner.

## Decision statement
This project succeeds if the owner can read a one-page memo and, within five
minutes, decide to (a) cap discounts at a specific tier, (b) reprice or delist
named SKUs, and (c) reallocate promotional spend — each with a dollar value
attached and a named owner.

## Scope

### In scope
- Data audit + weighted quality scorecard (Module 1)
- Modular SQL analytics layer with explicit metric definitions (Module 2)
- Diagnostic notebook: SKU-level, discount-tier, and category-level margin (Module 3)
- One-page executive dashboard (Module 4)
- One-page recommendation memo with five owned actions (Module 5)
- Quality gate + interview rehearsal (Module 6)
- Optional ML scoring module (Module 6.5) — conditional on Modules 1–5 passing DoD

### Explicitly out of scope
- Demand forecasting (diagnostic, not forecasting)
- Recommendation engine / personalized marketing
- Competitor pricing
- Fixed-cost / overhead allocation (dataset has none)
- Customer lifetime value modeling (Customer ID 65% null; cannot support it)
- A/B testing framework (no experimental data)

## Role-targeting map

| Target role | Where the project serves it | Artifact |
|---|---|---|
| Data analyst | SQL layer, metric definitions | Module 2 |
| BI analyst | Dashboard design, decision surface | Module 4 |
| Business analyst | Memo, stakeholder framing | Module 5 |
| Analytics consultant | Full arc: diagnosis → mechanism → intervention | Modules 1–5 |
| Junior data scientist | Optional triage classifier | Module 6.5 |
| Applied AI | Module 6.5 + honest scope discussion | Model card |

## Success criteria (all six must be true at Phase 6)
1. Memo is one page and ends in five owned actions with dollar values.
2. Every number in the memo is traceable to a named SQL query or notebook cell.
3. Dashboard answers the business question in under 30 seconds of cold viewing.
4. Project can be walked through in five minutes without opening a chart.
5. All code is reproducible: `docker compose up` runs the environment; a
   documented command sequence rebuilds the full analysis from raw CSVs.
6. README is readable in 90 seconds and makes the reviewer open the memo.

## Non-success metrics (do not optimize for these)
- Number of charts, tools, or lines of code.
- ML sophistication. A simple model that serves the decision beats a complex
  one that doesn't.
- Speed of completion.

## Locked assumptions (Phase 0 sign-off)
1. Line-level grain: one row = one (Transaction ID, Item, Unit Price, Discount)
   tuple. All 970,838 rows retained.
2. Net Sales = Gross Sales + Discounts (Discounts stored as negative). Verified 100%.
3. Discount % = −Discounts / Gross Sales × 100, computed per line where
   Gross Sales > 0 and Event Type = 'Payment'.
4. Refunds = Event Type = 'Refund' rows. Negative mirrors, retained in
   aggregations (they net out naturally at SKU/category level).
5. Gross Profit = Net Sales − Unit Cost × Qty (native column).
   **Contribution Margin ≡ Gross Profit** in this dataset, because there is no
   fixed-cost allocation. State this explicitly in every downstream artifact.
6. COGS is 100% complete. No cost assumption is used anywhere.
7. Repeat-purchase analysis is scoped to the loyalty segment (34.7% of payments
   carry a Customer ID). Stated as a limitation wherever relevant.
8. Two missing days (Christmas 2024, 2025) are documented store closures, not
   data loss. The event calendar confirms Store Closed = 1 on both.

## Tech stack (locked)

| Layer | Choice | Reason |
|---|---|---|
| Storage | CSV → PostgreSQL 16 in Docker | Production-realistic; portable; resume signal |
| Primary SQL | PostgreSQL 16 | Phase 2 queries |
| Notebook SQL | DuckDB (Python) | Fast iteration in Phase 3 only |
| Notebook | Jupyter, pandas, numpy, matplotlib, seaborn | Standard |
| ML (optional) | scikit-learn | Module 6.5 only |
| Dashboard | Power BI Desktop | Installed; native for target roles |
| Version control | Public GitHub | User choice |

## Timeline
Up to 40 hrs/week available. Phase length is set by DoD, not by clock.
Finishing fast is not the goal. Finishing defensible is.

## Approval
Phase 0 signs off when this charter is approved and PROJECT_LOG.md is updated.