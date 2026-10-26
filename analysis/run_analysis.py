"""Customer segmentation and cohort retention analysis for Online Retail II.

Outputs:
- reports/results.json (reproducible metrics quoted in decision memo & README)
"""
import json
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reports"
REP.mkdir(parents=True, exist_ok=True)


def load_model():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())
    con.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())
    return con


def run():
    con = load_model()

    # 1. Headline KPIs
    kpi_query = """
    SELECT
        count(DISTINCT customer_id)                             AS total_customers,
        sum(frequency)                                          AS total_invoices,
        round(sum(monetary_value), 2)                           AS net_revenue,
        round(avg(monetary_value), 2)                           AS avg_customer_ltv,
        round(count(CASE WHEN frequency > 1 THEN 1 END) * 100.0 / count(*), 2) AS overall_repeat_rate_pct
    FROM dim_rfm_customer;
    """
    kpis = con.execute(kpi_query).fetchdf().to_dict(orient="records")[0]

    # 2. 180-day Right-Censored Repeat Purchase Rate (Fair evaluation window)
    censored_query = """
    WITH mature_customers AS (
        SELECT customer_id, first_order_date
        FROM dim_rfm_customer
        WHERE first_order_date <= DATE '2011-12-10' - INTERVAL 180 DAY
    )
    SELECT
        count(*) AS mature_cohort_size,
        count(CASE WHEN c.frequency > 1 THEN 1 END) AS mature_repeaters,
        round(count(CASE WHEN c.frequency > 1 THEN 1 END) * 100.0 / count(*), 2) AS mature_repeat_rate_pct
    FROM mature_customers m
    JOIN dim_rfm_customer c USING (customer_id);
    """
    mature = con.execute(censored_query).fetchdf().to_dict(orient="records")[0]

    # 3. RFM Segment Breakdown
    seg_query = """
    SELECT
        segment_label,
        count(*)                                                AS customer_count,
        round(count(*) * 100.0 / (SELECT count(*) FROM dim_rfm_customer), 2) AS customer_share_pct,
        round(sum(monetary_value), 2)                           AS total_spend,
        round(sum(monetary_value) * 100.0 / (SELECT sum(monetary_value) FROM dim_rfm_customer), 2) AS revenue_share_pct,
        round(avg(monetary_value), 2)                           AS aov_spend_per_customer,
        round(avg(recency_days), 1)                             AS avg_recency_days,
        round(avg(frequency), 1)                                AS avg_frequency
    FROM dim_rfm_customer
    GROUP BY segment_label
    ORDER BY total_spend DESC;
    """
    segments = con.execute(seg_query).fetchdf().to_dict(orient="records")

    # 4. Cohort Retention Matrix (Months 0 to 12 for 2010 cohorts)
    cohort_query = """
    WITH cohort_activity AS (
        SELECT
            c.customer_id,
            c.cohort_month,
            t.invoice_month,
            date_diff('month', c.cohort_month, t.invoice_month) AS period_month
        FROM dim_customer_cohort c
        JOIN clean_transactions t USING (customer_id)
        WHERE NOT t.is_cancelled
          AND c.cohort_month BETWEEN DATE '2010-01-01' AND DATE '2010-12-01'
    ),
    cohort_sizes AS (
        SELECT cohort_month, count(DISTINCT customer_id) AS initial_size
        FROM dim_customer_cohort
        WHERE cohort_month BETWEEN DATE '2010-01-01' AND DATE '2010-12-01'
        GROUP BY cohort_month
    )
    SELECT
        strftime(a.cohort_month, '%Y-%m') AS cohort,
        s.initial_size,
        a.period_month,
        count(DISTINCT a.customer_id) AS active_customers,
        round(count(DISTINCT a.customer_id) * 100.0 / s.initial_size, 1) AS retention_rate_pct
    FROM cohort_activity a
    JOIN cohort_sizes s USING (cohort_month)
    WHERE a.period_month <= 12
    GROUP BY a.cohort_month, s.initial_size, a.period_month
    ORDER BY a.cohort_month, a.period_month;
    """
    cohorts = con.execute(cohort_query).fetchdf().to_dict(orient="records")

    results = {
        "kpis": kpis,
        "mature_180d_cohort": mature,
        "segments": segments,
        "sample_cohort_retention": cohorts[:20]
    }

    out_file = REP / "results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Online Retail analysis completed! Saved to {out_file}")
    print("\n--- Headline Findings ---")
    print(f"Total Registered Customers: {kpis['total_customers']:,} | Net Revenue: £{kpis['net_revenue']:,.2f}")
    print(f"Overall Repeat Rate: {kpis['overall_repeat_rate_pct']}% | Mature (180d+) Repeat Rate: {mature['mature_repeat_rate_pct']}%")
    print(f"Top Segment: {segments[0]['segment_label']} accounts for {segments[0]['revenue_share_pct']}% of revenue from {segments[0]['customer_share_pct']}% of customers!")


if __name__ == "__main__":
    run()
