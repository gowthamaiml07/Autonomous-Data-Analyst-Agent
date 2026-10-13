"""Deterministic analytical calculator for metrics, aggregations, growth rates, and statistical tests."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd


@dataclass
class CalculationResult:
    """Structured result of a calculation."""
    success: bool
    operation: str
    result_value: Any
    formatted_value: str
    formula: str
    explanation: str
    table: Optional[pd.DataFrame] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class DataCalculator:
    """Provides validated, deterministic calculations over pandas DataFrames."""

    @classmethod
    def calculate_metric(
        cls,
        df: pd.DataFrame,
        column: str,
        operation: str  # 'sum', 'mean', 'median', 'min', 'max', 'count', 'std', 'variance'
    ) -> CalculationResult:
        """Calculate single scalar aggregation on a column with validation."""
        if column not in df.columns:
            return CalculationResult(
                success=False,
                operation=operation,
                result_value=None,
                formatted_value="Error",
                formula="",
                explanation="",
                error=f"Column '{column}' does not exist in dataset."
            )

        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            return CalculationResult(
                success=False,
                operation=operation,
                result_value=None,
                formatted_value="N/A",
                formula="",
                explanation=f"Column '{column}' has no valid numerical values.",
                error=f"Column '{column}' has no valid numerical values."
            )

        op = operation.lower().strip()
        val = None
        formula = ""
        exp = ""

        if op == "sum":
            val = float(series.sum())
            formula = f"SUM({column})"
            exp = f"The sum of '{column}' across {len(series):,} valid records is {val:,.2f}."
        elif op in ["mean", "average"]:
            val = float(series.mean())
            formula = f"MEAN({column}) = SUM({column}) / COUNT({column})"
            exp = f"The average value of '{column}' is {val:,.2f}."
        elif op == "median":
            val = float(series.median())
            formula = f"MEDIAN({column})"
            exp = f"The 50th percentile (median) of '{column}' is {val:,.2f}."
        elif op == "min":
            val = float(series.min())
            formula = f"MIN({column})"
            exp = f"The minimum value of '{column}' is {val:,.2f}."
        elif op == "max":
            val = float(series.max())
            formula = f"MAX({column})"
            exp = f"The maximum value of '{column}' is {val:,.2f}."
        elif op == "count":
            val = int(len(series))
            formula = f"COUNT_NON_NULL({column})"
            exp = f"There are {val:,} non-null records in '{column}'."
        elif op == "std":
            val = float(series.std()) if len(series) > 1 else 0.0
            formula = f"STDEV({column})"
            exp = f"The standard deviation of '{column}' is {val:,.2f}."
        else:
            return CalculationResult(
                success=False,
                operation=operation,
                result_value=None,
                formatted_value="Error",
                formula="",
                explanation="",
                error=f"Unsupported operation '{operation}'."
            )

        formatted = f"{val:,.2f}" if isinstance(val, (int, float)) and op != "count" else f"{val:,}"
        return CalculationResult(
            success=True,
            operation=op,
            result_value=val,
            formatted_value=formatted,
            formula=formula,
            explanation=exp,
            inputs={"column": column, "valid_rows": len(series), "total_rows": len(df)}
        )

    @classmethod
    def group_by_aggregation(
        cls,
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        agg_func: str = "sum",
        top_n: Optional[int] = None,
        ascending: bool = False
    ) -> CalculationResult:
        """Group by categorical column and aggregate a numerical column."""
        if group_col not in df.columns:
            return CalculationResult(
                success=False, operation="group_by", result_value=None, formatted_value="Error",
                formula="", explanation="", error=f"Group column '{group_col}' not found."
            )
        if value_col not in df.columns:
            return CalculationResult(
                success=False, operation="group_by", result_value=None, formatted_value="Error",
                formula="", explanation="", error=f"Value column '{value_col}' not found."
            )

        df_work = df[[group_col, value_col]].copy()
        df_work[value_col] = pd.to_numeric(df_work[value_col], errors="coerce")
        df_work = df_work.dropna()

        if df_work.empty:
            return CalculationResult(
                success=False, operation="group_by", result_value=None, formatted_value="N/A",
                formula="", explanation="", error="No valid data available after dropping nulls."
            )

        grouped = df_work.groupby(group_col)[value_col].agg(agg_func).reset_index()
        grouped = grouped.sort_values(by=value_col, ascending=ascending)

        total_groups = len(grouped)
        if top_n and top_n > 0:
            grouped = grouped.head(top_n)

        # Round values for display
        grouped[value_col] = grouped[value_col].round(2)

        top_entity = grouped.iloc[0][group_col] if not grouped.empty else "N/A"
        top_val = grouped.iloc[0][value_col] if not grouped.empty else 0

        formula = f"{agg_func.upper()}({value_col}) GROUP BY {group_col}"
        exp = (
            f"Aggregated {value_col} by {group_col} ({total_groups} distinct categories). "
            f"The highest value is '{top_entity}' with {top_val:,.2f}."
        )

        return CalculationResult(
            success=True,
            operation="group_by",
            result_value=top_val,
            formatted_value=f"{top_entity}: {top_val:,.2f}",
            formula=formula,
            explanation=exp,
            table=grouped,
            inputs={"group_col": group_col, "value_col": value_col, "agg": agg_func, "top_n": top_n}
        )

    @classmethod
    def top_rankings(
        cls,
        df: pd.DataFrame,
        entity_col: str,
        metric_col: str,
        n: int = 10,
        ascending: bool = False
    ) -> CalculationResult:
        """Find top N entities based on a metric."""
        return cls.group_by_aggregation(
            df=df,
            group_col=entity_col,
            value_col=metric_col,
            agg_func="sum",
            top_n=n,
            ascending=ascending
        )

    @classmethod
    def calculate_growth_rate(
        cls,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        freq: str = "ME"  # 'ME' for month-end, 'QE' for quarter, 'D' for daily
    ) -> CalculationResult:
        """Calculate period-over-period growth rates with zero-division protection."""
        if date_col not in df.columns or value_col not in df.columns:
            return CalculationResult(
                success=False, operation="growth_rate", result_value=None, formatted_value="Error",
                formula="", explanation="", error=f"Columns '{date_col}' or '{value_col}' not found."
            )

        df_work = df[[date_col, value_col]].copy()
        df_work[date_col] = pd.to_datetime(df_work[date_col], errors="coerce")
        df_work[value_col] = pd.to_numeric(df_work[value_col], errors="coerce")
        df_work = df_work.dropna().sort_values(date_col)

        if len(df_work) < 2:
            return CalculationResult(
                success=False, operation="growth_rate", result_value=None, formatted_value="N/A",
                formula="", explanation="At least 2 chronological records required for growth rate.",
                error="Insufficient data points."
            )

        df_work.set_index(date_col, inplace=True)
        # Resample by period
        try:
            periodic = df_work[value_col].resample(freq).sum().reset_index()
        except Exception:
            # Fallback to monthly
            periodic = df_work[value_col].resample("M").sum().reset_index()

        # Calculate growth rate: (Current - Prev) / Prev * 100
        periodic["Previous_Period"] = periodic[value_col].shift(1)
        
        # Zero division safe percentage change
        def safe_pct(curr, prev):
            if pd.isna(prev) or prev == 0:
                return np.nan
            return ((curr - prev) / abs(prev)) * 100

        periodic["Growth_Pct"] = [
            safe_pct(c, p) for c, p in zip(periodic[value_col], periodic["Previous_Period"])
        ]
        periodic[value_col] = periodic[value_col].round(2)
        periodic["Growth_Pct"] = periodic["Growth_Pct"].round(2)

        valid_growths = periodic["Growth_Pct"].dropna()
        avg_growth = float(valid_growths.mean()) if not valid_growths.empty else 0.0
        latest_growth = float(valid_growths.iloc[-1]) if not valid_growths.empty else 0.0

        formula = "Growth Rate = ((Period_t - Period_{t-1}) / |Period_{t-1}|) * 100%"
        exp = (
            f"Analyzed {len(periodic)} periods. Average periodic growth was {avg_growth:+.2f}%. "
            f"The most recent period growth was {latest_growth:+.2f}%."
        )

        return CalculationResult(
            success=True,
            operation="growth_rate",
            result_value=latest_growth,
            formatted_value=f"{latest_growth:+.2f}%",
            formula=formula,
            explanation=exp,
            table=periodic,
            inputs={"date_col": date_col, "value_col": value_col, "periods": len(periodic)}
        )

    @classmethod
    def calculate_profit_margin(
        cls,
        df: pd.DataFrame,
        revenue_col: str,
        profit_col: Optional[str] = None,
        cost_col: Optional[str] = None
    ) -> CalculationResult:
        """Calculate aggregate profit margin percentage."""
        if revenue_col not in df.columns:
            return CalculationResult(
                success=False, operation="profit_margin", result_value=None, formatted_value="Error",
                formula="", explanation="", error=f"Revenue column '{revenue_col}' not found."
            )

        total_rev = float(pd.to_numeric(df[revenue_col], errors="coerce").sum())

        if total_rev <= 0:
            return CalculationResult(
                success=False, operation="profit_margin", result_value=None, formatted_value="0.00%",
                formula="", explanation="Total revenue is zero or negative. Cannot compute profit margin.",
                error="Division by zero: zero revenue."
            )

        if profit_col and profit_col in df.columns:
            total_profit = float(pd.to_numeric(df[profit_col], errors="coerce").sum())
            formula = f"(SUM({profit_col}) / SUM({revenue_col})) * 100%"
        elif cost_col and cost_col in df.columns:
            total_cost = float(pd.to_numeric(df[cost_col], errors="coerce").sum())
            total_profit = total_rev - total_cost
            formula = f"((SUM({revenue_col}) - SUM({cost_col})) / SUM({revenue_col})) * 100%"
        else:
            return CalculationResult(
                success=False, operation="profit_margin", result_value=None, formatted_value="Error",
                formula="", explanation="", error="Must supply either profit_col or cost_col."
            )

        margin_pct = (total_profit / total_rev) * 100.0
        exp = (
            f"Overall Profit Margin is {margin_pct:.2f}% "
            f"(Total Profit: ${total_profit:,.2f} on Total Revenue: ${total_rev:,.2f})."
        )

        return CalculationResult(
            success=True,
            operation="profit_margin",
            result_value=round(margin_pct, 2),
            formatted_value=f"{margin_pct:.2f}%",
            formula=formula,
            explanation=exp,
            inputs={"revenue": total_rev, "profit": total_profit}
        )

    @classmethod
    def calculate_correlations(cls, df: pd.DataFrame, columns: Optional[List[str]] = None) -> CalculationResult:
        """Compute Pearson correlation matrix on numerical features."""
        num_cols = [c for c in (columns or df.columns) if pd.api.types.is_numeric_dtype(df[c])]

        if len(num_cols) < 2:
            return CalculationResult(
                success=False, operation="correlation", result_value=None, formatted_value="Error",
                formula="", explanation="", error="At least 2 numerical columns required for correlation."
            )

        corr_matrix = df[num_cols].corr(numeric_only=True).round(3)

        # Find strongest positive and negative correlations (excluding self 1.0)
        pairs = []
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                c1 = num_cols[i]
                c2 = num_cols[j]
                val = corr_matrix.loc[c1, c2]
                if not pd.isna(val):
                    pairs.append((c1, c2, float(val)))

        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        top_corr = pairs[0] if pairs else ("None", "None", 0.0)

        exp = (
            f"Computed pairwise correlation matrix across {len(num_cols)} numerical features. "
            f"Strongest relationship is between '{top_corr[0]}' and '{top_corr[1]}' (r = {top_corr[2]:+.2f})."
        )

        return CalculationResult(
            success=True,
            operation="correlation",
            result_value=corr_matrix.to_dict(),
            formatted_value=f"Max r = {top_corr[2]:+.2f}",
            formula="Pearson Correlation Coefficient r = Cov(X,Y) / (Std(X)*Std(Y))",
            explanation=exp,
            table=corr_matrix.reset_index(),
            inputs={"columns": num_cols}
        )

    @classmethod
    def detect_outliers(cls, df: pd.DataFrame, column: str, method: str = "iqr") -> CalculationResult:
        """Detect outliers using IQR or Z-score method."""
        if column not in df.columns:
            return CalculationResult(
                success=False, operation="outlier_detection", result_value=None, formatted_value="Error",
                formula="", explanation="", error=f"Column '{column}' not found."
            )

        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(series) < 5:
            return CalculationResult(
                success=False, operation="outlier_detection", result_value=None, formatted_value="N/A",
                formula="", explanation="Insufficient data for outlier detection.", error="Too few rows."
            )

        if method == "iqr":
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers_mask = (series < lower_bound) | (series > upper_bound)
            formula = f"Outliers: {column} < Q1 - 1.5*IQR or {column} > Q3 + 1.5*IQR (IQR = {iqr:.2f})"
        else:
            mean = float(series.mean())
            std = float(series.std())
            if std == 0:
                outliers_mask = pd.Series(False, index=series.index)
                lower_bound, upper_bound = mean, mean
            else:
                z_scores = (series - mean) / std
                outliers_mask = z_scores.abs() > 3
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
            formula = f"Outliers: |Z-score| > 3 where Z = (x - mean)/std"

        outlier_count = int(outliers_mask.sum())
        outlier_pct = round((outlier_count / len(series)) * 100, 2)
        outlier_rows = df.loc[series[outliers_mask].index]

        exp = (
            f"Detected {outlier_count:,} outliers ({outlier_pct}% of records) in '{column}' "
            f"outside [{lower_bound:,.2f}, {upper_bound:,.2f}]."
        )

        return CalculationResult(
            success=True,
            operation="outlier_detection",
            result_value=outlier_count,
            formatted_value=f"{outlier_count:,} outliers ({outlier_pct}%)",
            formula=formula,
            explanation=exp,
            table=outlier_rows.head(20),
            inputs={"column": column, "method": method, "lower_bound": lower_bound, "upper_bound": upper_bound}
        )
