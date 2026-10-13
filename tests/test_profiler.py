"""Unit tests for DataProfiler."""
import pandas as pd
import pytest
from src.data.profiler import DataProfiler


def test_profiler_sales_data():
    df = pd.read_csv("samples/sales_data.csv")
    profile = DataProfiler.profile(df)
    
    assert profile.row_count == len(df)
    assert profile.column_count == len(df.columns)
    assert "Revenue" in profile.numerical_columns
    assert "Profit" in profile.numerical_columns
    assert "Region" in profile.categorical_columns
    assert "Date" in profile.datetime_columns
    assert len(profile.plain_english_summary) > 50
    assert "Revenue" in profile.potential_targets or "Profit" in profile.potential_targets


def test_profiler_customer_churn():
    df = pd.read_csv("samples/customer_churn.csv")
    profile = DataProfiler.profile(df)
    
    assert profile.row_count == len(df)
    assert "Churn" in profile.potential_targets
    assert "Monthly_Charges" in profile.numerical_columns
    assert "CustomerID" in profile.id_columns or profile.columns["CustomerID"].is_unique


def test_profiler_empty_dataframe():
    df = pd.DataFrame()
    profile = DataProfiler.profile(df)
    assert profile.row_count == 0
    assert profile.column_count == 0
    assert "empty" in profile.plain_english_summary.lower()


def test_profiler_null_detection():
    df = pd.DataFrame({
        "A": [1, 2, None, 4],
        "B": ["x", None, "y", "z"]
    })
    profile = DataProfiler.profile(df)
    assert profile.missing_cells == 2
    assert profile.missing_pct == 25.0
    assert profile.columns["A"].null_count == 1
