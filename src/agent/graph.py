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
from src.agent.prompts import (
    DN_AI_NAME, COORDINATOR_SYSTEM_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT, GENERAL_AI_SYSTEM_PROMPT
)
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
    df: Optional[pd.DataFrame]
    profile: Optional[ProfileReport]
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
    """Orchestrates DN AI dual-mode assistant and data analysis via LangGraph and Groq with streaming support."""

    @classmethod
    def _is_general_ai_query(cls, query: str, df: Optional[pd.DataFrame] = None) -> bool:
        """Identify if query is general knowledge, programming, AI/ML theory, or educational without dataset."""
        q_lower = query.lower().strip()

        # If query references any column in the active dataset, treat as data query
        if df is not None:
            for col in df.columns:
                c_name = str(col).lower()
                if len(c_name) >= 3 and re.search(r'\b' + re.escape(c_name) + r'\b', q_lower):
                    return False

        # General programming, conceptual, and educational regex patterns
        patterns = [
            r"^explain\s+(artificial\s+intelligence|agent|agents|gradient\s+descent|machine\s+learning|deep\s+learning|neural\s+network|transformer|llm|nlp|statistics|probability|calculus|python|sql)",
            r"^what\s+is\s+(artificial\s+intelligence|gradient\s+descent|a\s+database|an\s+agent|a\s+neural\s+network|a\s+transformer|an\s+llm|machine\s+learning|deep\s+learning|linear\s+regression|overfitting|regularization|p-value|standard\s+deviation)",
            r"^how\s+to\s+(debug|write|code|implement|optimize|learn|train|build)",
            r"^how\s+do\s+i\s+(debug|write|code|reverse|optimize|sort)",
            r"debug\s+(this|my|the)?\s*(python|code|error|exception|script|traceback)",
            r"(syntaxerror|typeerror|valueerror|indexerror|keyerror|attributeerror|importerror|indentationerror)",
            r"^write\s+(a\s+)?(python|script|code|function|sql|email|essay|paragraph|poem|summary)",
            r"difference\s+between\s+(supervised|unsupervised|classification|regression|bagging|boosting|sql|nosql)",
            r"(what\s+is\s+a\s+database|what\s+are\s+databases|explain\s+databases)"
        ]
        for p in patterns:
            if re.search(p, q_lower):
                return True

        # Pure educational or definition queries without calculation keywords
        conceptual_starts = ["explain ", "what is ", "what are ", "how does ", "why does ", "tutorial on ", "teach me ", "define "]
        data_calc_terms = [
            "calculate", "sum", "average", "mean", "median", "total", "max", "min",
            "highest", "lowest", "count", "forecast", "predict", "chart", "graph",
            "plot", "filter", "profit", "revenue", "margin", "sales", "churn",
            "outlier", "my data", "this dataset", "the file", "the data", "compare with last year", "show a chart"
        ]
        if any(q_lower.startswith(cs) for cs in conceptual_starts):
            if not any(term in q_lower for term in data_calc_terms):
                return True

        return False

    @classmethod
    def _is_data_analysis_intent(cls, query: str) -> bool:
        """Check if query is asking to analyze dataset when no dataset is loaded."""
        q_lower = query.lower().strip()
        data_terms = [
            "data", "dataset", "revenue", "profit", "sales", "cost", "margin",
            "calculate", "sum", "average", "mean", "median", "total", "max", "min",
            "highest", "lowest", "chart", "graph", "plot", "forecast", "predict",
            "filter", "group by", "outlier", "churn", "rows", "columns", "table",
            "compare with last year", "growth rate", "trend"
        ]
        if any(term in q_lower for term in data_terms):
            if not (q_lower.startswith("what is a database") or q_lower.startswith("what is data science") or "explain database" in q_lower):
                return True
        return False

    @classmethod
    def _deterministic_general_answer(cls, query: str) -> str:
        """Provide structured educational answers when offline for common questions."""
        q_lower = query.lower().strip()

        if "artificial intelligence" in q_lower or "agent" in q_lower:
            return (
                "### Artificial Intelligence (AI) Agents\n\n"
                "An **AI Agent** is an autonomous entity that perceives its environment through inputs, "
                "reasons using internal policies or language models, and takes deterministic actions via tools "
                "to accomplish specific objectives.\n\n"
                "**Core Architectural Pillars**:\n"
                "1. **Perception**: Ingesting user instructions, multi-turn dialogue, and environment state.\n"
                "2. **Reasoning & Planning**: Decomposing complex tasks into execution sub-goals (e.g., ReAct, Chain-of-Thought, LangGraph state machines).\n"
                "3. **Memory**: Managing short-term working context and long-term episodic or semantic memory.\n"
                "4. **Tool Use & Actuation**: Interfacing with APIs, databases, Python calculators, and external environments.\n"
                "5. **Validation & Self-Correction**: Verifying tool outputs against ground truth and dynamically recovering from errors."
            )

        if "gradient descent" in q_lower:
            return (
                "### Gradient Descent Optimization\n\n"
                "**Gradient Descent** is an iterative first-order optimization algorithm used to minimize a loss (cost) function $J(\\theta)$ "
                "by adjusting parameters in the direction of steepest descent.\n\n"
                "**Mathematical Update Rule**:\n"
                "$$\\theta_{t+1} = \\theta_t - \\eta \\cdot \\nabla J(\\theta_t)$$\n"
                "- $\\theta$: Model parameters (weights and biases)\n"
                "- $\\eta$: Learning rate (step size controlling convergence)\n"
                "- $\\nabla J(\\theta)$: Gradient vector of partial derivatives with respect to parameters\n\n"
                "**Standard Variants**:\n"
                "- **Batch Gradient Descent**: Evaluates the full dataset per gradient update.\n"
                "- **Stochastic Gradient Descent (SGD)**: Updates weights using one random observation at a time.\n"
                "- **Mini-Batch Gradient Descent**: Updates weights over batches (e.g., 32-512 samples), balancing computational stability and speed."
            )

        if "debug" in q_lower or "error" in q_lower or "exception" in q_lower:
            return (
                "### Python Error Debugging Framework\n\n"
                "When debugging Python scripts, inspect the traceback from bottom to top to identify the exact exception location and type:\n\n"
                "```python\n"
                "# 1. IndexError: list index out of range\n"
                "# Fix: Ensure index is strictly within range [0, len(items) - 1]\n"
                "items = [10, 20, 30]\n"
                "if 0 <= target_idx < len(items):\n"
                "    print(items[target_idx])\n\n"
                "# 2. KeyError: 'column_name'\n"
                "# Fix: Check column existence before indexing or use dict.get()\n"
                "if 'Revenue' in df.columns:\n"
                "    total = df['Revenue'].sum()\n\n"
                "# 3. TypeError: unsupported operand type(s)\n"
                "# Fix: Convert data types explicitly (e.g., pd.to_numeric())\n"
                "df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')\n"
                "```\n\n"
                "Paste the specific error message or snippet, and DN AI will isolate the exact bug and provide the fix!"
            )

        if "database" in q_lower:
            return (
                "### What is a Database?\n\n"
                "A **database** is an organized collection of structured or semi-structured data stored electronically in a computer system, "
                "typically controlled by a **Database Management System (DBMS)**.\n\n"
                "- **Relational Databases (RDBMS)**: Use tables with rows and columns, enforce ACID properties, and utilize SQL (e.g., PostgreSQL, MySQL, BigQuery).\n"
                "- **NoSQL Databases**: Optimized for document, key-value, column-family, or graph architectures (e.g., MongoDB, Redis, Neo4j).\n"
                "- **Analytical Data Warehouses**: Columnar storage optimized for OLAP aggregations across billions of records (e.g., Snowflake, BigQuery, ClickHouse)."
            )

        return (
            "**DN AI**: I am ready to help with general programming, machine learning concepts, mathematics, writing, "
            "and autonomous data analysis. Feel free to ask any question or upload a dataset to begin!"
        )

    @classmethod
    def _resolve_context_from_history(
        cls,
        query: str,
        chat_history: Optional[List[Dict[str, str]]],
        profile: Optional[ProfileReport]
    ) -> Dict[str, Any]:
        """Extract referenced entities, metrics, or filters from prior conversation turns."""
        num_cols = profile.numerical_columns if profile else []
        cat_cols = profile.categorical_columns if profile else []

        context = {
            "last_metric": num_cols[0] if num_cols else None,
            "last_category": cat_cols[0] if cat_cols else None,
            "last_tool": None
        }

        if not chat_history:
            return context

        # Scan previous turns in reverse
        for msg in reversed(chat_history):
            content = msg.get("content", "").lower()
            if profile:
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
        df: Optional[pd.DataFrame],
        profile: Optional[ProfileReport],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """High-precision deterministic rule-based router with multi-turn memory."""
        q_lower = query.lower().strip()

        # If no dataset is active
        if df is None:
            if cls._is_data_analysis_intent(query):
                return {"intent": "needs_dataset", "tool_name": "prompt_dataset_upload", "tool_args": {}}
            return {"intent": "general_ai", "tool_name": "general_chat", "tool_args": {"query": query}}

        # When dataset is active: check if this is purely a general AI query
        if cls._is_general_ai_query(query, df):
            return {"intent": "general_ai", "tool_name": "general_chat", "tool_args": {"query": query}}

        num_cols = profile.numerical_columns if profile else []
        cat_cols = profile.categorical_columns if profile else []
        dt_cols = profile.datetime_columns if profile else []

        # Context resolution for pronouns like "it", "that", "this"
        context = cls._resolve_context_from_history(query, chat_history, profile)
        referenced_metric = context.get("last_metric") or (num_cols[0] if num_cols else None)
        referenced_category = context.get("last_category") or (cat_cols[0] if cat_cols else None)

        # 0. Conversational follow-ups to prior turns
        if chat_history and len(chat_history) > 0:
            if any(w in q_lower for w in ["explain simply", "explain it simply", "in simple words", "explain the result in simple words", "simplify this"]):
                return {"intent": "follow_up_explanation", "tool_name": "general_chat", "tool_args": {"mode": "explain_simply"}}

            if any(w in q_lower for w in ["why is it performing better", "why is it doing better", "why is this happening", "why is it higher", "why is it lower"]):
                return {"intent": "follow_up_reasoning", "tool_name": "general_chat", "tool_args": {"mode": "explain_factors"}}

            if any(w in q_lower for w in ["show me a chart", "show a chart of it", "chart it", "plot it", "visualize it"]):
                c_type = "bar"
                if "line" in q_lower or "trend" in q_lower:
                    c_type = "line"
                elif "pie" in q_lower or "donut" in q_lower:
                    c_type = "pie"
                return {
                    "intent": "visualization",
                    "tool_name": "build_chart",
                    "tool_args": {
                        "chart_type": c_type,
                        "x_col": referenced_category or (cat_cols[0] if cat_cols else None),
                        "y_col": referenced_metric or (num_cols[0] if num_cols else None)
                    }
                }

        # 1. Dataset Overview / "Analyze my sales data"
        if any(w in q_lower for w in ["analyze my sales data", "analyze the data", "analyze my data", "overview of the data", "dataset overview", "inspect my data", "analyze dataset"]):
            return {"intent": "recommendation", "tool_name": "dataset_overview", "tool_args": {}}

        # 2. Recommendations Intent
        if any(w in q_lower for w in ["recommend", "action", "strategic", "advice", "opportunity", "what should i do"]):
            return {"intent": "recommendation", "tool_name": "generate_recommendations", "tool_args": {}}

        # 3. Outlier / Anomaly Detection Intent
        if any(w in q_lower for w in ["outlier", "anomaly", "irregular", "extreme values"]):
            target_col = None
            for col in num_cols:
                if col.lower() in q_lower:
                    target_col = col
                    break
            target_col = target_col or referenced_metric or (num_cols[0] if num_cols else None)
            return {"intent": "calculation", "tool_name": "detect_outliers", "tool_args": {"column": target_col, "method": "iqr"}}

        # 4. Correlation Intent
        if any(w in q_lower for w in ["correlat", "relationship between", "association"]):
            return {"intent": "calculation", "tool_name": "calculate_correlations", "tool_args": {"columns": num_cols}}

        # 5. Profit Margin Intent
        if any(w in q_lower for w in ["profit margin", "margin percentage", "margin %"]):
            return {"intent": "calculation", "tool_name": "calculate_profit_margin", "tool_args": {}}

        # 6. Time-Series Forecasting Intent
        if any(w in q_lower for w in ["forecast", "predict next", "future", "trajectory", "expected next"]):
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
        if any(w in q_lower for w in ["compare with last year", "last year", "compared to previous", "versus last year", "compare it with last year", "growth", "month with last month", "compare this month"]):
            val_col = referenced_metric or (num_cols[0] if num_cols else None)
            date_col = dt_cols[0] if dt_cols else (df.columns[0] if df is not None and len(df.columns) > 0 else "")
            return {"intent": "calculation", "tool_name": "calculate_growth_rate", "tool_args": {"date_col": date_col, "value_col": val_col, "freq": "ME"}}

        # 8. ML Model Training Intent (predict churn, classification, regression)
        if any(w in q_lower for w in ["train", "machine learning", "model to predict", "predict churn", "classification", "regression"]):
            if profile and profile.potential_targets:
                for col in profile.potential_targets:
                    if col.lower() in q_lower:
                        if col in cat_cols or df[col].nunique() <= 5:
                            return {"intent": "prediction", "tool_name": "train_classification", "tool_args": {"target_col": col}}
                        else:
                            return {"intent": "prediction", "tool_name": "train_regression", "tool_args": {"target_col": col}}

        # 9. Visualization Intent
        if any(w in q_lower for w in ["chart", "graph", "plot", "visualize", "histogram", "scatter", "bar", "pie", "regional performance"]):
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
        if any(w in q_lower for w in ["top", "highest", "lowest", "best", "worst", "by region", "by category", "by product", "most profitable", "highest profit"]):
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
        if not target_col and op == "count" and df is not None and len(df.columns) > 0:
            target_col = df.columns[0]
        target_col = target_col or referenced_metric or (num_cols[0] if num_cols else (df.columns[0] if df is not None and len(df.columns) > 0 else None))

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

        # 1. No dataset loaded
        if df is None:
            det_routed = cls._deterministic_router(query, None, None, chat_history)
            state["intent"] = det_routed.get("intent", "general_ai")
            state["tool_name"] = det_routed.get("tool_name", "general_chat")
            state["tool_args"] = det_routed.get("tool_args", {})
            return state

        # 2. General AI query even with dataset loaded
        if cls._is_general_ai_query(query, df):
            state["intent"] = "general_ai"
            state["tool_name"] = "general_chat"
            state["tool_args"] = {"query": query}
            return state

        schema_summary = {
            "columns": list(df.columns),
            "numerical_columns": profile.numerical_columns if profile else [],
            "categorical_columns": profile.categorical_columns if profile else [],
            "datetime_columns": profile.datetime_columns if profile else [],
            "row_count": profile.row_count if profile else len(df),
            "potential_targets": profile.potential_targets if profile else []
        }

        routed = None

        # 3. Try Groq LLM Coordinator if key is available
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

        # 4. Fallback to deterministic routing with multi-turn memory
        if not routed or "tool_name" not in routed or routed.get("tool_name") == "ask_clarification":
            det_routed = cls._deterministic_router(query, df, profile, chat_history)
            if det_routed and det_routed.get("tool_name") != "ask_clarification":
                routed = det_routed
            elif not routed or "tool_name" not in routed:
                routed = det_routed

        state["intent"] = routed.get("intent", "calculation")
        state["tool_name"] = routed.get("tool_name")
        state["tool_args"] = routed.get("tool_args", {})
        return state

    @classmethod
    def execute_node(cls, state: AgentState) -> AgentState:
        """Invoke planned tool through safe tools registry."""
        tool_name = state.get("tool_name")
        tool_args = state.get("tool_args", {})
        intent = state.get("intent", "")
        df = state.get("df")
        profile = state.get("profile")

        if intent == "general_ai" or tool_name == "general_chat":
            output = ToolOutput(
                tool_name="general_chat",
                success=True,
                text_summary=state.get("query", ""),
                raw_result={"status": "general_ai"}
            )
        elif intent == "needs_dataset" or tool_name == "prompt_dataset_upload":
            output = ToolOutput(
                tool_name="prompt_dataset_upload",
                success=True,
                text_summary="To analyze metrics or generate charts, please upload a dataset.",
                raw_result={"status": "needs_dataset"}
            )
        elif intent in ("follow_up_explanation", "follow_up_reasoning"):
            output = ToolOutput(
                tool_name="general_chat",
                success=True,
                text_summary=state.get("query", ""),
                raw_result={"status": intent}
            )
        else:
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
        intent = state.get("intent", "")
        tool_name = state.get("tool_name", "")
        chat_history = state.get("chat_history")

        # 1. General AI mode
        if intent == "general_ai" or tool_name == "general_chat":
            if LLMClient.is_available(api_key):
                messages = [{"role": "system", "content": GENERAL_AI_SYSTEM_PROMPT}]
                if chat_history:
                    for turn in chat_history[-6:]:
                        if turn.get("role") in ("user", "assistant") and turn.get("content"):
                            messages.append({"role": turn["role"], "content": turn["content"]})
                messages.append({"role": "user", "content": query})

                llm_ans = LLMClient.call_raw(messages=messages, explicit_key=api_key, model_name=model_name)
                if llm_ans:
                    state["final_response"] = llm_ans
                    return state

            state["final_response"] = cls._deterministic_general_answer(query)
            return state

        # 2. Needs dataset mode
        if intent == "needs_dataset" or tool_name == "prompt_dataset_upload":
            state["final_response"] = (
                "📂 **Dataset Required for Analysis**\n\n"
                "To analyze specific metrics, build charts, or run predictions, please upload your CSV or Excel file via the **Home** or **Data Workspace** page.\n\n"
                "💡 *Quick Tip*: You can also choose one of our curated sample datasets on the **Home** page (*Sales & Profitability*, *Customer Churn*, or *Student Performance*) to test DN AI immediately!"
            )
            return state

        # 3. Follow-up conversational reasoning
        if intent in ("follow_up_explanation", "follow_up_reasoning"):
            if LLMClient.is_available(api_key):
                prompt_followup = (
                    f"USER FOLLOW-UP: '{query}'\n"
                    f"INTENT: {'Explain the previous result simply in plain words' if intent == 'follow_up_explanation' else 'Examine available data evidence and explain possible business drivers, distinguishing measured facts from hypotheses'}\n\n"
                    f"CONVERSATION HISTORY:\n"
                )
                messages = [{"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT}]
                if chat_history:
                    for turn in chat_history[-6:]:
                        messages.append({"role": turn["role"], "content": turn["content"]})
                messages.append({"role": "user", "content": prompt_followup})

                llm_follow = LLMClient.call_raw(messages=messages, explicit_key=api_key, model_name=model_name)
                if llm_follow:
                    state["final_response"] = llm_follow
                    return state

        if not output or not output.success:
            err_msg = output.error if output else "Unable to execute requested analysis."
            col_hint = f"`{', '.join(list(state['df'].columns)[:6])}`" if state.get("df") is not None else "Please upload a dataset."
            state["final_response"] = (
                f"⚠️ **Could not complete calculation**: {err_msg}\n\n"
                f"Please verify that the requested metrics match the dataset columns: {col_hint}."
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
                    "Synthesize an authoritative, professional executive data analysis response "
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
        df: Optional[pd.DataFrame] = None,
        profile: Optional[ProfileReport] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL
    ) -> Dict[str, Any]:
        """Execute query end-to-end synchronously."""
        if profile is None and df is not None:
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
        df: Optional[pd.DataFrame] = None,
        profile: Optional[ProfileReport] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL
    ) -> Tuple[Iterator[str], Dict[str, Any]]:
        """Executes tool deterministically and returns a generator stream for text synthesis."""
        if profile is None and df is not None:
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
        intent = state.get("intent", "")
        tool_name = state.get("tool_name", "")

        metadata = {
            "intent": intent,
            "tool_name": tool_name,
            "table": state.get("table"),
            "figure": state.get("figure"),
            "formula": output.formula if output else None,
            "success": state.get("validation_passed", False),
            "error": output.error if output else None
        }

        # 2. Generator function yielding tokens
        def stream_generator() -> Iterator[str]:
            # Mode A: General AI stream
            if intent == "general_ai" or tool_name == "general_chat":
                if LLMClient.is_available(api_key):
                    messages = [{"role": "system", "content": GENERAL_AI_SYSTEM_PROMPT}]
                    if chat_history:
                        for turn in chat_history[-6:]:
                            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                                messages.append({"role": turn["role"], "content": turn["content"]})
                    messages.append({"role": "user", "content": query})

                    streamed_any = False
                    for token in LLMClient.stream_raw(messages, explicit_key=api_key, model_name=model_name):
                        streamed_any = True
                        yield token
                    if streamed_any:
                        return

                # Offline fallback for general questions
                det_ans = cls._deterministic_general_answer(query)
                for chunk in det_ans.split(" "):
                    yield chunk + " "
                    time.sleep(0.01)
                return

            # Needs dataset guidance
            if intent == "needs_dataset" or tool_name == "prompt_dataset_upload":
                advice = (
                    "📂 **Dataset Required for Analysis**\n\n"
                    "To analyze specific metrics, build charts, or run predictions, please upload your CSV or Excel file via the **Home** or **Data Workspace** page.\n\n"
                    "💡 *Quick Tip*: You can also choose one of our curated sample datasets on the **Home** page (*Sales & Profitability*, *Customer Churn*, or *Student Performance*) to test DN AI immediately!"
                )
                for chunk in advice.split(" "):
                    yield chunk + " "
                    time.sleep(0.01)
                return

            # Follow-up conversational reasoning / simple explanation
            if intent in ("follow_up_explanation", "follow_up_reasoning"):
                if LLMClient.is_available(api_key):
                    prompt_followup = (
                        f"USER FOLLOW-UP: '{query}'\n"
                        f"INTENT: {'Explain the previous result simply in plain words' if intent == 'follow_up_explanation' else 'Examine available data evidence and explain possible business drivers, distinguishing measured facts from hypotheses'}\n\n"
                        f"CONVERSATION HISTORY:\n"
                    )
                    messages = [{"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT}]
                    if chat_history:
                        for turn in chat_history[-6:]:
                            messages.append({"role": turn["role"], "content": turn["content"]})
                    messages.append({"role": "user", "content": prompt_followup})

                    streamed_any = False
                    for token in LLMClient.stream_raw(messages, explicit_key=api_key, model_name=model_name):
                        streamed_any = True
                        yield token
                    if streamed_any:
                        return

            # Failed tool output
            if not output or not output.success:
                err_msg = output.error if output else "Unable to execute requested analysis."
                yield f"⚠️ **Could not complete calculation**: {err_msg}\n\n"
                if df is not None and len(df.columns) > 0:
                    yield f"Please verify that the requested metrics match the dataset columns: "
                    yield f"`{', '.join(list(df.columns)[:6])}`."
                return

            # Mode B: Validated dataset tool synthesis
            if LLMClient.is_available(api_key):
                prompt = (
                    f"User asked: '{query}'\n"
                    f"Validated Tool Used: '{output.tool_name}'\n"
                    f"Formula: '{output.formula or 'None'}'\n"
                    f"Result Summary: '{output.text_summary}'\n\n"
                    "Synthesize an authoritative, professional executive data analysis response "
                    "following the SYNTHESIS_SYSTEM_PROMPT. "
                    "Include Direct Answer first with exact numbers, Key Metrics, Insights, Method, and 2-3 Follow-up Suggestions. "
                    "Do not alter any numbers."
                )
                messages = [
                    {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
                tokens_streamed = []
                for token in LLMClient.stream_raw(messages, explicit_key=api_key, model_name=model_name):
                    tokens_streamed.append(token)
                    yield token
                if len(tokens_streamed) >= 5:
                    return

            # Fallback deterministic streaming
            det_text = f"### Analysis Result\n\n{output.text_summary}\n\n"
            if output.formula:
                det_text += f"**Calculation Method**: `{output.formula}`\n\n"
            det_text += "💡 *Follow-up: You can ask to visualize this, forecast future periods, or segment by categories.*"

            chunks = det_text.split(" ")
            for i, chunk in enumerate(chunks):
                yield chunk + (" " if i < len(chunks) - 1 else "")
                time.sleep(0.015)

        return stream_generator(), metadata


# Export alias for DN AI
DNAIAgent = AnalystAgent
