"""
Phase 3 validation — data_tools.py functions tested against the real dataset.
Run with: pytest tests/test_data_tools.py -v
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "hde_overland_sales_2022_2024.csv"


@pytest.fixture
def raw_df():
    from tools.data_tools import load_dataframe
    return load_dataframe(SAMPLE_CSV)


@pytest.fixture
def clean_df(raw_df):
    from tools.data_tools import clean_dataframe
    return clean_dataframe(raw_df)


def test_load_dataframe(raw_df):
    assert raw_df is not None
    assert len(raw_df) == 3500
    assert "transaction_id" in raw_df.columns


def test_clean_dataframe(clean_df):
    for col in clean_df.columns:
        assert col == col.lower()
        assert " " not in col
    assert len(clean_df) > 0


def test_profile_dataframe(clean_df):
    from tools.data_tools import profile_dataframe
    profile = profile_dataframe(clean_df)
    assert "shape" in profile
    assert profile["shape"]["rows"] == 3500
    assert "data_health_score" in profile
    assert 0 <= profile["data_health_score"] <= 100
    assert "numeric_summary" in profile
    assert "categorical_summary" in profile


def test_data_health_score_is_high(clean_df):
    from tools.data_tools import profile_dataframe
    profile = profile_dataframe(clean_df)
    assert profile["data_health_score"] >= 70


def test_revenue_by_dimension(clean_df):
    from tools.data_tools import get_revenue_by_dimension
    result = get_revenue_by_dimension(clean_df, "build_category")
    assert len(result) > 0
    assert "baja_prerunner" in result
    assert all(v > 0 for v in result.values())


def test_trend_by_year(clean_df):
    from tools.data_tools import get_trend_by_period
    result = get_trend_by_period(clean_df, "year")
    assert "2022" in result
    assert "2023" in result
    assert "2024" in result


def test_baja_growth_rates_increasing(clean_df):
    from tools.data_tools import get_growth_rates
    growth = get_growth_rates(clean_df, "build_category")
    baja = growth.get("baja_prerunner", {})
    assert float(baja.get("2022", 0)) > 0
    assert float(baja.get("2024", 0)) > float(baja.get("2022", 0))


def test_top_performers(clean_df):
    from tools.data_tools import get_top_performers
    result = get_top_performers(clean_df, "vehicle_platform", n=5)
    assert len(result) == 5


def test_missing_column_returns_empty(clean_df):
    from tools.data_tools import get_revenue_by_dimension
    result = get_revenue_by_dimension(clean_df, "nonexistent_column")
    assert result == {}


def test_data_ingestion_error_on_bad_file():
    from tools.data_tools import load_dataframe
    from tools.exceptions import DataIngestionError
    with pytest.raises(DataIngestionError):
        load_dataframe("/nonexistent/path/file.csv")