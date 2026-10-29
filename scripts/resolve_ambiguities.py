"""
Phase 0 — resolve the three ambiguities from verification.
Run:  python resolve_ambiguities.py
"""
import pandas as pd
import numpy as np

DATA = r"D:\retail_demand_and_profitabilty_diagnostic\_extracted\A Synthetic Multi-Store Retail Point-of-Sale Trans"
df  = pd.read_csv(rf"{DATA}\01_square_item_sales_detail_24mo.csv.gz", low_memory=False)
cal = pd.read_csv(rf"{DATA}\02_ground_truth_event_calendar.csv",   low_memory=False)

def sec(n, t):
    print("\n" + "="*72); print(f"{n}. {t}"); print("="*72)

sec(1, "EVENT TYPE VALUES")
print(df["Event Type"].value_counts(dropna=False).to_string())

sec(2, "EVENT TYPE x QTY SIGN")
df["qty_sign"] = np.sign(df["Qty"]).map({-1:"Negative", 0:"Zero", 1:"Positive"})
print(pd.crosstab(df["Event Type"], df["qty_sign"]).to_string())

sec(3, "SAMPLE NON-PAYMENT ROWS (refund candidates)")
non_pay = df[df["Event Type"] != "Payment"]
if len(non_pay):
    print(non_pay[["Date","Qty","Unit Price","Gross Sales","Discounts",
                   "Net Sales","Unit Cost","Gross Profit","Event Type"]]
          .head(5).to_string())
else:
    print("No non-Payment rows — refunds must be signaled another way.")

sec(4, "CORRECTED DISCOUNT FORMULA CHECK  (net = gross + discount)")
diff = (df["Net Sales"] - (df["Gross Sales"] + df["Discounts"])).abs()
print(f"Match (|diff|<=$0.01): {(diff <= 0.01).mean()*100:.2f}%   "
      f"median err: ${diff.median():.4f}")

sec(5, "DERIVED DISCOUNT % (payments only)")
pay = df[df["Event Type"] == "Payment"].copy()
pay["discount_pct"] = np.where(pay["Gross Sales"] > 0,
                               -pay["Discounts"] / pay["Gross Sales"] * 100, np.nan)
print(pay["discount_pct"].describe().round(2).to_string())
bins   = [-np.inf, 0, 5, 10, 15, 20, 30, 50, np.inf]
labels = ["0%","1-5%","6-10%","11-15%","16-20%","21-30%","31-50%",">50%"]
print("\nDiscount-band distribution (payment rows):")
print(pd.cut(pay["discount_pct"], bins=bins, labels=labels)
        .value_counts().sort_index().to_string())

sec(6, "DUPLICATE (Transaction ID, Item) BREAKDOWN")
dup_mask = df.duplicated(subset=["Transaction ID","Item"], keep=False)
dups = df[dup_mask]
print(f"Duplicate-key rows: {len(dups):,}")
if len(dups):
    print(f"  By Event Type : {dups['Event Type'].value_counts().to_dict()}")
    print(f"  By Qty sign   : {dups['qty_sign'].value_counts().to_dict()}")
    print("\n  Sample:")
    print(dups[["Transaction ID","Item","Event Type","Qty","Unit Price","Net Sales"]]
          .head(10).to_string())

sec(7, "MISSING DAYS vs STORE CLOSED FLAG")
df["date_only"]  = pd.to_datetime(df["Date"]).dt.date
cal["date_only"] = pd.to_datetime(cal["Date"]).dt.date
missing = sorted(set(cal["date_only"]) - set(df["date_only"]))
print(f"Missing days: {len(missing)}")
for d in missing:
    row = cal[cal["date_only"] == d].iloc[0]
    print(f"  {d} | {row['Event']:<30s} | Store Closed = {row['Store Closed']}")
print(f"\nTotal days flagged Store Closed: {int(cal['Store Closed'].sum())}")
print(f"Closed days that DO have transactions: "
      f"{len(set(cal[cal['Store Closed']==1]['date_only']) & set(df['date_only']))}")

sec(8, "PRICE POINT NAME (variant codes)")
print(df["Price Point Name"].value_counts().to_string())

sec(9, "CUSTOMER ID NULLS BY EVENT TYPE")
print(df.groupby("Event Type")["Customer ID"]
        .apply(lambda x: f"{x.isna().mean()*100:.1f}% null")
        .to_string())