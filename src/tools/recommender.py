"""Evidence-based recommendation engine synthesizing observations into actionable next steps."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from src.data.profiler import ProfileReport
from src.tools.calculator import DataCalculator


@dataclass
class RecommendationItem:
    """Structured actionable recommendation."""
    id: str
    category: str  # e.g. 'Revenue & Profitability', 'Customer Churn', 'Data Quality', 'Operational'
    title: str
    observation: str  # Observed Fact with metric
    why_it_matters: str  # Impact / Business Significance
    suggested_action: str  # Concrete Actionable Next Step
    evidence_type: str = "Observed Fact"  # 'Observed Fact', 'Statistical Correlation', 'Model Prediction'
    priority: str = "High"  # 'High', 'Medium', 'Low'


@dataclass
class RecommendationReport:
    """Collection of evidence-backed recommendations."""
    recommendations: List[RecommendationItem] = field(default_factory=list)
    total_recommendations: int = 0
    high_priority_count: int = 0
    summary_markdown: str = ""


class RecommendationEngine:
    """Analyzes datasets to synthesize deterministic, evidence-backed strategic guidance."""

    @classmethod
    def generate_recommendations(
        cls,
        df: pd.DataFrame,
        profile: Optional[ProfileReport] = None
    ) -> RecommendationReport:
        """Scan dataset and generate prioritized, evidence-backed recommendations."""
        if df is None or df.empty:
            return RecommendationReport(
                recommendations=[],
                summary_markdown="No recommendations can be derived from an empty dataset."
            )

        items: List[RecommendationItem] = []
        cols_lower = {c.lower(): c for c in df.columns}

        # 1. Check Data Quality & Completeness
        if profile and profile.missing_cells > 0:
            high_null_cols = [c for c, p in profile.columns.items() if p.null_pct > 5.0]
            if high_null_cols:
                items.append(RecommendationItem(
                    id="REC-DQ-01",
                    category="Data Quality & Governance",
                    title="Impute or Cleanse High-Missingness Columns",
                    observation=f"Columns {', '.join([f'`{c}` ({profile.columns[c].null_pct}%)' for c in high_null_cols[:3]])} exhibit significant missingness (> 5% null values).",
                    why_it_matters="Missing feature values introduce bias into statistical aggregations and degrade downstream machine learning performance.",
                    suggested_action="Navigate to Data Lab to impute numerical columns with median/mean or apply categorical forward-fill before training models.",
                    evidence_type="Observed Fact",
                    priority="Medium"
                ))

        if profile and profile.duplicate_rows > 0:
            items.append(RecommendationItem(
                id="REC-DQ-02",
                category="Data Quality & Governance",
                title="Deduplicate Redundant Records",
                observation=f"Dataset contains {profile.duplicate_rows:,} exact duplicate rows ({profile.duplicate_pct}% of total rows).",
                why_it_matters="Duplicate observations artificially inflate volume counts, skew averages, and can lead to double-counting financial metrics.",
                suggested_action="Use the 'Deduplicate' tool in the Data Lab to retain only distinct records.",
                evidence_type="Observed Fact",
                priority="High"
            ))

        # 2. Check Financial / Revenue / Profitability Data
        rev_col = cols_lower.get("revenue") or cols_lower.get("sales")
        cost_col = cols_lower.get("cost") or cols_lower.get("expense")
        profit_col = cols_lower.get("profit") or cols_lower.get("margin")

        if rev_col and profit_col:
            rev_sum = float(pd.to_numeric(df[rev_col], errors="coerce").sum())
            prof_sum = float(pd.to_numeric(df[profit_col], errors="coerce").sum())
            if rev_sum > 0:
                overall_margin = (prof_sum / rev_sum) * 100.0
                
                # Check negative profit rows
                neg_profit_count = int((pd.to_numeric(df[profit_col], errors="coerce") < 0).sum())
                if neg_profit_count > 0:
                    neg_pct = round((neg_profit_count / len(df)) * 100, 1)
                    items.append(RecommendationItem(
                        id="REC-FIN-01",
                        category="Revenue & Profitability Optimization",
                        title="Investigate Unprofitable Transactions",
                        observation=f"Found {neg_profit_count:,} transactions ({neg_pct}% of sales) with negative profit, eroding overall margin.",
                        why_it_matters="Selling at a net loss directly drains company cash reserves and degrades aggregate profitability.",
                        suggested_action="Filter transactions where Profit < 0 in Data Lab, verify whether excessive discounting or shipping surcharges caused the loss, and set minimum pricing floors.",
                        evidence_type="Observed Fact",
                        priority="High"
                    ))

                # Category breakdown
                cat_col = cols_lower.get("product_category") or cols_lower.get("category") or cols_lower.get("region")
                if cat_col:
                    cat_margins = df.groupby(cat_col).apply(
                        lambda g: (g[profit_col].sum() / g[rev_col].sum() * 100) if g[rev_col].sum() > 0 else 0
                    ).sort_values()
                    
                    lowest_cat = cat_margins.index[0]
                    lowest_margin = cat_margins.iloc[0]
                    highest_cat = cat_margins.index[-1]
                    highest_margin = cat_margins.iloc[-1]

                    if lowest_margin < overall_margin:
                        items.append(RecommendationItem(
                            id="REC-FIN-02",
                            category="Revenue & Profitability Optimization",
                            title=f"Rebalance Product/Regional Portfolio ({lowest_cat})",
                            observation=f"'{lowest_cat}' has the lowest profit margin ({lowest_margin:.1f}%), compared to '{highest_cat}' at {highest_margin:.1f}%.",
                            why_it_matters="Capital allocation and marketing spend yield significantly lower returns in low-margin segments.",
                            suggested_action=f"Consider shifting promotional spend toward high-margin '{highest_cat}', and renegotiate supplier costs or adjust pricing for '{lowest_cat}'.",
                            evidence_type="Observed Fact",
                            priority="High"
                        ))

        # 3. Check Customer Churn Data
        churn_col = cols_lower.get("churn")
        tenure_col = cols_lower.get("tenure_months") or cols_lower.get("tenure")
        contract_col = cols_lower.get("contract_type") or cols_lower.get("contract")

        if churn_col and contract_col:
            churn_rates = df.groupby(contract_col)[churn_col].apply(
                lambda s: (s.astype(str).str.lower().isin(["yes", "1", "true"])).mean() * 100
            ).sort_values(ascending=False)

            highest_churn_contract = churn_rates.index[0]
            highest_rate = churn_rates.iloc[0]

            if highest_rate > 20.0:
                items.append(RecommendationItem(
                    id="REC-RET-01",
                    category="Customer Retention & Churn Mitigation",
                    title=f"Incentivize Long-Term Commitments ({highest_churn_contract})",
                    observation=f"Customers on '{highest_churn_contract}' exhibit a {highest_rate:.1f}% churn rate.",
                    why_it_matters="High churn creates a customer acquisition treadmill, drastically lowering Customer Lifetime Value (LTV).",
                    suggested_action="Introduce discounted annual billing or loyalty perks to transition Month-to-Month accounts into multi-year contracts.",
                    evidence_type="Observed Fact",
                    priority="High"
                ))

        # 4. Check Academic Performance Data
        math_col = cols_lower.get("math_score")
        prep_col = cols_lower.get("prep_course")
        att_col = cols_lower.get("attendance_rate") or cols_lower.get("absences")

        if math_col and prep_col:
            prep_diff = df.groupby(prep_col)[math_col].mean()
            if len(prep_diff) >= 2:
                items.append(RecommendationItem(
                    id="REC-EDU-01",
                    category="Academic Performance & Student Success",
                    title="Expand Test Preparation Participation",
                    observation=f"Average {math_col} differs across {prep_col} cohorts: {', '.join([f'{k}: {v:.1f}' for k, v in prep_diff.items()])}.",
                    why_it_matters="Structured preparatory curricula provide statistically noticeable boosts in foundational comprehension.",
                    suggested_action="Offer supplemental tutoring and mandatory prep modules for students in lower-performing brackets.",
                    evidence_type="Observed Fact",
                    priority="Medium"
                ))

        # If no domain-specific items triggered, add generic exploratory recommendation
        if not items:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) >= 2:
                corr_res = DataCalculator.calculate_correlations(df, columns=num_cols[:5])
                items.append(RecommendationItem(
                    id="REC-GEN-01",
                    category="Exploratory Analysis",
                    title="Deepen Bivariate Feature Investigation",
                    observation=f"Identified multiple numerical features ({', '.join(num_cols[:3])}) with varying variances.",
                    why_it_matters="Understanding inter-variable dependencies uncovers latent cost drivers or revenue levers.",
                    suggested_action="Use the Visualization Studio to inspect scatter plots and test correlation hypotheses between primary metrics.",
                    evidence_type="Statistical Correlation",
                    priority="Medium"
                ))

        high_count = sum(1 for item in items if item.priority == "High")

        summary_md = f"### Strategic Recommendations Summary\n\nIdentified **{len(items)} evidence-backed recommendations** ({high_count} high priority) derived from dataset metrics.\n\n"
        for item in items:
            summary_md += f"#### [{item.priority}] {item.title}\n"
            summary_md += f"- **Observation (Fact)**: {item.observation}\n"
            summary_md += f"- **Why It Matters**: {item.why_it_matters}\n"
            summary_md += f"- **Suggested Next Step**: {item.suggested_action}\n"
            summary_md += f"- *Evidence Type*: `{item.evidence_type}`\n\n"

        return RecommendationReport(
            recommendations=items,
            total_recommendations=len(items),
            high_priority_count=high_count,
            summary_markdown=summary_md
        )

    @classmethod
    def generate_proactive_insights_ticker(
        cls,
        df: pd.DataFrame,
        profile: Optional[ProfileReport] = None
    ) -> List[Dict[str, str]]:
        """Extract quick, actionable 'Aha! Moments' for the proactive discovery ticker."""
        if df is None or df.empty:
            return []

        ticker: List[Dict[str, str]] = []
        cols_lower = {c.lower(): c for c in df.columns}

        # 1. Negative profit check
        rev_col = cols_lower.get("revenue") or cols_lower.get("sales")
        prof_col = cols_lower.get("profit") or cols_lower.get("margin")
        if prof_col:
            neg_profit = (pd.to_numeric(df[prof_col], errors="coerce") < 0).sum()
            if neg_profit > 0:
                ticker.append({
                    "id": "AHA-01",
                    "icon": "🚨",
                    "tag": "Profit Alert",
                    "badge": "Profit Alert",
                    "title": f"Found {neg_profit:,} Loss-Making Orders",
                    "desc": f"{neg_profit:,} transactions have negative profit eroding margins.",
                    "description": f"{neg_profit:,} transactions have negative profit eroding margins.",
                    "query": f"Filter rows where {prof_col} is negative"
                })

        # 2. Top category revenue share
        cat_col = cols_lower.get("product_category") or cols_lower.get("category") or cols_lower.get("region")
        if rev_col and cat_col:
            rev_by_cat = df.groupby(cat_col)[rev_col].sum().sort_values(ascending=False)
            if not rev_by_cat.empty:
                top_cat = rev_by_cat.index[0]
                top_rev = rev_by_cat.iloc[0]
                tot_rev = rev_by_cat.sum()
                pct = round((top_rev / tot_rev * 100), 1) if tot_rev > 0 else 0
                ticker.append({
                    "id": "AHA-02",
                    "icon": "🏆",
                    "tag": "Top Driver",
                    "badge": "Top Driver",
                    "title": f"'{top_cat}' Drives {pct}% of Revenue",
                    "desc": f"Generates ${top_rev:,.2f} of total ${tot_rev:,.2f}.",
                    "description": f"Generates ${top_rev:,.2f} of total ${tot_rev:,.2f}.",
                    "query": f"Create a graph of {rev_col} by {cat_col}"
                })

        # 3. Churn risk hotspot
        churn_col = cols_lower.get("churn")
        contract_col = cols_lower.get("contract_type") or cols_lower.get("contract")
        if churn_col and contract_col:
            c_rates = df.groupby(contract_col)[churn_col].apply(
                lambda s: (s.astype(str).str.lower().isin(["yes", "1", "true"])).mean() * 100
            ).sort_values(ascending=False)
            if not c_rates.empty and c_rates.iloc[0] > 20:
                ticker.append({
                    "id": "AHA-03",
                    "icon": "⚠️",
                    "tag": "Churn Hotspot",
                    "badge": "Churn Hotspot",
                    "title": f"High Churn on '{c_rates.index[0]}'",
                    "desc": f"Cohort exhibits {c_rates.iloc[0]:.1f}% churn rate.",
                    "description": f"Cohort exhibits {c_rates.iloc[0]:.1f}% churn rate.",
                    "query": "Recommend actions to improve customer retention"
                })

        # 4. Data hygiene
        if profile and profile.duplicate_rows > 0:
            ticker.append({
                "id": "AHA-04",
                "icon": "🧹",
                "tag": "Data Hygiene",
                "badge": "Data Hygiene",
                "title": f"Found {profile.duplicate_rows:,} Duplicate Rows",
                "desc": f"{profile.duplicate_pct}% of records are exact duplicates.",
                "description": f"{profile.duplicate_pct}% of records are exact duplicates.",
                "query": "Identify missing values and duplicates"
            })

        # 5. Temporal growth
        date_col = profile.datetime_columns[0] if (profile and profile.datetime_columns) else None
        if rev_col and date_col:
            ticker.append({
                "id": "AHA-05",
                "icon": "📈",
                "tag": "Forecast Available",
                "badge": "Forecast Available",
                "title": f"Predict Next 30 Days of {rev_col}",
                "desc": f"Historical timeline detected from `{date_col}`.",
                "description": f"Historical timeline detected from `{date_col}`.",
                "query": f"Forecast {rev_col} for the next 30 days"
            })

        return ticker[:4]
