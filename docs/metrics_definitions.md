# Metric Definitions — Retail Profitability Diagnostic

All metrics in this project use one of these definitions. Where a metric
appears in a SQL query, notebook, dashboard, or memo, its definition is the
one below. If a later artifact needs a new metric, it is added here first.

## The single most important rule

**Never average a per-row ratio.** The correct group-level margin is
`SUM(contribution_margin) / SUM(net_sales)`, never `AVG(cm_pct)`. Averaging
per-row percentages weights a $5 line the same as a $500 line and produces a
margin number that is arithmetically wrong and misleading in a memo. Every
group-level margin in this project uses the ratio-of-sums rule, without
exception. The `cm_pct` column exists only for line-level inspection.

## Core metrics

| Metric | Definition | Notes |
|---|---|---|
| **Net Sales** | `gross_sales + discounts` (discounts are negative) | Verified 100% consistent with source (CHK3) |
| **Discount %** | `-discounts / gross_sales × 100`, computed per line where `gross_sales > 0` AND `event_type = 'Payment'` | NULL on refund rows and on zero-value lines |
| **Discount Tier** | The nominal tier in `{0, 10, 15, 20, 25, 30, 40}` within ±0.1 of `Discount %`. **Seven tiers exist**, not six — `30%` was missed in the initial scan and recovered by distinct-value verification. 11 floating-point edge values (`14.95`, `24.99`, etc.) are folded into the nearest tier. | Line counts by tier are documented in `data_dictionary.md` §D1 |
| **Contribution Margin** | `net_sales − unit_cost × qty` | **Identical to `gross_profit`** in this dataset — no fixed-cost allocation exists |
| **Contribution Margin %** | `SUM(contribution_margin) / SUM(net_sales)` at the group grain | Never `AVG(cm_pct)`; see rule above |
| **Revenue** | Synonym for `net_sales` when shown to the owner; `gross_sales` when discussing pre-discount top line | State which at every mention |

## Row-type metrics

| Metric | Definition |
|---|---|
| **Payment row** | `event_type = 'Payment'`. Positive Qty, positive Net Sales. |
| **Refund row** | `event_type = 'Refund'`. Negative Qty, negative Net Sales, negative Contribution Margin. **Never dropped** — they net out at SKU/category grain. |
| **Refund Rate** | `SUM(ABS(net_sales)) over Refund rows / SUM(net_sales) over Payment rows`, per group |

## Customer-segment metrics

| Metric | Definition | Limitation |
|---|---|---|
| **Identified customer** | A payment row where `customer_id IS NOT NULL` | 65% of payment rows are guest checkouts — this metric describes the loyalty segment only, never the total customer base |
| **Repeat customer** | An identified customer with ≥ 2 distinct `transaction_id` values | Scoped to loyalty segment; 100% repeat rate among identified customers is expected (loyalty members are enrolled by definition) |
| **Repeat-customer CM share** | `SUM(contribution_margin) for repeat customers / SUM(contribution_margin) for all identified customers` | Same limitation |

## Event-context metrics

| Metric | Definition | Source |
|---|---|---|
| **Event-driven discount** | A discount line on a date where `discount_line_prob` in the event calendar is above its 75th percentile | `stg_event_calendar` |
| **Organic discount** | A discount line on a date where `discount_line_prob` is below the 25th percentile | `stg_event_calendar` |
| **Refund-risk day** | A date where `refund_txn_prob` is above its 75th percentile | `stg_event_calendar` |

These three metrics exist so the memo can distinguish *discounting we chose* from *discounting the calendar forced on us*. Never tell an owner to discount less on Black Friday. Do tell them not to discount on the January returns tail.

## Non-metrics (explicitly not computed)

- **Customer Lifetime Value** — cannot be computed; customer ID is 65% NULL and observation window is 24 months.
- **Delivery delay** — no delivery field exists in this dataset. Any reference to "delayed delivery" in a template must be replaced with "refund rate" or removed entirely.
- **Return-adjusted margin** — refunds are reflected in the line items; there is no separate returns cost to allocate.