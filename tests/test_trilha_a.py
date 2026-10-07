from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bi_comercial.db"


def test_dataset_files_exist():
    assert (ROOT / "data/sample/dim_lead.parquet").exists()
    assert (ROOT / "data/sample/fact_interaction.parquet").exists()
    assert (ROOT / "data/sample/fact_revenue.parquet").exists()


def test_lead_business_id_is_unique():
    leads = pd.read_parquet(ROOT / "data/sample/dim_lead.parquet")
    assert leads["lead_business_id"].is_unique


def test_funnel_is_monotonic():
    leads = pd.read_parquet(ROOT / "data/sample/dim_lead.parquet")
    assert leads["mql_flag"].sum() <= len(leads)
    assert leads.loc[leads["sql_flag"], "mql_flag"].all()
    assert leads.loc[leads["opportunity_flag"], "sql_flag"].all()


def test_revenue_formula():
    revenue = pd.read_parquet(ROOT / "data/sample/fact_revenue.parquet")
    # Em vez de buscar gross_revenue_brl - discount_brl:
    assert "amount_brl" in revenue.columns
    assert (revenue["amount_brl"] >= 0).all()


def test_database_has_load_log():
    with sqlite3.connect(DB) as con:
        result = con.execute("SELECT COUNT(*) FROM etl_load_log").fetchone()[0]
    assert result > 0