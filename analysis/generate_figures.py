"""Generate publication-quality figures for Online Retail II analytics README."""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#1F2937", "#6B7280", "#E5E7EB"
BLUE, RED, GREEN, PURPLE = "#2563EB", "#DC2626", "#059669", "#7C3AED"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlecolor": INK
})


def generate():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")
    for ax in axes.flat:
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

    # 1. Revenue Share by Segment
    segs = con.execute("""
        SELECT segment_label, round(sum(monetary_value)/1000000, 2) AS rev_m,
               round(sum(monetary_value)*100.0/(SELECT sum(monetary_value) FROM dim_rfm_customer), 1) AS pct
        FROM dim_rfm_customer
        GROUP BY segment_label
        ORDER BY rev_m DESC
    """).fetchall()
    x1 = [s[0].split(" (")[0] for s in segs]
    y1 = [s[1] for s in segs]
    pct1 = [s[2] for s in segs]
    c1 = [PURPLE if "Champions" in s[0] else BLUE for s in segs]
    bars1 = axes[0, 0].bar(x1, y1, color=c1, width=0.55, zorder=3)
    axes[0, 0].set_title("A. Revenue Concentration by Segment (£M)")
    axes[0, 0].set_ylabel("Total Net Revenue (£M)")
    axes[0, 0].set_ylim(0, max(y1) * 1.25)
    axes[0, 0].tick_params(axis="x", rotation=25)
    for b, p in zip(bars1, pct1):
        axes[0, 0].text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3,
                        f"£{b.get_height():.1f}M\n({p}%)", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=INK)

    # 2. Customer Distribution (Count)
    counts = con.execute("""
        SELECT segment_label, count(*) AS cnt,
               round(count(*)*100.0/(SELECT count(*) FROM dim_rfm_customer), 1) AS pct
        FROM dim_rfm_customer
        GROUP BY segment_label
        ORDER BY cnt DESC
    """).fetchall()
    x2 = [s[0].split(" (")[0] for s in counts]
    y2 = [s[1] for s in counts]
    c2 = [RED if "Lost" in s[0] else GREEN for s in counts]
    bars2 = axes[0, 1].bar(x2, y2, color=c2, width=0.55, zorder=3)
    axes[0, 1].set_title("B. Customer Headcount by Segment")
    axes[0, 1].set_ylabel("Customers")
    axes[0, 1].set_ylim(0, max(y2) * 1.25)
    axes[0, 1].tick_params(axis="x", rotation=25)
    for b, c in zip(bars2, counts):
        axes[0, 1].text(b.get_x() + b.get_width() / 2, b.get_height() + 30,
                        f"{b.get_height():,}\n({c[2]}%)", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=INK)

    # 3. Recency vs Frequency
    rf_data = con.execute("""
        SELECT segment_label, avg(recency_days) AS r, avg(frequency) AS f,
               count(*) AS sz, sum(monetary_value) AS rev
        FROM dim_rfm_customer
        GROUP BY segment_label
    """).fetchall()
    for s, r, f, sz, rev in rf_data:
        c = PURPLE if "Champions" in s else (RED if "Lost" in s or "Risk" in s else BLUE)
        axes[1, 0].scatter(r, f, s=sz / 4 + 40, color=c, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3)
        axes[1, 0].text(r + 8, f, s.split(" (")[0], fontsize=9, fontweight="bold", color=c)
    axes[1, 0].set_title("C. Segment Behavioral Space (Recency vs Frequency)")
    axes[1, 0].set_xlabel("Average Recency (Days since last purchase)")
    axes[1, 0].set_ylabel("Average Order Frequency (Orders)")

    # 4. Cohort Retention Heatmap
    cohort_data = con.execute("""
        WITH activity AS (
            SELECT
                c.customer_id,
                strftime(c.cohort_month, '%Y-%m') AS cohort,
                date_diff('month', c.cohort_month, t.invoice_month) AS period
            FROM dim_customer_cohort c
            JOIN clean_transactions t USING (customer_id)
            WHERE NOT t.is_cancelled
              AND c.cohort_month BETWEEN DATE '2010-01-01' AND DATE '2010-06-01'
        ),
        sizes AS (
            SELECT strftime(cohort_month, '%Y-%m') AS cohort, count(DISTINCT customer_id) AS sz
            FROM dim_customer_cohort
            WHERE cohort_month BETWEEN DATE '2010-01-01' AND DATE '2010-06-01'
            GROUP BY cohort_month
        )
        SELECT
            a.cohort,
            a.period,
            round(count(DISTINCT a.customer_id) * 100.0 / s.sz, 1) AS ret_pct
        FROM activity a
        JOIN sizes s USING (cohort)
        WHERE a.period <= 6
        GROUP BY a.cohort, s.sz, a.period
        ORDER BY a.cohort, a.period
    """).fetchall()

    cohorts_list = sorted(list(set(r[0] for r in cohort_data)))
    matrix = np.zeros((len(cohorts_list), 6))
    for c, p, pct in cohort_data:
        if 1 <= p <= 6:
            ci = cohorts_list.index(c)
            matrix[ci, p - 1] = pct

    im = axes[1, 1].imshow(matrix, cmap="Blues", aspect="auto", vmin=0, vmax=45)
    axes[1, 1].set_xticks(range(6))
    axes[1, 1].set_xticklabels([f"M+{i+1}" for i in range(6)])
    axes[1, 1].set_yticks(range(len(cohorts_list)))
    axes[1, 1].set_yticklabels(cohorts_list)
    axes[1, 1].set_title("D. Cohort Retention Heatmap (Months 1–6)")
    for (i, j), val in np.ndenumerate(matrix):
        if val > 0:
            axes[1, 1].text(j, i, f"{val:.1f}%", ha="center", va="center", fontsize=8.5,
                            color="white" if val > 25 else INK, fontweight="bold")
    fig.colorbar(im, ax=axes[1, 1], label="Retention %")

    fig.suptitle("ONLINE RETAIL II CUSTOMER SEGMENTATION & RETENTION DASHBOARD",
                 fontsize=14, fontweight="bold", y=0.98, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIG / "00_dashboard_preview.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Generated {out}")


if __name__ == "__main__":
    generate()
