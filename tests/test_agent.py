"""Unit tests for LangGraph AnalystAgent workflow."""
import pandas as pd
import pytest
from src.agent.graph import AnalystAgent
from src.data.profiler import DataProfiler


@pytest.fixture
def sample_sales():
    return pd.read_csv("samples/sales_data.csv")


def test_agent_total_revenue(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("What is the total revenue?", sample_sales, profile=prof)
    assert res["success"] is True
    assert "Revenue" in res["response"] or "sum" in res["response"].lower()
    assert res["tool_name"] == "calculate_metric"


def test_agent_top_products(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("Which product has the highest profit?", sample_sales, profile=prof)
    assert res["success"] is True
    assert res["table"] is not None


def test_agent_growth_rate(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("Calculate month-over-month growth of Revenue", sample_sales, profile=prof)
    assert res["success"] is True
    assert res["table"] is not None


def test_agent_create_graph(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("Create a graph of revenue by region", sample_sales, profile=prof)
    assert res["success"] is True
    assert res["figure"] is not None


def test_agent_forecast(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("Forecast sales for the next 14 days", sample_sales, profile=prof)
    assert res["success"] is True
    assert res["table"] is not None
    assert len(res["table"]) == 14


def test_agent_recommendations(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("Recommend actions to improve profitability", sample_sales, profile=prof)
    assert res["success"] is True
    assert "recommend" in res["response"].lower() or "action" in res["response"].lower()


def test_agent_outlier_detection(sample_sales):
    prof = DataProfiler.profile(sample_sales)
    res = AnalystAgent.run("Identify outliers in Revenue", sample_sales, profile=prof)
    assert res["success"] is True
    assert "outlier" in res["response"].lower()
