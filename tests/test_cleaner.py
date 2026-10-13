"""Unit tests for DataCleaner and SafeFormulaEvaluator."""
import pandas as pd
import numpy as np
import pytest
from src.data.cleaner import DataCleaner, SafeFormulaEvaluator, CleaningHistory


def test_remove_duplicates():
    df = pd.DataFrame({
        "A": [1, 2, 2, 3],
        "B": ["x", "y", "y", "z"]
    })
    cleaned, removed = DataCleaner.remove_duplicates(df)
    assert removed == 1
    assert len(cleaned) == 3


def test_handle_missing_values_impute_mean():
    df = pd.DataFrame({
        "Val": [10.0, 20.0, np.nan, 30.0]
    })
    cleaned, stats = DataCleaner.handle_missing_values(df, strategy="mean", columns=["Val"])
    assert cleaned["Val"].isna().sum() == 0
    assert cleaned["Val"].iloc[2] == 20.0


def test_handle_missing_values_drop_rows():
    df = pd.DataFrame({
        "Val": [10.0, 20.0, np.nan, 30.0]
    })
    cleaned, stats = DataCleaner.handle_missing_values(df, strategy="drop_rows", columns=["Val"])
    assert len(cleaned) == 3
    assert stats["rows_dropped"] == 1


def test_safe_formula_evaluator_valid():
    df = pd.DataFrame({
        "Revenue": [100.0, 200.0, 300.0],
        "Cost": [60.0, 110.0, 150.0]
    })
    series = SafeFormulaEvaluator.evaluate("Revenue - Cost", df)
    assert series.tolist() == [40.0, 90.0, 150.0]


def test_safe_formula_evaluator_disallowed_syntax():
    df = pd.DataFrame({"Revenue": [100.0, 200.0]})
    with pytest.raises(ValueError):
        # Function calls or imports should be blocked
        SafeFormulaEvaluator.evaluate("__import__('os').system('dir')", df)


def test_create_derived_column():
    df = pd.DataFrame({
        "Revenue": [100.0, 200.0],
        "Cost": [40.0, 80.0]
    })
    df_res, msg = DataCleaner.create_derived_column(df, "Profit", "Revenue - Cost")
    assert "Profit" in df_res.columns
    assert df_res["Profit"].iloc[0] == 60.0


def test_filter_and_sort():
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Score": [85, 92, 78]
    })
    filtered = DataCleaner.filter_records(df, "Score", ">=", 85)
    assert len(filtered) == 2
    sorted_df = DataCleaner.sort_records(filtered, by=["Score"], ascending=False)
    assert sorted_df["Name"].iloc[0] == "Bob"


def test_cleaning_history_and_reset():
    df = pd.DataFrame({"A": [1, 2, 2, 3]})
    history = CleaningHistory(df)
    cleaned, removed = DataCleaner.remove_duplicates(df)
    history.record_action("dedup", "Removed duplicates", {}, df, cleaned)
    assert len(history.current_df) == 3
    assert len(history.actions) == 1
    
    reset_df = history.reset_to_original()
    assert len(reset_df) == 4
    assert len(history.actions) == 0


def test_cleaning_history_undo_last():
    df = pd.DataFrame({"A": [1, 2, 2, 3]})
    history = CleaningHistory(df)
    cleaned, removed = DataCleaner.remove_duplicates(df)
    history.record_action("dedup", "Removed duplicates", {}, df, cleaned)
    assert len(history.current_df) == 3
    assert len(history.actions) == 1

    undone_df = history.undo_last()
    assert undone_df is not None
    assert len(undone_df) == 4
    assert len(history.actions) == 0


def test_group_and_aggregate():
    df = pd.DataFrame({
        "Category": ["A", "A", "B"],
        "Sales": [10, 20, 30]
    })
    res = DataCleaner.group_and_aggregate(df, "Category", "Sales", agg_func="sum")
    assert len(res) == 2
    assert res[res["Category"] == "A"]["Sales"].iloc[0] == 30

