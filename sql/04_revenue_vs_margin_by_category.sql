-- =============================================================================
-- Query 10: Revenue vs. Margin by Category
-- Business question: Which categories generate the most revenue, and which
-- generate the most contribution margin? Where is the gap?
--
-- GRAIN: Category
-- METRICS:
--   - Gross Revenue   = SUM(gross_sales) / 1_000_000  (shown in $ millions)
--   - Net Revenue     = SUM(net_sales) / 1_000_000
--   - COGS            = SUM(unit_cost * qty) / 1_000_000
--   - Refund Cost     = SUM(refund contribution_margin) / 1_000_000
--   - Contribution Margin = SUM(contribution_margin) / 1_000_000
--   - CM %            = SUM(contribution_margin) / SUM(net_sales)  [ratio of sums]
-- =============================================================================

SET search_path TO retail, public;

WITH category_agg AS (
    SELECT
        p.category,
        SUM(f.gross_sales)                          AS gross_revenue,
        SUM(f.net_sales)                            AS net_revenue,
        SUM(f.unit_cost * f.qty)                    AS cogs,
        SUM(CASE WHEN f.event_type = 'Refund'
                 THEN f.contribution_margin ELSE 0 END) AS refund_impact,
        SUM(f.contribution_margin)                  AS contribution_margin
    FROM fact_line_items f
    JOIN dim_product p USING (sku)
    GROUP BY p.category
)
SELECT
    category,
    ROUND(gross_revenue / 1e6, 2)      AS gross_rev_m,
    ROUND(net_revenue / 1e6, 2)        AS net_rev_m,
    ROUND(cogs / 1e6, 2)               AS cogs_m,
    ROUND(refund_impact / 1e6, 2)      AS refund_cost_m,
    ROUND(contribution_margin / 1e6, 2) AS cm_m,
    ROUND(
        (contribution_margin / NULLIF(net_revenue, 0) * 100)::numeric,
        2
    ) AS cm_pct
FROM category_agg
ORDER BY cm_m DESC;  -- sorted by absolute margin dollars, not revenue