# Cleaning Log — Retail Profitability Diagnostic

Every decision that changed, preserved, or interpreted the data is recorded
here. Entries are in chronological order. Each entry states: what happened,
why it happened, and what was decided.

---

### 2026-10-29 — No rows excluded from the raw dataset

`scripts/verify_dataset.py` was run against the raw CSV and reported
970,838 rows with **zero full-row duplicates**. All rows were retained. The
initial script output flagged what appeared to be missing columns and
arithmetic failures; each was investigated in the entries below and none
required row exclusion.

---

### 2026-10-29 — Discounts are stored as negative dollar amounts, not percentages

`scripts/verify_dataset.py` initially classified the `Discounts` column as a
fraction (0–1). Follow-up check (`scripts/resolve_ambiguities.py`) showed the
actual range is `-154.80 → 0.00`, meaning discounts are stored as **negative
dollars**. The correct arithmetic is `net_sales = gross_sales + discounts`,
which was verified at 100% match across all 970,838 rows. A derived
`discount_pct` column was added: `-discounts / gross_sales × 100`. The original
`Discounts` column is preserved unchanged in staging and fact.

---

### 2026-10-29 — Refund column does not exist; `Event Type` is the refund indicator

The verification script looked for a `refund` column and did not find one.
Investigation showed `Event Type` has two values: `Payment` (961,389 rows) and
`Refund` (9,449 rows). Every `Refund` row has negative `Qty`, negative
`Gross Sales`, and negative `Gross Profit`, mirroring an earlier `Payment` row.
All 9,449 refund rows were retained. Dropping them would overstate net sales
and contribution margin at every group grain.

---

### 2026-10-29 — Duplicate (Transaction ID, Item) keys are legitimate business variants

32,342 rows share a `(Transaction ID, Item)` pair. All are `Payment` rows with
positive `Qty`. Sample inspection shows the same item appearing at different
`Unit Price` / `Price Point Name` / discount levels within one transaction —
e.g. a "buy 2, get 10% off the second" pattern. These are legitimate
line-level variants, not data errors. All retained.

---

### 2026-10-29 — Customer ID is 65.3% null; retained, with scoping rule

634,393 of 970,838 rows (65.3%) have a NULL `Customer ID`. This reflects guest
checkout: 100% of `Refund` rows and 65.0% of `Payment` rows lack a customer
identifier. NULLs were retained (no imputation, no dropping). **Locked rule:**
every customer-behavior metric in this project (repeat purchase, segment
margin) is explicitly scoped to the *identified loyalty segment only* and is
never presented as describing the full customer base.

---

### 2026-10-29 — Two missing days are documented store closures

Calendar range is 2024-01-01 → 2025-12-31 (731 days); 729 distinct dates
appear in the transaction data. The two absent dates are 2024-12-25 and
2025-12-25. Both are flagged `Store Closed = 1` in
`02_ground_truth_event_calendar.csv`, and zero transactions exist on those
dates in the raw file. This is expected business behavior, not a data-quality
issue. No action taken.

---

### 2026-10-29 — Validation script CHK4/CHK6 referenced a nonexistent column

`sql/03_validation_tests.sql` initially referenced
`fact_line_items.gross_profit` in CHK4 and CHK6. The fact table's column is
named `contribution_margin` (locked assumption #5: the two terms are
equivalent in this dataset because no fixed-cost allocation exists). The first
validation run raised `column "gross_profit" does not exist` after CHK1–CHK3
had already passed. The fix was to point CHK4 and CHK6 at
`contribution_margin`. No data was changed. The bug was caught by the
validation layer itself, before any downstream artifact depended on the
naming — which is the point of having a validation layer.

---

### 2026-10-29 — Reconciliation against vendor summary file passes at delta 0.00

`sql/03_validation_tests.sql` CHK9 aggregates `fact_line_items.gross_sales` by
store and compares to `stg_store_summary.gross_sales`. All 30 stores match at
**exactly 0.00 delta**, not merely within tolerance. This is the load's
primary integrity evidence: the vendor's summary file and the line-item
detail reconcile to the cent over 970,838 rows. Documented as the
authoritative proof that the ETL preserved the source's arithmetic.

---

### 2026-10-29 — Discount tiers corrected from six to seven; edge values bucketed

The initial Phase 0 analysis reported the discount tiers as exactly
`{0, 10, 15, 20, 25, 40}` — six values. A distinct-value query run during
Phase 1B-i pre-commit verification (`SELECT discount_pct, COUNT(*) FROM
fact_line_items WHERE discount_pct IS NOT NULL GROUP BY 1`) exposed two
errors in that claim:

1. **A seventh tier exists: 30%** (9,008 lines). The original scan had used
   banded ranges ("21–30%") that silently collapsed 30% into the 25% band.
2. **Eleven edge values exist** (`14.95, 14.97, 14.98, 14.99, 15.01, 24.98,
   24.99, 25.01, 25.03, 25.05`) produced by rounding when the source dollar
   discount is not an exact multiple of gross. All fall within ±0.1 of a
   nominal tier.

Resolution: document the seven nominal tiers. For any tier-level analysis,
derive `discount_tier` as the nearest nominal tier within ±0.1. Bucketed line
counts reconcile to 961,389 (all `Payment` rows), confirming no line is
orphaned. This correction was caught before commit by the pre-commit
verification queries; no artifact downstream of Phase 1B-i inherited the
wrong tier count.

---

### 2026-10-29 — Scorecard overall corrected from 99.0% to 98.8%

The scorecard's stated overall of "99.0%" was a rounding impression written
at Phase 1B-i. The actual weighted computation
(`0.25×95 + 0.20×100 + 0.20×100 + 0.15×100 + 0.20×100`) is **98.75%**. The
discrepancy was caught when `notebooks/01_data_audit.ipynb` cell 5 recomputed
the scorecard from the same inputs and printed 98.8%. The doc and the notebook
now agree. No data or dimension scores changed — only the arithmetic summary.