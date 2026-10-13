"""Unit tests for DataLoader."""
import os
import io
import pandas as pd
import pytest
from src.data.loader import DataLoader, LoadResult


def test_load_valid_csv():
    csv_path = "samples/sales_data.csv"
    res = DataLoader.load(csv_path)
    assert res.success is True
    assert res.file_type == "csv"
    assert res.df is not None
    assert res.row_count > 1000
    assert "Revenue" in res.df.columns
    assert "Profit" in res.df.columns


def test_load_excel_multi_sheet():
    excel_path = "samples/student_performance.xlsx"
    res = DataLoader.load(excel_path)
    assert res.success is True
    assert res.file_type == "xlsx"
    assert len(res.sheets) == 3
    assert "Exam_Scores" in res.sheets
    assert "Attendance_Records" in res.sheets
    assert res.active_sheet == "Exam_Scores"
    assert "Math_Score" in res.df.columns


def test_load_excel_specific_sheet():
    excel_path = "samples/student_performance.xlsx"
    res = DataLoader.load(excel_path, sheet_name="Attendance_Records")
    assert res.success is True
    assert res.active_sheet == "Attendance_Records"
    assert "Attendance_Rate" in res.df.columns


def test_load_nonexistent_file():
    res = DataLoader.load("samples/non_existent.csv")
    assert res.success is False
    assert "File not found" in res.error


def test_load_unsupported_extension():
    res = DataLoader.load("samples/data.parquet", file_name="data.parquet")
    assert res.success is False
    assert "Unsupported file format" in res.error


def test_load_empty_csv():
    empty_csv = io.BytesIO(b"")
    res = DataLoader.load(empty_csv, file_name="empty.csv")
    assert res.success is False
    assert "empty" in res.error.lower()


def test_inspect_file():
    excel_path = "samples/student_performance.xlsx"
    info = DataLoader.inspect_file(excel_path, file_name="student_performance.xlsx")
    assert info["is_excel"] is True
    assert len(info["sheets"]) == 3
