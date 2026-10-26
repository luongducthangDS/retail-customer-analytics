"""Data quality and business rule tests for Online Retail analytics model."""
from pathlib import Path
import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    c.execute("SET enable_progress_bar = false")
    c.execute(f"SET file_search_path = '{ROOT}'")
    c.execute((ROOT / "sql" / "00_model.sql").read_text())
    c.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())
    return c


def one(con, sql):
    return con.execute(sql).fetchone()[0]


def test_transactions_exist_and_clean(con):
    total = one(con, "SELECT count(*) FROM fct_transactions")
    assert total > 700_000, f"Expected >700k clean transactions, got {total}"


def test_no_null_customer_ids(con):
    assert one(con, "SELECT count(*) FROM fct_transactions WHERE customer_id IS NULL") == 0


def test_rfm_customers_unique_keys(con):
    assert one(con, "SELECT count(*) - count(DISTINCT customer_id) FROM dim_rfm_customer") == 0


def test_rfm_scores_in_range(con):
    bad = one(con, """
        SELECT count(*) FROM dim_rfm_customer
        WHERE r_score NOT BETWEEN 1 AND 5
           OR f_score NOT BETWEEN 1 AND 5
           OR m_score NOT BETWEEN 1 AND 5
    """)
    assert bad == 0


def test_powerbi_dimensions_unique_keys(con):
    dims = [
        ("pbi_dim_customer", "customer_id"),
        ("pbi_dim_product", "stock_code"),
        ("pbi_dim_date", "date"),
        ("pbi_dim_cohort", "cohort_month"),
    ]
    for table, pk in dims:
        dups = one(con, f"SELECT count(*) - count(DISTINCT {pk}) FROM {table}")
        assert dups == 0, f"Duplicate keys in {table} on {pk}"


def test_referential_integrity(con):
    assert one(con, """
        SELECT count(*) FROM pbi_fact_transactions t
        LEFT JOIN pbi_dim_customer c USING (customer_id)
        WHERE c.customer_id IS NULL
    """) == 0

    assert one(con, """
        SELECT count(*) FROM pbi_fact_transactions t
        LEFT JOIN pbi_dim_date d ON t.invoice_day = d.date
        WHERE d.date IS NULL
    """) == 0
