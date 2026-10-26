-- Online Retail II Customer Segmentation & Retention Analytics Model
-- Grain: 1 row per transaction item in fct_transactions

CREATE OR REPLACE TABLE clean_transactions AS
SELECT
    TRIM("Invoice")                                                     AS invoice_no,
    TRIM("StockCode")                                                   AS stock_code,
    COALESCE(NULLIF(TRIM("Description"), ''), 'Unknown Product')       AS description,
    CAST("Quantity" AS INTEGER)                                         AS quantity,
    CAST("InvoiceDate" AS TIMESTAMP)                                    AS invoice_date,
    CAST("InvoiceDate" AS DATE)                                         AS invoice_day,
    date_trunc('month', CAST("InvoiceDate" AS DATE))::DATE              AS invoice_month,
    ROUND(CAST("Price" AS DOUBLE), 2)                                   AS unit_price,
    ROUND(CAST("Quantity" AS INTEGER) * CAST("Price" AS DOUBLE), 2)    AS line_amount,
    CAST("Customer ID" AS BIGINT)                                       AS customer_id,
    TRIM("Country")                                                     AS country,
    "Invoice" LIKE 'C%' OR CAST("Quantity" AS INTEGER) < 0              AS is_cancelled
FROM read_csv_auto('data/raw/online_retail_raw.csv')
WHERE "Customer ID" IS NOT NULL
  AND TRIM("StockCode") NOT IN ('POST', 'D', 'M', 'BANK CHARGES', 'PADS', 'CRUK')
  AND CAST("Price" AS DOUBLE) > 0;

-- 1. Fact Table
CREATE OR REPLACE TABLE fct_transactions AS
SELECT
    row_number() OVER () AS transaction_id,
    invoice_no,
    stock_code,
    description,
    quantity,
    invoice_date,
    invoice_day,
    invoice_month,
    unit_price,
    line_amount,
    customer_id,
    country,
    is_cancelled
FROM clean_transactions;

-- 2. Customer Cohort Mapping
CREATE OR REPLACE TABLE dim_customer_cohort AS
SELECT
    customer_id,
    min(invoice_month) AS cohort_month,
    min(invoice_day)   AS first_order_date
FROM clean_transactions
WHERE NOT is_cancelled
GROUP BY customer_id;

-- 3. Customer RFM Aggregations & NTILE Segmentation
CREATE OR REPLACE TABLE dim_rfm_customer AS
WITH raw_rfm AS (
    SELECT
        t.customer_id,
        date_diff('day', max(t.invoice_day), DATE '2011-12-10')         AS recency_days,
        count(DISTINCT CASE WHEN NOT t.is_cancelled THEN t.invoice_no END) AS frequency,
        round(sum(CASE WHEN NOT t.is_cancelled THEN t.line_amount ELSE 0 END), 2) AS monetary_value,
        round(sum(CASE WHEN t.is_cancelled THEN abs(t.line_amount) ELSE 0 END), 2) AS returned_value,
        count(CASE WHEN t.is_cancelled THEN 1 END)                      AS return_items_count
    FROM clean_transactions t
    GROUP BY t.customer_id
    HAVING sum(t.line_amount) > 0
),
scored_rfm AS (
    SELECT
        r.*,
        -- R score: Lowest recency days gets highest score (5)
        6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)        AS f_score,
        NTILE(5) OVER (ORDER BY monetary_value ASC)   AS m_score
    FROM raw_rfm r
)
SELECT
    s.customer_id,
    c.cohort_month,
    c.first_order_date,
    s.recency_days,
    s.frequency,
    s.monetary_value,
    s.returned_value,
    s.return_items_count,
    s.r_score,
    s.f_score,
    s.m_score,
    (s.r_score || s.f_score || s.m_score) AS rfm_cell,
    CASE
        WHEN s.r_score >= 4 AND s.f_score >= 4 THEN 'Champions (VIP)'
        WHEN s.r_score >= 3 AND s.f_score >= 3 THEN 'Loyal Customers'
        WHEN s.r_score >= 4 AND s.f_score <= 2 THEN 'Recent New Customers'
        WHEN s.r_score = 3 AND s.f_score <= 2 THEN 'Promising / Potential'
        WHEN s.r_score <= 2 AND s.f_score >= 3 THEN 'At Risk / Need Attention'
        WHEN s.r_score = 1 AND s.f_score >= 4 THEN 'Cant Lose Them (High Value Slipping)'
        WHEN s.r_score <= 2 AND s.f_score <= 2 THEN 'Hibernating / Lost'
        ELSE 'Average Customers'
    END AS segment_label
FROM scored_rfm s
JOIN dim_customer_cohort c USING (customer_id);
