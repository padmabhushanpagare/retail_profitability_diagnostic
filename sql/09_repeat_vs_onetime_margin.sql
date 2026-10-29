-- =============================================================================
-- Query 09: Repeat vs One-Time Customer Margin (Loyalty Segment Only)
-- Business question: Within our identified customer base, do repeat customers
-- generate better margin than one-time buyers?
--
-- SCOPING NOTE: This query is restricted to rows where customer_id IS NOT NULL
-- (34.7% of Payment rows). It does NOT describe the full customer base.
-- =============================================================================

SET search_path TO retail, public;

WITH customer_orders AS (
    -- Identify transaction counts per customer (Payment rows only)
    SELECT
        customer_id,
        COUNT(DISTINCT transaction_id) AS order_count
    FROM fact_line_items
    WHERE customer_id IS NOT NULL
      AND event_type = 'Payment'
    GROUP BY customer_id
),
customer_segments AS (
    -- Assign segment label
    SELECT
        customer_id,
        CASE 
            WHEN order_count = 1 THEN 'One-time'
            ELSE 'Repeat'
        END AS segment
    FROM customer_orders
),
segment_metrics AS (
    -- Aggregate financials by segment
    SELECT
        cs.segment,
        COUNT(DISTINCT f.customer_id)           AS customers,
        SUM(f.net_sales)                        AS net_revenue,
        SUM(f.contribution_margin)              AS contribution_margin
    FROM fact_line_items f
    JOIN customer_segments cs USING (customer_id)
    WHERE f.event_type = 'Payment'
    GROUP BY cs.segment
)
SELECT
    segment,
    customers,
    ROUND(100.0 * customers / SUM(customers) OVER (), 1) AS pct_of_customers,
    ROUND(net_revenue / 1e6, 2)                         AS net_rev_m,
    ROUND(100.0 * net_revenue / SUM(net_revenue) OVER (), 1) AS pct_of_revenue,
    ROUND(contribution_margin / 1e6, 2)                 AS cm_m,
    ROUND(100.0 * contribution_margin / SUM(contribution_margin) OVER (), 1) AS pct_of_cm,
    ROUND(
        (contribution_margin / NULLIF(net_revenue, 0) * 100)::numeric,
        2
    ) AS cm_pct,
    ROUND(contribution_margin / customers, 0)           AS avg_cm_per_customer
FROM segment_metrics
ORDER BY cm_m DESC;