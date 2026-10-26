"""Build Power BI star schema CSVs and an interactive Plotly HTML dashboard for Online Retail II.

Outputs:
- powerbi/*.csv
- reports/dashboard.html
"""
from pathlib import Path
import duckdb
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
REP = ROOT / "reports"
PBI.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)


def main():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())
    con.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())

    # 1. Export Power BI CSVs
    pbi_tables = [
        ("pbi_fact_transactions", "fact_transactions.csv"),
        ("pbi_dim_customer", "dim_customer.csv"),
        ("pbi_dim_product", "dim_product.csv"),
        ("pbi_dim_date", "dim_date.csv"),
        ("pbi_dim_cohort", "dim_cohort.csv"),
    ]
    for tbl, fname in pbi_tables:
        csv_path = (PBI / fname).as_posix()
        con.execute(f"COPY {tbl} TO '{csv_path}' (HEADER, DELIMITER ',')")
        print(f"Exported {tbl} -> {PBI / fname}")

    # 2. Build Interactive HTML Dashboard
    df_segments = con.execute("""
        SELECT
            segment_label,
            count(*) AS customers,
            round(sum(monetary_value), 2) AS revenue,
            round(avg(recency_days), 1) AS avg_recency,
            round(avg(frequency), 1) AS avg_freq
        FROM dim_rfm_customer
        GROUP BY segment_label
        ORDER BY revenue DESC
    """).fetchdf()

    df_cohort = con.execute("""
        WITH activity AS (
            SELECT
                c.customer_id,
                strftime(c.cohort_month, '%Y-%m') AS cohort,
                date_diff('month', c.cohort_month, t.invoice_month) AS period
            FROM dim_customer_cohort c
            JOIN clean_transactions t USING (customer_id)
            WHERE NOT t.is_cancelled
              AND c.cohort_month BETWEEN DATE '2010-01-01' AND DATE '2010-09-01'
        ),
        sizes AS (
            SELECT strftime(cohort_month, '%Y-%m') AS cohort, count(DISTINCT customer_id) AS sz
            FROM dim_customer_cohort
            WHERE cohort_month BETWEEN DATE '2010-01-01' AND DATE '2010-09-01'
            GROUP BY cohort_month
        )
        SELECT
            a.cohort,
            a.period,
            round(count(DISTINCT a.customer_id) * 100.0 / s.sz, 1) AS retention_pct
        FROM activity a
        JOIN sizes s USING (cohort)
        WHERE a.period <= 8
        GROUP BY a.cohort, s.sz, a.period
        ORDER BY a.cohort, a.period
    """).fetchdf()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Revenue by Customer Segment (The 70% VIP Concentration)",
            "Customer Count by Segment",
            "Customer Recency vs Frequency by Segment",
            "Monthly Cohort Retention (%) over 8 Months"
        ),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "scatter"}]]
    )

    # 1. Revenue by Segment
    fig.add_trace(
        go.Bar(
            x=df_segments["segment_label"],
            y=df_segments["revenue"],
            text=df_segments["revenue"].apply(lambda x: f"£{x:,.0f}"),
            textposition="auto",
            marker_color="#3B82F6",
            name="Revenue (£)"
        ),
        row=1, col=1
    )

    # 2. Customers by Segment
    fig.add_trace(
        go.Bar(
            x=df_segments["segment_label"],
            y=df_segments["customers"],
            text=df_segments["customers"].apply(lambda x: f"{x:,}"),
            textposition="auto",
            marker_color="#10B981",
            name="Customer Count"
        ),
        row=1, col=2
    )

    # 3. Scatter: Recency vs Frequency
    fig.add_trace(
        go.Scatter(
            x=df_segments["avg_recency"],
            y=df_segments["avg_freq"],
            mode="markers+text",
            text=df_segments["segment_label"],
            textposition="top center",
            marker=dict(
                size=df_segments["customers"] / 80 + 12,
                color=df_segments["revenue"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Spend (£)", x=1.05)
            ),
            name="Segments"
        ),
        row=2, col=1
    )

    # 4. Cohort Retention Curves
    for c in df_cohort["cohort"].unique()[:4]:
        sub = df_cohort[df_cohort["cohort"] == c]
        fig.add_trace(
            go.Scatter(
                x=sub["period"],
                y=sub["retention_pct"],
                mode="lines+markers",
                name=f"Cohort {c}"
            ),
            row=2, col=2
        )

    fig.update_layout(
        title_text="<b>Customer Segmentation & Retention Executive Dashboard</b><br><sup>Online Retail II: RFM Value Distribution and Longitudinal Cohort Retention</sup>",
        template="plotly_white",
        height=850,
        showlegend=True
    )

    dashboard_path = REP / "dashboard.html"
    fig.write_html(str(dashboard_path), include_plotlyjs="cdn")
    print(f"Generated interactive dashboard: {dashboard_path}")


if __name__ == "__main__":
    main()
