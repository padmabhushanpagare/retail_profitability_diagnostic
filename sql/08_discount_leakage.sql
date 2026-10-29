-- =============================================================================
-- Query 08: Discount Leakage (Opportunity Cost)
-- Business question: How much total contribution margin is lost by selling
-- at a discount compared to selling at the category's full-price baseline?
--
-- GRAIN: Category, Discount Tier
-- METRICS:
--   - Actual CM       = SUM(contribution_margin)
--   - Baseline CM %   = CM % at 0% discount for that category
--   - Hypothetical CM = Net Revenue * Baseline CM %
--   - Leakage         = Hypothetical CM - Actual CM
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
),
category_baselines AS (
    -- Get the 0% margin for each category to use as the benchmark
    SELECT
        category,
        SUM(contribution_margin) / NULLIF(SUM(net_sales), 0) AS baseline_cm_pct
    FROM tiered_payments
    WHERE discount_tier = 0
    GROUP BY category
),
leakage_calc AS (
    SELECT
        t.category,
        t.discount_tier,
        COUNT(*) AS lines,
        SUM(t.net_sales) AS net_revenue,
        SUM(t.contribution_margin) AS actual_cm,
        b.baseline_cm_pct,
        SUM(t.net_sales) * b.baseline_cm_pct AS hypothetical_cm,
        (SUM(t.net_sales) * b.baseline_cm_pct) - SUM(t.contribution_margin) AS leakage
    FROM tiered_payments t
    JOIN category_baselines b USING (category)
    WHERE t.discount_tier IS NOT NULL AND t.discount_tier > 0 -- Look only at discounts
    GROUP BY t.category, t.discount_tier, b.baseline_cm_pct
)
SELECT
    category,
    discount_tier,
    lines,
    ROUND(net_revenue / 1e3, 1) AS net_rev_k,       -- in thousands
    ROUND(actual_cm / 1e3, 1) AS actual_cm_k,
    ROUND(hypothetical_cm / 1e3, 1) AS hypot_cm_k,
    ROUND(leakage / 1e3, 1) AS leakage_k,           -- in thousands
    ROUND((baseline_cm_pct * 100)::numeric, 1) AS baseline_cm_pct
FROM leakage_calc
ORDER BY leakage_k DESC;