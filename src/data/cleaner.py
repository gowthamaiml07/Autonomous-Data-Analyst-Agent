"""Safe data cleaning, transformation, and history tracker."""
import ast
import operator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class CleaningAction:
    """Record of a transformation step applied to the dataset."""
    id: str
    action_type: str
    description: str
    timestamp: str
    parameters: Dict[str, Any]
    rows_before: int
    rows_after: int
    cols_before: int
    cols_after: int


class CleaningHistory:
    """Manages the undo/redo/audit history of transformations."""

    def __init__(self, initial_df: pd.DataFrame):
        self.original_df: pd.DataFrame = initial_df.copy()
        self.current_df: pd.DataFrame = initial_df.copy()
        self.actions: List[CleaningAction] = []
        self._snapshots: List[pd.DataFrame] = [initial_df.copy()]

    def record_action(
        self,
        action_type: str,
        description: str,
        params: Dict[str, Any],
        df_before: pd.DataFrame,
        df_after: pd.DataFrame
    ) -> CleaningAction:
        action = CleaningAction(
            id=f"act_{len(self.actions) + 1}_{int(datetime.now().timestamp())}",
            action_type=action_type,
            description=description,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            parameters=params,
            rows_before=len(df_before),
            rows_after=len(df_after),
            cols_before=len(df_before.columns),
            cols_after=len(df_after.columns)
        )
        self.actions.append(action)
        self.current_df = df_after.copy()
        self._snapshots.append(df_after.copy())
        return action

    def undo_last(self) -> Optional[pd.DataFrame]:
        """Revert the most recent transformation step."""
        if len(self._snapshots) > 1 and len(self.actions) > 0:
            self._snapshots.pop()
            self.actions.pop()
            self.current_df = self._snapshots[-1].copy()
            return self.current_df
        return None

    def reset_to_original(self) -> pd.DataFrame:
        """Reset current dataset back to original state."""
        self.current_df = self.original_df.copy()
        self.actions.clear()
        self._snapshots = [self.original_df.copy()]
        return self.current_df


class SafeFormulaEvaluator:
    """Safely evaluates mathematical expressions without arbitrary code execution."""

    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @classmethod
    def evaluate(cls, expression: str, df: pd.DataFrame) -> pd.Series:
        """Evaluate a math expression containing column names (e.g. 'Revenue - Cost')."""
        try:
            tree = ast.parse(expression.strip(), mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid formula syntax: {e}")

        return cls._eval_node(tree.body, df)

    @classmethod
    def _eval_node(cls, node: ast.AST, df: pd.DataFrame) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # Match column name directly or case-insensitively
            col_name = node.id
            if col_name in df.columns:
                return df[col_name]
            for c in df.columns:
                if c.lower() == col_name.lower():
                    return df[c]
            raise ValueError(f"Column '{col_name}' not found in dataset columns: {list(df.columns)}")
        elif isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left, df)
            right = cls._eval_node(node.right, df)
            op_type = type(node.op)
            if op_type in cls.ALLOWED_OPERATORS:
                op_func = cls.ALLOWED_OPERATORS[op_type]
                # Protect division by zero
                if op_type in (ast.Div, ast.FloorDiv):
                    if isinstance(right, (int, float)) and right == 0:
                        raise ZeroDivisionError("Division by zero in formula.")
                    elif isinstance(right, pd.Series):
                        # Replace 0 with NaN to avoid inf or error
                        right_safe = right.replace(0, np.nan)
                        return op_func(left, right_safe)
                return op_func(left, right)
            else:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand, df)
            op_type = type(node.op)
            if op_type in cls.ALLOWED_OPERATORS:
                return cls.ALLOWED_OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise ValueError(f"Disallowed expression element: {type(node).__name__}")


class DataCleaner:
    """Performs deterministic and safe dataset cleaning and transformation."""

    @classmethod
    def remove_duplicates(
        cls,
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: str = "first"
    ) -> Tuple[pd.DataFrame, int]:
        """Remove duplicate records."""
        initial_count = len(df)
        cleaned_df = df.drop_duplicates(subset=subset, keep=keep).copy()
        removed_count = initial_count - len(cleaned_df)
        return cleaned_df, removed_count

    @classmethod
    def handle_missing_values(
        cls,
        df: pd.DataFrame,
        strategy: str,
        columns: Optional[List[str]] = None,
        fill_value: Any = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Impute or drop missing values based on strategy.
        
        Strategies:
            - 'drop_rows': drop rows containing any missing value in target columns
            - 'drop_cols': drop columns that have missing values exceeding threshold
            - 'mean': impute with numerical mean
            - 'median': impute with numerical median
            - 'mode': impute with most frequent value
            - 'ffill': forward fill
            - 'bfill': backward fill
            - 'constant': replace with user-provided constant
        """
        df_clean = df.copy()
        target_cols = columns if columns else list(df.columns)
        stats_affected = {}

        if strategy == "drop_rows":
            rows_before = len(df_clean)
            df_clean = df_clean.dropna(subset=target_cols).copy()
            stats_affected["rows_dropped"] = rows_before - len(df_clean)

        elif strategy == "drop_cols":
            cols_to_drop = [c for c in target_cols if df_clean[c].isna().any()]
            df_clean = df_clean.drop(columns=cols_to_drop)
            stats_affected["cols_dropped"] = cols_to_drop

        elif strategy in ["mean", "median"]:
            for col in target_cols:
                if pd.api.types.is_numeric_dtype(df_clean[col]):
                    val = df_clean[col].mean() if strategy == "mean" else df_clean[col].median()
                    null_c = int(df_clean[col].isna().sum())
                    df_clean[col] = df_clean[col].fillna(val)
                    stats_affected[col] = {"imputed_value": round(float(val), 3), "count": null_c}

        elif strategy == "mode":
            for col in target_cols:
                mode_vals = df_clean[col].mode()
                if not mode_vals.empty:
                    val = mode_vals[0]
                    null_c = int(df_clean[col].isna().sum())
                    df_clean[col] = df_clean[col].fillna(val)
                    stats_affected[col] = {"imputed_value": str(val), "count": null_c}

        elif strategy == "ffill":
            df_clean[target_cols] = df_clean[target_cols].ffill()
            stats_affected["strategy"] = "forward_fill"

        elif strategy == "bfill":
            df_clean[target_cols] = df_clean[target_cols].bfill()
            stats_affected["strategy"] = "backward_fill"

        elif strategy == "constant":
            for col in target_cols:
                null_c = int(df_clean[col].isna().sum())
                df_clean[col] = df_clean[col].fillna(fill_value)
                stats_affected[col] = {"fill_value": fill_value, "count": null_c}

        else:
            raise ValueError(f"Unknown missing value strategy: {strategy}")

        return df_clean, stats_affected

    @classmethod
    def convert_column_type(
        cls,
        df: pd.DataFrame,
        column: str,
        target_type: str,
        date_format: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """Convert a column to a new data type."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' does not exist.")

        df_clean = df.copy()
        msg = ""

        if target_type == "numeric":
            df_clean[column] = pd.to_numeric(df_clean[column], errors="coerce")
            msg = f"Converted '{column}' to numeric (float/int)."
        elif target_type == "integer":
            df_clean[column] = pd.to_numeric(df_clean[column], errors="coerce").fillna(0).astype("int64")
            msg = f"Converted '{column}' to integer (int64)."
        elif target_type == "string":
            df_clean[column] = df_clean[column].astype(str)
            msg = f"Converted '{column}' to string."
        elif target_type == "categorical":
            df_clean[column] = df_clean[column].astype("category")
            msg = f"Converted '{column}' to categorical."
        elif target_type == "datetime":
            df_clean[column] = pd.to_datetime(df_clean[column], format=date_format, errors="coerce")
            msg = f"Converted '{column}' to datetime."
        elif target_type == "boolean":
            df_clean[column] = df_clean[column].astype(bool)
            msg = f"Converted '{column}' to boolean."
        else:
            raise ValueError(f"Unsupported target type: {target_type}")

        return df_clean, msg

    @classmethod
    def rename_columns(cls, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """Rename specified columns."""
        return df.rename(columns=mapping).copy()

    @classmethod
    def filter_records(
        cls,
        df: pd.DataFrame,
        column: str,
        operator_str: str,
        value: Any
    ) -> pd.DataFrame:
        """Filter records by condition safely."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

        series = df[column]

        if operator_str == "==":
            return df[series == value].copy()
        elif operator_str == "!=":
            return df[series != value].copy()
        elif operator_str == ">":
            return df[series > float(value)].copy()
        elif operator_str == ">=":
            return df[series >= float(value)].copy()
        elif operator_str == "<":
            return df[series < float(value)].copy()
        elif operator_str == "<=":
            return df[series <= float(value)].copy()
        elif operator_str == "contains":
            return df[series.astype(str).str.contains(str(value), case=False, na=False)].copy()
        elif operator_str == "is_null":
            return df[series.isna()].copy()
        elif operator_str == "not_null":
            return df[series.notna()].copy()
        else:
            raise ValueError(f"Unsupported filter operator: {operator_str}")

    @classmethod
    def sort_records(
        cls,
        df: pd.DataFrame,
        by: List[str],
        ascending: Union[bool, List[bool]] = True
    ) -> pd.DataFrame:
        """Sort records by specified column(s)."""
        return df.sort_values(by=by, ascending=ascending).reset_index(drop=True)

    @classmethod
    def create_derived_column(
        cls,
        df: pd.DataFrame,
        new_column_name: str,
        expression: str
    ) -> Tuple[pd.DataFrame, str]:
        """Create a new derived column using safe math evaluation."""
        if not new_column_name.strip():
            raise ValueError("New column name cannot be empty.")

        calculated_series = SafeFormulaEvaluator.evaluate(expression, df)
        df_result = df.copy()
        df_result[new_column_name.strip()] = calculated_series
        return df_result, f"Created derived column '{new_column_name}' from '{expression}'."

    @classmethod
    def pivot_data(
        cls,
        df: pd.DataFrame,
        index_col: str,
        columns_col: str,
        values_col: str,
        aggfunc: str = "mean"
    ) -> pd.DataFrame:
        """Pivot and reshape dataset."""
        return df.pivot_table(
            index=index_col,
            columns=columns_col,
            values=values_col,
            aggfunc=aggfunc
        ).reset_index()

    @classmethod
    def trim_outliers(
        cls,
        df: pd.DataFrame,
        column: str,
        multiplier: float = 1.5
    ) -> Tuple[pd.DataFrame, int, float, float]:
        """Trim outlier records beyond [Q1 - multiplier*IQR, Q3 + multiplier*IQR]."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")
        s = pd.to_numeric(df[column], errors="coerce")
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        mask = (s >= lower_bound) & (s <= upper_bound)
        trimmed_df = df[mask].copy()
        removed_count = len(df) - len(trimmed_df)
        return trimmed_df, removed_count, float(lower_bound), float(upper_bound)

    @classmethod
    def group_and_aggregate(
        cls,
        df: pd.DataFrame,
        group_by_col: str,
        value_col: str,
        agg_func: str = "sum"
    ) -> pd.DataFrame:
        """Group by category and aggregate target metric."""
        if group_by_col not in df.columns:
            raise ValueError(f"Column '{group_by_col}' not found.")
        if value_col not in df.columns:
            raise ValueError(f"Column '{value_col}' not found.")
        return df.groupby(group_by_col)[value_col].agg(agg_func).reset_index()

