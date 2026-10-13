"""LangGraph Agent workflow orchestrating request understanding, tool selection, execution, and streaming responses."""
import json
import re
import time
from typing import Dict, List, Any, Optional, TypedDict, Iterator, Tuple
import pandas as pd
import plotly.graph_objects as go
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from src.data.profiler import ProfileReport, DataProfiler
from src.agent.llm import LLMClient
from src.agent.prompts import COORDINATOR_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from src.agent.tools_registry import ToolsRegistry, ToolOutput
from src.config import DEFAULT_GROQ_MODEL


class ToolSelectionModel(BaseModel):
    """Pydantic schema validating coordinator LLM tool selection."""
    thought: Optional[str] = ""
    intent: str = Field(default="calculation")
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    clarification_needed: bool = False


class AgentState(TypedDict, total=False):
    query: str
    chat_history: Optional[List[Dict[str, str]]]
    df: pd.DataFrame
    profile: ProfileReport
    api_key: Optional[str]
    model_name: str
    intent: str
    tool_name: Optional[str]
    tool_args: Dict[str, Any]
    tool_output: Optional[ToolOutput]
    validation_passed: bool
    retry_count: int
    final_response: str
    table: Optional[pd.DataFrame]
    figure: Optional[go.Figure]


class AnalystAgent:
    """Orchestrates autonomous data analysis via LangGraph and Groq with streaming support."""

    @classmethod
    def _resolve_context_from_history(
        cls,
        query: str,
        chat_history: Optional[List[Dict[str, str]]],
        profile: ProfileReport
    ) -> Dict[str, Any]:
        """Extract referenced entities, metrics, or filters from prior conversation turns."""
        context = {
            "last_metric": profile.numerical_columns[0] if profile.numerical_columns else None,
            "last_category": profile.categorical_columns[0] if profile.categorical_columns else None,
            "last_tool": None
        }

        if not chat_history:
            return context

        # Scan previous turns in reverse
        for msg in reversed(chat_history):
            content = msg.get("content", "").lower()
            # Match columns from profile
            for col in profile.numerical_columns:
                if col.lower() in content:
                    context["last_metric"] = col
                    break
            for col in profile.categorical_columns:
                if col.lower() in content:
                    context["last_category"] = col
                    break
            if context["last_metric"] and context["last_category"]:
                break

        return context

    @classmethod
    def _deterministic_router(
        cls,
        query: str,
        df: pd.DataFrame,
        profile: ProfileReport,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """High-precision deterministic rule-based router with multi-turn memory."""
        q_lower = query.lower().strip()
        num_cols = profile.numerical_columns
        cat_cols = profile.categorical_columns
        dt_cols = profile.datetime_columns

        # Context resolution for pronouns like "it", "that", "this"
        context = cls._resolve_context_from_history(query, chat_history, profile)
        referenced_metric = context.get("last_metric") or (num_cols[0] if num_cols else None)
        referenced_category = context.get("last_category") or (cat_cols[0] if cat_cols else None)

        # 1. Recommendation Intent
        if any(w in q_lower for w in ["recommend", "suggestion", "improve", "action", "advice", "opportunity"]):
            return {"intent": "recommendation", "tool_name": "generate_recommendations", "tool_args": {}}

        # 2. Outliers / Anomaly Intent
        if any(w in q_lower for w in ["outlier", "anomaly", "anomalies", "extreme"]):
            target_col = None
            for col in num_cols:
                if col.lower() in q_lower:
                    target_col = col
                    break
            target_col = target_col or referenced_metric or (num_cols[0] if num_cols else None)
            return {"intent": "calculation", "tool_name": "detect_outliers", "tool_args": {"column": target_col, "method": "iqr"}}

        # 3. Missing values / Data Quality Intent
        if any(w in q_lower for w in ["missing", "null", "clean", "nan", "empty"]):
            return {"intent": "calculation", "tool_name": "generate_recommendations", "tool_args": {}}

        # 4. Profit Margin
        if "profit margin" in q_lower or "margin" in q_lower:
            return {"intent": "calculation", "tool_name": "calculate_profit_margin", "tool_args": {"revenue_col": "Revenue", "profit_col": "Profit"}}

        # 5. Correlation Intent
        if any(w in q_lower for w in ["correlation", "relationship between", "relate", "correlate"]):
            cols = [c for c in num_cols if c.lower() in q_lower]
            return {"intent": "calculation", "tool_name": "calculate_correlations", "tool_args": {"columns": cols or num_cols[:4]}}

        # 6. Forecasting / Prediction Intent
        if any(w in q_lower for w in ["forecast", "predict next", "future", "next 30 days", "next 14 days", "projection"]):
            val_col = None
            for col in num_cols:
                if col.lower() in q_lower:
                    val_col = col
                    break
            val_col = val_col or referenced_metric or (num_cols[0] if num_cols else None)
            date_col = dt_cols[0] if dt_cols else "Date"
            
            horizon = 30
            days_match = re.search(r"(\d+)\s*(days|periods|months)", q_lower)
            if days_match:
                horizon = int(days_match.group(1))

            return {"intent": "prediction", "tool_name": "forecast_timeseries", "tool_args": {"date_col": date_col, "value_col": val_col, "horizon_periods": horizon}}

        # 7. Follow-up "Compare with last year" or Period-over-Period
        if any(w in q_lower for w in ["compare with last year", "last year", "compared to previous", "versus last year", "growth"]):
            val_col = referenced_metric or (num_cols[0] if num_cols else None)
            date_col = dt_cols[0] if dt_cols else (df.columns[0] if len(df.columns) > 0 else "")
            return {"intent": "calculation", "tool_name": "calculate_growth_rate", "tool_args": {"date_col": date_col, "value_col": val_col, "freq": "ME"}}

        # 8. ML Model Training Intent (predict churn, classification, regression)
        if any(w in q_lower for w in ["train", "machine learning", "model to predict", "predict churn", "classification", "regression"]):
            for col in profile.potential_targets:
                if col.lower() in q_lower:
                    if col in cat_cols or df[col].nunique() <= 5:
                        return {"intent": "prediction", "tool_name": "train_classification", "tool_args": {"target_col": col}}
                    else:
                        return {"intent": "prediction", "tool_name": "train_regression", "tool_args": {"target_col": col}}

        # 9. Visualization Intent
        if any(w in q_lower for w in ["chart", "graph", "plot", "visualize", "histogram", "scatter", "bar", "pie"]):
            c_type = "bar"
            if "line" in q_lower or "trend" in q_lower:
                c_type = "line"
            elif "pie" in q_lower or "donut" in q_lower:
                c_type = "pie"
            elif "scatter" in q_lower:
                c_type = "scatter"
            elif "box" in q_lower:
                c_type = "box"
            elif "histogram" in q_lower:
                c_type = "histogram"
            elif "heatmap" in q_lower:
                c_type = "heatmap"

            matched_num = [c for c in num_cols if c.lower() in q_lower]
            matched_cat = [c for c in cat_cols if c.lower() in q_lower]
            matched_dt = [c for c in dt_cols if c.lower() in q_lower]

            x_c = matched_dt[0] if matched_dt else (matched_cat[0] if matched_cat else referenced_category)
            y_c = matched_num[0] if matched_num else referenced_metric

            return {"intent": "visualization", "tool_name": "build_chart", "tool_args": {"chart_type": c_type, "x_col": x_c, "y_col": y_c}}

        # 10. Filter Intent
        if any(w in q_lower for w in ["filter", "where", "only rows with", "show rows where"]):
            if "profit is negative" in q_lower or "profit < 0" in q_lower:
                prof_col = ToolsRegistry.resolve_column("Profit", df) or "Profit"
                return {"intent": "filter", "tool_name": "filter_data", "tool_args": {"column": prof_col, "operator": "<", "value": 0}}

        # 11. Top N / Rankings / Group By
        if any(w in q_lower for w in ["top", "highest", "lowest", "best", "worst", "by region", "by category", "by product"]):
            n = 10
            top_match = re.search(r"top\s*(\d+)", q_lower)
            if top_match:
                n = int(top_match.group(1))

            v_col = None
            for col in num_cols:
                if col.lower() in q_lower:
                    v_col = col
                    break
            v_col = v_col or referenced_metric or (num_cols[0] if num_cols else None)

            g_col = None
            for col in cat_cols:
                if col.lower() in q_lower:
                    g_col = col
                    break
            g_col = g_col or referenced_category or (cat_cols[0] if cat_cols else None)

            if g_col and v_col:
                return {"intent": "calculation", "tool_name": "group_by_aggregation", "tool_args": {"group_col": g_col, "value_col": v_col, "top_n": n, "agg_func": "sum"}}

        # 12. Single Column Metric Calculation (sum, average, total, mean, min, max, count)
        op = "sum"
        if any(w in q_lower for w in ["average", "mean", "avg"]):
            op = "mean"
        elif "median" in q_lower:
            op = "median"
        elif any(w in q_lower for w in ["minimum", "min", "lowest"]):
            op = "min"
        elif any(w in q_lower for w in ["maximum", "max", "highest", "peak"]):
            op = "max"
        elif any(w in q_lower for w in ["count", "how many", "number of"]):
            op = "count"

        target_col = None
        for col in num_cols:
            if col.lower() in q_lower:
                target_col = col
                break
        if not target_col and op == "count" and len(df.columns) > 0:
            target_col = df.columns[0]
        target_col = target_col or referenced_metric or (num_cols[0] if num_cols else df.columns[0])

        return {"intent": "calculation", "tool_name": "calculate_metric", "tool_args": {"column": target_col, "operation": op}}

    @classmethod
    def understand_node(cls, state: AgentState) -> AgentState:
        """Parse user query against dataset schema and plan tool."""
        query = state.get("query", "")
        chat_history = state.get("chat_history")
        df = state.get("df")
        profile = state.get("profile")
        api_key = state.get("api_key")
        model_name = state.get("model_name", DEFAULT_GROQ_MODEL)

        schema_summary = {
            "columns": list(df.columns),
            "numerical_columns": profile.numerical_columns,
            "categorical_columns": profile.categorical_columns,
            "datetime_columns": profile.datetime_columns,
            "row_count": profile.row_count,
            "potential_targets": profile.potential_targets
        }

        routed = None

        # Try Groq LLM if key is available
        if LLMClient.is_available(api_key):
            try:
                system_prompt = COORDINATOR_SYSTEM_PROMPT + f"\n\nCURRENT DATASET SCHEMA:\n{json.dumps(schema_summary)}"
                messages = [{"role": "system", "content": system_prompt}]

                # Include prior conversation turns for context
                if chat_history:
                    for turn in chat_history[-6:]:
                        messages.append({"role": turn["role"], "content": turn["content"]})

                messages.append({"role": "user", "content": f"User query: '{query}'"})

                raw_resp = LLMClient.call_raw(
                    messages=messages,
                    explicit_key=api_key,
                    model_name=model_name,
                    response_format={"type": "json_object"}
                )
                if raw_resp:
                    parsed_raw = json.loads(raw_resp)
                    validated_selection = ToolSelectionModel.model_validate(parsed_raw)
                    routed = validated_selection.model_dump()
            except Exception:
                routed = None

        # Fallback to deterministic routing with multi-turn memory
        if not routed or "tool_name" not in routed:
            routed = cls._deterministic_router(query, df, profile, chat_history)

        state["intent"] = routed.get("intent", "calculation")
        state["tool_name"] = routed.get("tool_name")
        state["tool_args"] = routed.get("tool_args", {})
        return state

    @classmethod
    def execute_node(cls, state: AgentState) -> AgentState:
        """Invoke planned tool through safe tools registry."""
        tool_name = state.get("tool_name")
        tool_args = state.get("tool_args", {})
        df = state.get("df")
        profile = state.get("profile")

        output = ToolsRegistry.execute(
            tool_name=tool_name,
            tool_args=tool_args,
            df=df,
            profile=profile
        )

        state["tool_output"] = output
        state["table"] = output.table
        state["figure"] = output.figure
        return state

    @classmethod
    def validate_node(cls, state: AgentState) -> AgentState:
        """Verify tool output accuracy and completeness."""
        output: Optional[ToolOutput] = state.get("tool_output")
        retries = state.get("retry_count", 0)

        if output and output.success:
            state["validation_passed"] = True
        else:
            state["validation_passed"] = False
            state["retry_count"] = retries + 1

        return state

    @classmethod
    def synthesize_node(cls, state: AgentState) -> AgentState:
        """Formulate executive response based strictly on validated output."""
        query = state.get("query", "")
        output: Optional[ToolOutput] = state.get("tool_output")
        api_key = state.get("api_key")
        model_name = state.get("model_name", DEFAULT_GROQ_MODEL)

        if not output or not output.success:
            err_msg = output.error if output else "Unable to execute requested analysis."
            state["final_response"] = (
                f"⚠️ **Could not complete calculation**: {err_msg}\n\n"
                f"Please verify that the requested metrics match the dataset columns: "
                f"`{', '.join(list(state['df'].columns)[:6])}`."
            )
            return state

        deterministic_resp = f"### Analysis Result\n\n{output.text_summary}\n\n"
        if output.formula:
            deterministic_resp += f"**Calculation Method**: `{output.formula}`\n\n"

        if LLMClient.is_available(api_key):
            try:
                prompt = (
                    f"User asked: '{query}'\n"
                    f"Validated Tool Used: '{output.tool_name}'\n"
                    f"Formula: '{output.formula}'\n"
                    f"Result Summary: '{output.text_summary}'\n\n"
                    "Synthesize a polished, professional 2-3 paragraph data analysis response "
                    "following the SYNTHESIS_SYSTEM_PROMPT. Do not alter any numbers."
                )
                messages = [
                    {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
                llm_synth = LLMClient.call_raw(
                    messages=messages,
                    explicit_key=api_key,
                    model_name=model_name
                )
                if llm_synth:
                    state["final_response"] = llm_synth
                    return state
            except Exception:
                pass

        state["final_response"] = deterministic_resp
        return state

    @classmethod
    def build_graph(cls):
        """Compile the LangGraph workflow."""
        builder = StateGraph(AgentState)

        builder.add_node("understand_request", cls.understand_node)
        builder.add_node("execute_tool", cls.execute_node)
        builder.add_node("validate_result", cls.validate_node)
        builder.add_node("synthesize_response", cls.synthesize_node)

        builder.set_entry_point("understand_request")
        builder.add_edge("understand_request", "execute_tool")
        builder.add_edge("execute_tool", "validate_result")

        def should_retry(state: AgentState):
            if not state.get("validation_passed") and state.get("retry_count", 0) <= 1:
                state["tool_name"] = "generate_recommendations"
                state["tool_args"] = {}
                return "execute_tool"
            return "synthesize_response"

        builder.add_conditional_edges("validate_result", should_retry, {
            "execute_tool": "execute_tool",
            "synthesize_response": "synthesize_response"
        })
        builder.add_edge("synthesize_response", END)

        return builder.compile()

    @classmethod
    def run(
        cls,
        query: str,
        df: pd.DataFrame,
        profile: Optional[ProfileReport] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL
    ) -> Dict[str, Any]:
        """Execute query end-to-end synchronously."""
        if profile is None:
            profile = DataProfiler.profile(df)

        graph = cls.build_graph()
        initial_state: AgentState = {
            "query": query,
            "chat_history": chat_history,
            "df": df,
            "profile": profile,
            "api_key": api_key,
            "model_name": model_name,
            "retry_count": 0,
            "validation_passed": False
        }

        final_state = graph.invoke(initial_state)
        return {
            "response": final_state.get("final_response", ""),
            "intent": final_state.get("intent", ""),
            "tool_name": final_state.get("tool_name", ""),
            "table": final_state.get("table"),
            "figure": final_state.get("figure"),
            "formula": getattr(final_state.get("tool_output"), "formula", None) if final_state.get("tool_output") else None,
            "success": final_state.get("validation_passed", False)
        }

    @classmethod
    def run_stream(
        cls,
        query: str,
        df: pd.DataFrame,
        profile: Optional[ProfileReport] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL
    ) -> Tuple[Iterator[str], Dict[str, Any]]:
        """Executes tool deterministically and returns a generator stream for text synthesis."""
        if profile is None:
            profile = DataProfiler.profile(df)

        # 1. Run understanding and tool execution synchronously
        state: AgentState = {
            "query": query,
            "chat_history": chat_history,
            "df": df,
            "profile": profile,
            "api_key": api_key,
            "model_name": model_name,
            "retry_count": 0,
            "validation_passed": False
        }
        state = cls.understand_node(state)
        state = cls.execute_node(state)
        state = cls.validate_node(state)

        output: Optional[ToolOutput] = state.get("tool_output")

        metadata = {
            "intent": state.get("intent", ""),
            "tool_name": state.get("tool_name", ""),
            "table": state.get("table"),
            "figure": state.get("figure"),
            "formula": output.formula if output else None,
            "success": state.get("validation_passed", False),
            "error": output.error if output else None
        }

        # 2. Generator function yielding tokens
        def stream_generator() -> Iterator[str]:
            if not output or not output.success:
                err_msg = output.error if output else "Unable to execute requested analysis."
                yield f"⚠️ **Could not complete calculation**: {err_msg}\n\n"
                yield f"Please verify that the requested metrics match the dataset columns: "
                yield f"`{', '.join(list(df.columns)[:6])}`."
                return

            if LLMClient.is_available(api_key):
                prompt = (
                    f"User asked: '{query}'\n"
                    f"Validated Tool Used: '{output.tool_name}'\n"
                    f"Formula: '{output.formula}'\n"
                    f"Result Summary: '{output.text_summary}'\n\n"
                    "Synthesize a polished, professional 2-3 paragraph data analysis response "
                    "following the SYNTHESIS_SYSTEM_PROMPT. Do not alter any numbers."
                )
                messages = [
                    {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
                streamed_any = False
                for token in LLMClient.stream_raw(messages, explicit_key=api_key, model_name=model_name):
                    streamed_any = True
                    yield token
                if streamed_any:
                    return

            # Fallback deterministic streaming
            det_text = f"### Analysis Result\n\n{output.text_summary}\n\n"
            if output.formula:
                det_text += f"**Calculation Method**: `{output.formula}`\n\n"
            det_text += "💡 *Follow-up: You can ask to visualize this, forecast future periods, or segment by categories.*"

            # Smooth token chunking
            chunks = det_text.split(" ")
            for i, chunk in enumerate(chunks):
                yield chunk + (" " if i < len(chunks) - 1 else "")
                time.sleep(0.015)

        return stream_generator(), metadata
