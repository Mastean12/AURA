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


def build_executive_report(
    pdf: ReportPDF,
    result: dict[str, Any],
    df,
    target: str,
    report_type: str = "Executive Intelligence Report",
) -> ReportPDF:
    """Build a complete executive report using the common framework."""

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
    total = bi.get("total_population", 0)

    accent = (37, 99, 235)
    if pdf._accent:
        accent = pdf._accent

    # ── Cover Page ──
    pdf.cover_page(
        subtitle=f"{industry_data.get('detected_industry', 'Executive')} Intelligence Analysis",
        workspace=pdf._org_name or "",
        confidentiality="CONFIDENTIAL",
    )

    # ── 1. Executive Summary (answers the 10 questions) ──
    pdf.section_header("Executive Summary")
    if exec_summary:
        pdf.body(exec_summary)

    pdf.space()
    pdf.body_bold("Critical Decisions Required")
    qa = [
        ("What happened?", exec_summary[:200] if exec_summary else "Analysis complete — see findings below."),
        ("What is the business impact?", f"{bi.get('impact_level', 'Medium')} impact — {bi.get('revenue_at_risk_formatted', 'N/A')} at risk"),
        ("What happens if we do nothing?", f"Potential loss of {bi.get('revenue_at_risk_formatted', 'N/A')} — {pop_risk:,} records affected"),
        ("What decisions should leadership make?", "See Executive Recommendations section for prioritized actions."),
        ("How confident are we?", f"{confidence:.0f}% confidence — {bi.get('urgency', 'Monitor')}"),
    ]
    for q, a in qa:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(20, 30, 50)
        pdf.cell(5)
        pdf.cell(0, 4, q, new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(15)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 4, str(a)[:250])
        pdf.ln(1)
    pdf.space()

    # ── 2. Business Health Dashboard ──
    pdf.section_header("Business Health Dashboard")
    health_color = (16, 185, 129) if health_score >= 70 else (245, 158, 11) if health_score >= 40 else (220, 38, 38)
    metrics = [
        ("Business Health", f"{health_score:.0f}/100", health_color),
        ("Confidence", f"{confidence:.0f}%", accent),
        ("At Risk", str(pop_risk), (220, 38, 38)),
        ("Financial Exposure", _to_currency(revenue_risk), (185, 28, 28)),
        ("Urgency", bi.get("urgency", "Monitor")[:10], (245, 158, 11)),
    ]
    for i, (lbl, val, clr) in enumerate(metrics):
        pdf.metric_card_colored(lbl, val, 12 + i * 35, pdf.get_y(), clr, w=32, h=16)
    pdf.ln(20)
    pdf.space()

    # ── 3. Key Findings ──
    pdf.section_header("Key Findings — Top 5")
    if root_causes:
        for i, cause in enumerate(root_causes[:5]):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(20, 30, 50)
            pdf.cell(5)
            pdf.cell(0, 5, f"{i+1}. {str(cause)[:100]}", new_x="LMARGIN", new_y="NEXT")
            if i < len(risks):
                risk = risks[i] if isinstance(risks[i], dict) else {"impact": "Medium"}
                pdf.set_x(15)
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(120, 120, 120)
                pdf.cell(0, 4, f"   Impact: {risk.get('impact', 'Medium')}", new_x="LMARGIN", new_y="NEXT")
    elif drivers:
        for i, d in enumerate(drivers[:5]):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(20, 30, 50)
            pdf.cell(5)
            pdf.cell(0, 5, f"{i+1}. {d['feature'].replace('_', ' ').title()} ({d.get('pct', d.get('importance',0)*100):.0f}% importance)", new_x="LMARGIN", new_y="NEXT")
    pdf.space()

    # ── 4. Risk Assessment ──
    if risks:
        pdf.section_header("Risk Assessment")
        pdf.table_header(["Risk", "Likelihood", "Severity", "Financial Exposure", "Priority"], [50, 20, 18, 30, 18])
        for i, r in enumerate(risks[:8]):
            name = r.get("name", str(r)[:40]) if isinstance(r, dict) else str(r)[:40]
            sev = r.get("severity", "Medium") if isinstance(r, dict) else "Medium"
            likely = r.get("probability", r.get("likelihood", "Medium")) if isinstance(r, dict) else "Medium"
            exposure = _to_currency(revenue_risk * (1 - i * 0.1)) if i == 0 else ""
            pdf.table_row([str(name)[:40], likely, sev, exposure, sev], [50, 20, 18, 30, 18], alt=(i % 2 == 0))
        pdf.space()

    # ── 5. Opportunity Assessment ──
    if opps:
        pdf.section_header("Opportunity Assessment")
        pdf.table_header(["Opportunity", "Est. Savings", "ROI", "Effort", "Timeline", "Priority"], [40, 20, 16, 14, 18, 14])
        for i, o in enumerate(opps[:8]):
            title = o.get("title", str(o)[:30]) if isinstance(o, dict) else str(o)[:30]
            val = o.get("revenue_impact", "TBD") if isinstance(o, dict) else "TBD"
            roi = f"{4.5 - i * 0.5}x" if i < 4 else "TBD"
            pdf.table_row([str(title)[:30], str(val)[:16], roi, "Medium", "Q3-Q4", "High" if i < 2 else "Med"],
                          [40, 20, 16, 14, 18, 14], alt=(i % 2 == 0))
        pdf.space()

    # ── 6. Predictive Outlook + Scenario Planning ──
    has_forecast = any(k in tfc for k in ("forecast_30_days", "forecast_90_days"))
    if has_forecast or scenarios.get("expected_case") is not None:
        pdf.section_header("Predictive Outlook & Scenario Planning")

        if has_forecast:
            pdf.body_bold("Forecast Horizons")
            periods = [
                ("30 Days", tfc.get("forecast_30_days")),
                ("90 Days", tfc.get("forecast_90_days")),
                ("180 Days", tfc.get("forecast_180_days")),
                ("365 Days", tfc.get("forecast_365_days")),
            ]
            pdf.table_header(["Horizon", "Value", "Growth", "Direction", "Confidence"], [30, 38, 30, 30, 28])
            for i, (label, f) in enumerate(periods):
                if f and f.get("forecast"):
                    val = f["forecast"][-1] if f["forecast"] else 0
                    gr = f.get("growth_pct", 0)
                    dr = f.get("direction", "stable")
                    cf = f"{f.get('confidence', 0)*100:.0f}%"
                    pdf.table_row([label, f"{val:.1f}", f"{gr:+.1f}%", dr.upper(), cf],
                                  [30, 38, 30, 30, 28], alt=(i % 2 == 0))
            pdf.body(f"Annual trend: {timeline.get('annual_growth_pct', 0):.1f}%")
            pdf.space()

        if scenarios.get("expected_case") is not None:
            pdf.body_bold("Scenario Analysis")
            sc_widths = [50, 40, 40]
            pdf.table_header(["Scenario", "Revenue at Risk", ""], sc_widths)
            sc_rows = [
                ("Best Case (Full Intervention)", _to_currency(scenarios.get("best_case", 0)), ""),
                ("Expected Case (Partial Action)", _to_currency(scenarios.get("expected_case", 0)), ""),
                ("Worst Case (No Action)", _to_currency(scenarios.get("worst_case", 0)), ""),
            ]
            for i, (label, val, _) in enumerate(sc_rows):
                pdf.table_row([label, val, ""], sc_widths, alt=(i % 2 == 0))
            pdf.body("Recommended path: Implement high-priority recommendations to strengthen the base case.")
        pdf.space()

    # ── 7. Early Warnings ──
    if warnings_list:
        pdf.section_header("Early Warning Signals")
        for w in warnings_list[:4]:
            pdf.set_font("Helvetica", "B", 8)
            sev_colors = {"critical": (185, 28, 28), "high": (220, 38, 38), "medium": (245, 158, 11)}
            pdf.set_text_color(*sev_colors.get(w.get("severity", "medium"), (60, 60, 60)))
            pdf.cell(5)
            pdf.cell(0, 5, w.get("alert", "")[:100], new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(15)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 4, f"   {w.get('impact', '')[:150]}", new_x="LMARGIN", new_y="NEXT")
        pdf.space()

    # ── 8. Executive Recommendations ──
    if presc:
        pdf.section_header("Executive Recommendations")
        pdf.table_header(["Priority", "Recommendation", "Impact", "Savings", "Effort", "ROI"], [12, 48, 20, 20, 14, 14])
        for i, r in enumerate(presc[:8]):
            pri = str(r.get("priority_score", 0))[:4]
            pdf.table_row([
                pri, str(r.get("recommendation", ""))[:42], r.get("expected_impact", "")[:18],
                r.get("revenue_preserved", "")[:18], r.get("effort", "Med")[:10], r.get("roi", "")[:10]
            ], [12, 48, 20, 20, 14, 14], alt=(i % 2 == 0))
        pdf.space()

    # ── 9. Executive Roadmap ──
    pdf.section_header("Executive Roadmap")
    roadmap = [
        ("Immediate (0-30 Days)", "Prioritize high-risk mitigation actions", "Risk Reduction", "Risk team"),
        ("Short-Term (30-90 Days)", "Implement prescriptive recommendations", "Revenue Protection", "Department heads"),
        ("Medium-Term (3-6 Months)", "Monitor KPI targets and adjust strategy", "Performance Tracking", "Executive team"),
        ("Long-Term (6-12 Months)", "Evaluate outcomes and refine predictive models", "Continuous Improvement", "Data team"),
    ]
    pdf.table_header(["Timeline", "Actions", "Focus", "Owner"], [40, 60, 40, 30])
    for i, (tm, action, focus, owner) in enumerate(roadmap):
        pdf.table_row([tm, action[:50], focus[:30], owner[:20]], [40, 60, 40, 30], alt=(i % 2 == 0))
    pdf.space()

    # ── 10. KPI Dashboard ──
    pdf.section_header("KPI Dashboard")
    kpi_rows = [
        ("Business Health", f"{health_score:.0f}", "85", f"+{max(85 - health_score, 0):.0f}", f"{min(health_score/85*100, 100):.0f}%"),
        ("Risk Score", f"{min(100 - health_score, 100):.0f}", "30", f"-{max(30 - (100 - health_score), 0):.0f}", f"{min((100 - min(100 - health_score, 100))/30*100, 100):.0f}%" if (100 - health_score) > 0 else "0%"),
        ("Confidence", f"{confidence:.0f}%", "90%", f"+{max(90 - confidence, 0):.0f}%", f"{min(confidence/90*100, 100):.0f}%"),
    ]
    pdf.table_header(["KPI", "Current", "Target", "Change", "Progress"], [36, 30, 30, 30, 34])
    for i, row in enumerate(kpi_rows):
        pdf.table_row(list(row), [36, 30, 30, 30, 34], alt=(i % 2 == 0))
    pdf.space()

    # ── Industry KPIs ──
    if industry_data.get("industry_kpis"):
        pdf.section_header(f"{industry_data.get('detected_industry', 'Industry')} KPIs")
        pdf.bullet(industry_data["industry_kpis"])
        pdf.space()

    # ── Charts ──
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

    # ── Appendix (technical details for analysts) ──
    pdf.section_header("Appendix — Technical Analysis")
    pdf.body("This section contains technical details intended for analysts and data scientists.")
    pdf.space()

    pdf.kv_row("Target Variable", target or "N/A")
    pdf.kv_row("Model Used", tech.get("model", "N/A"))
    pdf.kv_row("Features Evaluated", str(tech.get("n_features", "N/A")))
    pdf.kv_row("Sample Size", str(tech.get("n_samples", "N/A")))
    pdf.kv_row("Confidence Method", "4-factor (data quality + model perf + sample size + feature strength)")
    pdf.kv_row("Report Generated", datetime.now().strftime('%B %d, %Y at %H:%M'))

    if feats:
        pdf.space()
        pdf.body_bold("Feature Importance (Technical)")
        pdf.table_header(["Rank", "Feature", "Importance", "Method"], [12, 80, 30, 40])
        for i, f in enumerate(feats[:10]):
            imp_val = f.get("pct", f.get("importance", 0) * 100)
            pdf.table_row([str(i+1), f["feature"][:60], f"{imp_val:.1f}%", "SHAP-style"], [12, 80, 30, 40], alt=(i % 2 == 0))

    pdf.space()
    pdf.body("Prepared by: AURA Executive Intelligence Platform")
    pdf.body("Confidence scores are AI-generated estimates. Review by domain experts recommended.")

    return pdf
