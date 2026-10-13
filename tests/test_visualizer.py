"""Unit tests for DataVisualizer."""
import pandas as pd
import pytest
from src.tools.visualizer import DataVisualizer


@pytest.fixture
def sample_sales():
    return pd.read_csv("samples/sales_data.csv")


def test_build_bar_chart(sample_sales):
    res = DataVisualizer.build_chart(sample_sales, "bar", x_col="Region", y_col="Revenue")
    assert res.success is True
    assert res.fig is not None
    assert "Region" in res.rationale


def test_build_line_chart(sample_sales):
    res = DataVisualizer.build_chart(sample_sales, "line", x_col="Date", y_col="Revenue")
    assert res.success is True
    assert res.fig is not None


def test_build_pie_chart(sample_sales):
    res = DataVisualizer.build_chart(sample_sales, "pie", x_col="Product_Category", y_col="Profit")
    assert res.success is True


def test_build_scatter_plot(sample_sales):
    res = DataVisualizer.build_chart(sample_sales, "scatter", x_col="Cost", y_col="Revenue")
    assert res.success is True


def test_build_box_plot(sample_sales):
    res = DataVisualizer.build_chart(sample_sales, "box", x_col="Region", y_col="Profit")
    assert res.success is True


def test_build_correlation_heatmap(sample_sales):
    res = DataVisualizer.build_chart(sample_sales, "heatmap")
    assert res.success is True


def test_recommend_best_chart(sample_sales):
    rec = DataVisualizer.recommend_best_chart(sample_sales)
    assert "chart_type" in rec
    assert rec["chart_type"] in ["line", "bar", "scatter"]
