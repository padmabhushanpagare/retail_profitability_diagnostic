-- =============================================================================
-- Query 07: Category x Discount Matrix
-- Business question: Which specific combinations of Category and Discount
-- Tier destroy margin?
--
-- GRAIN: Category, Discount Tier
-- METRICS:
--   - Lines            = COUNT(*)
--   - Net Revenue      = SUM(net_sales) / 1_000_000
--   - Contribution Margin = SUM(contribution_margin) / 1_000_000
--   - CM %             = SUM(contribution_margin) / SUM(net_sales)
-- =============================================================================

SET search_path TO retail, public;

WITH tiered_payments AS (
    SELECT
        p.category,
        CASE
            WHEN f.discount_pct BETWEEN -0.1 AND  0.1 THEN 0
            WHEN f.discount_pct BETWEEN  9.9 AND 10.1 THEN 10
            WHEN f.discount_pct BETWEEN 14.9 AND 15.1 THEN 15
            WHEN f.discount_pct BETWEEN 19.9 AND 20.1 THEN 20
            WHEN f.discount_pct BETWEEN 24.9 AND 25.1 THEN 25
            WHEN f.discount_pct BETWEEN 29.9 AND 30.1 THEN 30
            WHEN f.discount_pct BETWEEN 39.9 AND 40.1 THEN 40
            ELSE NULL
        END AS discount_tier,
        f.net_sales,
        f.contribution_margin
    FROM fact_line_items f
    JOIN dim_product p USING (sku)
    WHERE f.event_type = 'Payment'
)
SELECT
    category,
    discount_tier,
    COUNT(*)                                  AS lines,
    ROUND(SUM(net_sales) / 1e6, 2)            AS net_rev_m,
    ROUND(SUM(contribution_margin) / 1e6, 2)  AS cm_m,
    ROUND(
        (SUM(contribution_margin) / NULLIF(SUM(net_sales), 0) * 100)::numeric,
        2
    ) AS cm_pct
FROM tiered_payments
WHERE discount_tier IS NOT NULL
GROUP BY category, discount_tier
ORDER BY category, discount_tier;