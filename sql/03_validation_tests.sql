SET search_path TO retail, public;

DO $$
DECLARE
    n BIGINT;
    bad BIGINT;
    stores_bad BIGINT;
BEGIN
    -- 1. row counts
    SELECT COUNT(*) INTO n FROM stg_line_items;
    IF n <> 970838 THEN RAISE EXCEPTION 'CHK1 stg row count = % (expected 970838)', n; END IF;
    RAISE NOTICE 'CHK1  stg_line_items rows = %', n;

    SELECT COUNT(*) INTO n FROM fact_line_items;
    IF n <> 970838 THEN RAISE EXCEPTION 'CHK2 fact row count = % (expected 970838)', n; END IF;
    RAISE NOTICE 'CHK2  fact_line_items rows = %', n;

    -- 2. net = gross + discounts
    SELECT COUNT(*) INTO bad FROM fact_line_items
     WHERE ABS(net_sales - (gross_sales + discounts)) > 0.011;
    IF bad > 0 THEN RAISE EXCEPTION 'CHK3 net != gross + discounts on % rows', bad; END IF;
    RAISE NOTICE 'CHK3  net_sales = gross_sales + discounts  OK (0 violations)';

    -- 3. contribution_margin = net_sales - unit_cost * qty
    --    (equivalently gross_profit in the source; fact column is named contribution_margin)
    SELECT COUNT(*) INTO bad FROM fact_line_items
     WHERE ABS(contribution_margin - (net_sales - unit_cost * qty)) > 0.011;
    IF bad > 0 THEN RAISE EXCEPTION 'CHK4 contribution_margin mismatch on % rows', bad; END IF;
    RAISE NOTICE 'CHK4  contribution_margin = net_sales - unit_cost*qty  OK (0 violations)';

    -- 4. discount_pct within [0, 40]
    SELECT COUNT(*) INTO bad FROM fact_line_items
     WHERE discount_pct IS NOT NULL AND (discount_pct < 0 OR discount_pct > 40.01);
    IF bad > 0 THEN RAISE EXCEPTION 'CHK5 discount_pct out of range on % rows', bad; END IF;
    RAISE NOTICE 'CHK5  discount_pct in [0,40]  OK (0 violations)';

    -- 5. no NULLs in money columns
    SELECT COUNT(*) INTO bad FROM fact_line_items
     WHERE unit_cost IS NULL OR net_sales IS NULL OR contribution_margin IS NULL;
    IF bad > 0 THEN RAISE EXCEPTION 'CHK6 NULL money values on % rows', bad; END IF;
    RAISE NOTICE 'CHK6  no NULLs in money columns  OK';

    -- 6. sign rules
    SELECT COUNT(*) INTO bad FROM fact_line_items
     WHERE (event_type = 'Refund'  AND qty >= 0)
        OR (event_type = 'Payment' AND qty <= 0);
    IF bad > 0 THEN RAISE EXCEPTION 'CHK7 qty sign wrong on % rows', bad; END IF;
    RAISE NOTICE 'CHK7  Refund qty<0, Payment qty>0  OK';

    -- 7. referential integrity to dim_date
    SELECT COUNT(*) INTO bad
      FROM fact_line_items f LEFT JOIN dim_date d USING (sale_date)
     WHERE d.sale_date IS NULL;
    IF bad > 0 THEN RAISE EXCEPTION 'CHK8 % fact rows have no dim_date match', bad; END IF;
    RAISE NOTICE 'CHK8  every fact date present in dim_date  OK';

    -- 9. RECONCILIATION vs vendor store summary
    SELECT COUNT(*) INTO stores_bad
      FROM (
        SELECT f.location,
               SUM(f.gross_sales) AS mine,
               s.gross_sales      AS theirs
          FROM fact_line_items f
          JOIN stg_store_summary s USING (location)
         GROUP BY f.location, s.gross_sales
      ) x
     WHERE ABS(mine - theirs) > 0.05;
    IF stores_bad > 0 THEN
        RAISE EXCEPTION 'CHK9 reconciliation failed for % stores', stores_bad;
    END IF;
    RAISE NOTICE 'CHK9  gross_sales reconciles to vendor summary for all 30 stores  OK';

    RAISE NOTICE '============================================';
    RAISE NOTICE 'ALL CHECKS PASSED';
    RAISE NOTICE '============================================';
END $$;

-- Reconciliation detail (visible output)
SELECT
    f.location,
    ROUND(SUM(f.gross_sales), 2) AS my_gross_sales,
    s.gross_sales                AS vendor_gross_sales,
    ROUND(SUM(f.gross_sales) - s.gross_sales, 2) AS delta
FROM fact_line_items f
JOIN stg_store_summary s USING (location)
GROUP BY f.location, s.gross_sales
ORDER BY f.location;