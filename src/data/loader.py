"""Robust file loader for CSV and Excel files."""
import io
import os
from dataclasses import dataclass, field
from typing import List, Optional, Union, BinaryIO
import pandas as pd


@dataclass
class LoadResult:
    """Result of loading a data file."""
    success: bool
    df: Optional[pd.DataFrame] = None
    file_type: str = ""
    file_name: str = ""
    sheets: List[str] = field(default_factory=list)
    active_sheet: Optional[str] = None
    error: Optional[str] = None
    row_count: int = 0
    column_count: int = 0


class DataLoader:
    """Handles loading and parsing of CSV, XLSX, and XLS datasets."""

    SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".xls"]

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        return cls.SUPPORTED_EXTENSIONS

    @classmethod
    def inspect_file(cls, file_source: Union[str, BinaryIO, io.BytesIO], file_name: str = "") -> dict:
        """Inspect file without full parsing (detect format, sheets)."""
        ext = os.path.splitext(file_name)[1].lower() if file_name else ""
        info = {
            "is_excel": ext in [".xlsx", ".xls"],
            "is_csv": ext == ".csv",
            "sheets": [],
            "error": None
        }

        if not info["is_excel"] and not info["is_csv"]:
            info["error"] = f"Unsupported file format '{ext}'. Supported formats: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            return info

        if info["is_excel"]:
            try:
                # Seek to start if file-like
                if hasattr(file_source, "seek"):
                    file_source.seek(0)
                excel_file = pd.ExcelFile(file_source, engine="openpyxl" if ext == ".xlsx" else None)
                info["sheets"] = excel_file.sheet_names
            except Exception as e:
                info["error"] = f"Failed to inspect Excel workbook: {str(e)}"

        return info

    @classmethod
    def load(
        cls,
        file_source: Union[str, BinaryIO, io.BytesIO],
        file_name: str = "",
        sheet_name: Optional[Union[str, int]] = None
    ) -> LoadResult:
        """Load dataframe from CSV or Excel source.
        
        Args:
            file_source: Path string or binary file-like object.
            file_name: Original file name.
            sheet_name: Sheet name or index for Excel workbooks.
        """
        ext = os.path.splitext(file_name)[1].lower() if file_name else ""
        if not ext and isinstance(file_source, str):
            ext = os.path.splitext(file_source)[1].lower()
            file_name = os.path.basename(file_source)

        if ext not in cls.SUPPORTED_EXTENSIONS:
            return LoadResult(
                success=False,
                file_name=file_name,
                error=f"Unsupported file format '{ext}'. Please upload CSV, XLSX, or XLS files."
            )

        # Check if source is a filepath and exists
        if isinstance(file_source, str) and not os.path.exists(file_source):
            return LoadResult(
                success=False,
                file_name=file_name or os.path.basename(file_source),
                error=f"File not found: {file_source}"
            )

        try:
            if ext == ".csv":
                return cls._load_csv(file_source, file_name)
            else:
                return cls._load_excel(file_source, file_name, sheet_name)
        except Exception as e:
            return LoadResult(
                success=False,
                file_name=file_name,
                file_type=ext.lstrip("."),
                error=f"Error reading file '{file_name}': {str(e)}"
            )

    @classmethod
    def _clean_column_names(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names: trim spaces, preserve cases, handle unnamed columns."""
        clean_cols = []
        for i, col in enumerate(df.columns):
            c_str = str(col).strip()
            if not c_str or c_str.lower().startswith("unnamed:"):
                clean_cols.append(f"Column_{i+1}")
            else:
                clean_cols.append(c_str)
        df.columns = clean_cols
        return df

    @classmethod
    def _load_csv(cls, file_source: Union[str, BinaryIO, io.BytesIO], file_name: str) -> LoadResult:
        """Load CSV with automatic encoding fallbacks and delimiter detection."""
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        last_error = None

        for encoding in encodings:
            try:
                if hasattr(file_source, "seek"):
                    file_source.seek(0)
                
                df = pd.read_csv(file_source, encoding=encoding, low_memory=False)
                
                if df.empty and len(df.columns) == 0:
                    return LoadResult(
                        success=False,
                        file_type="csv",
                        file_name=file_name,
                        error="The CSV file is empty and contains no data or headers."
                    )
                
                df = cls._clean_column_names(df)
                return LoadResult(
                    success=True,
                    df=df,
                    file_type="csv",
                    file_name=file_name,
                    sheets=[],
                    active_sheet=None,
                    row_count=len(df),
                    column_count=len(df.columns)
                )
            except UnicodeDecodeError as ue:
                last_error = ue
                continue
            except pd.errors.EmptyDataError:
                return LoadResult(
                    success=False,
                    file_type="csv",
                    file_name=file_name,
                    error="The uploaded CSV file is empty."
                )
            except Exception as e:
                last_error = e
                break

        return LoadResult(
            success=False,
            file_type="csv",
            file_name=file_name,
            error=f"Failed to read CSV: {str(last_error)}"
        )

    @classmethod
    def _load_excel(
        cls,
        file_source: Union[str, BinaryIO, io.BytesIO],
        file_name: str,
        sheet_name: Optional[Union[str, int]] = None
    ) -> LoadResult:
        """Load Excel workbook with worksheet selection and validation."""
        ext = os.path.splitext(file_name)[1].lower() if file_name else ".xlsx"
        engine = "openpyxl" if ext == ".xlsx" else None

        if hasattr(file_source, "seek"):
            file_source.seek(0)

        try:
            excel_file = pd.ExcelFile(file_source, engine=engine)
            sheet_names = excel_file.sheet_names
        except Exception as e:
            return LoadResult(
                success=False,
                file_type=ext.lstrip("."),
                file_name=file_name,
                error=f"Could not open Excel file: {str(e)}"
            )

        if not sheet_names:
            return LoadResult(
                success=False,
                file_type=ext.lstrip("."),
                file_name=file_name,
                error="The Excel file contains no worksheets."
            )

        # Determine target sheet
        target_sheet = sheet_name
        if target_sheet is None:
            target_sheet = sheet_names[0]
        elif isinstance(target_sheet, int):
            if 0 <= target_sheet < len(sheet_names):
                target_sheet = sheet_names[target_sheet]
            else:
                return LoadResult(
                    success=False,
                    file_type=ext.lstrip("."),
                    file_name=file_name,
                    sheets=sheet_names,
                    error=f"Sheet index {sheet_name} is out of bounds. Available sheets: {sheet_names}"
                )
        elif target_sheet not in sheet_names:
            return LoadResult(
                success=False,
                file_type=ext.lstrip("."),
                file_name=file_name,
                sheets=sheet_names,
                error=f"Worksheet '{target_sheet}' not found. Available sheets: {sheet_names}"
            )

        # Read specific sheet
        if hasattr(file_source, "seek"):
            file_source.seek(0)

        df = pd.read_excel(file_source, sheet_name=target_sheet, engine=engine)

        if df.empty and len(df.columns) == 0:
            return LoadResult(
                success=False,
                file_type=ext.lstrip("."),
                file_name=file_name,
                sheets=sheet_names,
                active_sheet=target_sheet,
                error=f"Worksheet '{target_sheet}' is empty and contains no data."
            )

        df = cls._clean_column_names(df)

        return LoadResult(
            success=True,
            df=df,
            file_type=ext.lstrip("."),
            file_name=file_name,
            sheets=sheet_names,
            active_sheet=target_sheet,
            row_count=len(df),
            column_count=len(df.columns)
        )
