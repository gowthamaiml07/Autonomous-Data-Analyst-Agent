"""Unit tests for true streaming, multi-turn context memory, and security protections."""
import os
import pandas as pd
import pytest
from src.agent.graph import AnalystAgent
from src.agent.llm import LLMClient
from src.data.profiler import DataProfiler


@pytest.fixture
def sample_sales():
    return pd.read_csv("samples/sales_data.csv")


def test_agent_run_stream(sample_sales):
    """Test that run_stream yields text chunks and returns valid metadata."""
    prof = DataProfiler.profile(sample_sales)
    stream_iter, meta = AnalystAgent.run_stream(
        query="What is the total revenue?",
        df=sample_sales,
        profile=prof
    )
    assert meta["success"] is True
    assert meta["tool_name"] == "calculate_metric"

    # Consume stream chunks
    tokens = list(stream_iter)
    assert len(tokens) > 0
    full_text = "".join(tokens)
    assert "Revenue" in full_text or "total" in full_text.lower()


def test_multi_turn_context_resolution(sample_sales):
    """Test that pronouns like 'it' resolve to the prior turn's entity/metric."""
    prof = DataProfiler.profile(sample_sales)
    
    # Turn 1
    chat_history = [
        {"role": "user", "content": "Which product has the highest profit?"},
        {"role": "assistant", "content": "Smartphone Pro generated the highest profit."}
    ]

    # Turn 2: Follow-up referencing "it"
    res = AnalystAgent.run(
        query="Show a chart of it",
        df=sample_sales,
        profile=prof,
        chat_history=chat_history
    )
    assert res["success"] is True
    assert res["figure"] is not None


def test_follow_up_compare_with_last_year(sample_sales):
    """Test follow-up 'compare it with last year' resolves to growth rate."""
    prof = DataProfiler.profile(sample_sales)
    chat_history = [
        {"role": "user", "content": "What is the total revenue?"},
        {"role": "assistant", "content": "Total revenue is $5,000,000."}
    ]

    res = AnalystAgent.run(
        query="Compare it with last year",
        df=sample_sales,
        profile=prof,
        chat_history=chat_history
    )
    assert res["success"] is True
    assert res["tool_name"] == "calculate_growth_rate"
    assert res["table"] is not None


def test_security_secrets_file_and_gitignore():
    """Verify that secrets are protected and example files exist."""
    assert os.path.exists(".gitignore")
    with open(".gitignore", "r") as f:
        gitignore_content = f.read()
    assert ".env" in gitignore_content
    assert "secrets.toml" in gitignore_content

    assert os.path.exists(".streamlit/secrets.toml.example")
    with open(".streamlit/secrets.toml.example", "r") as f:
        example_content = f.read()
    assert "gsk_your_groq_api_key_here" in example_content
