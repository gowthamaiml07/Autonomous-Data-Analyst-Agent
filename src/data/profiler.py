"""Deterministic Data Profiler for comprehensive dataset analysis."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


@dataclass
class ColumnProfile:
    """Detailed profile for a single column."""
    name: str
    dtype: str
    inferred_type: str  # 'numerical', 'categorical', 'datetime', 'boolean', 'id'
    null_count: int
    null_pct: float
    unique_count: int
    is_unique: bool
    sample_values: List[Any] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfileReport:
    """Complete dataset profile report."""
    row_count: int
    column_count: int
    total_cells: int
    missing_cells: int
    missing_pct: float
    duplicate_rows: int
    duplicate_pct: float
    memory_usage_mb: float
    columns: Dict[str, ColumnProfile] = field(default_factory=dict)
    numerical_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    datetime_columns: List[str] = field(default_factory=list)
    boolean_columns: List[str] = field(default_factory=list)
    id_columns: List[str] = field(default_factory=list)
    potential_targets: List[str] = field(default_factory=list)
    plain_english_summary: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "missing_cells": self.missing_cells,
            "missing_pct": self.missing_pct,
            "duplicate_rows": self.duplicate_rows,
            "duplicate_pct": self.duplicate_pct,
            "memory_usage_mb": self.memory_usage_mb,
            "numerical_columns": self.numerical_columns,
            "categorical_columns": self.categorical_columns,
            "datetime_columns": self.datetime_columns,
            "boolean_columns": self.boolean_columns,
            "id_columns": self.id_columns,
            "potential_targets": self.potential_targets,
            "warnings": self.warnings,
            "summary": self.plain_english_summary
        }


class DataProfiler:
    """Analyzes a pandas DataFrame deterministically without LLM hallucinations."""

    TARGET_KEYWORDS = [
        "churn", "target", "label", "revenue", "profit", "sales", "price",
        "score", "status", "class", "outcome", "survived", "fraud", "default",
        "conversion", "growth", "rating", "units_sold"
    ]

    @classmethod
    def profile(cls, df: pd.DataFrame) -> ProfileReport:
        """Generate comprehensive profile report for DataFrame."""
        if df is None or df.empty:
            return ProfileReport(
                row_count=0,
                column_count=0,
                total_cells=0,
                missing_cells=0,
                missing_pct=0.0,
                duplicate_rows=0,
                duplicate_pct=0.0,
                memory_usage_mb=0.0,
                plain_english_summary="The dataset is empty."
            )

        row_count = len(df)
        col_count = len(df.columns)
        total_cells = row_count * col_count
        missing_cells = int(df.isna().sum().sum())
        missing_pct = round((missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

        dup_rows = int(df.duplicated().sum())
        dup_pct = round((dup_rows / row_count * 100), 2) if row_count > 0 else 0.0
        mem_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        columns_profile = {}
        num_cols = []
        cat_cols = []
        dt_cols = []
        bool_cols = []
        id_cols = []
        warnings = []

        for col in df.columns:
            series = df[col]
            inferred = cls._infer_column_type(series, col, row_count)
            col_prof = cls._profile_single_column(series, col, inferred, row_count)
            columns_profile[col] = col_prof

            if inferred == "numerical":
                num_cols.append(col)
            elif inferred == "categorical":
                cat_cols.append(col)
            elif inferred == "datetime":
                dt_cols.append(col)
            elif inferred == "boolean":
                bool_cols.append(col)
            elif inferred == "id":
                id_cols.append(col)

            # Check column warnings
            if col_prof.null_pct > 30.0:
                warnings.append(f"Column '{col}' has high missingness ({col_prof.null_pct}% nulls).")
            if col_prof.unique_count == 1:
                warnings.append(f"Column '{col}' has constant value across all rows.")
            elif col_prof.unique_count == row_count and inferred != "id" and row_count > 50:
                warnings.append(f"Column '{col}' has 100% unique values (potential identifier).")

        if dup_rows > 0:
            warnings.append(f"Dataset contains {dup_rows:,} duplicate rows ({dup_pct}%).")

        potential_targets = cls._detect_potential_targets(df, num_cols, cat_cols)

        # Generate summary narrative
        summary = cls._generate_narrative_summary(
            row_count, col_count, num_cols, cat_cols, dt_cols,
            missing_cells, missing_pct, dup_rows, columns_profile, potential_targets
        )

        return ProfileReport(
            row_count=row_count,
            column_count=col_count,
            total_cells=total_cells,
            missing_cells=missing_cells,
            missing_pct=missing_pct,
            duplicate_rows=dup_rows,
            duplicate_pct=dup_pct,
            memory_usage_mb=mem_mb,
            columns=columns_profile,
            numerical_columns=num_cols,
            categorical_columns=cat_cols,
            datetime_columns=dt_cols,
            boolean_columns=bool_cols,
            id_columns=id_cols,
            potential_targets=potential_targets,
            plain_english_summary=summary,
            warnings=warnings
        )

    @classmethod
    def _infer_column_type(cls, series: pd.Series, col_name: str, row_count: int) -> str:
        """Infer business and functional column type."""
        col_lower = str(col_name).lower()
        non_nulls = series.dropna()

        # Check boolean
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        if len(non_nulls) > 0 and set(non_nulls.unique()).issubset({True, False, 0, 1, "0", "1", "True", "False"}):
            if len(non_nulls.unique()) <= 2 and col_lower.startswith(("is_", "has_", "flag_")):
                return "boolean"

        # Check datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            if "date" in col_lower or "time" in col_lower or "timestamp" in col_lower or "dt" in col_lower:
                # Try sample parse
                sample = non_nulls.head(20)
                if len(sample) > 0:
                    try:
                        pd.to_datetime(sample, errors="raise")
                        return "datetime"
                    except Exception:
                        pass

        # Check numerical
        if pd.api.types.is_numeric_dtype(series):
            # Check if it behaves as an ID (strictly increasing integer or 100% unique integer)
            if ("id" in col_lower or "key" in col_lower or "code" in col_lower) and series.nunique() == row_count:
                return "id"
            return "numerical"

        # Check string / object ID
        if ("id" in col_lower or "uuid" in col_lower or "key" in col_lower or "code" in col_lower):
            if series.nunique() >= row_count * 0.90:
                return "id"

        return "categorical"

    @classmethod
    def _profile_single_column(cls, series: pd.Series, col_name: str, inferred: str, row_count: int) -> ColumnProfile:
        """Compute statistics for one column based on its inferred type."""
        null_count = int(series.isna().sum())
        null_pct = round((null_count / row_count * 100), 2) if row_count > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        is_unique = (unique_count == row_count and null_count == 0)
        
        sample_vals = series.dropna().head(5).tolist()

        stats: Dict[str, Any] = {}
        if inferred == "numerical":
            num_series = pd.to_numeric(series, errors="coerce").dropna()
            if not num_series.empty:
                stats = {
                    "min": float(num_series.min()),
                    "max": float(num_series.max()),
                    "mean": round(float(num_series.mean()), 3),
                    "median": round(float(num_series.median()), 3),
                    "std": round(float(num_series.std()), 3) if len(num_series) > 1 else 0.0,
                    "q25": round(float(num_series.quantile(0.25)), 3),
                    "q75": round(float(num_series.quantile(0.75)), 3),
                    "zero_count": int((num_series == 0).sum())
                }
        elif inferred in ["categorical", "boolean", "id"]:
            non_null = series.dropna()
            if not non_null.empty:
                top_counts = non_null.value_counts().head(5).to_dict()
                stats = {
                    "mode": str(non_null.mode()[0]) if len(non_null.mode()) > 0 else None,
                    "top_frequencies": {str(k): int(v) for k, v in top_counts.items()}
                }
        elif inferred == "datetime":
            dt_series = pd.to_datetime(series, errors="coerce").dropna()
            if not dt_series.empty:
                stats = {
                    "min_date": str(dt_series.min()),
                    "max_date": str(dt_series.max()),
                    "timespan_days": (dt_series.max() - dt_series.min()).days
                }

        return ColumnProfile(
            name=col_name,
            dtype=str(series.dtype),
            inferred_type=inferred,
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            is_unique=is_unique,
            sample_values=sample_vals,
            stats=stats
        )

    @classmethod
    def _detect_potential_targets(
        cls,
        df: pd.DataFrame,
        num_cols: List[str],
        cat_cols: List[str]
    ) -> List[str]:
        """Identify candidate columns for prediction and forecasting."""
        candidates = []
        all_cols = list(df.columns)

        for col in all_cols:
            col_clean = str(col).lower().replace(" ", "_").replace("-", "_")
            for kw in cls.TARGET_KEYWORDS:
                if kw in col_clean:
                    candidates.append(col)
                    break

        # Fallbacks if none matched
        if not candidates and num_cols:
            candidates.append(num_cols[-1])  # often the last numerical column is a target
        elif not candidates and cat_cols:
            candidates.append(cat_cols[-1])

        return list(dict.fromkeys(candidates))

    @classmethod
    def _generate_narrative_summary(
        cls,
        row_count: int,
        col_count: int,
        num_cols: List[str],
        cat_cols: List[str],
        dt_cols: List[str],
        missing_cells: int,
        missing_pct: float,
        dup_rows: int,
        columns_profile: Dict[str, ColumnProfile],
        potential_targets: List[str]
    ) -> str:
        """Create a clear plain-English dataset narrative."""
        sentences = [
            f"The dataset contains **{row_count:,} rows** and **{col_count} columns**."
        ]

        # Column breakdown
        comp = []
        if num_cols:
            comp.append(f"{len(num_cols)} numerical")
        if cat_cols:
            comp.append(f"{len(cat_cols)} categorical")
        if dt_cols:
            comp.append(f"{len(dt_cols)} temporal/date")
        if comp:
            sentences.append(f"It includes {', '.join(comp)} features.")

        # Data cleanliness
        if missing_cells == 0:
            sentences.append("The data is completely complete with **no missing values** (100% data density).")
        else:
            sentences.append(
                f"There are **{missing_cells:,} missing values** ({missing_pct}% of total cells) across the dataset."
            )

        if dup_rows > 0:
            sentences.append(f"Detected **{dup_rows:,} duplicate rows** that may require deduplication.")
        else:
            sentences.append("No exact duplicate records were found.")

        # Date range note
        if dt_cols:
            primary_dt = dt_cols[0]
            dt_stats = columns_profile[primary_dt].stats
            if "min_date" in dt_stats and "max_date" in dt_stats:
                min_d = str(dt_stats['min_date']).split()[0]
                max_d = str(dt_stats['max_date']).split()[0]
                sentences.append(
                    f"Temporal coverage ranges from **{min_d}** to **{max_d}** based on `{primary_dt}`."
                )

        # Potential target
        if potential_targets:
            sentences.append(
                f"Key candidate target metrics for prediction and KPI analysis include: {', '.join([f'`{t}`' for t in potential_targets[:3]])}."
            )

        return " ".join(sentences)
