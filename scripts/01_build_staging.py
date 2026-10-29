"""
Phase 1A — build staging CSVs with snake_case headers.
Derivation happens later, in sql/02_transform_to_star.sql.

Run:  python scripts/01_build_staging.py
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

SALES_RENAME = {
    "Date": "date", "Time": "time", "Time Zone": "time_zone",
    "Category": "category", "Item": "item", "Qty": "qty",
    "Price Point Name": "price_point_name", "SKU": "sku",
    "Unit Price": "unit_price", "Gross Sales": "gross_sales",
    "Discounts": "discounts", "Net Sales": "net_sales", "Tax": "tax",
    "Total Collected": "total_collected", "Transaction ID": "transaction_id",
    "Payment Method": "payment_method", "Device Name": "device_name",
    "Location": "location", "Customer ID": "customer_id",
    "Event Type": "event_type", "Unit Cost": "unit_cost",
    "Gross Profit": "gross_profit",
}

CAL_RENAME = {
    "Date": "date", "Weekday": "weekday", "Event": "event",
    "Season x Month x Event Mult": "demand_mult", "DOW Mult": "dow_mult",
    "Month Mult": "month_mult", "Event Mult": "event_mult",
    "Discount Line Prob": "discount_line_prob",
    "Refund Txn Prob": "refund_txn_prob", "Store Closed": "store_closed",
}

STORE_SUM_RENAME = {
    "Location": "location", "Gross Sales": "gross_sales",
    "Discounts": "discounts", "Net Sales": "net_sales", "Tax": "tax",
    "Total Collected": "total_collected", "Transactions": "transactions",
    "Items Sold": "items_sold",
}

ITEM_SUM_RENAME = {
    "Location": "location", "Category": "category", "Item": "item",
    "SKU": "sku", "Price Point Name": "price_point_name",
    "Unit Price": "unit_price", "Items Sold": "items_sold",
    "Gross Sales": "gross_sales", "Discounts": "discounts",
    "Net Sales": "net_sales", "Tax": "tax", "Gross Profit": "gross_profit",
    "Transactions": "transactions",
}

def build(src, dst, rename, expect_rows=None):
    print(f"  {src.name} -> {dst.name}")
    df = pd.read_csv(src, low_memory=False)
    missing = set(rename) - set(df.columns)
    if missing:
        raise SystemExit(f"FATAL: {src.name} missing expected columns: {missing}")
    df = df.rename(columns=rename)
    if expect_rows is not None and len(df) != expect_rows:
        raise SystemExit(f"FATAL: {src.name} expected {expect_rows} rows, got {len(df)}")
    df.to_csv(dst, index=False, na_rep="")
    print(f"    {len(df):,} rows x {len(df.columns)} cols")
    return df

if __name__ == "__main__":
    print("Building staging CSVs")
    build(RAW / "01_square_item_sales_detail_24mo.csv.gz",
          OUT / "stg_line_items.csv", SALES_RENAME, expect_rows=970_838)
    build(RAW / "02_ground_truth_event_calendar.csv",
          OUT / "stg_event_calendar.csv", CAL_RENAME, expect_rows=731)
    build(RAW / "03_square_item_sales_summary_by_store_24mo.csv",
          OUT / "stg_item_summary.csv", ITEM_SUM_RENAME, expect_rows=2_010)
    build(RAW / "04_square_sales_summary_by_store_24mo.csv",
          OUT / "stg_store_summary.csv", STORE_SUM_RENAME, expect_rows=30)
    print("\nDone. Files in data/processed/")