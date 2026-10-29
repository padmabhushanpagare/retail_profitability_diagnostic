SET search_path TO retail, public;
TRUNCATE fact_line_items, dim_date, dim_product, dim_store RESTART IDENTITY CASCADE;

-- ---------- dim_date (from event calendar) ----------
INSERT INTO dim_date
SELECT
    TO_CHAR(date,'YYYYMMDD')::INT,
    date,
    EXTRACT(YEAR FROM date)::SMALLINT,
    EXTRACT(QUARTER FROM date)::SMALLINT,
    EXTRACT(MONTH FROM date)::SMALLINT,
    TO_CHAR(date,'FMMonth'),
    EXTRACT(WEEK FROM date)::SMALLINT,
    (EXTRACT(ISODOW FROM date) - 1)::SMALLINT,
    TO_CHAR(date,'FMDay'),
    EXTRACT(ISODOW FROM date) IN (6,7),
    event, event_mult, demand_mult, discount_line_prob, refund_txn_prob,
    (store_closed = 1)
FROM stg_event_calendar;

-- ---------- dim_store ----------
INSERT INTO dim_store SELECT DISTINCT location FROM stg_line_items;

-- ---------- dim_product (SKU grain) ----------
INSERT INTO dim_product (sku, item, category)
SELECT sku, MIN(item), MIN(category)
FROM stg_line_items
GROUP BY sku;

-- ---------- fact ----------
INSERT INTO fact_line_items (
    source_row, transaction_id, sale_date, sale_time, sku, location,
    customer_id, payment_method, device_name, event_type, qty, unit_price,
    gross_sales, discounts, net_sales, tax, total_collected, unit_cost,
    discount_pct, contribution_margin, cm_pct
)
SELECT
    ROW_NUMBER() OVER (),
    transaction_id,
    date,
    time,
    sku,
    location,
    NULLIF(TRIM(customer_id), ''),
    payment_method,
    device_name,
    event_type,
    qty,
    unit_price,
    gross_sales,
    discounts,
    net_sales,
    tax,
    total_collected,
    unit_cost,
    CASE
        WHEN event_type = 'Payment' AND gross_sales > 0
        THEN ROUND((-discounts / gross_sales * 100)::numeric, 2)
    END,
    gross_profit,
    CASE
        WHEN net_sales <> 0
        THEN ROUND((gross_profit / net_sales)::numeric, 4)
    END
FROM stg_line_items;

ANALYZE fact_line_items;