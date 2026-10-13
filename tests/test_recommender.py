"""Unit tests for RecommendationEngine and PDFReportGenerator."""
import pandas as pd
import pytest
from src.data.profiler import DataProfiler
from src.tools.recommender import RecommendationEngine
from src.reports.pdf_generator import PDFReportGenerator


def test_recommendation_engine_sales():
    df = pd.read_csv("samples/sales_data.csv")
    prof = DataProfiler.profile(df)
    report = RecommendationEngine.generate_recommendations(df, prof)
    assert report.total_recommendations > 0
    assert any(r.category == "Revenue & Profitability Optimization" for r in report.recommendations)
    assert len(report.summary_markdown) > 50


def test_recommendation_engine_churn():
    df = pd.read_csv("samples/customer_churn.csv")
    prof = DataProfiler.profile(df)
    report = RecommendationEngine.generate_recommendations(df, prof)
    assert report.total_recommendations > 0
    assert any("Retention" in r.category or "Churn" in r.category for r in report.recommendations)


def test_pdf_report_generation():
    df = pd.read_csv("samples/sales_data.csv")
    prof = DataProfiler.profile(df)
    recs = RecommendationEngine.generate_recommendations(df, prof)
    pdf_bytes = PDFReportGenerator.generate_report(df, prof, recs)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
