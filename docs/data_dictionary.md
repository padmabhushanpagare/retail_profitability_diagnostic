# Data Dictionary — Retail Profitability Diagnostic

**Project:** Local Retail Demand and Profitability Diagnostic
**Source:** Mendeley synthetic multi-store POS dataset (`39xdjxgnmf`, v1)
**Last updated:** 2026-10-29
**Database:** PostgreSQL 16, schema `retail`

This file defines every column present in the project, from raw source file to
final fact table. Where a later artifact (SQL query, notebook, dashboard,
memo) references a column, its meaning is the one below. New columns are added
here before they are used anywhere else.

---

## A. Source file `01_square_item_sales_detail_24mo.csv.gz`

**Shape:** 970,838 rows × 22 columns. 24 months (2024-01-01 → 2025-12-31).

| # | Source column | DB column (staging & fact) | Type | Description | Allowed values / range | Nullable |
|---|---|---|---|---|---|---|
| 1 | Date | date / sale_date | DATE | Transaction date | 2024-01-01 → 2025-12-31; 729 distinct days | No |
| 2 | Time | time / sale_time | TIME | Transaction time (local) | 00:00 → 23:59 | No |
| 3 | Time Zone | time_zone | TEXT | Store time zone | Only `CST` in this dataset | No |
| 4 | Category | category (via dim_product) | TEXT | Product category | `Apparel`, `Footwear`, `Electronics`, `Home Goods`, `Accessories`, `Beauty` | No |
| 5 | Item | item (via dim_product) | TEXT | Product name | 32 distinct items | No |
| 6 | Qty | qty | INTEGER | Units on this line | Positive for Payment rows; negative for Refund rows; never zero | No |
| 7 | Price Point Name | price_point_name | TEXT | Variant label (size, color, variant code) | 25 distinct values (e.g. `Regular`, `S`, `M`, `L`, `XL`, `8oz`, `White`, `34x32`) | No |
| 8 | SKU | sku | TEXT | Stock-keeping unit | 67 distinct values (`SQ-xxxx` format) | No |
| 9 | Unit Price | unit_price | NUMERIC(10,2) | List price per unit before discount | $8.00 → $199.00 | No |
| 10 | Gross Sales | gross_sales | NUMERIC(12,2) | Pre-discount line total = `unit_price × qty` | Positive on Payment, negative on Refund | No |
| 11 | Discounts | discounts | NUMERIC(12,2) | **Negative dollar amount** off gross | ≤ 0; discrete tiers 0, 10, 15, 20, 25,30, 40 % of gross. Rounding produces 11 edge values around 15% and 25% (see D1). | No |
| 12 | Net Sales | net_sales | NUMERIC(12,2) | Post-discount total = `gross_sales + discounts` | Verified 100% consistent (CHK3) | No |
| 13 | Tax | tax | NUMERIC(12,2) | Sales tax on net | 0–10% of net sales | No |
| 14 | Total Collected | total_collected | NUMERIC(12,2) | Customer-paid total = `net_sales + tax` | Positive on Payment, negative on Refund | No |
| 15 | Transaction ID | transaction_id | TEXT | Order identifier; groups line items | 585,691 distinct (`TXN#######` format) | No |
| 16 | Payment Method | payment_method | TEXT | Tender type | `Card`, `Cash`, `Other` | No |
| 17 | Device Name | device_name | TEXT | Register / POS device | 3 distinct values | No |
| 18 | Location | location | TEXT | Store name | 30 distinct values (`Store NN - City`) | No |
| 19 | Customer ID | customer_id | TEXT | Loyalty member identifier | 19,999 distinct. **65.3% NULL of all rows; 65.0% NULL of Payment rows; 100% NULL of Refund rows.** NULL = guest checkout. | **Yes** |
| 20 | Event Type | event_type | TEXT | Row type | `Payment`, `Refund` | No |
| 21 | Unit Cost | unit_cost | NUMERIC(10,2) | Cost of goods per unit | Always > 0; never exceeds unit_price | No |
| 22 | Gross Profit | gross_profit → **contribution_margin** in fact | NUMERIC(12,2) | `net_sales − unit_cost × qty` | Negative on most Refund rows | No |

**Row-type note:** every `Refund` row mirrors an earlier `Payment` row with
negative `qty` and negative money columns. Refunds are retained, not dropped —
they net out at any group grain above the transaction.

---

## B. Companion files

### B1. `02_ground_truth_event_calendar.csv` — 731 rows × 10 cols

| Source column | DB column | Type | Description |
|---|---|---|---|
| Date | date | DATE | Calendar date (primary key of `dim_date`) |
| Weekday | weekday | TEXT | Day name |
| Event | event | TEXT | Named event, or `'None'`-type filler label on ordinary days |
| Season x Month x Event Mult | demand_mult | NUMERIC | Composite demand multiplier for the day |
| DOW Mult | dow_mult | NUMERIC | Day-of-week demand multiplier |
| Month Mult | month_mult | NUMERIC | Month demand multiplier |
| Event Mult | event_mult | NUMERIC | Event-specific demand multiplier |
| Discount Line Prob | discount_line_prob | NUMERIC | Probability a line is discounted on this day (0–1) |
| Refund Txn Prob | refund_txn_prob | NUMERIC | Probability a transaction is refunded on this day (0–1) |
| Store Closed | store_closed | INTEGER | 1 if the store was closed all day, else 0 |

### B2. `03_square_item_sales_summary_by_store_24mo.csv` — 2,010 rows × 13 cols

Vendor-provided summary. **Not used for analysis** — used only as the
reconciliation source in `sql/03_validation_tests.sql` CHK9. Columns:
`Location`, `Category`, `Item`, `SKU`, `Price Point Name`, `Unit Price`,
`Items Sold`, `Gross Sales`, `Discounts`, `Net Sales`, `Tax`, `Gross Profit`,
`Transactions`.

### B3. `04_square_sales_summary_by_store_24mo.csv` — 30 rows × 8 cols

Vendor-provided store-level summary. **Not used for analysis** — used only as
the CHK9 reconciliation source. Columns: `Location`, `Gross Sales`,
`Discounts`, `Net Sales`, `Tax`, `Total Collected`, `Transactions`,
`Items Sold`.

---

## C. Star schema

### C1. `dim_date` — 731 rows

| Column | Type | Description |
|---|---|---|
| date_key | INTEGER PK | YYYYMMDD surrogate key |
| sale_date | DATE UNIQUE | Natural key; foreign-key target of `fact_line_items` |
| year | SMALLINT | 2024 or 2025 |
| quarter | SMALLINT | 1–4 |
| month | SMALLINT | 1–12 |
| month_name | TEXT | e.g. `January` |
| week_of_year | SMALLINT | 1–53 |
| day_of_week | SMALLINT | 0 = Monday, 6 = Sunday |
| day_name | TEXT | e.g. `Monday` |
| is_weekend | BOOLEAN | True on Saturday, Sunday |
| event | TEXT | From event calendar |
| event_mult | NUMERIC(8,4) | From event calendar |
| demand_mult | NUMERIC(8,4) | From event calendar |
| discount_line_prob | NUMERIC(8,4) | From event calendar |
| refund_txn_prob | NUMERIC(8,4) | From event calendar |
| store_closed | BOOLEAN | True on Christmas 2024 & 2025 |

### C2. `dim_product` — 67 rows

| Column | Type | Description |
|---|---|---|
| sku | TEXT PK | From source |
| item | TEXT | Product name; one per SKU |
| category | TEXT | One of 6 categories |

### C3. `dim_store` — 30 rows

| Column | Type | Description |
|---|---|---|
| location | TEXT PK | Store name |

### C4. `fact_line_items` — 970,838 rows

| Column | Type | Source | Description |
|---|---|---|---|
| line_item_id | BIGSERIAL PK | derived | Surrogate key |
| source_row | INTEGER | derived | 1-based row number in source; traceability |
| transaction_id | TEXT | Transaction ID | Order identifier |
| sale_date | DATE FK | Date | Links to `dim_date` |
| sale_time | TIME | Time | Local transaction time |
| sku | TEXT FK | SKU | Links to `dim_product` |
| location | TEXT FK | Location | Links to `dim_store` |
| customer_id | TEXT | Customer ID | NULL = guest checkout (65% of rows) |
| payment_method | TEXT | Payment Method | `Card`, `Cash`, `Other` |
| device_name | TEXT | Device Name | Register identifier |
| event_type | TEXT | Event Type | `Payment` or `Refund` (CHECK constraint) |
| qty | INTEGER | Qty | Positive Payment, negative Refund |
| unit_price | NUMERIC(10,2) | Unit Price | Per-unit list price |
| gross_sales | NUMERIC(12,2) | Gross Sales | Pre-discount line total |
| discounts | NUMERIC(12,2) | Discounts | Negative dollar off |
| net_sales | NUMERIC(12,2) | Net Sales | Post-discount total |
| tax | NUMERIC(12,2) | Tax | Line tax |
| total_collected | NUMERIC(12,2) | Total Collected | Net + tax |
| unit_cost | NUMERIC(10,2) | Unit Cost | Per-unit cost |
| discount_pct | NUMERIC(6,2) | **derived** | See Section D |
| contribution_margin | NUMERIC(12,2) | **derived** | See Section D; equals source `gross_profit` |
| cm_pct | NUMERIC(9,4) | **derived** | See Section D; line-level only |

---

## D. Derived columns

### D1. `discount_pct`

- **Formula:** `round(-discounts / gross_sales × 100, 2)`
- **Why:** the source stores discounts as negative dollars; the business
  reasoner needs a percentage. Line-level percent also enables discount-tier
  grouping.
- **NULL when:** `event_type = 'Refund'`, or `gross_sales ≤ 0`.
- **Range and tiers:** observed range 0.00 → 40.00. **Seven nominal tiers
  exist: `{0, 10, 15, 20, 25, 30, 40}`.** Rounding produces edge values within
  ±0.1 of the 15% and 25% nominal tiers (`14.95, 14.97, 14.98, 14.99, 15.01,
  24.98, 24.99, 25.01, 25.03, 25.05`) because the underlying dollar discount
  is not always an exact multiple of the gross.
- **Bucketing rule (locked):** for any tier-level analysis, derive
  `discount_tier` as the nominal tier within **±0.1** of `discount_pct`. All
  observed values fall within ±0.1 of one nominal tier. Line counts:
  `{0: 649,336, 10: 89,411, 15: 92,594, 20: 98,305, 25: 16,999, 30: 9,008, 40: 5,736}`
  (sum = 961,389, matching all `Payment` rows).
- **Aggregation rule:** `discount_pct` is never averaged at a group grain.
  For group analysis, bucket to `discount_tier` first, then
  `SUM(contribution_margin) / SUM(net_sales)` within each tier.

### D2. `contribution_margin`

- **Formula:** `net_sales − unit_cost × qty` (identical to source `gross_profit`)
- **Why:** "contribution margin" is the business term; "gross profit" is the
  POS export term. Locked assumption #5 states they are equivalent in this
  dataset because there is **no fixed-cost allocation** available.
- **NULL when:** never. Source is 100% complete.
- **Aggregation rule:** `SUM(contribution_margin)` at any group grain.

### D3. `cm_pct` (line-level ratio)

- **Formula:** `round(contribution_margin / net_sales, 4)` when `net_sales ≠ 0`
- **Why:** for inspecting individual rows and labeling scatter plots.
- **NULL when:** `net_sales = 0`.
- **⚠️ Aggregation rule — the project's most important definitional rule:**
  `cm_pct` is **never** averaged at any group grain. The correct group-level
  margin is `SUM(contribution_margin) / SUM(net_sales)`. Averaging per-row
  percentages over-weights small lines and produces a wrong number. This rule
  is repeated in `metrics_definitions.md` and enforced in every SQL query.