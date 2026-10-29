-- Phase 1A schema: staging + star
SET client_min_messages TO WARNING;
DROP SCHEMA IF EXISTS retail CASCADE;
CREATE SCHEMA retail;
SET search_path TO retail, public;

-- ============ STAGING (mirrors source, snake_case) ============
CREATE TABLE stg_line_items (
    date              DATE,
    time              TIME,
    time_zone         TEXT,
    category          TEXT,
    item              TEXT,
    qty               INTEGER,
    price_point_name  TEXT,
    sku               TEXT,
    unit_price        NUMERIC(10,2),
    gross_sales       NUMERIC(12,2),
    discounts         NUMERIC(12,2),
    net_sales         NUMERIC(12,2),
    tax               NUMERIC(12,2),
    total_collected   NUMERIC(12,2),
    transaction_id    TEXT,
    payment_method    TEXT,
    device_name       TEXT,
    location          TEXT,
    customer_id       TEXT,
    event_type        TEXT,
    unit_cost         NUMERIC(10,2),
    gross_profit      NUMERIC(12,2)
);

CREATE TABLE stg_event_calendar (
    date                DATE PRIMARY KEY,
    weekday             TEXT,
    event               TEXT,
    demand_mult         NUMERIC(8,4),
    dow_mult            NUMERIC(8,4),
    month_mult          NUMERIC(8,4),
    event_mult          NUMERIC(8,4),
    discount_line_prob  NUMERIC(8,4),
    refund_txn_prob     NUMERIC(8,4),
    store_closed        INTEGER
);

CREATE TABLE stg_store_summary (
    location          TEXT PRIMARY KEY,
    gross_sales       NUMERIC(14,2),
    discounts         NUMERIC(14,2),
    net_sales         NUMERIC(14,2),
    tax               NUMERIC(14,2),
    total_collected   NUMERIC(14,2),
    transactions      INTEGER,
    items_sold        INTEGER
);

CREATE TABLE stg_item_summary (
    location          TEXT,
    category          TEXT,
    item              TEXT,
    sku               TEXT,
    price_point_name  TEXT,
    unit_price        NUMERIC(10,2),
    items_sold        INTEGER,
    gross_sales       NUMERIC(14,2),
    discounts         NUMERIC(14,2),
    net_sales         NUMERIC(14,2),
    tax               NUMERIC(14,2),
    gross_profit      NUMERIC(14,2),
    transactions      INTEGER
);

-- ============ STAR SCHEMA ============
CREATE TABLE dim_date (
    date_key            INTEGER PRIMARY KEY,       -- YYYYMMDD
    sale_date           DATE NOT NULL UNIQUE,
    year                SMALLINT NOT NULL,
    quarter             SMALLINT NOT NULL,
    month               SMALLINT NOT NULL,
    month_name          TEXT NOT NULL,
    week_of_year        SMALLINT NOT NULL,
    day_of_week         SMALLINT NOT NULL,          -- 0 = Monday
    day_name            TEXT NOT NULL,
    is_weekend          BOOLEAN NOT NULL,
    event               TEXT,
    event_mult          NUMERIC(8,4),
    demand_mult         NUMERIC(8,4),
    discount_line_prob  NUMERIC(8,4),
    refund_txn_prob     NUMERIC(8,4),
    store_closed        BOOLEAN NOT NULL
);

CREATE TABLE dim_product (
    sku         TEXT PRIMARY KEY,
    item        TEXT NOT NULL,
    category    TEXT NOT NULL
);

CREATE TABLE dim_store (
    location    TEXT PRIMARY KEY
);

CREATE TABLE fact_line_items (
    line_item_id         BIGSERIAL PRIMARY KEY,
    source_row           INTEGER NOT NULL,          -- traceability to staging row
    transaction_id       TEXT NOT NULL,
    sale_date            DATE NOT NULL REFERENCES dim_date(sale_date),
    sale_time            TIME NOT NULL,
    sku                  TEXT NOT NULL REFERENCES dim_product(sku),
    location             TEXT NOT NULL REFERENCES dim_store(location),
    customer_id          TEXT,                      -- NULL = guest checkout
    payment_method       TEXT NOT NULL,
    device_name          TEXT NOT NULL,
    event_type           TEXT NOT NULL CHECK (event_type IN ('Payment','Refund')),
    qty                  INTEGER NOT NULL,
    unit_price           NUMERIC(10,2) NOT NULL,
    gross_sales          NUMERIC(12,2) NOT NULL,
    discounts            NUMERIC(12,2) NOT NULL,
    net_sales            NUMERIC(12,2) NOT NULL,
    tax                  NUMERIC(12,2) NOT NULL,
    total_collected      NUMERIC(12,2) NOT NULL,
    unit_cost            NUMERIC(10,2) NOT NULL,
    -- derived
    discount_pct         NUMERIC(6,2),              -- NULL on refunds and $0 lines
    contribution_margin  NUMERIC(12,2) NOT NULL,    -- == gross_profit (no fixed costs in source)
    cm_pct               NUMERIC(9,4)               -- per-line ratio; never AVG this
);

CREATE INDEX ix_fact_sku        ON fact_line_items (sku);
CREATE INDEX ix_fact_date       ON fact_line_items (sale_date);
CREATE INDEX ix_fact_location   ON fact_line_items (location);
CREATE INDEX ix_fact_event_type ON fact_line_items (event_type);
CREATE INDEX ix_fact_txn        ON fact_line_items (transaction_id);
CREATE INDEX ix_fact_discount   ON fact_line_items (discount_pct);