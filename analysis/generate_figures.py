"""Generate publication-quality figures for Online Retail II analytics README.
Generates:
- 00_dashboard_preview.png (Composite 4-panel executive overview, zero collision)
- 01_rfm_pareto_concentration.png (Standalone: Pareto revenue concentration)
- 02_cohort_retention_heatmap.png (Standalone: Cohort retention matrix)
- 03_behavioral_rfm_matrix.png (Standalone: Recency vs Frequency behavioral space)
"""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#111827", "#4B5563", "#E5E7EB"
BLUE, RED, GREEN, PURPLE, AMBER = "#1D4ED8", "#DC2626", "#059669", "#7C3AED", "#D97706"

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

    # =========================================================================
    # 1. COMPOSITE DASHBOARD PREVIEW (00_dashboard_preview.png)
    # =========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(15, 9.8), dpi=160)
    fig.patch.set_facecolor("#FAFAFA")
    for ax in axes.flat:
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

    # Panel A: Revenue Share by Segment (Horizontal barh eliminates label collision!)
    segs = con.execute("""
        SELECT segment_label, round(sum(monetary_value)/1000000, 2) AS rev_m,
               round(sum(monetary_value)*100.0/(SELECT sum(monetary_value) FROM dim_rfm_customer), 1) AS pct
        FROM dim_rfm_customer
        GROUP BY segment_label
        ORDER BY rev_m ASC
    """).fetchall()
    y1_names = [s[0].split(" (")[0] for s in segs]
    x1_vals = [s[1] for s in segs]
    pct1 = [s[2] for s in segs]
    c1 = [PURPLE if "Champions" in s[0] else BLUE for s in segs]

    bars1 = axes[0, 0].barh(y1_names, x1_vals, color=c1, height=0.55, zorder=3)
    axes[0, 0].set_title("A. Net Revenue Concentration by Segment (£M)")
    axes[0, 0].set_xlabel("Total Net Revenue (£M)")
    axes[0, 0].set_xlim(0, max(x1_vals) * 1.35)
    for b, p in zip(bars1, pct1):
        w = b.get_width()
        axes[0, 0].text(w + 0.3, b.get_y() + b.get_height() / 2,
                        f"£{w:.2f}M ({p}%)", va="center", ha="left",
                        fontsize=8.5, fontweight="bold", color=INK)

    # Panel B: Customer Headcount by Segment (Horizontal barh)
    counts = con.execute("""
        SELECT segment_label, count(*) AS cnt,
               round(count(*)*100.0/(SELECT count(*) FROM dim_rfm_customer), 1) AS pct
        FROM dim_rfm_customer
        GROUP BY segment_label
        ORDER BY cnt ASC
    """).fetchall()
    y2_names = [s[0].split(" (")[0] for s in counts]
    x2_vals = [s[1] for s in counts]
    pct2 = [s[2] for s in counts]
    c2 = [RED if "Lost" in s[0] else GREEN for s in counts]

    bars2 = axes[0, 1].barh(y2_names, x2_vals, color=c2, height=0.55, zorder=3)
    axes[0, 1].set_title("B. Customer Headcount Distribution by Segment")
    axes[0, 1].set_xlabel("Registered Customer Accounts")
    axes[0, 1].set_xlim(0, max(x2_vals) * 1.35)
    for b, p in zip(bars2, pct2):
        w = b.get_width()
        axes[0, 1].text(w + 25, b.get_y() + b.get_height() / 2,
                        f"{int(w):,} ({p}%)", va="center", ha="left",
                        fontsize=8.5, fontweight="bold", color=INK)

    # Panel C: Recency vs Frequency Behavioral Space (With smart non-colliding callouts)
    axes[1, 0].grid(True, color=GRID, linestyle="--", alpha=0.7)
    rf_data = con.execute("""
        SELECT segment_label, avg(recency_days) AS r, avg(frequency) AS f,
               count(*) AS sz, sum(monetary_value) AS rev
        FROM dim_rfm_customer
        GROUP BY segment_label
    """).fetchall()
    for s, r, f, sz, rev in rf_data:
        c = PURPLE if "Champions" in s else (RED if "Lost" in s or "Risk" in s else BLUE)
        axes[1, 0].scatter(r, f, s=sz / 4 + 50, color=c, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3)

    offsets_rf_panel = {
        "Champions (VIP)": (18, 0, PURPLE, "left", "center"),
        "Loyal Customers": (18, 0, BLUE, "left", "center"),
        "Recent New Customers": (15, 0.3, GREEN, "left", "bottom"),
        "Promising / Potential": (15, 0.3, BLUE, "left", "bottom"),
        "At Risk / Need Attention": (0, 1.2, RED, "center", "bottom"),
        "Hibernating / Lost": (0, 1.2, RED, "center", "bottom"),
    }
    for s, r, f, sz, rev in rf_data:
        if s in offsets_rf_panel:
            dx, dy, col, ha, va = offsets_rf_panel[s]
            name = s.split(" (")[0]
            axes[1, 0].text(r + dx, f + dy, name, fontsize=8.5, fontweight="bold", color=col, ha=ha, va=va)

    axes[1, 0].set_title("C. Behavioral Space (Recency vs Frequency)")
    axes[1, 0].set_xlabel("Average Recency (Days since last order)")
    axes[1, 0].set_ylabel("Average Frequency (Orders)")
    axes[1, 0].set_xlim(-15, 520)
    axes[1, 0].set_ylim(-0.5, 19)

    # Panel D: Cohort Retention Heatmap
    axes[1, 1].grid(False)
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
                            color="white" if val > 22 else INK, fontweight="bold")
    fig.colorbar(im, ax=axes[1, 1], label="Retention %", shrink=0.85, pad=0.03)

    fig.suptitle("ONLINE RETAIL II CUSTOMER SEGMENTATION & RETENTION DASHBOARD",
                 fontsize=14, fontweight="bold", y=0.98, color=INK)
    fig.subplots_adjust(top=0.92, bottom=0.08, left=0.18, right=0.96, hspace=0.34, wspace=0.30)
    out0 = FIG / "00_dashboard_preview.png"
    fig.savefig(out0, dpi=160)
    plt.close(fig)
    print(f"Generated {out0}")

    # =========================================================================
    # 2. STANDALONE FIGURE 1: PARETO REVENUE CONCENTRATION (01_rfm_pareto_concentration.png)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(10, 5.5), dpi=160)
    fig1.patch.set_facecolor("white")
    ax1.set_facecolor("white")
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.grid(axis="x", color=GRID, linestyle="--", alpha=0.7)
    ax1.set_axisbelow(True)

    b_p = ax1.barh(y1_names[::-1], x1_vals[::-1], color=[PURPLE if "Champions" in n else BLUE for n in y1_names[::-1]], height=0.55, zorder=3)
    ax1.set_title("Extreme Value Concentration: Champions VIP Generate 69.6% of Net Revenue", fontsize=12, pad=12)
    ax1.set_xlabel("Total Net Revenue (£M)", fontsize=10)
    ax1.set_xlim(0, max(x1_vals) * 1.50)
    for b, p in zip(b_p, pct1[::-1]):
        w = b.get_width()
        ax1.text(w + 0.3, b.get_y() + b.get_height() / 2,
                 f"£{w:.2f}M  ({p}% of revenue)", va="center", ha="left",
                 fontsize=9, fontweight="bold", color=INK)

    fig1.subplots_adjust(left=0.22, right=0.95, top=0.90, bottom=0.12)
    out1 = FIG / "01_rfm_pareto_concentration.png"
    fig1.savefig(out1, dpi=160)
    plt.close(fig1)
    print(f"Generated {out1}")

    # =========================================================================
    # 3. STANDALONE FIGURE 2: COHORT RETENTION MATRIX (02_cohort_retention_heatmap.png)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(11, 5.8), dpi=160)
    fig2.patch.set_facecolor("white")
    ax2.set_facecolor("white")
    im2 = ax2.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=0, vmax=45)
    ax2.set_xticks(range(6))
    ax2.set_xticklabels([f"Month +{i+1}" for i in range(6)], fontsize=9.5)
    ax2.set_yticks(range(len(cohorts_list)))
    ax2.set_yticklabels([f"Cohort {c}" for c in cohorts_list], fontsize=9.5)
    ax2.set_title("The 45-Day Retention Cliff: Month 1 Repeats Drop to 22.5% Before Stabilizing", fontsize=12, pad=12)
    for (i, j), val in np.ndenumerate(matrix):
        if val > 0:
            ax2.text(j, i, f"{val:.1f}%", ha="center", va="center", fontsize=9,
                     color="white" if val > 22 else INK, fontweight="bold")
    fig2.colorbar(im2, ax=ax2, label="Cohort Repeat Purchase Rate (%)", pad=0.03)
    fig2.tight_layout()
    out2 = FIG / "02_cohort_retention_heatmap.png"
    fig2.savefig(out2, dpi=160)
    plt.close(fig2)
    print(f"Generated {out2}")

    # =========================================================================
    # 4. STANDALONE FIGURE 3: BEHAVIORAL RFM SPACE (03_behavioral_rfm_space.png)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(11, 6), dpi=160)
    fig3.patch.set_facecolor("white")
    ax3.set_facecolor("white")
    ax3.spines[["top", "right"]].set_visible(False)
    ax3.grid(True, color=GRID, linestyle="--", alpha=0.7)
    ax3.set_axisbelow(True)

    for s, r, f, sz, rev in rf_data:
        c = PURPLE if "Champions" in s else (RED if "Lost" in s or "Risk" in s else BLUE)
        ax3.scatter(r, f, s=sz / 3 + 60, color=c, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3)

    offsets_rf_stand = {
        "Champions (VIP)": (18, 0, PURPLE, "left", "center"),
        "Loyal Customers": (18, 0, BLUE, "left", "center"),
        "Recent New Customers": (15, 0.3, GREEN, "left", "bottom"),
        "Promising / Potential": (15, 0.3, BLUE, "left", "bottom"),
        "At Risk / Need Attention": (0, 1.2, RED, "center", "bottom"),
        "Hibernating / Lost": (0, 1.2, RED, "center", "bottom"),
    }
    for s, r, f, sz, rev in rf_data:
        if s in offsets_rf_stand:
            dx, dy, col, ha, va = offsets_rf_stand[s]
            name = s.split(" (")[0]
            ax3.text(r + dx, f + dy, f"{name}\n({sz:,} cust, £{rev/1e6:.2f}M)",
                     fontsize=9, fontweight="bold", color=col, ha=ha, va=va)

    ax3.set_title("Customer Lifecycle Space: Recency vs Frequency (Bubble Size = Headcount)", fontsize=12, pad=12)
    ax3.set_xlabel("Recency: Days Since Last Order", fontsize=10)
    ax3.set_ylabel("Frequency: Total Lifetime Orders", fontsize=10)
    ax3.set_xlim(-15, 520)
    ax3.set_ylim(-0.5, 19.5)
    fig3.tight_layout()
    out3 = FIG / "03_behavioral_rfm_space.png"
    fig3.savefig(out3, dpi=160)
    plt.close(fig3)
    print(f"Generated {out3}")


if __name__ == "__main__":
    generate()
