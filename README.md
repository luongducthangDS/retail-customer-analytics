# Online Retail II: Customer Segmentation & Retention Analytics

Analysis of **1,067,371 transactions** across 2009–2011 (£17.29M net sales) from the UK-based Online Retail II dataset (UCI Machine Learning Repository). It addresses customer lifetime value concentration, isolates returns and cancellations, models behavioral RFM segmentation via NTILE quantiles, and produces an actionable CRM retention strategy with an interactive dashboard.

## Executive Answer

**Customer value is heavily concentrated, and customer drop-off happens within 45 days.** The top **24.2% of customers (Champions VIP)** generate **69.6% of company net revenue** (£12.04M). Conversely, without automated onboarding, newly acquired buyers drop from 100% to **22.5% retention by Month 1**.

| Finding | Metric |
|---|---|
| Clean Transactions Analyzed | **805k+ line items** with verified customer IDs and positive prices |
| Total Registered Customers | **5,848 distinct customer accounts** |
| Net Revenue | **£17,291,751.71** (after deducting all cancellations and returns) |
| Overall Repeat Customer Rate | **72.4%** across all customers |
| Mature 180-Day Repeat Rate | **76.9%** (controlling for right-censoring of recent buyers) |
| Champions Segment Share | 24.23% of customers generate **69.62% of revenue** (AOV £8,502) |
| At-Risk / Slipping Segment | 8.4% of customers holding **£2.1M past revenue** inactive >90 days |
| Month-1 Retention Cliff | **22.5%** repeat rate in Month 1, stabilizing at 18–20% |

**So what:** Cease paid remarketing to the 35% "Hibernating/Lost" accounts; launch an automated D+25 onboarding trigger to catch first-time buyers before the 45-day cliff; protect VIP Champions with early product access rather than blanket margin-diluting discount codes.

## Architecture & Method

1. **Model** (`sql/00_model.sql`, DuckDB): Cleans 1M+ rows. Filters system stock codes (`POST`, `BANK CHARGES`), flags cancellations (`Invoice` starting with 'C' or negative quantity), computes customer Recency (reference date 2011-12-10), Frequency, and Net Monetary spend.
2. **Segmentation**: Computes 5-point NTILE quantiles for R, F, and M. Maps customers into 7 actionable CRM lifecycle segments (`Champions`, `Loyal Customers`, `Recent New Customers`, `Promising`, `At Risk`, `Can't Lose Them`, `Hibernating/Lost`).
3. **Cohort Retention**: Tracks monthly customer acquisition cohorts (Months 0 to 12) with right-censoring checks.
4. **Checks** (`tests/test_model.py`, pytest): 6 tests verifying row volumes, non-null customer keys, RFM score distributions (1-5), dimension uniqueness, and star schema referential integrity.
5. **Outputs**:
   - `reports/results.json` (reproducible metrics).
   - `reports/dashboard.html` (interactive Plotly dashboard).
   - `powerbi/`: Star schema CSVs (`fact_transactions.csv`, `dim_customer.csv`, `dim_product.csv`, `dim_date.csv`, `dim_cohort.csv`), `measures.dax`, and `power_query.m`.

## How to Run It

```bash
pip install -r requirements.txt
python scripts/get_data.py              # Streams and converts raw XLSX sheets into unified CSV
pytest -q                               # Runs 6 data integrity and referential checks
python analysis/run_analysis.py         # Produces reports/results.json
python analysis/build_dashboard.py      # Exports powerbi/*.csv & reports/dashboard.html
```

## Decisions Worth Defending in an Interview

- **Why rule-based RFM via NTILEs rather than K-Means clustering?** K-Means produces clusters that change dynamically every run, is highly sensitive to extreme wholesale transaction outliers, and lacks interpretable business boundaries. NTILE-based RFM provides transparent, auditable rules that map directly into CRM automation triggers (e.g. HubSpot or Klaviyo workflows).
- **How are cancellations and returns handled?** Invoices with 'C' prefixes or negative quantities are not blindly discarded. They are separated into return metrics to calculate net spend (`sales - returns`) per customer. Discarding them would artificially inflate customer monetary values by up to 15%.
- **Why distinguish between raw repeat rate and the 180-day mature repeat rate?** Customers acquired in November 2011 have had less than 30 days to buy again. Including them drags the overall repeat rate down due to **right-censoring**. Restricting the metric to customers with $\ge$180 days of follow-up reveals the true mature retention rate (76.9% vs. 72.4%).

## Interview Questions this Project Prepares For

1. How did you handle guest orders without a Customer ID, and how would omitting them bias your findings?
2. Walk me through your RFM scoring formula: why did you reverse the order of Recency compared to Frequency and Monetary?
3. If the CMO asked whether a customer retention email campaign in month 2 was successful, how would you design a control group to measure true incremental lift?
