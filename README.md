# InsightFlow AI — Autonomous Data Analyst Agent (v2.0)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-2563EB.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-1D4ED8.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestrated-102A43.svg)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%20Streaming-2563EB.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-1D4ED8.svg)](LICENSE)

**InsightFlow AI** is a premium, enterprise-grade AI Data Analyst SaaS platform. Built with **Streamlit, Pandas, LangGraph, Groq, Plotly, Scikit-learn, and ReportLab**, it delivers a **ChatGPT-like conversational experience** paired with deterministic mathematical calculations, multi-turn follow-up reasoning, data transformations, interactive Plotly visualizations, time-series forecasting, and executive PDF intelligence reports.

---

## 🎨 Master Design System — Blue & White Theme

The application strictly implements the curated **Blue and White SaaS Palette**:
- **Primary Blue**: `#2563EB`
- **Primary Hover**: `#1D4ED8`
- **Dark Blue**: `#1E40AF`
- **Sidebar Background**: `#102A43`
- **Sidebar Gradient End**: `#163B63`
- **Light Blue**: `#DBEAFE`
- **Pale Blue**: `#EFF6FF`
- **Main Background**: `#FFFFFF`
- **Secondary Background**: `#F8FAFC`
- **Primary Text**: `#111827`
- **Secondary Text**: `#475569`
- **Border**: `#E2E8F0`
- **Success**: `#16A34A`
- **Success Background**: `#DCFCE7`
- **Warning**: `#D97706`
- **Error**: `#DC2626`

---

## 🧭 Application Navigation (8 Pages)

1. **🏠 Home**: Executive launchpad, quick-action cards, drag-and-drop CSV & Excel uploader, sample dataset loaders, KPI health indicators, proactive discoveries ticker, and suggested question chips.
2. **📁 Data Workspace**: File ingestion, multi-sheet Excel selector, schema inspection, dtypes table, summary statistics, and data quality distribution.
3. **💬 Ask AI**: ChatGPT-style conversational assistant with true token-by-token streaming, deterministic Python tool execution, multi-turn memory (resolves "it", "compare with last year", "show a chart of it"), formula pills, Plotly chart attachments, expandable data tables, and 1-click copy & retry actions.
4. **📊 Visualization Studio**: Interactive Plotly studio with manual configuration (Bar, Line, Area, Pie, Donut, Scatter, Box, Heatmap) and AI natural language chart generator, styled with the Blue SaaS colorway.
5. **🧪 Data Lab**: Deterministic data cleaning, deduplication, missing value treatment, type conversion, sort/filter, group/aggregate, safe derived column engineering (AST evaluator), pivot tables, visual outlier inspector & trimmer, and audit trail with 1-click undo/reset.
6. **🔮 Prediction & Insights**: Autoregressive time-series forecasting with 95% confidence intervals, leakage-free regression (Random Forest, Gradient Boosting, Linear) and classification models with interactive "What-If" scenario simulators.
7. **📑 Reports & History**: ReportLab executive PDF report generator, tabular file exports (CSV, XLSX, JSON), stored conversation history, and strategic evidence-based recommendations.
8. **⚙️ Settings & About**: Masked Groq API configuration, live connection latency test, model architecture selector, active color palette preview, system diagnostics, and architecture guides.

---

## 🏗️ Project Architecture

```
Autonomous Data Analyst Agent/
├── .streamlit/
│   ├── config.toml           # Streamlit theme (Blue & White palette)
│   └── secrets.toml.example  # Secrets placeholder template
├── src/
│   ├── config.py             # Centralized color tokens, constants, models
│   ├── data/
│   │   ├── loader.py         # CSV & multi-sheet Excel loader
│   │   ├── profiler.py       # Deterministic dataset profiler
│   │   ├── cleaner.py        # Safe cleaning, AST formula evaluator, pivot, undo & audit
│   │   └── exporter.py       # CSV, Excel XLSX, and JSON converters
│   ├── tools/
│   │   ├── calculator.py     # Metrics, aggregations, growth rates, profit margin, outliers
│   │   ├── visualizer.py     # Plotly chart builder with Blue SaaS palette
│   │   ├── predictor.py      # Scikit-learn regression, classification & forecasting
│   │   └── recommender.py    # Evidence-based recommendation engine
│   ├── agent/
│   │   ├── llm.py            # Groq API client with true token-by-token streaming
│   │   ├── prompts.py        # System instructions & conversational context rules
│   │   ├── tools_registry.py # Pydantic-validated tool dispatching & column resolution
│   │   └── graph.py          # LangGraph state machine & streaming generator
│   ├── reports/
│   │   └── pdf_generator.py  # ReportLab executive PDF report generator
│   └── ui/
│       ├── styles.py         # Blue & White SaaS master CSS tokens & dark navy sidebar
│       └── components.py     # Header banners, KPI cards, prompt cards
├── samples/
│   ├── sales_data.csv        # 1,000+ row sales & profitability dataset
│   ├── customer_churn.csv    # 1,200 row customer churn classification dataset
│   └── student_performance.xlsx # 3-sheet academic performance Excel workbook
├── tests/
│   ├── test_loader.py        # File loader tests
│   ├── test_profiler.py      # Profiler & narrative tests
│   ├── test_cleaner.py       # Cleaning, AST formula, undo & audit tests
│   ├── test_exporter.py      # File format export tests
│   ├── test_calculator.py    # Math & aggregation tests
│   ├── test_visualizer.py    # Plotly visualization tests
│   ├── test_predictor.py     # ML & time-series forecast tests
│   ├── test_recommender.py   # Recommendation & PDF report tests
│   ├── test_agent.py         # LangGraph agent routing tests
│   ├── test_interactive_features.py # Gauge, outlier trimmer & simulator tests
│   └── test_streaming_and_context.py # Streaming, context memory & security tests
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example              # Sample environment variables
├── .gitignore                # Git exclusion rules (secrets & caches protected)
└── README.md
```

---

## 🚀 Getting Started

### 1. Installation
Install the project dependencies using Python 3.12+:
```powershell
python -m pip install -r requirements.txt
```

### 2. Configure Groq API Key (Optional)
InsightFlow AI works in **Deterministic Offline Mode** out-of-the-box. To enable true streaming and advanced conversational reasoning:

1. Obtain a free API key at [Groq Console](https://console.groq.com).
2. Set the environment variable:
   ```powershell
   $env:GROQ_API_KEY="gsk_your_groq_api_key_here"
   ```
   *Alternatively*, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` or enter your API key directly on the **Settings & About** page inside the application.

### 3. Launch the Web Application
```powershell
python -m streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Automated Testing

Run the full automated test suite (67 tests):
```powershell
python -m pytest tests/
```

Run specific test modules:
```powershell
# Test streaming generator & multi-turn memory
python -m pytest tests/test_streaming_and_context.py

# Test LangGraph agent routing & Pydantic validation
python -m pytest tests/test_agent.py

# Test math calculator & safe transformations
python -m pytest tests/test_calculator.py tests/test_cleaner.py

# Test predictive modeling & visualizations
python -m pytest tests/test_predictor.py tests/test_visualizer.py
```

---

## 🛡️ Enterprise Security & Privacy Guarantees

- **Zero Arbitrary Code Execution**: `eval()` and `exec()` are strictly prohibited. User formulas are safely evaluated using Python's `ast` module with whitelist-only operators.
- **Pydantic Validation**: Tool arguments and coordinator outputs are strictly validated via Pydantic schemas.
- **Session Isolation**: All datasets, transformations, and conversations are isolated per session in memory.
- **Secret Protection**: API keys are masked, never exposed in client logs or committed to Git, and excluded by `.gitignore`.

---

## 📄 License
This project is open-source under the MIT License.
"# Autonomous-Data-Analyst-Agent" 
