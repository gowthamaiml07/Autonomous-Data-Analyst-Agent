"""Tools registry with typed validation, column resolution, and execution dispatching."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import plotly.graph_objects as go

from pydantic import BaseModel, Field

from src.data.profiler import ProfileReport
from src.tools.calculator import DataCalculator, CalculationResult
from src.tools.visualizer import DataVisualizer, ChartResult
from src.tools.predictor import DataPredictor, PredictionResult
from src.tools.recommender import RecommendationEngine, RecommendationReport
from src.data.cleaner import DataCleaner


class CalculateMetricArgs(BaseModel):
    column: Optional[str] = None
    operation: str = Field(default="sum")


class GroupByArgs(BaseModel):
    group_col: Optional[str] = None
    entity_col: Optional[str] = None
    value_col: Optional[str] = None
    metric_col: Optional[str] = None
    agg_func: str = Field(default="sum")
    top_n: Optional[int] = Field(default=10)


class GrowthRateArgs(BaseModel):
    date_col: Optional[str] = None
    value_col: Optional[str] = None
    freq: str = Field(default="ME")


class ProfitMarginArgs(BaseModel):
    revenue_col: Optional[str] = None
    profit_col: Optional[str] = None
    cost_col: Optional[str] = None


class CorrelationsArgs(BaseModel):
    columns: Optional[List[str]] = None


class DetectOutliersArgs(BaseModel):
    column: Optional[str] = None
    method: str = Field(default="iqr")


class BuildChartArgs(BaseModel):
    chart_type: str = Field(default="bar")
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    color_col: Optional[str] = None
    title: Optional[str] = None


class ForecastArgs(BaseModel):
    date_col: Optional[str] = None
    value_col: Optional[str] = None
    horizon_periods: int = Field(default=30)


class TrainRegressionArgs(BaseModel):
    target_col: Optional[str] = None
    model_type: str = Field(default="random_forest")


class TrainClassificationArgs(BaseModel):
    target_col: Optional[str] = None
    model_type: str = Field(default="random_forest")


class FilterDataArgs(BaseModel):
    column: Optional[str] = None
    operator: str = Field(default="==")
    value: Any = None


@dataclass
class ToolOutput:
    """Standardized output wrapper for all executed tools."""
    tool_name: str
    success: bool
    text_summary: str
    formula: Optional[str] = None
    table: Optional[pd.DataFrame] = None
    figure: Optional[go.Figure] = None
    raw_result: Any = None
    error: Optional[str] = None


class ToolsRegistry:
    """Executes validated tool operations with defensive column name resolution."""

    @classmethod
    def resolve_column(cls, requested_name: Optional[str], df: pd.DataFrame) -> Optional[str]:
        """Resolve requested column name against actual DataFrame columns."""
        if not requested_name or not isinstance(requested_name, str):
            return None

        clean_req = requested_name.strip()
        if clean_req in df.columns:
            return clean_req

        # Case-insensitive match
        for col in df.columns:
            if col.lower() == clean_req.lower():
                return col

        # Partial substring or alias match
        req_lower = clean_req.lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "sales": ["revenue", "sales", "total_sales", "amount"],
            "revenue": ["revenue", "sales", "total_revenue"],
            "profit": ["profit", "net_profit", "margin", "income"],
            "cost": ["cost", "expenses", "expense"],
            "date": ["date", "order_date", "timestamp", "day", "month"],
            "category": ["product_category", "category", "type"],
            "product": ["product_name", "product", "item"],
            "region": ["region", "territory", "location", "country", "area"],
            "churn": ["churn", "status", "target"]
        }

        # Check aliases
        if req_lower in aliases:
            for alias in aliases[req_lower]:
                for col in df.columns:
                    if col.lower() == alias or alias in col.lower():
                        return col

        # Substring match
        for col in df.columns:
            col_l = col.lower().replace(" ", "_")
            if req_lower in col_l or col_l in req_lower:
                return col

        return None

    @classmethod
    def execute(
        cls,
        tool_name: str,
        tool_args: Dict[str, Any],
        df: pd.DataFrame,
        profile: Optional[ProfileReport] = None
    ) -> ToolOutput:
        """Safely dispatch and execute a tool."""
        if df is None or df.empty:
            return ToolOutput(tool_name=tool_name, success=False, text_summary="Dataset is empty.", error="Empty dataset")

        t_name = tool_name.lower().strip()

        try:
            # 1. calculate_metric
            if t_name == "calculate_metric":
                col = cls.resolve_column(tool_args.get("column"), df)
                op = tool_args.get("operation", "sum")
                if not col:
                    return ToolOutput(tool_name=t_name, success=False, text_summary=f"Column '{tool_args.get('column')}' not found.", error="Column not found")
                res: CalculationResult = DataCalculator.calculate_metric(df, col, op)
                return ToolOutput(
                    tool_name=t_name,
                    success=res.success,
                    text_summary=res.explanation,
                    formula=res.formula,
                    raw_result=res.result_value,
                    error=res.error
                )

            # 2. group_by_aggregation
            elif t_name in ["group_by_aggregation", "group_by", "rankings"]:
                g_col = cls.resolve_column(tool_args.get("group_col") or tool_args.get("entity_col"), df)
                v_col = cls.resolve_column(tool_args.get("value_col") or tool_args.get("metric_col"), df)
                agg = tool_args.get("agg_func", "sum")
                top_n = tool_args.get("top_n", 10)
                if not g_col or not v_col:
                    return ToolOutput(tool_name=t_name, success=False, text_summary="Group column or value column not found.", error="Column not found")
                res = DataCalculator.group_by_aggregation(df, g_col, v_col, agg_func=agg, top_n=top_n)
                # Auto-generate a bar chart for grouped results
                chart_res = DataVisualizer.build_chart(
                    res.table, "bar", x_col=g_col, y_col=v_col,
                    title=f"{v_col} by {g_col}"
                )
                return ToolOutput(
                    tool_name=t_name,
                    success=res.success,
                    text_summary=res.explanation,
                    formula=res.formula,
                    table=res.table,
                    figure=chart_res.fig if chart_res.success else None,
                    raw_result=res.result_value,
                    error=res.error
                )

            # 3. calculate_growth_rate
            elif t_name in ["calculate_growth_rate", "growth_rate"]:
                d_col = cls.resolve_column(tool_args.get("date_col") or (profile.datetime_columns[0] if profile and profile.datetime_columns else None), df)
                v_col = cls.resolve_column(tool_args.get("value_col"), df)
                freq = tool_args.get("freq", "ME")
                if not d_col or not v_col:
                    return ToolOutput(tool_name=t_name, success=False, text_summary="Date column or metric column not found.", error="Column not found")
                res = DataCalculator.calculate_growth_rate(df, d_col, v_col, freq=freq)
                # Auto-generate a line chart for growth rate
                chart_res = None
                if res.success and res.table is not None:
                    chart_res = DataVisualizer.build_chart(
                        res.table, "line", x_col=d_col, y_col="Growth_Pct",
                        title=f"Period-over-Period Growth Rate ({v_col})"
                    )
                return ToolOutput(
                    tool_name=t_name,
                    success=res.success,
                    text_summary=res.explanation,
                    formula=res.formula,
                    table=res.table,
                    figure=chart_res.fig if chart_res and chart_res.success else None,
                    raw_result=res.result_value,
                    error=res.error
                )

            # 4. calculate_profit_margin
            elif t_name == "calculate_profit_margin":
                rev_col = cls.resolve_column(tool_args.get("revenue_col") or "Revenue", df)
                prof_col = cls.resolve_column(tool_args.get("profit_col") or "Profit", df)
                cost_col = cls.resolve_column(tool_args.get("cost_col") or "Cost", df)
                res = DataCalculator.calculate_profit_margin(df, rev_col, prof_col, cost_col)
                return ToolOutput(
                    tool_name=t_name,
                    success=res.success,
                    text_summary=res.explanation,
                    formula=res.formula,
                    raw_result=res.result_value,
                    error=res.error
                )

            # 5. calculate_correlations
            elif t_name == "calculate_correlations":
                cols = [cls.resolve_column(c, df) for c in tool_args.get("columns", [])]
                cols = [c for c in cols if c]
                res = DataCalculator.calculate_correlations(df, columns=cols if cols else None)
                chart_res = DataVisualizer.build_chart(df, "heatmap", title="Correlation Heatmap")
                return ToolOutput(
                    tool_name=t_name,
                    success=res.success,
                    text_summary=res.explanation,
                    formula=res.formula,
                    table=res.table,
                    figure=chart_res.fig if chart_res.success else None,
                    raw_result=res.result_value,
                    error=res.error
                )

            # 6. detect_outliers
            elif t_name == "detect_outliers":
                col = cls.resolve_column(tool_args.get("column"), df)
                method = tool_args.get("method", "iqr")
                if not col:
                    return ToolOutput(tool_name=t_name, success=False, text_summary="Target column for outlier analysis not found.", error="Column not found")
                res = DataCalculator.detect_outliers(df, col, method=method)
                chart_res = DataVisualizer.build_chart(df, "box", y_col=col, title=f"Outlier Distribution ({col})")
                return ToolOutput(
                    tool_name=t_name,
                    success=res.success,
                    text_summary=res.explanation,
                    formula=res.formula,
                    table=res.table,
                    figure=chart_res.fig if chart_res.success else None,
                    raw_result=res.result_value,
                    error=res.error
                )

            # 7. build_chart
            elif t_name == "build_chart":
                c_type = tool_args.get("chart_type", "bar")
                x = cls.resolve_column(tool_args.get("x_col"), df)
                y = cls.resolve_column(tool_args.get("y_col"), df)
                color = cls.resolve_column(tool_args.get("color_col"), df)
                title = tool_args.get("title")

                # If missing coordinates, ask recommendation
                if not x and not y:
                    rec = DataVisualizer.recommend_best_chart(df)
                    c_type = rec["chart_type"]
                    x = rec.get("x_col")
                    y = rec.get("y_col")

                c_res: ChartResult = DataVisualizer.build_chart(
                    df, chart_type=c_type, x_col=x, y_col=y, color_col=color, title=title
                )
                return ToolOutput(
                    tool_name=t_name,
                    success=c_res.success,
                    text_summary=c_res.rationale or f"Generated {c_type} chart.",
                    figure=c_res.fig,
                    raw_result=c_res.json_spec,
                    error=c_res.error
                )

            # 8. forecast_timeseries
            elif t_name == "forecast_timeseries":
                d_col = cls.resolve_column(tool_args.get("date_col") or (profile.datetime_columns[0] if profile and profile.datetime_columns else None), df)
                v_col = cls.resolve_column(tool_args.get("value_col") or (profile.numerical_columns[0] if profile and profile.numerical_columns else None), df)
                horizon = int(tool_args.get("horizon_periods", 30))
                p_res: PredictionResult = DataPredictor.forecast_timeseries(df, d_col, v_col, horizon_periods=horizon)
                return ToolOutput(
                    tool_name=t_name,
                    success=p_res.success,
                    text_summary=p_res.executive_summary,
                    table=p_res.forecast_table,
                    figure=p_res.forecast_chart,
                    raw_result=p_res.metrics,
                    error=p_res.error
                )

            # 9. train_regression
            elif t_name == "train_regression":
                t_col = cls.resolve_column(tool_args.get("target_col") or (profile.potential_targets[0] if profile and profile.potential_targets else None), df)
                m_type = tool_args.get("model_type", "random_forest")
                p_res = DataPredictor.train_regression(df, target_col=t_col, model_type=m_type)
                return ToolOutput(
                    tool_name=t_name,
                    success=p_res.success,
                    text_summary=p_res.executive_summary,
                    table=p_res.test_comparison_table,
                    figure=p_res.comparison_chart,
                    raw_result=p_res.metrics,
                    error=p_res.error
                )

            # 10. train_classification
            elif t_name == "train_classification":
                t_col = cls.resolve_column(tool_args.get("target_col"), df)
                m_type = tool_args.get("model_type", "random_forest")
                p_res = DataPredictor.train_classification(df, target_col=t_col, model_type=m_type)
                return ToolOutput(
                    tool_name=t_name,
                    success=p_res.success,
                    text_summary=p_res.executive_summary,
                    table=p_res.test_comparison_table,
                    figure=p_res.comparison_chart,
                    raw_result=p_res.metrics,
                    error=p_res.error
                )

            # 11. generate_recommendations
            elif t_name == "generate_recommendations":
                r_rep: RecommendationReport = RecommendationEngine.generate_recommendations(df, profile)
                return ToolOutput(
                    tool_name=t_name,
                    success=True,
                    text_summary=r_rep.summary_markdown,
                    raw_result=r_rep.recommendations
                )

            # 12. filter_data
            elif t_name == "filter_data":
                col = cls.resolve_column(tool_args.get("column"), df)
                op = tool_args.get("operator", "==")
                val = tool_args.get("value")
                filt_df = DataCleaner.filter_records(df, col, op, val)
                return ToolOutput(
                    tool_name=t_name,
                    success=True,
                    text_summary=f"Filtered {len(filt_df):,} rows matching `{col} {op} {val}`.",
                    table=filt_df.head(50),
                    raw_result={"matching_rows": len(filt_df)}
                )

            # 13. dataset_overview / analyze_dataset
            elif t_name in ("dataset_overview", "analyze_dataset"):
                r_rep = RecommendationEngine.generate_recommendations(df, profile)
                summary_text = (
                    f"**Dataset Overview**: Analyzed {len(df):,} records across {len(df.columns)} dimensions.\n\n"
                    f"- **Numerical Attributes**: {', '.join(profile.numerical_columns[:5]) if profile and profile.numerical_columns else 'None'}\n"
                    f"- **Categorical Dimensions**: {', '.join(profile.categorical_columns[:5]) if profile and profile.categorical_columns else 'None'}\n"
                    f"- **Data Completeness**: {round(100.0 - (profile.missing_pct if profile else 0), 1)}%\n\n"
                    f"{r_rep.summary_markdown}"
                )
                chart_rec = DataVisualizer.recommend_best_chart(df)
                fig_out = None
                if chart_rec.get("x_col") and chart_rec.get("y_col"):
                    c_build = DataVisualizer.build_chart(
                        df, chart_type=chart_rec["chart_type"],
                        x_col=chart_rec["x_col"], y_col=chart_rec["y_col"],
                        title="Dataset Primary Distribution"
                    )
                    fig_out = c_build.fig
                return ToolOutput(
                    tool_name=t_name,
                    success=True,
                    text_summary=summary_text,
                    table=df.head(10),
                    figure=fig_out,
                    raw_result={"rows": len(df), "cols": len(df.columns)}
                )

            # 14. prompt_dataset_upload
            elif t_name == "prompt_dataset_upload":
                return ToolOutput(
                    tool_name=t_name,
                    success=True,
                    text_summary=(
                        "📂 **Dataset Required for Analysis**\n\n"
                        "To analyze specific metrics, build charts, or run predictions, please upload your CSV or Excel file via the **Home** or **Data Workspace** page.\n\n"
                        "💡 *Quick Tip*: You can also choose one of our curated sample datasets on the **Home** page (*Sales & Profitability*, *Customer Churn*, or *Student Performance*) to test DN AI immediately!"
                    ),
                    raw_result={"status": "needs_dataset"}
                )

            # 15. general_chat
            elif t_name == "general_chat":
                return ToolOutput(
                    tool_name=t_name,
                    success=True,
                    text_summary=tool_args.get("response", "DN AI is ready to help."),
                    raw_result={"status": "general_ai"}
                )

            else:
                return ToolOutput(
                    tool_name=t_name,
                    success=False,
                    text_summary=f"Unknown tool '{t_name}'.",
                    error="Unregistered tool"
                )

        except Exception as e:
            return ToolOutput(
                tool_name=t_name,
                success=False,
                text_summary=f"Tool execution failed: {str(e)}",
                error=str(e)
            )
