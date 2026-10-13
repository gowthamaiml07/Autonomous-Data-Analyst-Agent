"""Unit tests for DataCalculator."""
import pandas as pd
import pytest
from src.tools.calculator import DataCalculator, CalculationResult


@pytest.fixture
def sample_sales():
    return pd.read_csv("samples/sales_data.csv")


def test_calculate_metric_sum(sample_sales):
    res = DataCalculator.calculate_metric(sample_sales, "Revenue", "sum")
    assert res.success is True
    assert res.result_value > 0
    assert "SUM(Revenue)" in res.formula


def test_calculate_metric_mean(sample_sales):
    res = DataCalculator.calculate_metric(sample_sales, "Profit", "mean")
    assert res.success is True
    assert res.result_value > 0


def test_calculate_metric_invalid_col(sample_sales):
    res = DataCalculator.calculate_metric(sample_sales, "NonExistent", "sum")
    assert res.success is False
    assert "does not exist" in res.error


def test_group_by_aggregation(sample_sales):
    res = DataCalculator.group_by_aggregation(sample_sales, "Region", "Revenue", "sum")
    assert res.success is True
    assert res.table is not None
    assert len(res.table) == 4
    assert "Region" in res.table.columns
    assert "Revenue" in res.table.columns


def test_top_rankings(sample_sales):
    res = DataCalculator.top_rankings(sample_sales, "Product_Name", "Profit", n=5)
    assert res.success is True
    assert len(res.table) <= 5


def test_growth_rate(sample_sales):
    res = DataCalculator.calculate_growth_rate(sample_sales, "Date", "Revenue", freq="ME")
    assert res.success is True
    assert res.table is not None
    assert "Growth_Pct" in res.table.columns


def test_profit_margin(sample_sales):
    res = DataCalculator.calculate_profit_margin(sample_sales, revenue_col="Revenue", profit_col="Profit")
    assert res.success is True
    assert 0 < res.result_value < 100
    assert "%" in res.formatted_value


def test_calculate_correlations(sample_sales):
    res = DataCalculator.calculate_correlations(sample_sales, columns=["Revenue", "Cost", "Profit"])
    assert res.success is True
    assert res.table is not None


def test_detect_outliers(sample_sales):
    res = DataCalculator.detect_outliers(sample_sales, "Revenue", method="iqr")
    assert res.success is True
    assert isinstance(res.result_value, int)
