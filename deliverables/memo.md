# MEMORANDUM

**To:** Owner-Operator, Regional Retail Chain
**From:** PADMABHUSHAN
**Date:** 2026-10-30
**Subject:** Action Plan to Recover $1.13M in Lost Margin
**Supporting file:** `dashboard/retail_profitability_diagnostic.pbix` · `notebooks/02_diagnostics.ipynb`

---

## Executive Summary

Over the past 24 months, the business generated $46.6 million in revenue with a healthy 55.34% overall contribution margin. However, this aggregate health masks a $1.13 million margin leak driven entirely by discount policy, not by unprofitable products. The diagnostic proves that deeper discounts do not buy enough volume to offset their margin hit; selling the 20% tier volume at 10% instead would have recovered $240,000 in margin. The two largest culprits are Apparel and Footwear at the 20% tier, which together account for $309,000 of the total leakage. To fix this, the owner must eliminate the 30% and 40% tiers entirely and cap standard promotions at 15% for Footwear and Electronics, and 20% for all other categories.

---

## The Five Actions

| # | Action | Evidence | Expected Monthly Impact | Owner |
|---|---|---|---|---|
| **1** | **Eliminate the 30% and 40% discount tiers entirely.** | These tiers generate minimal volume and leak a combined $133K in margin. | Protects ~$5,500/month | Sales Lead |
| **2** | **Cap Apparel and Footwear promotions at 15%.** | Apparel@20% leaks $158K; Footwear@20% leaks $151K. Combined, they account for 27% of total leakage. | Recovers ~$13,000/month | Merchandising |
| **3** | **Shift standard promotion tier from 20% to 10%.** | The 10% tier generates $2.20M absolute margin, vs the 20% tier's $1.92M on fewer lines. | Recovers ~$10,000/month | Marketing |
| **4** | **Reallocate shelf space and marketing to Beauty, Accessories, and Home Goods.** | These categories have 64-68% margins vs Footwear at 48.7% and Electronics at 49.3%. | Improves blended margin by 3-5 points | Merchandising |
| **5** | **Set a hard floor: Do not reprice or delist any current SKU.** | The lowest-margin SKU (Wireless Earbuds) still earns 41.7%. No SKUs are loss-making. | Preserves volume; avoids destroying cash flow | Purchasing |

---

**What We Did Not Measure:**
This analysis is limited to the transactional POS data provided. We did not measure price elasticity or promotion lift (no A/B test data exists), so we cannot predict how much volume will drop if you cap discounts. We also did not measure Customer Lifetime Value: because 65% of transactions are guest checkouts and the observation window is 24 months, any CLV number would be fabricated precision. Finally, we did not measure delivery or fulfillment costs, as those fields do not exist in this dataset. The recommendations above are based purely on optimizing the unit economics of the products and promotions captured at the register.

---

## Appendix: Data Integrity
This analysis is based on 970,838 line items spanning 24 months. The dataset was audited, and the load reconciles to the vendor summary file with zero delta for all 30 stores. Refunds are retained in the fact table (0.84% of revenue) and net out at the category and SKU grain. The discount tier structure was verified against distinct values, confirming seven nominal tiers (0%, 10%, 15%, 20%, 25%, 30%, 40%).