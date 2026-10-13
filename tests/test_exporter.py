"""Unit tests for DataExporter."""
import io
import json
import pandas as pd
from src.data.exporter import DataExporter


def test_export_to_csv_bytes():
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    csv_bytes = DataExporter.to_csv_bytes(df)
    assert isinstance(csv_bytes, bytes)
    assert b"A,B" in csv_bytes


def test_export_to_excel_bytes():
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    excel_bytes = DataExporter.to_excel_bytes(df, sheet_name="TestSheet")
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 100
    
    # Verify openpyxl can read it
    df_read = pd.read_excel(io.BytesIO(excel_bytes), sheet_name="TestSheet")
    assert len(df_read) == 2


def test_export_to_json():
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    json_str = DataExporter.to_json_str(df, orient="records")
    data = json.loads(json_str)
    assert len(data) == 2
    assert data[0]["A"] == 1


def test_convert_csv_to_excel():
    csv_text = "Name,Age\nAlice,30\nBob,25"
    excel_bytes = DataExporter.convert_csv_to_excel(csv_text)
    assert len(excel_bytes) > 100


def test_convert_excel_to_csv():
    df = pd.DataFrame({"City": ["New York", "London"], "Temp": [22, 18]})
    excel_bytes = DataExporter.to_excel_bytes(df)
    csv_str = DataExporter.convert_excel_to_csv(excel_bytes)
    assert "New York" in csv_str
