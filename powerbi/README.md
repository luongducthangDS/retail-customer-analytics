# Power BI Rebuild Guide: Online Retail II Customer Segmentation & Retention

This directory contains star schema CSVs generated from `sql/10_powerbi_export.sql` via `python analysis/build_dashboard.py`.

## Data Model & Relationships

1. Load the 5 CSV files:
   - `fact_transactions.csv` (Transactions with cancellation flags)
   - `dim_customer.csv` (Unique customer RFM scores, segments, and cohorts)
   - `dim_product.csv` (Distinct stock codes and product descriptions)
   - `dim_date.csv` (Calendar dimension)
   - `dim_cohort.csv` (Cohort acquisition months and sizes)

2. Create 1-to-many relationships (Single direction filter):
   - `dim_date[date]` 1 ---> * `fact_transactions[invoice_day]`
   - `dim_customer[customer_id]` 1 ---> * `fact_transactions[customer_id]`
   - `dim_product[stock_code]` 1 ---> * `fact_transactions[stock_code]`
   - `dim_cohort[cohort_month]` 1 ---> * `dim_customer[cohort_month]`

3. Create DAX measures from `measures.dax`.
