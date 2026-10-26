-- Power BI Star Schema Export for Online Retail II

CREATE OR REPLACE TABLE pbi_dim_customer AS
SELECT
    customer_id,
    segment_label,
    rfm_cell,
    r_score,
    f_score,
    m_score,
    recency_days,
    frequency,
    monetary_value,
    returned_value,
    cohort_month,
    first_order_date
FROM dim_rfm_customer;

CREATE OR REPLACE TABLE pbi_dim_product AS
SELECT
    stock_code,
    max(description) AS description
FROM fct_transactions
GROUP BY stock_code;

CREATE OR REPLACE TABLE pbi_dim_date AS
WITH bounds AS (
    SELECT min(invoice_day) AS min_d, max(invoice_day) AS max_d FROM fct_transactions
),
dates AS (
    SELECT unnest(generate_series(min_d, max_d, INTERVAL 1 DAY))::DATE AS date
    FROM bounds
)
SELECT
    date,
    date_part('year', date)                             AS year,
    'Q' || date_part('quarter', date)                   AS quarter,
    date_part('month', date)                            AS month_num,
    strftime(date, '%B')                                AS month_name,
    strftime(date, '%Y-%m')                             AS year_month,
    strftime(date, '%A')                                AS day_name,
    date_part('isodow', date) IN (6, 7)                 AS is_weekend
FROM dates;

CREATE OR REPLACE TABLE pbi_dim_cohort AS
SELECT
    cohort_month,
    count(DISTINCT customer_id) AS cohort_size
FROM dim_customer_cohort
GROUP BY cohort_month;

CREATE OR REPLACE TABLE pbi_fact_transactions AS
SELECT
    t.transaction_id,
    t.invoice_no,
    t.invoice_day,
    t.customer_id,
    t.stock_code,
    t.country,
    t.quantity,
    t.unit_price,
    t.line_amount,
    t.is_cancelled
FROM fct_transactions t
JOIN dim_rfm_customer c USING (customer_id);
