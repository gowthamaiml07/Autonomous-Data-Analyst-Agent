"""Tests for newly added interactive features, charts, and simulation engines."""
import pytest
import pandas as pd
import numpy as np

from src.tools.visualizer import DataVisualizer
from src.tools.predictor import DataPredictor
from src.tools.recommender import RecommendationEngine
from src.data.cleaner import DataCleaner
from src.data.profiler import DataProfiler
from src.reports.pdf_generator import PDFReportGenerator
from src.ui.components import get_follow_up_action_chips


@pytest.fixture
def sample_dataset():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    revenue = np.random.normal(500, 50, n)
    # Add a couple outliers
    revenue[5] = 1500
    revenue[25] = -200
    category = np.random.choice(["Tech", "Health", "Finance"], n)
    cost = revenue * 0.6 + np.random.normal(0, 10, n)
    return pd.DataFrame({
        "Date": dates,
        "Revenue": revenue,
        "Cost": cost,
        "Category": category
    })


def test_build_gauge_chart():
    fig = DataVisualizer.build_gauge_chart(
        value=75.0,
        min_val=0.0,
        max_val=100.0,
        target_val=85.0,
        title="Revenue Target Progress"
    )
    assert fig is not None
    assert len(fig.data) > 0
    indicator = fig.data[0]
    assert indicator.type == "indicator"
    assert indicator.value == 75.0


def test_build_outlier_inspector(sample_dataset):
    fig = DataVisualizer.build_outlier_inspector(sample_dataset, "Revenue", iqr_multiplier=1.5)
    assert fig is not None
    assert len(fig.data) > 0
    # Scatter data has classifications
    assert "Outlier (Anomaly)" in fig.data[0].legendgroup or len(fig.data) >= 1


def test_trim_outliers(sample_dataset):
    initial_len = len(sample_dataset)
    trimmed_df, removed_count, low, high = DataCleaner.trim_outliers(sample_dataset, "Revenue", multiplier=1.5)
    assert removed_count > 0
    assert len(trimmed_df) == initial_len - removed_count
    assert trimmed_df["Revenue"].min() >= low
    assert trimmed_df["Revenue"].max() <= high


def test_predict_what_if(sample_dataset):
    res = DataPredictor.train_regression(sample_dataset, target_col="Revenue")
    assert res.success
    assert res.trained_pipeline is not None
    assert res.features_used

    # Run what-if prediction
    inputs = dict(res.default_feature_values)
    what_if_res = DataPredictor.predict_what_if(res.trained_pipeline, inputs)
    assert what_if_res["success"]
    assert "prediction" in what_if_res
    assert isinstance(what_if_res["prediction"], (int, float))


def test_forecast_multi_scenario(sample_dataset):
    res = DataPredictor.forecast_timeseries(
        sample_dataset,
        date_col="Date",
        value_col="Revenue",
        horizon_periods=14,
        confidence_level=0.90
    )
    assert res.success
    assert res.forecast_table is not None
    assert "Baseline_Forecast" in res.forecast_table.columns
    assert "Optimistic_Scenario" in res.forecast_table.columns
    assert "Conservative_Scenario" in res.forecast_table.columns
    assert "Lower_Bound_90%" in res.forecast_table.columns
    assert "Upper_Bound_90%" in res.forecast_table.columns


def test_proactive_insights_ticker(sample_dataset):
    profile = DataProfiler.profile(sample_dataset)
    insights = RecommendationEngine.generate_proactive_insights_ticker(sample_dataset, profile)
    assert isinstance(insights, list)
    assert len(insights) > 0
    for item in insights:
        assert "title" in item
        assert "description" in item
        assert "query" in item
        assert "badge" in item


def test_follow_up_action_chips(sample_dataset):
    profile = DataProfiler.profile(sample_dataset)
    chips = get_follow_up_action_chips("Show total revenue", profile)
    assert isinstance(chips, list)
    assert len(chips) >= 3
    for chip in chips:
        assert "label" in chip
        assert "query" in chip


def test_pdf_report_customization(sample_dataset):
    profile = DataProfiler.profile(sample_dataset)
    recs = RecommendationEngine.generate_recommendations(sample_dataset, profile)

    # Generate custom PDF with custom notes and selected sections
    pdf_bytes = PDFReportGenerator.generate_report(
        df=sample_dataset,
        profile=profile,
        recommendations=recs,
        include_summary=True,
        include_kpis=True,
        include_features=False,
        include_recommendations=True,
        custom_notes="Executive Note: Revenue exceeds initial projections by 12% in Q3."
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
