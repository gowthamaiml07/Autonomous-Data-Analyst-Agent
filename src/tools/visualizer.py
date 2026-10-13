"""Interactive Plotly chart generation with emerald-green SaaS styling and dynamic drill-downs."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_DARK_BLUE,
    COLOR_LIGHT_BLUE, COLOR_PALE_BLUE, PLOTLY_COLORWAY
)


@dataclass
class ChartResult:
    """Result of chart generation."""
    success: bool
    fig: Optional[go.Figure] = None
    chart_type: str = ""
    title: str = ""
    rationale: str = ""
    error: Optional[str] = None
    json_spec: Optional[str] = None


class DataVisualizer:
    """Builds interactive Plotly visualizations with validated schema mapping and live controls."""

    THEME_LAYOUT = dict(
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color="#111827"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        colorway=PLOTLY_COLORWAY,
        margin=dict(l=40, r=40, t=55, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            gridcolor="#E2E8F0",
            zerolinecolor="#CBD5E1",
            showline=True,
            linecolor="#CBD5E1"
        ),
        yaxis=dict(
            gridcolor="#E2E8F0",
            zerolinecolor="#CBD5E1",
            showline=True,
            linecolor="#CBD5E1"
        )
    )

    @classmethod
    def apply_theme(cls, fig: go.Figure) -> go.Figure:
        """Apply sleek emerald SaaS styling to a Plotly figure."""
        fig.update_layout(**cls.THEME_LAYOUT)
        return fig

    @classmethod
    def build_chart(
        cls,
        df: pd.DataFrame,
        chart_type: str,
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        color_col: Optional[str] = None,
        title: Optional[str] = None,
        barmode: str = "group",  # 'group', 'stack', 'relative'
        top_n: Optional[int] = None,
        log_y: bool = False,
        enable_rangeslider: bool = False
    ) -> ChartResult:
        """Generate interactive chart validated against DataFrame columns."""
        if df is None or df.empty:
            return ChartResult(
                success=False,
                error="Cannot generate visualization on an empty dataset."
            )

        c_type = chart_type.lower().strip()
        fig = None
        rationale = ""
        chart_title = title or f"{chart_type.title()} Chart"

        try:
            # 1. Bar Chart
            if c_type in ["bar", "column"]:
                if not x_col or not y_col:
                    return ChartResult(success=False, error="Bar chart requires both x_col and y_col.")
                
                plot_df = df
                if top_n and top_n > 0:
                    top_cats = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(top_n).index
                    plot_df = df[df[x_col].isin(top_cats)]

                fig = px.bar(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    barmode=barmode,
                    log_y=log_y,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )
                rationale = f"A bar chart clearly highlights magnitude and ranking of '{y_col}' across '{x_col}' categories."

            # 2. Line Chart
            elif c_type in ["line", "trend"]:
                if not x_col or not y_col:
                    return ChartResult(success=False, error="Line chart requires both x_col and y_col.")
                
                plot_df = df.sort_values(x_col) if x_col in df.columns else df
                fig = px.line(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    markers=True,
                    log_y=log_y,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )

                # Add interactive time range slider and selector buttons if date column or enabled
                is_dt = pd.api.types.is_datetime64_any_dtype(df[x_col]) or "date" in str(x_col).lower()
                if is_dt or enable_rangeslider:
                    fig.update_xaxes(
                        rangeslider_visible=True,
                        rangeselector=dict(
                            buttons=list([
                                dict(count=7, label="7D", step="day", stepmode="backward"),
                                dict(count=1, label="1M", step="month", stepmode="backward"),
                                dict(count=3, label="3M", step="month", stepmode="backward"),
                                dict(step="all", label="All")
                            ])
                        )
                    )

                rationale = f"A line chart reveals continuous trends, trajectories, and momentum of '{y_col}' over '{x_col}'."

            # 3. Area Chart
            elif c_type == "area":
                if not x_col or not y_col:
                    return ChartResult(success=False, error="Area chart requires both x_col and y_col.")
                plot_df = df.sort_values(x_col) if x_col in df.columns else df
                fig = px.area(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    log_y=log_y,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )
                rationale = f"An area chart depicts cumulative volume and progression over '{x_col}'."

            # 4. Pie / Donut Chart
            elif c_type in ["pie", "donut"]:
                names_col = x_col or color_col
                values_col = y_col
                if not names_col or not values_col:
                    return ChartResult(success=False, error="Pie chart requires categorical labels and numerical values.")
                
                fig = px.pie(
                    df,
                    names=names_col,
                    values=values_col,
                    hole=0.45 if c_type == "donut" else 0.0,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                rationale = f"A {c_type} chart illustrates proportional share and composition of '{values_col}' by '{names_col}'."

            # 5. Histogram
            elif c_type in ["histogram", "dist", "distribution"]:
                target_col = x_col or y_col
                if not target_col:
                    return ChartResult(success=False, error="Histogram requires a target column.")
                
                fig = px.histogram(
                    df,
                    x=target_col,
                    color=color_col,
                    marginal="box",
                    log_y=log_y,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )
                rationale = f"A histogram visualizes the distribution shape, spread, skewness, and frequency density of '{target_col}'."

            # 6. Scatter Plot
            elif c_type in ["scatter", "correlation_plot"]:
                if not x_col or not y_col:
                    return ChartResult(success=False, error="Scatter plot requires both x_col and y_col.")
                
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    log_y=log_y,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )
                rationale = f"A scatter plot examines the correlation, clustering, and potential outliers between '{x_col}' and '{y_col}'."

            # 7. Box Plot
            elif c_type in ["box", "boxplot"]:
                target_col = y_col or x_col
                cat_col = x_col if y_col else None
                if not target_col:
                    return ChartResult(success=False, error="Box plot requires a numerical target column.")
                
                fig = px.box(
                    df,
                    x=cat_col,
                    y=target_col,
                    color=color_col or cat_col,
                    points="outliers",
                    log_y=log_y,
                    title=chart_title,
                    color_discrete_sequence=PLOTLY_COLORWAY
                )
                rationale = f"A box plot highlights median, quartiles, interquartile range (IQR), and anomalies in '{target_col}'."

            # 8. Correlation Heatmap
            elif c_type in ["heatmap", "correlation_heatmap"]:
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(num_cols) < 2:
                    return ChartResult(success=False, error="Heatmap requires at least 2 numerical columns.")
                
                corr = df[num_cols].corr().round(2)
                fig = px.imshow(
                    corr,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale=[[0, "#E2E8F0"], [0.5, "#DBEAFE"], [1, "#1E40AF"]],
                    title=chart_title
                )
                rationale = "A correlation heatmap exposes linear co-movements and dependencies across all numerical dimensions."

            else:
                return ChartResult(
                    success=False,
                    error=f"Unsupported chart type '{chart_type}'. Supported: bar, line, area, pie, donut, histogram, scatter, box, heatmap."
                )

            cls.apply_theme(fig)

            return ChartResult(
                success=True,
                fig=fig,
                chart_type=c_type,
                title=chart_title,
                rationale=rationale,
                json_spec=fig.to_json()
            )

        except Exception as e:
            return ChartResult(
                success=False,
                chart_type=c_type,
                error=f"Failed to generate {chart_type} chart: {str(e)}"
            )

    @classmethod
    def build_gauge_chart(
        cls,
        value: float,
        min_val: float = 0.0,
        max_val: float = 100.0,
        target_val: Optional[float] = None,
        title: str = "Performance Gauge"
    ) -> go.Figure:
        """Create an interactive animated blue KPI gauge chart."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta" if target_val is not None else "gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 18, 'color': '#111827', 'family': 'Inter'}},
            delta={'reference': target_val, 'increasing': {'color': "#16A34A"}, 'decreasing': {'color': "#DC2626"}} if target_val is not None else None,
            gauge={
                'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#2563EB"},
                'bgcolor': "#FFFFFF",
                'borderwidth': 2,
                'bordercolor': "#E2E8F0",
                'steps': [
                    {'range': [min_val, min_val + (max_val - min_val) * 0.4], 'color': '#EFF6FF'},
                    {'range': [min_val + (max_val - min_val) * 0.4, min_val + (max_val - min_val) * 0.8], 'color': '#DBEAFE'},
                    {'range': [min_val + (max_val - min_val) * 0.8, max_val], 'color': '#BFDBFE'}
                ],
                'threshold': {
                    'line': {'color': "#1E40AF", 'width': 4},
                    'thickness': 0.75,
                    'value': target_val if target_val is not None else max_val * 0.9
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            font=dict(family="Inter, sans-serif"),
            height=280,
            margin=dict(l=25, r=25, t=40, b=25)
        )
        return fig

    @classmethod
    def build_outlier_inspector(
        cls,
        df: pd.DataFrame,
        column: str,
        iqr_multiplier: float = 1.5
    ) -> go.Figure:
        """Interactive outlier inspector highlighting anomalies in amber/red."""
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr

        is_outlier = (series < lower) | (series > upper)
        plot_df = pd.DataFrame({
            "Index": series.index,
            column: series,
            "Classification": np.where(is_outlier, "Outlier (Anomaly)", "Normal Range")
        })

        fig = px.scatter(
            plot_df,
            x="Index",
            y=column,
            color="Classification",
            color_discrete_map={"Normal Range": "#2563EB", "Outlier (Anomaly)": "#DC2626"},
            title=f"Outlier Boundary Inspector: {column} ({iqr_multiplier}x IQR)",
            hover_data=[column]
        )

        # Add horizontal threshold boundary lines
        fig.add_hline(y=upper, line_dash="dash", line_color="#D97706", annotation_text=f"Upper Bound: {upper:,.2f}")
        fig.add_hline(y=lower, line_dash="dash", line_color="#D97706", annotation_text=f"Lower Bound: {lower:,.2f}")
        fig.add_hline(y=float(series.median()), line_dash="dot", line_color="#1E40AF", annotation_text=f"Median: {series.median():,.2f}")

        cls.apply_theme(fig)
        return fig

    @classmethod
    def recommend_best_chart(cls, df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
        """Automatically suggest suitable chart configuration based on dataset schemas."""
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["category", "str"]).columns.tolist() if "str" in df.dtypes else df.select_dtypes(exclude=[np.number, "datetime64"]).columns.tolist()
        dt_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        if not dt_cols:
            for c in cat_cols:
                if "date" in c.lower() or "time" in c.lower():
                    dt_cols.append(c)
                    break

        if dt_cols and num_cols:
            return {
                "chart_type": "line",
                "x_col": dt_cols[0],
                "y_col": target_col if target_col in num_cols else num_cols[0],
                "reason": "Temporal column detected; line chart is optimal for observing changes over time."
            }
        elif cat_cols and num_cols:
            return {
                "chart_type": "bar",
                "x_col": cat_cols[0],
                "y_col": target_col if target_col in num_cols else num_cols[0],
                "reason": "Categorical and numerical pairing identified; bar chart best communicates categorical comparisons."
            }
        elif len(num_cols) >= 2:
            return {
                "chart_type": "scatter",
                "x_col": num_cols[0],
                "y_col": num_cols[1],
                "reason": "Multiple numerical metrics available; scatter plot evaluates bivariate distribution and correlation."
            }
        elif num_cols:
            return {
                "chart_type": "histogram",
                "x_col": num_cols[0],
                "reason": "Single numerical feature; histogram reveals distribution shape and variance."
            }
        return {
            "chart_type": "bar",
            "x_col": df.columns[0],
            "y_col": None,
            "reason": "Default categorical representation."
        }
