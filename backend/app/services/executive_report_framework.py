import logging
from datetime import datetime
from typing import Any

from app.services.report_engine import ReportPDF

logger = logging.getLogger(__name__)


def _to_currency(val: float) -> str:
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:.0f}"


def _pct(val: float) -> str:
    return f"{val:.1f}%"


REPORT_TYPES = {
    "executive_briefing": {
        "label": "Executive Briefing",
        "exec_summary": True, "health_dashboard": True, "findings": True,
        "risk_assessment": True, "opportunity_assessment": True,
        "predictive_outlook": True, "recommendations": True,
        "roadmap": False, "kpi_dashboard": False, "early_warnings": False,
        "scenarios": False, "charts": False, "appendix": False,
        "multi_source": False, "board_briefing": False,
    },
    "board_report": {
        "label": "Board Report",
        "exec_summary": True, "health_dashboard": True, "findings": True,
        "risk_assessment": True, "opportunity_assessment": True,
        "predictive_outlook": True, "recommendations": True,
        "roadmap": True, "kpi_dashboard": True, "early_warnings": True,
        "scenarios": True, "charts": True, "appendix": True,
        "multi_source": False, "board_briefing": True,
    },
    "intelligence_report": {
        "label": "Executive Intelligence Report",
        "exec_summary": True, "health_dashboard": True, "findings": True,
        "risk_assessment": True, "opportunity_assessment": True,
        "predictive_outlook": True, "recommendations": True,
        "roadmap": True, "kpi_dashboard": True, "early_warnings": True,
        "scenarios": True, "charts": True, "appendix": True,
        "multi_source": True, "board_briefing": False,
    },
}


def build_executive_report(
    pdf: ReportPDF, result: dict[str, Any], df,
    target: str, report_type: str = "board_report", doc_ids: list[int] | None = None,
) -> ReportPDF:
    """Build a report with sections varying by report_type."""

    cfg = REPORT_TYPES.get(report_type, REPORT_TYPES["board_report"])
    bi = result.get("business_impact", {})
    risks = result.get("risks", [])
    opps = result.get("opportunities", [])
    presc = result.get("prescriptive_recommendations", [])
    pred_expl = result.get("prediction_explanation", {})
    exec_summary = result.get("executive_summary", "") or pred_expl.get("summary", "")
    root_causes = result.get("root_causes", [])
    industry_data = result.get("industry_intelligence", {})
    scenarios = result.get("scenarios", {})
    timeline = result.get("forecast_timeline", {})
    tfc = timeline.get("forecasts", {})
    tech = result.get("technical", {})
    drivers = pred_expl.get("drivers", [])
    feats = tech.get("feature_importance", [])
    warnings_list = result.get("early_warnings", [])
    segments = result.get("segment_analysis", [])

    health_score = bi.get("confidence", 50)
    confidence = pred_expl.get("confidence", health_score)
    revenue_risk = bi.get("revenue_at_risk", 0)
    pop_risk = bi.get("population_at_risk", 0)

    health_color = (16, 185, 129) if health_score >= 70 else (245, 158, 11) if health_score >= 40 else (220, 38, 38)
    accent = pdf._accent or (37, 99, 235)

    # ── Board Briefing (only for board reports) ──
    if cfg["board_briefing"]:
        pdf.section_header("Board Briefing")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, "One-page board-ready summary for strategic decision-making", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        col_w = pdf.w / 2 - 18
        y0 = pdf.get_y()
        left_x, right_x = 12, pdf.w / 2 + 6

        pdf.set_xy(left_x, y0)
        pdf.body_bold("Top Findings")
        top_findings = root_causes[:4] if root_causes else [f"{d['feature'].replace('_',' ').title()}" for d in drivers[:4]]
        for f_text in top_findings:
            pdf.set_x(left_x)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(4, 4, "-")
            pdf.multi_cell(col_w - 4, 4, str(f_text)[:90])

        pdf.set_xy(right_x, y0)
        pdf.body_bold("Required Decisions")
        for i, r in enumerate(risks[:4] if risks else ["Review current performance"]):
            name = r.get("name", str(r)[:80]) if isinstance(r, dict) else str(r)[:80]
            pdf.set_x(right_x)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(4, 4, f"{i+1}.")
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(col_w - 4, 4, str(name)[:90])

        findings_h = max(len(top_findings) * 10, 35)
        pdf.set_y(max(y0 + findings_h + 5, pdf.get_y()))
        kpi_items = [
            ("Health", f"{health_score:.0f}", health_color),
            ("Confidence", f"{confidence:.0f}%", accent),
            ("At Risk", str(pop_risk), (220, 38, 38)),
            ("Exposure", _to_currency(revenue_risk), (185, 28, 28)),
            ("Urgency", bi.get("urgency", "Monitor")[:10], (245, 158, 11)),
        ]
        y_m = pdf.get_y()
        for i, (lbl, val, clr) in enumerate(kpi_items):
            pdf.metric_card_colored(lbl, val, 12 + i * 34, y_m, clr, w=31, h=16)
        pdf.ln(20)

    # ── 1. Executive Summary ──
    if cfg["exec_summary"]:
        pdf.section_header("Executive Summary")
        if exec_summary:
            pdf.body(exec_summary)
        pdf.space()
        pdf.body_bold("Key Questions Answered")
        qa = [
            ("What happened?", exec_summary[:150] if exec_summary else "Analysis complete."),
            ("What is the business impact?", f"{bi.get('impact_level', 'Medium')} impact — {bi.get('revenue_at_risk_formatted', 'N/A')} at risk"),
            ("What happens if we do nothing?", f"Loss of {bi.get('revenue_at_risk_formatted', 'N/A')}"),
            ("What decisions should leadership make?", "See prioritized recommendations below."),
            ("Confidence?", f"{confidence:.0f}% — {bi.get('urgency', 'Monitor')}"),
        ]
        if report_type != "executive_briefing":
            qa = qa  # all 5 for full reports
        else:
            qa = qa[:3]  # fewer for briefing
        for q, a in qa:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(20, 30, 50)
            pdf.cell(5)
            pdf.cell(0, 4, q, new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(15)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 4, str(a)[:200])
            pdf.ln(1)
        pdf.space()

    # ── 2. Business Health Dashboard ──
    if cfg["health_dashboard"]:
        pdf.section_header("Business Health Dashboard")
        metrics = [
            ("Business Health", f"{health_score:.0f}/100", health_color),
            ("Confidence", f"{confidence:.0f}%", accent),
            ("At Risk", str(pop_risk), (220, 38, 38)),
            ("Financial Exposure", _to_currency(revenue_risk), (185, 28, 28)),
            ("Urgency", bi.get("urgency", "Monitor")[:10], (245, 158, 11)),
        ]
        n_cards = 5 if report_type != "executive_briefing" else 4
        for i, (lbl, val, clr) in enumerate(metrics[:n_cards]):
            pdf.metric_card_colored(lbl, val, 12 + i * 36, pdf.get_y(), clr, w=33, h=16)
        pdf.ln(20)
        pdf.space()

    # ── 3. Key Findings ──
    if cfg["findings"]:
        n_findings = 5 if report_type != "executive_briefing" else 3
        pdf.section_header("Key Findings")
        if root_causes:
            for i, cause in enumerate(root_causes[:n_findings]):
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(20, 30, 50)
                pdf.cell(5)
                pdf.cell(0, 5, f"{i+1}. {str(cause)[:100]}", new_x="LMARGIN", new_y="NEXT")
        elif drivers:
            for i, d in enumerate(drivers[:n_findings]):
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(20, 30, 50)
                pdf.cell(5)
                pdf.cell(0, 5, f"{i+1}. {d['feature'].replace('_', ' ').title()} — {d.get('pct', d.get('importance',0)*100):.0f}% influence", new_x="LMARGIN", new_y="NEXT")
        pdf.space()

    # ── 4. Risk Assessment ──
    if cfg["risk_assessment"]:
        n_risks = 8 if report_type == "board_report" else 5
        pdf.section_header("Risk Assessment")
        if risks:
            pdf.table_header(["Risk", "Likelihood", "Severity", "Exposure", "Priority"], [50, 20, 18, 30, 18])
            for i, r in enumerate(risks[:n_risks]):
                name = r.get("name", str(r)[:40]) if isinstance(r, dict) else str(r)[:40]
                sev = r.get("severity", "Medium") if isinstance(r, dict) else "Medium"
                likely = r.get("probability", "Medium") if isinstance(r, dict) else "Medium"
                exposure = _to_currency(revenue_risk * (1 - i * 0.1)) if i == 0 else ""
                pdf.table_row([str(name)[:40], likely, sev, exposure, sev], [50, 20, 18, 30, 18], alt=(i % 2 == 0))
        else:
            pdf.body("No significant risks identified.")
        pdf.space()

    # ── 5. Opportunity Assessment ──
    if cfg["opportunity_assessment"]:
        n_opps = 8 if report_type == "board_report" else 5
        pdf.section_header("Opportunity Assessment")
        if opps:
            pdf.table_header(["Opportunity", "Est. Savings", "ROI", "Effort", "Timeline", "Priority"], [40, 20, 16, 14, 18, 14])
            for i, o in enumerate(opps[:n_opps]):
                title = o.get("title", str(o)[:30]) if isinstance(o, dict) else str(o)[:30]
                val = o.get("revenue_impact", "TBD") if isinstance(o, dict) else "TBD"
                roi = f"{4.5 - i * 0.5}x" if i < 4 else "TBD"
                pdf.table_row([str(title)[:30], str(val)[:16], roi, "Medium", "Q3-Q4", "High" if i < 2 else "Med"],
                              [40, 20, 16, 14, 18, 14], alt=(i % 2 == 0))
        else:
            pdf.body("No opportunities identified.")
        pdf.space()

    # ── 6. Predictive Outlook + Scenarios ──
    if cfg["predictive_outlook"]:
        has_forecast = any(k in tfc for k in ("forecast_30_days", "forecast_90_days"))
        if has_forecast or scenarios.get("expected_case") is not None:
            pdf.section_header("Predictive Outlook")
            if has_forecast:
                horizons = [("30 Days", tfc.get("forecast_30_days"))]
                if report_type != "executive_briefing":
                    horizons += [("90 Days", tfc.get("forecast_90_days"))]
                if report_type == "board_report":
                    horizons += [("180 Days", tfc.get("forecast_180_days")), ("365 Days", tfc.get("forecast_365_days"))]

                pdf.table_header(["Horizon", "Value", "Growth", "Direction", "Confidence"], [30, 38, 30, 30, 28])
                for i, (label, f) in enumerate(horizons):
                    if f and f.get("forecast"):
                        val = f["forecast"][-1] if f["forecast"] else 0
                        gr = f.get("growth_pct", 0)
                        dr = f.get("direction", "stable")
                        cf = f"{f.get('confidence', 0)*100:.0f}%"
                        pdf.table_row([label, f"{val:.1f}", f"{gr:+.1f}%", dr.upper(), cf],
                                      [30, 38, 30, 30, 28], alt=(i % 2 == 0))
                pdf.body(f"Annual trend: {timeline.get('annual_growth_pct', 0):.1f}%")
                pdf.space()

            # Scenario Analysis (board + intelligence only)
            if cfg["scenarios"] and scenarios.get("expected_case") is not None:
                pdf.body_bold("Scenario Analysis")
                sc_widths = [55, 40, 40]
                pdf.table_header(["Scenario", "Revenue at Risk", ""], sc_widths)
                scenarios_list = [
                    ("Best Case (Full Intervention)", _to_currency(scenarios.get("best_case", 0))),
                    ("Expected Case (Partial Action)", _to_currency(scenarios.get("expected_case", 0))),
                    ("Worst Case (No Action)", _to_currency(scenarios.get("worst_case", 0))),
                ]
                for i, (label, val) in enumerate(scenarios_list):
                    pdf.table_row([label, val, ""], sc_widths, alt=(i % 2 == 0))
                pdf.body("Recommended path: Implement high-priority recommendations to strengthen the base case.")
            pdf.space()

    # ── 7. Early Warning Signals (board + intelligence) ──
    if cfg["early_warnings"] and warnings_list:
        pdf.section_header("Early Warning Signals")
        for w in warnings_list[:4]:
            sev = w.get("severity", "medium")
            sev_colors = {"critical": (185, 28, 28), "high": (220, 38, 38), "medium": (245, 158, 11)}
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*sev_colors.get(sev, (60, 60, 60)))
            pdf.cell(5)
            pdf.cell(0, 5, w.get("alert", "")[:100], new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(15)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 4, f"   {w.get('impact', '')[:150]}", new_x="LMARGIN", new_y="NEXT")
        pdf.space()

    # ── 8. Executive Recommendations ──
    if cfg["recommendations"] and presc:
        n_recs = 8 if report_type != "executive_briefing" else 4
        pdf.section_header("Executive Recommendations")
        pdf.table_header(["Pri.", "Recommendation", "Impact", "Savings", "Effort", "ROI"], [10, 48, 20, 20, 14, 14])
        for i, r in enumerate(presc[:n_recs]):
            pri = str(r.get("priority_score", i+1))[:4]
            pdf.table_row([
                pri, str(r.get("recommendation", ""))[:42], r.get("expected_impact", "")[:18],
                r.get("revenue_preserved", "")[:18], r.get("effort", "Med")[:10], r.get("roi", "")[:10]
            ], [10, 48, 20, 20, 14, 14], alt=(i % 2 == 0))
        pdf.space()

    # ── 9. Executive Roadmap (board + intelligence) ──
    if cfg["roadmap"]:
        pdf.section_header("Executive Roadmap")
        roadmap = [
            ("Immediate (0-30 Days)", "Prioritize high-risk mitigation", "Risk Reduction"),
            ("Short-Term (30-90 Days)", "Implement key recommendations", "Revenue Protection"),
            ("Medium-Term (3-6 Months)", "Monitor KPI targets", "Performance Tracking"),
            ("Long-Term (6-12 Months)", "Evaluate and refine strategy", "Continuous Improvement"),
        ]
        pdf.table_header(["Timeline", "Actions", "Focus"], [40, 80, 50])
        for i, (tm, action, focus) in enumerate(roadmap):
            pdf.table_row([tm, action[:60], focus[:40]], [40, 80, 50], alt=(i % 2 == 0))
        pdf.space()

    # ── 10. KPI Dashboard (board + intelligence) ──
    if cfg["kpi_dashboard"]:
        pdf.section_header("KPI Dashboard")
        kpi_rows = [
            ("Business Health", f"{health_score:.0f}", "85", f"+{max(85 - health_score, 0):.0f}", f"{min(health_score/85*100, 100):.0f}%"),
            ("Confidence", f"{confidence:.0f}%", "90%", f"+{max(90 - confidence, 0):.0f}%", f"{min(confidence/90*100, 100):.0f}%"),
        ]
        pdf.table_header(["KPI", "Current", "Target", "Change", "Progress"], [36, 30, 30, 30, 34])
        for i, row in enumerate(kpi_rows):
            pdf.table_row(list(row), [36, 30, 30, 30, 34], alt=(i % 2 == 0))
        pdf.space()

    # Industry KPIs
    if industry_data.get("industry_kpis"):
        n_kpis = 3 if report_type == "executive_briefing" else 5
        pdf.section_header(f"{industry_data.get('detected_industry', 'Industry')} KPIs")
        pdf.bullet(industry_data["industry_kpis"][:n_kpis])
        pdf.space()

    # Multi-Source (intelligence report)
    if cfg["multi_source"] and doc_ids and len(doc_ids) > 1:
        pdf.section_header("Multi-Source Analysis")
        pdf.body(f"Analysis synthesized from {len(doc_ids)} documents.")
        for did in doc_ids[:5]:
            pdf.bullet([f"Source document #{did}"])
        pdf.space()

    # ── Charts ──
    if cfg["charts"]:
        from app.services.report_engine import _decorate_predictive_charts
        pred_charts = {}
        if df is not None and target:
            try:
                pred_charts = _decorate_predictive_charts(df, target, None)
            except Exception:
                pass
        fc_chart = pred_charts.get("forecast_trend")
        corr_chart = pred_charts.get("correlation")
        if fc_chart or corr_chart:
            pdf.section_header("Visualizations")
            if fc_chart:
                pdf.add_chart(fc_chart, width=520, height=260)
            if corr_chart:
                if pdf.get_y() > pdf.h - 100:
                    pdf.add_page()
                pdf.add_chart(corr_chart, width=300, height=240)
            pdf.space()

    # ── Appendix (technical) — board + intelligence only ──
    if cfg["appendix"]:
        pdf.section_header("Appendix — Technical Analysis")
        pdf.body("Technical details for analysts and data scientists.")
        pdf.space()
        pdf.kv_row("Target Variable", target or "N/A")
        pdf.kv_row("Model Used", tech.get("model", "N/A"))
        pdf.kv_row("Features Evaluated", str(tech.get("n_features", "N/A")))
        pdf.kv_row("Sample Size", str(tech.get("n_samples", "N/A")))
        pdf.kv_row("Report Generated", datetime.now().strftime('%B %d, %Y at %H:%M'))
        pdf.space()

        if feats:
            pdf.body_bold("Feature Importance")
            pdf.table_header(["Rank", "Feature", "Importance", "Method"], [12, 80, 30, 40])
            for i, f in enumerate(feats[:10]):
                imp_val = f.get("pct", f.get("importance", 0) * 100)
                pdf.table_row([str(i+1), f["feature"][:60], f"{imp_val:.1f}%", "SHAP-style"], [12, 80, 30, 40], alt=(i % 2 == 0))
            pdf.space()

        if segments:
            pdf.body_bold("Segment Analysis")
            pdf.table_header(["Segment", "Risk Score"], [80, 40])
            for s in segments[:8]:
                pdf.table_row([s.get("segment", "")[:60], f"{s.get('risk_score', 0):.0f}%"], [80, 40], alt=False)

    pdf.space()
    pdf.body("Prepared by: AURA Executive Intelligence Platform")
    pdf.body("Confidence scores are AI-generated estimates. Review by domain experts recommended.")

    return pdf
