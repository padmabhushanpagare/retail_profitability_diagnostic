-- =============================================================================
-- Query 06: Top Loss-Making SKUs
-- Business question: Which specific products generate revenue but destroy
-- or barely contribute to margin?
--
-- GRAIN: SKU / Product
-- FILTER: At least 500 units sold total to filter out noise.
-- METRICS:
--   - Units Sold          = SUM(qty)
--   - Net Revenue         = SUM(net_sales)
--   - Contribution Margin = SUM(contribution_margin)
--   - CM %                = SUM(contribution_margin) / SUM(net_sales)
--   - Avg Discount %      = SUM(-discounts) / SUM(gross_sales)
-- =============================================================================

SET search_path TO retail, public;

WITH sku_agg AS (
    SELECT
        f.sku,
        p.item,
        p.category,
        SUM(f.qty)                                  AS units_sold,
        SUM(f.net_sales)                            AS net_revenue,
        SUM(f.contribution_margin)                  AS contribution_margin,
        SUM(f.gross_sales)                          AS gross_sales,
        SUM(-f.discounts)                           AS total_discounts
    FROM fact_line_items f
    JOIN dim_product p USING (sku)
    WHERE f.event_type = 'Payment'
    GROUP BY f.sku, p.item, p.category
    HAVING SUM(f.qty) >= 500
)
SELECT
    sku,
    item,
    category,
    units_sold,
    ROUND(net_revenue, 0)                         AS net_rev,
    ROUND(contribution_margin, 0)                 AS cm,
    ROUND(
        (contribution_margin / NULLIF(net_revenue, 0) * 100)::numeric, 
        2
    ) AS cm_pct,
    ROUND(
        (total_discounts / NULLIF(gross_sales, 0) * 100)::numeric, 
        2
    ) AS avg_discount_pct
FROM sku_agg
ORDER BY cm_pct ASC, net_revenue DESC  -- Worst margin first, then highest revenue
LIMIT 15;