"""Executive PDF report generator using ReportLab."""
import io
import os
from typing import Dict, List, Any, Optional
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether

from src.data.profiler import ProfileReport
from src.tools.recommender import RecommendationReport


class PDFReportGenerator:
    """Generates styled executive PDF reports summarizing data profile, metrics, and strategic recommendations."""

    @classmethod
    def generate_report(
        cls,
        df: pd.DataFrame,
        profile: ProfileReport,
        recommendations: Optional[RecommendationReport] = None,
        key_metrics: Optional[Dict[str, Any]] = None,
        report_title: str = "Executive Data Intelligence Report",
        include_summary: bool = True,
        include_kpis: bool = True,
        include_features: bool = True,
        include_recommendations: bool = True,
        custom_notes: Optional[str] = None
    ) -> bytes:
        """Generate a complete PDF document and return byte buffer with customizable sections."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom Blue Theme Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1E40AF"),
            spaceAfter=6,
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=15,
            fontName="Helvetica"
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6,
            fontName="Helvetica-Bold"
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
            fontName="Helvetica"
        )
        cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1E293B"),
            fontName="Helvetica"
        )
        cell_header_style = ParagraphStyle(
            "TableCellHeader",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )

        elements = []

        # 1. Header & Title Banner
        elements.append(Paragraph(f"DataPilot AI | {report_title}", title_style))
        elements.append(Paragraph(
            f"Generated autonomously • Analyzed {len(df):,} records across {len(df.columns)} dimensions",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=12))

        sec_idx = 1

        # Optional Custom Analyst Notes
        if custom_notes and custom_notes.strip():
            elements.append(Paragraph(f"{sec_idx}. Analyst Notes & Strategic Context", h2_style))
            elements.append(Paragraph(custom_notes.strip().replace("\n", "<br/>"), body_style))
            elements.append(Spacer(1, 8))
            sec_idx += 1

        # 2. Executive Narrative Summary
        if include_summary:
            elements.append(Paragraph(f"{sec_idx}. Executive Summary", h2_style))
            summary_text = profile.plain_english_summary.replace("**", "").replace("`", "")
            elements.append(Paragraph(summary_text, body_style))
            elements.append(Spacer(1, 8))
            sec_idx += 1

        # 3. High-Level KPI Summary Table
        if include_kpis:
            elements.append(Paragraph(f"{sec_idx}. Dataset Composition & Health", h2_style))
            kpi_data = [
                [
                    Paragraph("<b>Total Rows</b>", cell_style), Paragraph(f"{profile.row_count:,}", cell_style),
                    Paragraph("<b>Numerical Features</b>", cell_style), Paragraph(f"{len(profile.numerical_columns)}", cell_style)
                ],
                [
                    Paragraph("<b>Total Columns</b>", cell_style), Paragraph(f"{profile.column_count}", cell_style),
                    Paragraph("<b>Categorical Features</b>", cell_style), Paragraph(f"{len(profile.categorical_columns)}", cell_style)
                ],
                [
                    Paragraph("<b>Missing Cells</b>", cell_style), Paragraph(f"{profile.missing_cells:,} ({profile.missing_pct}%)", cell_style),
                    Paragraph("<b>Temporal Features</b>", cell_style), Paragraph(f"{len(profile.datetime_columns)}", cell_style)
                ],
                [
                    Paragraph("<b>Duplicate Rows</b>", cell_style), Paragraph(f"{profile.duplicate_rows:,} ({profile.duplicate_pct}%)", cell_style),
                    Paragraph("<b>Memory Footprint</b>", cell_style), Paragraph(f"{profile.memory_usage_mb} MB", cell_style)
                ]
            ]
            kpi_table = Table(kpi_data, colWidths=[120, 140, 130, 140])
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(kpi_table)
            elements.append(Spacer(1, 10))
            sec_idx += 1

        # 4. Feature Profile Sample (Top 8 Columns)
        if include_features:
            elements.append(Paragraph(f"{sec_idx}. Feature Schema & Summary Statistics", h2_style))
            feature_headers = ["Column Name", "Inferred Type", "Missing (%)", "Unique", "Summary / Range"]
            feature_rows = [[Paragraph(f"<b>{h}</b>", cell_header_style) for h in feature_headers]]

            for col_name, col_prof in list(profile.columns.items())[:8]:
                stat_summary = ""
                if col_prof.inferred_type == "numerical" and col_prof.stats:
                    s = col_prof.stats
                    stat_summary = f"Mean: {s.get('mean', 'N/A')}, Min: {s.get('min', 'N/A')}, Max: {s.get('max', 'N/A')}"
                elif col_prof.inferred_type == "categorical" and col_prof.stats:
                    stat_summary = f"Mode: {col_prof.stats.get('mode', 'N/A')}"
                elif col_prof.inferred_type == "datetime" and col_prof.stats:
                    stat_summary = f"{str(col_prof.stats.get('min_date', '')).split()[0]} to {str(col_prof.stats.get('max_date', '')).split()[0]}"
                else:
                    stat_summary = "N/A"

                feature_rows.append([
                    Paragraph(col_name[:20], cell_style),
                    Paragraph(col_prof.inferred_type.capitalize(), cell_style),
                    Paragraph(f"{col_prof.null_pct}%", cell_style),
                    Paragraph(f"{col_prof.unique_count:,}", cell_style),
                    Paragraph(stat_summary[:35], cell_style)
                ])

            feat_table = Table(feature_rows, colWidths=[120, 80, 70, 60, 200])
            feat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(feat_table)
            elements.append(Spacer(1, 10))
            sec_idx += 1

        # 5. Strategic Recommendations
        if include_recommendations and recommendations and recommendations.recommendations:
            elements.append(Paragraph(f"{sec_idx}. Actionable Evidence-Based Recommendations", h2_style))
            for rec in recommendations.recommendations[:5]:
                rec_block = [
                    Paragraph(f"<b>[{rec.priority}] {rec.title}</b> ({rec.evidence_type})", ParagraphStyle("H3", parent=body_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#1E40AF"))),
                    Paragraph(f"• <b>Observed Fact:</b> {rec.observation.replace('`', '')}", body_style),
                    Paragraph(f"• <b>Impact:</b> {rec.why_it_matters}", body_style),
                    Paragraph(f"• <b>Action:</b> {rec.suggested_action}", body_style),
                    Spacer(1, 4)
                ]
                elements.append(KeepTogether(rec_block))

        # Build document
        doc.build(elements)
        return buffer.getvalue()
