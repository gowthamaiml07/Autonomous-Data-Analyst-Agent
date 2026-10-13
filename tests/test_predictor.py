"""Unit tests for DataPredictor."""
import pandas as pd
import pytest
from src.tools.predictor import DataPredictor


def test_regression_pipeline():
    df = pd.read_csv("samples/sales_data.csv")
    res = DataPredictor.train_regression(df, target_col="Revenue", model_type="random_forest")
    assert res.success is True
    assert "R2" in res.metrics
    assert "MAE" in res.metrics
    assert res.test_comparison_table is not None
    assert len(res.limitations) > 0


def test_classification_pipeline():
    df = pd.read_csv("samples/customer_churn.csv")
    res = DataPredictor.train_classification(df, target_col="Churn", model_type="logistic")
    assert res.success is True
    assert "Accuracy" in res.metrics
    assert "F1" in res.metrics
    assert res.comparison_chart is not None


def test_timeseries_forecast():
    df = pd.read_csv("samples/sales_data.csv")
    res = DataPredictor.forecast_timeseries(df, date_col="Date", value_col="Revenue", horizon_periods=14)
    assert res.success is True
    assert res.forecast_table is not None
    assert len(res.forecast_table) == 14
    assert "Forecasted" in res.forecast_table.columns
    assert "Upper_Bound_95%" in res.forecast_table.columns
