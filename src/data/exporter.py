"""File exporter and format converter for CSV, Excel, and JSON."""
import io
import json
from typing import Optional, Union, Dict, Any
import pandas as pd


class DataExporter:
    """Exports and converts tabular data into CSV, Excel, and JSON formats."""

    @classmethod
    def to_csv_bytes(cls, df: pd.DataFrame, index: bool = False) -> bytes:
        """Export dataframe to CSV byte buffer."""
        buffer = io.StringIO()
        df.to_csv(buffer, index=index)
        return buffer.getvalue().encode("utf-8")

    @classmethod
    def to_excel_bytes(cls, df: pd.DataFrame, sheet_name: str = "Data", index: bool = False) -> bytes:
        """Export dataframe to Excel XLSX byte buffer using openpyxl."""
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name[:31], index=index)
        return buffer.getvalue()

    @classmethod
    def to_json_str(cls, df: pd.DataFrame, orient: str = "records", indent: int = 2) -> str:
        """Export dataframe to formatted JSON string.
        
        Args:
            orient: 'records', 'split', 'index', or 'columns'
        """
        if orient not in ["records", "split", "index", "columns"]:
            orient = "records"
        return df.to_json(orient=orient, date_format="iso", indent=indent)

    @classmethod
    def to_json_bytes(cls, df: pd.DataFrame, orient: str = "records") -> bytes:
        """Export dataframe to JSON bytes."""
        json_str = cls.to_json_str(df, orient=orient)
        return json_str.encode("utf-8")

    @classmethod
    def convert_csv_to_excel(cls, csv_content: Union[str, bytes], sheet_name: str = "Sheet1") -> bytes:
        """Convert raw CSV to Excel bytes."""
        if isinstance(csv_content, bytes):
            buffer_in = io.BytesIO(csv_content)
        else:
            buffer_in = io.StringIO(csv_content)
        df = pd.read_csv(buffer_in)
        return cls.to_excel_bytes(df, sheet_name=sheet_name)

    @classmethod
    def convert_excel_to_csv(cls, excel_bytes: bytes, sheet_name: Optional[str] = None) -> str:
        """Convert Excel sheet bytes to CSV string."""
        buffer_in = io.BytesIO(excel_bytes)
        df = pd.read_excel(buffer_in, sheet_name=sheet_name or 0)
        buffer_out = io.StringIO()
        df.to_csv(buffer_out, index=False)
        return buffer_out.getvalue()
