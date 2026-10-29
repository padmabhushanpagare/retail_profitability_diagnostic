"""
Phase 0/1 Data Verification
Target: Mendeley synthetic multi-store POS dataset (and any similar retail dataset)

RUN:
    python verify_dataset.py
    (or)  python verify_dataset.py "D:\\path\\to\\dataset.zip"
    (or)  python verify_dataset.py "D:\\path\\to\\folder\\"
    (or)  python verify_dataset.py "D:\\path\\to\\file.csv"

OUTPUT:
    Console report + verification_report.md saved next to input

Requires: pandas, numpy  (pip install pandas numpy)
"""

import sys
import zipfile
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

# ---------------------------------------------------------------- CONFIG
DEFAULT_PATH = r"D:\retail_demand_and_profitabilty_diagnostic"

CRITICAL_COLUMNS = {
    "order_id":       ["order_id", "transaction_id", "sale_id", "receipt_id", "invoice_id", "orderid"],
    "line_id":        ["line_id", "line_item_id", "lineitemid", "row_id"],
    "date":           ["date", "transaction_date", "sale_date", "order_date", "timestamp", "datetime"],
    "product_id":     ["product_id", "sku", "item_id", "productid", "itemid"],
    "quantity":       ["quantity", "qty", "units"],
    "unit_price":     ["unit_price", "price", "item_price", "saleprice"],
    "discount":       ["discount", "discount_pct", "discount_percent", "discount_pct_of_price"],
    "unit_cost":      ["unit_cost", "cost", "item_cost", "cogs", "cost_of_goods"],
    "gross_profit":   ["gross_profit", "profit", "gross_margin"],
    "refund":         ["refund", "refund_flag", "is_refund", "return_flag", "refund_amount"],
    "customer_id":    ["customer_id", "customer", "customerid", "loyalty_id"],
    "store_id":       ["store_id", "store", "location", "storeid"],
    "category":       ["category", "product_category", "department"],
    "payment_method": ["payment_method", "payment_type"],
}

OUTPUT_LINES = []

# ---------------------------------------------------------------- HELPERS
def norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

def find_col(df, candidates):
    """Return actual column name, or None. Exact match after normalization."""
    mapping = {c: norm(c) for c in df.columns}
    for cand in candidates:
        cn = norm(cand)
        for actual, an in mapping.items():
            if an == cn:
                return actual
    # substring fallback only if unambiguous
    hits = []
    for cand in candidates:
        cn = norm(cand)
        for actual, an in mapping.items():
            if cn in an or an in cn:
                hits.append(actual)
    hits = list(set(hits))
    return hits[0] if len(hits) == 1 else None

def echo(text=""):
    print(text)
    OUTPUT_LINES.append(text)

def header(title):
    echo()
    echo("=" * 72)
    echo(title)
    echo("=" * 72)

def discover_files(target):
    """Return (workdir, list_of_files). Extracts zips if needed."""
    target = Path(target)
    if not target.exists():
        raise FileNotFoundError(target)

    if target.is_file():
        if target.suffix.lower() == ".zip":
            workdir = target.parent / f"{target.stem}_extracted"
            workdir.mkdir(exist_ok=True)
            print(f"Extracting {target.name} -> {workdir}")
            with zipfile.ZipFile(target) as zf:
                zf.extractall(workdir)
            files = [p for p in workdir.rglob("*") if p.is_file()]
            return workdir, files
        return target.parent, [target]

    if target.is_dir():
        zips = list(target.glob("*.zip"))
        other_files = [p for p in target.iterdir()
                       if p.is_file() and p.suffix.lower() != ".zip"]
        if zips:
            workdir = target / "_extracted"
            workdir.mkdir(exist_ok=True)
            for z in zips:
                print(f"Extracting {z.name} -> {workdir}")
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(workdir)
            files = [p for p in workdir.rglob("*") if p.is_file()] + other_files
            return workdir, files
        return target, other_files

    raise ValueError("Unsupported target")

# ---------------------------------------------------------------- MAIN
def main(target):
    OUTPUT_LINES.clear()
    OUTPUT_LINES.append(f"# Data Verification Report")
    OUTPUT_LINES.append(f"**Generated:** {datetime.now():%Y-%m-%d %H:%M:%S}")
    OUTPUT_LINES.append(f"**Target:** `{target}`")

    # ---- 1. FILE DISCOVERY
    header("1. FILE DISCOVERY")
    workdir, files = discover_files(target)

    echo(f"\nFiles found ({len(files)}):")
    OUTPUT_LINES.append("\n### Files found")
    for f in files:
        try:
            mb = f.stat().st_size / (1024 * 1024)
            echo(f"  {f.name:60s} {mb:8.2f} MB")
            OUTPUT_LINES.append(f"- `{f.name}` — {mb:.2f} MB")
        except Exception:
            pass

    data_candidates = [f for f in files
                       if f.name.lower().endswith((".csv", ".csv.gz", ".tsv", ".parquet"))]
    if not data_candidates:
        echo("\n!! No CSV/TSV/Parquet file found. Stopping.")
        return

    main_file = max(data_candidates, key=lambda f: f.stat().st_size)
    companions = [f for f in data_candidates if f != main_file]
    echo(f"\nMain POS file: {main_file.name}")
    echo(f"Companion data files: {[f.name for f in companions] or 'none'}")
    OUTPUT_LINES.append(f"\n**Main file:** `{main_file.name}`")
    OUTPUT_LINES.append(f"**Companion files:** {', '.join(f'`{f.name}`' for f in companions) or 'none'}")

    # ---- 2. LOAD
    header("2. LOADING MAIN POS FILE")
    try:
        if main_file.name.lower().endswith(".parquet"):
            df = pd.read_parquet(main_file)
        else:
            sep = "\t" if main_file.name.lower().endswith(".tsv") else ","
            df = pd.read_csv(main_file, sep=sep, low_memory=False)
    except Exception as e:
        echo(f"!! Could not load: {e}")
        return

    n_rows, n_cols = df.shape
    echo(f"Shape: {n_rows:,} rows × {n_cols} columns")
    OUTPUT_LINES.append(f"\n### Shape\n- **Rows:** {n_rows:,}\n- **Columns:** {n_cols}")

    echo("\nFirst 3 rows:")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        echo(df.head(3).to_string())

    # ---- 3. COLUMN INVENTORY
    header("3. COLUMN INVENTORY")
    echo(f"{'column':35s} {'dtype':10s} {'non-null':>10s} {'null%':>7s} {'unique':>10s}  sample")
    echo("-" * 110)
    OUTPUT_LINES.append("\n### Column inventory")
    OUTPUT_LINES.append("| Column | dtype | Non-null | Null % | Unique | Sample |")
    OUTPUT_LINES.append("|---|---|---|---|---|---|")
    for c in df.columns:
        nn = df[c].notna().sum()
        npct = 100 * (1 - nn / n_rows) if n_rows else 0
        uniq = df[c].nunique(dropna=True)
        samples = df[c].dropna().head(2).tolist()
        sstr = " | ".join(str(s)[:20] for s in samples)
        echo(f"{c:35s} {str(df[c].dtype):10s} {nn:>10,} {npct:>6.1f}% {uniq:>10,}  {sstr}")
        OUTPUT_LINES.append(f"| `{c}` | {df[c].dtype} | {nn:,} | {npct:.1f}% | {uniq:,} | {sstr} |")

    # ---- 4. CRITICAL COLUMN CHECK
    header("4. CRITICAL COLUMN CHECK")
    detected = {}
    missing = []
    echo(f"{'business need':20s} {'matched column':30s} status")
    echo("-" * 80)
    OUTPUT_LINES.append("\n### Critical column check")
    OUTPUT_LINES.append("| Business need | Matched column | Status |")
    OUTPUT_LINES.append("|---|---|---|")
    for k, cands in CRITICAL_COLUMNS.items():
        actual = find_col(df, cands)
        detected[k] = actual
        status = "OK" if actual else "**MISSING**"
        if not actual:
            missing.append(k)
        echo(f"{k:20s} {str(actual):30s} {status}")
        OUTPUT_LINES.append(f"| {k} | {actual or '—'} | {status} |")

    if missing:
        echo(f"\n!! Critical columns NOT found: {missing}")
        echo("   Reply to lead with the full column list so I can adjust detection.")

    # ---- 5. DATE COVERAGE
    header("5. DATE COVERAGE")
    date_col = detected.get("date")
    date_info = {}
    if date_col:
        try:
            d = pd.to_datetime(df[date_col], errors="coerce")
            valid = d.dropna()
            if len(valid) > 0:
                dmin, dmax = valid.min(), valid.max()
                n_cal = (dmax - dmin).days + 1
                n_present = valid.dt.date.nunique()
                echo(f"  Range: {dmin.date()}  →  {dmax.date()}  ({n_cal} calendar days)")
                echo(f"  Distinct days present: {n_present:,}  |  missing: {n_cal - n_present:,}")
                echo(f"  Unparseable dates: {d.isna().sum() - df[date_col].isna().sum():,}")
                monthly = valid.dt.to_period("M").value_counts().sort_index()
                echo(f"  Months covered: {len(monthly)}")
                echo("  First 3 / last 3 months:")
                for p, c in list(monthly.items())[:3]:
                    echo(f"    {p}: {c:,}")
                echo("    ...")
                for p, c in list(monthly.items())[-3:]:
                    echo(f"    {p}: {c:,}")
                date_info = {"min": str(dmin.date()), "max": str(dmax.date()),
                             "missing_days": int(n_cal - n_present), "months": len(monthly)}
                OUTPUT_LINES.append(
                    f"\n### Date coverage\n- Range: **{dmin.date()} → {dmax.date()}**"
                    f"\n- Calendar days: {n_cal}\n- Missing days: {n_cal - n_present}"
                    f"\n- Months covered: {len(monthly)}"
                )
        except Exception as e:
            echo(f"  Could not parse date column: {e}")
    else:
        echo("  !! No date column detected")

    # ---- 6. MISSINGNESS
    header("6. MISSINGNESS")
    miss = df.isna().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    if miss.empty:
        echo("  No missing values in any column.")
        OUTPUT_LINES.append("\n### Missingness\nNone.")
    else:
        echo(f"  {len(miss)} columns with nulls:")
        OUTPUT_LINES.append("\n### Missingness\n| Column | Missing | % |")
        OUTPUT_LINES.append("|---|---|---|")
        for c, n in miss.items():
            pct = 100 * n / n_rows
            echo(f"    {c:35s} {n:>10,} ({pct:5.2f}%)")
            OUTPUT_LINES.append(f"| `{c}` | {n:,} | {pct:.2f}% |")

    # ---- 7. DUPLICATES
    header("7. DUPLICATES")
    full_dup = int(df.duplicated().sum())
    echo(f"  Full-row duplicates: {full_dup:,} ({100*full_dup/n_rows:.3f}%)")
    OUTPUT_LINES.append(f"\n### Duplicates\n- Full-row: {full_dup:,} ({100*full_dup/n_rows:.3f}%)")
    o = detected.get("order_id"); l = detected.get("line_id")
    if o and l:
        key_dup = int(df.duplicated(subset=[o, l]).sum())
        echo(f"  Duplicate ({o}, {l}) keys: {key_dup:,} ({100*key_dup/n_rows:.3f}%)")
        OUTPUT_LINES.append(f"- Duplicate `({o}, {l})`: {key_dup:,}")

    # ---- 8. BUSINESS RULES
    header("8. BUSINESS RULE VALIDITY")
    violations = {}
    q = detected.get("quantity")
    if q:
        qv = pd.to_numeric(df[q], errors="coerce")
        violations["negative_quantity"] = int((qv < 0).sum())
        violations["zero_quantity"] = int((qv == 0).sum())
        echo(f"  Negative quantity: {violations['negative_quantity']:,}")
        echo(f"  Zero quantity:     {violations['zero_quantity']:,}")

    p = detected.get("unit_price")
    if p:
        pv = pd.to_numeric(df[p], errors="coerce")
        violations["negative_price"] = int((pv < 0).sum())
        violations["zero_price"] = int((pv == 0).sum())
        echo(f"  Negative price:    {violations['negative_price']:,}")
        echo(f"  Zero price:        {violations['zero_price']:,}")

    disc_col = detected.get("discount")
    disc_encoding = "unknown"
    if disc_col:
        dv = pd.to_numeric(df[disc_col], errors="coerce")
        dmin, dmax = float(dv.min()), float(dv.max())
        echo(f"  Discount range: {dmin:.4f}  →  {dmax:.4f}")
        if dmax > 1.5:
            disc_encoding = "percent"
            echo("  → Encoding appears to be PERCENTAGE (0–100)")
            violations["discount_over_100"] = int((dv > 100).sum())
        else:
            disc_encoding = "fraction"
            echo("  → Encoding appears to be FRACTION (0–1)")
            violations["discount_over_1"] = int((dv > 1).sum())
        violations["negative_discount"] = int((dv < 0).sum())
        echo(f"  Negative discount: {violations['negative_discount']:,}")

    c = detected.get("unit_cost")
    cost_gt_price = 0
    if c:
        cv = pd.to_numeric(df[c], errors="coerce")
        violations["negative_cost"] = int((cv < 0).sum())
        violations["zero_cost"] = int((cv == 0).sum())
        echo(f"  Negative cost:     {violations['negative_cost']:,}")
        echo(f"  Zero cost:         {violations['zero_cost']:,}")
        if p:
            pv2 = pd.to_numeric(df[p], errors="coerce")
            mask = (cv > pv2) & (pv2 > 0) & cv.notna() & pv2.notna()
            cost_gt_price = int(mask.sum())
            violations["cost_gt_price"] = cost_gt_price
            echo(f"  Cost > price:      {cost_gt_price:,} ({100*cost_gt_price/n_rows:.3f}%)")

    OUTPUT_LINES.append("\n### Business rule violations\n| Rule | Count |")
    OUTPUT_LINES.append("|---|---|")
    for k, v in violations.items():
        OUTPUT_LINES.append(f"| {k} | {v:,} |")

    # ---- 9. ARITHMETIC CONSISTENCY
    header("9. ARITHMETIC CONSISTENCY")
    net_col = find_col(df, ["net_sales", "netsales", "net_sale"])
    gross_col = find_col(df, ["gross_sales", "grosssales", "gross_sale", "extended_sales"])
    gp_col = detected.get("gross_profit")
    consistency = []

    if gross_col and disc_col and net_col:
        try:
            g = pd.to_numeric(df[gross_col], errors="coerce")
            d = pd.to_numeric(df[disc_col], errors="coerce")
            n = pd.to_numeric(df[net_col], errors="coerce")
            div = 100 if disc_encoding == "percent" else 1
            expected = g * (1 - d / div)
            diff = (n - expected).abs()
            ok = diff.notna() & (diff <= 0.01)
            rate = 100 * ok.sum() / diff.notna().sum() if diff.notna().sum() else 0
            echo(f"  net_sales ≈ gross_sales × (1 − discount/{div})")
            echo(f"    Match (|diff| ≤ $0.01): {rate:.2f}%  |  median err: ${diff.median():.4f}")
            consistency.append(("net_sales arithmetic", f"{rate:.2f}% match"))
        except Exception as e:
            echo(f"  net_sales check failed: {e}")

    if gp_col and c and q:
        try:
            gp = pd.to_numeric(df[gp_col], errors="coerce")
            cv2 = pd.to_numeric(df[c], errors="coerce")
            qv2 = pd.to_numeric(df[q], errors="coerce")
            if net_col:
                exp = pd.to_numeric(df[net_col], errors="coerce") - cv2 * qv2
            elif p and disc_col:
                pv3 = pd.to_numeric(df[p], errors="coerce")
                dv3 = pd.to_numeric(df[disc_col], errors="coerce")
                div = 100 if disc_encoding == "percent" else 1
                exp = (pv3 * (1 - dv3 / div) - cv2) * qv2
            else:
                exp = None
            if exp is not None:
                diff = (gp - exp).abs()
                ok = diff.notna() & (diff <= 0.01)
                rate = 100 * ok.sum() / diff.notna().sum() if diff.notna().sum() else 0
                echo(f"  gross_profit ≈ (net_price − unit_cost) × quantity")
                echo(f"    Match (|diff| ≤ $0.01): {rate:.2f}%  |  median err: ${diff.median():.4f}")
                consistency.append(("gross_profit arithmetic", f"{rate:.2f}% match"))
        except Exception as e:
            echo(f"  gross_profit check failed: {e}")

    OUTPUT_LINES.append("\n### Arithmetic consistency")
    OUTPUT_LINES.append("| Check | Result |")
    OUTPUT_LINES.append("|---|---|")
    for k, v in consistency or [("No checks possible", "—")]:
        OUTPUT_LINES.append(f"| {k} | {v} |")

    # ---- 10. DISTRIBUTIONS
    header("10. DISTRIBUTIONS")
    def dist(col, label, top=10):
        if not col: return
        echo(f"\n  {label} ({df[col].nunique()} unique):")
        vc = df[col].value_counts().head(top)
        for val, cnt in vc.items():
            echo(f"    {str(val)[:40]:40s} {cnt:>10,}  ({100*cnt/n_rows:.1f}%)")

    dist(detected.get("store_id"), "Store distribution")
    dist(detected.get("category"), "Category distribution")
    dist(detected.get("payment_method"), "Payment method")
    dist(detected.get("refund"), "Refund flag values")

    cust = detected.get("customer_id")
    if cust and o:
        try:
            opc = df.groupby(cust)[o].nunique()
            rep = 100 * (opc > 1).sum() / len(opc)
            echo(f"\n  Customers: {len(opc):,}  |  repeat (≥2 orders): {rep:.1f}%")
            OUTPUT_LINES.append(f"\n### Distributions\n- Stores: {df[detected['store_id']].nunique() if detected.get('store_id') else '—'}"
                                f"\n- Categories: {df[detected['category']].nunique() if detected.get('category') else '—'}"
                                f"\n- Customers: {len(opc):,}\n- Repeat customer share: {rep:.1f}%")
        except Exception:
            pass

    # ---- 11. COMPANION FILES
    header("11. COMPANION FILES")
    for f in companions:
        try:
            if f.name.lower().endswith((".csv", ".csv.gz")):
                cdf = pd.read_csv(f, low_memory=False)
            elif f.name.lower().endswith(".tsv"):
                cdf = pd.read_csv(f, sep="\t", low_memory=False)
            elif f.name.lower().endswith(".parquet"):
                cdf = pd.read_parquet(f)
            else:
                continue
            echo(f"\n  {f.name}: {cdf.shape[0]:,} rows × {cdf.shape[1]} cols")
            echo(f"    Columns: {cdf.columns.tolist()}")
            with pd.option_context("display.width", 200):
                echo(cdf.head(3).to_string())
            OUTPUT_LINES.append(f"\n#### `{f.name}`\n- Shape: {cdf.shape[0]:,} × {cdf.shape[1]}\n- Columns: {', '.join(cdf.columns)}")
        except Exception as e:
            echo(f"  Could not read {f.name}: {e}")

    # ---- 12. SCORECARD
    header("12. DATA QUALITY SCORECARD")
    crit = [detected[k] for k in ["unit_cost", "unit_price", "quantity", "order_id", "date", "customer_id"] if detected.get(k)]
    completeness_pct = 100 * (1 - df[crit].isna().mean().mean()) if crit else 0
    uniqueness_pct = 100 * (1 - full_dup / n_rows)
    total_viol = sum(violations.values())
    validity_pct = max(0, 100 * (1 - total_viol / n_rows))
    if consistency:
        rates = [float(s.split("%")[0]) for _, s in consistency if "%" in s]
        consistency_pct = np.mean(rates) if rates else 100
    else:
        consistency_pct = 100
    timeliness_pct = 100 * min(1, date_info.get("months", 0) / 24) if date_info else 0

    def to_score(pct):
        return min(5.0, max(1.0, pct / 20))

    scores = {
        "Completeness": (0.25, to_score(completeness_pct), completeness_pct),
        "Uniqueness":   (0.20, to_score(uniqueness_pct), uniqueness_pct),
        "Validity":     (0.20, to_score(validity_pct), validity_pct),
        "Consistency":  (0.15, to_score(consistency_pct), consistency_pct),
        "Timeliness":   (0.20, to_score(timeliness_pct), timeliness_pct),
    }
    overall = sum(w * s for w, s, _ in scores.values())
    overall_100 = overall * 20

    echo(f"\n  {'dimension':15s} {'weight':>8s} {'score/5':>10s} {'score%':>8s}")
    echo("  " + "-" * 45)
    for dim, (w, s, pct) in scores.items():
        echo(f"  {dim:15s} {w*100:>7.0f}% {s:>10.2f} {pct:>7.1f}%")
    echo("  " + "-" * 45)
    echo(f"  {'OVERALL':15s} {'':>8s} {overall:>10.2f} {overall_100:>7.1f}%")

    if overall_100 >= 90:
        verdict = "EXCELLENT — proceed to Phase 1 sign-off."
    elif overall_100 >= 75:
        verdict = "ACCEPTABLE — proceed; document flagged issues in cleaning log."
    else:
        verdict = "POOR — resolve issues before Phase 1."
    echo(f"\n  Verdict: {verdict}")

    OUTPUT_LINES.append("\n### Scorecard")
    OUTPUT_LINES.append("| Dimension | Weight | Score /5 | Score % |")
    OUTPUT_LINES.append("|---|---|---|---|")
    for dim, (w, s, pct) in scores.items():
        OUTPUT_LINES.append(f"| {dim} | {w*100:.0f}% | {s:.2f} | {pct:.1f}% |")
    OUTPUT_LINES.append(f"| **Overall** | 100% | **{overall:.2f}** | **{overall_100:.1f}%** |")
    OUTPUT_LINES.append(f"\n**Verdict:** {verdict}")

    # ---- SAVE REPORT
    out_path = Path(workdir) / "verification_report.md"
    out_path.write_text("\n".join(OUTPUT_LINES), encoding="utf-8")
    print(f"\n\nReport saved: {out_path}")
    print("\nReply to lead with:")
    print("  1) The critical-column check block (section 4)")
    print("  2) The scorecard block (section 12)")
    print("  3) Any missing columns flagged in section 4")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_PATH
    main(target)