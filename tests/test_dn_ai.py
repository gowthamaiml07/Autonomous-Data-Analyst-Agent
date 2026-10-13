"""Unit tests for DN AI Dual-Mode Conversational Assistant & Data Analyst."""
import pandas as pd
import pytest
from src.agent.graph import DNAIAgent, AnalystAgent
from src.data.profiler import DataProfiler


@pytest.fixture
def sample_sales():
    return pd.read_csv("samples/sales_data.csv")


def test_dn_ai_alias():
    """Verify DNAIAgent alias matches AnalystAgent."""
    assert DNAIAgent is AnalystAgent


def test_mode_a_general_ai_no_dataset():
    """Mode A: General questions without dataset succeed and route to general_ai."""
    res_ai = DNAIAgent.run("Explain artificial intelligence agents.", df=None)
    assert res_ai["success"] is True
    assert res_ai["intent"] == "general_ai"
    assert "agent" in res_ai["response"].lower() or "ai" in res_ai["response"].lower()

    res_gd = DNAIAgent.run("What is gradient descent?", df=None)
    assert res_gd["success"] is True
    assert res_gd["intent"] == "general_ai"
    assert "gradient" in res_gd["response"].lower()

    res_debug = DNAIAgent.run("Help me debug this Python error.", df=None)
    assert res_debug["success"] is True
    assert res_debug["intent"] == "general_ai"
    assert "python" in res_debug["response"].lower() or "error" in res_debug["response"].lower()

    res_db = DNAIAgent.run("What is a database?", df=None)
    assert res_db["success"] is True
    assert res_db["intent"] == "general_ai"
    assert "database" in res_db["response"].lower()


def test_mode_a_when_dataset_is_active(sample_sales):
    """Mode A: General questions when dataset is active do not force data analysis."""
    prof = DataProfiler.profile(sample_sales)
    res = DNAIAgent.run("Explain artificial intelligence agents.", df=sample_sales, profile=prof)
    assert res["success"] is True
    assert res["intent"] == "general_ai"
    assert "agent" in res["response"].lower() or "ai" in res["response"].lower()


def test_data_query_without_dataset_prompts_upload():
    """Data analysis query without active dataset prompts user to upload."""
    res = DNAIAgent.run("What is the total revenue?", df=None)
    assert res["success"] is True
    assert res["intent"] == "needs_dataset"
    assert "upload" in res["response"].lower() or "dataset" in res["response"].lower()


def test_mode_b_analyze_sales_data_overview(sample_sales):
    """Mode B: 'Analyze my sales data' triggers dataset overview with recommendations."""
    prof = DataProfiler.profile(sample_sales)
    res = DNAIAgent.run("Analyze my sales data.", df=sample_sales, profile=prof)
    assert res["success"] is True
    assert res["tool_name"] == "dataset_overview"
    assert res["table"] is not None


def test_mode_b_deterministic_calculations(sample_sales):
    """Mode B: Deterministic calculations compute exact figures."""
    prof = DataProfiler.profile(sample_sales)
    res = DNAIAgent.run("Which product generated the highest profit?", df=sample_sales, profile=prof)
    assert res["success"] is True
    assert res["table"] is not None

    res_growth = DNAIAgent.run("Compare this month with last month.", df=sample_sales, profile=prof)
    assert res_growth["success"] is True
    assert res_growth["tool_name"] == "calculate_growth_rate"


def test_mode_b_dynamic_visualization(sample_sales):
    """Mode B: Chart request creates interactive Plotly figure."""
    prof = DataProfiler.profile(sample_sales)
    res = DNAIAgent.run("Create a chart showing regional performance.", df=sample_sales, profile=prof)
    assert res["success"] is True
    assert res["figure"] is not None


def test_mode_b_forecasting(sample_sales):
    """Mode B: Prediction request validates data and forecasts time-series."""
    prof = DataProfiler.profile(sample_sales)
    res = DNAIAgent.run("Predict next month's revenue.", df=sample_sales, profile=prof)
    assert res["success"] is True
    assert res["tool_name"] == "forecast_timeseries"
    assert res["table"] is not None


def test_conversational_follow_ups(sample_sales):
    """Multi-turn conversational follow-ups resolve seamlessly."""
    prof = DataProfiler.profile(sample_sales)
    chat_history = [
        {"role": "user", "content": "Which product generated the highest profit?"},
        {"role": "assistant", "content": "Smartphone Pro generated the highest profit of $120,000."}
    ]

    # Follow-up: show me a chart
    res_chart = DNAIAgent.run("Show me a chart.", df=sample_sales, profile=prof, chat_history=chat_history)
    assert res_chart["success"] is True
    assert res_chart["figure"] is not None

    # Follow-up: explain it simply
    res_simple = DNAIAgent.run("Explain the result in simple words.", df=sample_sales, profile=prof, chat_history=chat_history)
    assert res_simple["success"] is True

    # Follow-up: why is it performing better?
    res_why = DNAIAgent.run("Why is it performing better?", df=sample_sales, profile=prof, chat_history=chat_history)
    assert res_why["success"] is True


def test_dn_ai_streaming_both_modes(sample_sales):
    """Verify run_stream returns token generator and metadata for both modes."""
    # Mode A stream
    stream_gen, meta_a = DNAIAgent.run_stream("What is gradient descent?", df=None)
    tokens_a = list(stream_gen)
    assert len(tokens_a) > 0
    assert meta_a["success"] is True
    assert meta_a["intent"] == "general_ai"

    # Mode B stream
    prof = DataProfiler.profile(sample_sales)
    stream_gen_b, meta_b = DNAIAgent.run_stream("What is the total revenue?", df=sample_sales, profile=prof)
    tokens_b = list(stream_gen_b)
    assert len(tokens_b) > 0
    assert meta_b["success"] is True
    assert meta_b["tool_name"] == "calculate_metric"
