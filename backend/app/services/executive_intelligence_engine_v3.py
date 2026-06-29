import io
import json
import logging
from typing import Any

import numpy as np
import pandas as pd

from app.services.business_analytics_engine_v2 import get_business_analytics
from app.services.data_quality_service import run_data_quality_audit
from app.services.ai_service import generate_response_async
from app.services.column_intelligence_service import filter_feature_columns

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# ENGINE 1: Deterministic Business Rules Engine
# ──────────────────────────────────────────────

def _extract_regional_patterns(df: pd.DataFrame, kpi_cols: list[str], geo_cols: list[str]) -> list[dict]:
    """Extract regional/department contributions to key KPIs."""
    patterns = []
    for kpi in kpi_cols[:2]:
        for geo in geo_cols[:2]:
            if geo not in df.columns or kpi not in df.columns:
                continue
            try:
                grouped = df.groupby(geo)[kpi].sum().sort_values(ascending=False)
                total = grouped.sum()
                if total == 0:
                    continue
                top = grouped.head(3)
                for region, val in top.items():
                    pct = round(val / total * 100, 1)
                    if pct > 10:
                        patterns.append({
                            "dimension": geo,
                            "segment": str(region),
                            "kpi": kpi,
                            "value": round(float(val), 2),
                            "contribution_pct": pct,
                            "insight": f"{str(region)} contributed {pct}% of {kpi} ({round(float(val), 2)})",
                        })
            except Exception:
                pass
    return patterns


def _extract_department_patterns(df: pd.DataFrame, kpi_cols: list[str], dept_cols: list[str]) -> list[dict]:
    """Extract department performance patterns."""
    patterns = []
    for kpi in kpi_cols[:2]:
        for dept in dept_cols[:2]:
            if dept not in df.columns or kpi not in df.columns:
                continue
            try:
                grouped = df.groupby(dept)[kpi].mean().sort_values(ascending=False)
                if len(grouped) < 2:
                    continue
                best_dept = str(grouped.index[0])
                worst_dept = str(grouped.index[-1])
                best_val = round(float(grouped.iloc[0]), 2)
                worst_val = round(float(grouped.iloc[-1]), 2)
                gap_pct = round((best_val - worst_val) / abs(worst_val) * 100, 1) if worst_val != 0 else 0
                if gap_pct > 10:
                    patterns.append({
                        "kpi": kpi,
                        "best_department": best_dept,
                        "best_value": best_val,
                        "worst_department": worst_dept,
                        "worst_value": worst_val,
                        "gap_pct": gap_pct,
                        "insight": f"{best_dept} leads in {kpi} ({best_val}), while {worst_dept} trails ({worst_val}) — a {gap_pct}% gap",
                    })
            except Exception:
                pass
    return patterns


def _compute_growth_rates(df: pd.DataFrame, kpi_cols: list[str]) -> list[dict]:
    """Compute growth rates for key KPIs."""
    rates = []
    for col in kpi_cols[:3]:
        if col not in df.columns:
            continue
        vals = df[col].dropna().values.astype(float)
        if len(vals) < 4:
            continue
        recent = vals[-3:].mean()
        earlier = vals[:3].mean()
        growth = ((recent - earlier) / earlier) * 100 if earlier != 0 else 0
        direction = "increased" if growth > 2 else "decreased" if growth < -2 else "remained stable"
        rates.append({
            "metric": col,
            "directional_word": direction,
            "change_pct": round(float(growth), 1),
            "recent_avg": round(float(recent), 2),
            "earlier_avg": round(float(earlier), 2),
            "sentence": f"{col} {direction} by {abs(round(growth, 1))}% (from {round(earlier, 2)} to {round(recent, 2)})",
        })
    return rates


def _detect_margin_squeeze(df: pd.DataFrame, revenue_cols: list[str], profit_cols: list[str]) -> dict | None:
    """Detect profit margin squeeze despite revenue growth."""
    for rev in revenue_cols:
        for prof in profit_cols:
            if rev not in df.columns or prof not in df.columns:
                continue
            try:
                rev_vals = df[rev].dropna().values.astype(float)
                prof_vals = df[prof].dropna().values.astype(float)
                if len(rev_vals) < 4 or len(prof_vals) < 4:
                    continue
                rev_growth = (rev_vals[-3:].mean() / rev_vals[:3].mean() - 1) * 100
                prof_growth = (prof_vals[-3:].mean() / prof_vals[:3].mean() - 1) * 100
                if rev_growth > 5 and prof_growth < rev_growth / 2:
                    return {
                        "revenue_growth_pct": round(float(rev_growth), 1),
                        "profit_growth_pct": round(float(prof_growth), 1),
                        "insight": f"Revenue grew {round(rev_growth, 1)}% but profit only grew {round(prof_growth, 1)}%, indicating shrinking margins",
                        "recommendation": "Review cost structure and optimize expenses to protect margins",
                    }
            except Exception:
                pass
    return None


# ──────────────────────────────────────────────
# ENGINE 2: Root Cause Engine
# ──────────────────────────────────────────────

def _find_root_causes(df: pd.DataFrame, target: str, ds: dict) -> list[dict]:
    """Identify root causes from correlations and comparative analysis."""
    causes = []
    numeric_cols = ds.get("numeric_columns", [])
    cat_cols = ds.get("categorical_columns", [])

    for col in numeric_cols[:5]:
        if col not in df.columns or target not in df.columns or col == target:
            continue
        try:
            corr = df[col].corr(df[target])
            if not pd.isna(corr) and abs(corr) >= 0.3:
                direction = "increases" if corr > 0 else "decreases"
                strength = "strongly" if abs(corr) >= 0.7 else "moderately"
                causes.append({
                    "cause": f"{col} {direction} {target}",
                    "evidence": f"Correlation of {corr:.3f} — {strength} {direction} relationship with {target}",
                    "impact_area": "Revenue" if any(kw in col.lower() for kw in ["revenue", "sales", "income"]) else "Cost" if any(kw in col.lower() for kw in ["cost", "expense"]) else "Operations",
                    "confidence": round(abs(corr) * 100, 1),
                })
        except Exception:
            pass

    for col in cat_cols[:3]:
        if col not in df.columns or target not in df.columns:
            continue
        try:
            grouped = df.groupby(col)[target].mean().sort_values(ascending=False)
            if len(grouped) >= 2:
                top = str(grouped.index[0])
                bottom = str(grouped.index[-1])
                gap = round(float(grouped.iloc[0] - grouped.iloc[-1]), 3)
                if abs(gap) > 0.05:
                    causes.append({
                        "cause": f"'{top}' segment shows highest {target} risk",
                        "evidence": f"'{top}' group has {round(min(float(grouped.iloc[0]), 1)*100, 1)}% rate vs '{bottom}' group at {round(min(float(grouped.iloc[-1]), 1)*100, 1)}%",
                        "impact_area": "Customers",
                        "confidence": round(min(abs(gap) * 200, 100), 1),
                    })
        except Exception:
            pass
    return causes


# ──────────────────────────────────────────────
# ENGINE 3: Narrative Generation Engine
# ──────────────────────────────────────────────

def _generate_narrative_blocks(analysis: dict, patterns: dict) -> dict:
    """Transform deterministic data into consulting-style narrative blocks."""
    blocks = {}
    growth_rates = patterns.get("growth_rates", [])
    regional = patterns.get("regional", [])
    departmental = patterns.get("departmental", [])
    margin = patterns.get("margin_squeeze")
    trend = analysis.get("trend_analysis", {})

    # Narrative: Revenue/Performance Summary
    perf_parts = []
    for g in growth_rates[:2]:
        perf_parts.append(g["sentence"])
    for r in regional[:2]:
        perf_parts.append(r["insight"])
    if margin:
        perf_parts.append(margin["insight"])
    blocks["performance_summary"] = ". ".join(perf_parts) if perf_parts else ""

    # Narrative: Department Comparison
    dept_parts = []
    for d in departmental[:2]:
        dept_parts.append(d["insight"])
    blocks["department_comparison"] = ". ".join(dept_parts) if dept_parts else ""

    # Narrative: Trend Summary
    trend_parts = []
    for col, t in list(trend.items())[:3]:
        trend_parts.append(f"{col} is trending {t.get('direction', 'stable')} ({t.get('change_pct', 0):.1f}%)")
    blocks["trend_summary"] = ". ".join(trend_parts) if trend_parts else ""

    # Build executive summary
    summary_parts = []
    if perf_parts:
        summary_parts.append(perf_parts[0])
    if margin:
        summary_parts.append(margin["insight"])
    if dept_parts:
        summary_parts.append(dept_parts[0])
    if trend_parts:
        summary_parts.append(trend_parts[0])
    blocks["executive_summary"] = ". ".join(summary_parts[:3]) if summary_parts else "Analysis complete."

    return blocks


# ──────────────────────────────────────────────
# ENGINE 4: Recommendation Engine
# ──────────────────────────────────────────────

def _generate_recommendations(patterns: dict, root_causes: list[dict]) -> list[dict]:
    """Generate business recommendations from patterns and root causes."""
    recs = []
    margin = patterns.get("margin_squeeze")
    regional = patterns.get("regional", [])
    growth_rates = patterns.get("growth_rates", [])
    departmental = patterns.get("departmental", [])

    if margin:
        recs.append({
            "title": "Optimize Cost Structure to Protect Margins",
            "description": margin["recommendation"],
            "priority": "Critical", "expected_outcome": "Improve profit margins by aligning cost growth with revenue growth",
            "roi": "3-5x based on margin recovery",
        })

    if regional:
        top_region = regional[0]
        recs.append({
            "title": f"Invest in High-Performing Region: {top_region['segment']}",
            "description": f"{top_region['segment']} contributes {top_region['contribution_pct']}% of {top_region['kpi']}. Increase investment to maximize returns.",
            "priority": "High",
            "expected_outcome": f"Potential {round(top_region['contribution_pct'] * 0.2, 1)}% uplift in {top_region['kpi']}",
            "roi": "4-6x based on current performance",
        })

    if departmental:
        dept = departmental[0]
        recs.append({
            "title": f"Address Performance Gap in {dept['worst_department']}",
            "description": f"Close the {dept['gap_pct']}% gap between {dept['best_department']} and {dept['worst_department']} in {dept['kpi']}",
            "priority": "High",
            "expected_outcome": f"Recover up to {dept['gap_pct']}% in {dept['kpi']} performance",
            "roi": "3-4x",
        })

    if root_causes:
        top_cause = root_causes[0]
        recs.append({
            "title": f"Address Root Cause: {top_cause['cause'][:60]}",
            "description": f"Evidence: {top_cause['evidence'][:100]}",
            "priority": "High", "expected_outcome": "Reduced risk exposure and improved business stability",
            "roi": "2-5x depending on implementation scope",
        })

    if growth_rates:
        for g in growth_rates[:1]:
            if g["change_pct"] < 0:
                recs.append({
                    "title": f"Reverse Decline in {g['metric']}",
                    "description": f"{g['metric']} decreased by {abs(g['change_pct'])}%. Investigate causes and develop recovery plan.",
                    "priority": "High", "expected_outcome": f"Return {g['metric']} to positive growth trajectory",
                    "roi": "3-6x",
                })

    recs.append({
        "title": "Implement Continuous Monitoring System",
        "description": "Set up automated monitoring for all identified KPIs with early warning thresholds",
        "priority": "Medium", "expected_outcome": "Early detection of risks and opportunities",
        "roi": "5-8x through avoided losses",
    })

    return recs[:6]


# ──────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────

async def run_executive_intelligence(doc_id: int) -> dict[str, Any]:
    """Run the complete Executive Intelligence Engine with all sub-engines."""
    from app.database.database import get_session_factory
    from app.models.document import Document
    from sqlalchemy import select

    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        return {"error": "Document not found"}

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip", engine="python") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    # Layer 1: Business Analytics
    analysis = await get_business_analytics(doc_id)
    if "error" in analysis:
        return analysis

    dq = run_data_quality_audit(df)
    ds = analysis.get("dataset_intelligence", {})
    kpi_cols = ds.get("kpi_columns", []) or ds.get("numeric_columns", [])[:5]
    geo_cols = ds.get("geographic_columns", [])
    cat_cols = ds.get("categorical_columns", [])
    target = ds.get("target_variable", "")
    all_cols_lower = " ".join(df.columns.str.lower())
    dept_cols = [c for c in cat_cols if any(kw in c.lower() for kw in ["department", "division", "unit", "team", "region", "branch"])] or cat_cols[:2]
    revenue_cols = [c for c in kpi_cols if any(kw in c.lower() for kw in ["revenue", "sales", "income"])] or kpi_cols[:1]
    profit_cols = [c for c in kpi_cols if any(kw in c.lower() for kw in ["profit", "margin", "earnings"])] or (kpi_cols[1:2] if len(kpi_cols) > 1 else [])

    # Engine 1: Business Rules
    growth_rates = _compute_growth_rates(df, kpi_cols)
    reg_patterns = _extract_regional_patterns(df, kpi_cols, geo_cols or cat_cols[:2])
    dept_patterns = _extract_department_patterns(df, kpi_cols, dept_cols)
    margin_squeeze = _detect_margin_squeeze(df, revenue_cols, profit_cols)
    patterns = {"growth_rates": growth_rates, "regional": reg_patterns, "departmental": dept_patterns, "margin_squeeze": margin_squeeze}

    # Engine 2: Root Cause
    root_causes = _find_root_causes(df, target, ds) if target else []

    # Engine 3: Narrative Generation
    narratives = _generate_narrative_blocks(analysis, patterns)

    # Engine 4: Recommendation
    recommendations = _generate_recommendations(patterns, root_causes)

    # Engine 5: AI Enhancement (optional - enhances narrative with consulting language)
    ai_enhanced = {}
    try:
        prompt_data = json.dumps({
            "patterns": {k: (v[:3] if isinstance(v, list) else v) for k, v in patterns.items()},
            "root_causes": root_causes[:3],
            "narrative": narratives,
            "business_type": ds.get("dataset_type", "General"),
        }, indent=2)

        prompt = f"""You are a Senior Executive Advisor at McKinsey. Based on this business analysis data, generate a polished executive summary and risk/opportunity assessment.

Return ONLY valid JSON:
{{
  "executive_summary": "3-4 sentences using the specific numbers provided. Consulting-grade language.",
  "risks": [{{"name": "Risk with context", "description": "Business consequence with numbers", "severity": "Critical|High|Medium", "financial_exposure": "$$$", "mitigation": "Action"}}],
  "opportunities": [{{"name": "Opportunity", "description": "Expected benefit with numbers", "impact": "high|medium", "estimated_value": "$$$", "action": "Action"}}],
  "business_health": {{"overall": 78, "revenue_health": 82, "cost_health": 65, "growth_health": 75, "risk_health": 60, "operations_health": 80, "customer_health": 85}},
  "confidence": 85
}}

Business Data:
{prompt_data}"""

        raw = await generate_response_async(prompt, request_type="executive_intelligence")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        ai_enhanced = json.loads(raw)
    except Exception as e:
        logger.warning("AI enhancement failed: %s", e)

    result = {
        "doc_id": doc_id,
        "executive_summary": narratives.get("executive_summary", ai_enhanced.get("executive_summary", analysis.get("dataset_intelligence", {}).get("dataset_type", "Analysis complete."))),
        "narratives": narratives,
        "key_findings": [
            {"title": g["sentence"], "detail": f"Recent avg: {g['recent_avg']}, Earlier avg: {g['earlier_avg']}", "impact": "high" if abs(g["change_pct"]) > 10 else "medium", "confidence": min(abs(g["change_pct"]) + 50, 95)} for g in growth_rates[:4]
        ] + [
            {"title": r["insight"], "detail": f"Contribution: {r['contribution_pct']}% of {r['kpi']}", "impact": "high" if r["contribution_pct"] > 30 else "medium", "confidence": 80} for r in reg_patterns[:2]
        ] + [
            {"title": d["insight"], "detail": f"Gap: {d['gap_pct']}%", "impact": "high" if d["gap_pct"] > 50 else "medium", "confidence": 85} for d in dept_patterns[:2]
        ],
        "root_causes": root_causes[:5],
        "business_impact": {
            "revenue_impact": f"Revenue growth of {growth_rates[0]['change_pct']}% in {growth_rates[0]['metric']}" if growth_rates else "Revenue trends stable",
            "cost_impact": margin_squeeze["insight"] if margin_squeeze else "Cost structure under review",
            "operational_impact": f"Departmental gap of {dept_patterns[0]['gap_pct']}% identified between top and bottom performers" if dept_patterns else "Operational metrics within normal range",
            "customer_impact": f"'{root_causes[0]['cause']}' affects customer segments" if root_causes else "Customer metrics stable",
        },
        "risks": ai_enhanced.get("risks", [
            {"name": f"Trend reversal in key metrics", "description": f"Current positive trends may reverse without intervention", "severity": "Medium", "financial_exposure": "TBD based on magnitude", "mitigation": "Implement continuous monitoring and early warning systems"}
        ]),
        "opportunities": ai_enhanced.get("opportunities", [
            {"name": f"Optimize underperforming segments", "description": f"Address identified gaps to unlock growth potential", "impact": "medium", "estimated_value": "Based on gap analysis", "action": "Develop targeted improvement plans"}
        ]),
        "recommendations": recommendations,
        "business_health": ai_enhanced.get("business_health", {
            "overall": round((dq.get("overall_score", 70) + (80 if growth_rates else 60) + (70 if not margin_squeeze else 50)) / 3),
            "revenue_health": min(round(abs(growth_rates[0]["change_pct"]) + 70 if growth_rates and growth_rates[0]["change_pct"] > 0 else 50), 95) if growth_rates else 70,
            "cost_health": 40 if margin_squeeze else 75,
            "growth_health": min(round(abs(growth_rates[0]["change_pct"]) + 60), 95) if growth_rates else 65,
            "risk_health": max(30, 80 - len(root_causes) * 8) if root_causes else 70,
            "operations_health": max(40, 85 - abs(dept_patterns[0]["gap_pct"])) if dept_patterns else 75,
            "customer_health": 80,
        }),
        "confidence": ai_enhanced.get("confidence", round(min((dq.get("overall_score", 70) + 50) / 100, 0.95), 2)),
        "data_quality": {"score": dq.get("overall_score"), "grade": dq.get("grade")},
        "kpi_summary": analysis.get("kpi_summary", {}),
        "charts": analysis.get("charts", []),
        "growth_rates": growth_rates,
        "regional_breakdown": reg_patterns,
        "department_breakdown": dept_patterns,
        "margin_analysis": margin_squeeze,
    }

    # Predictive pipeline: AutoML + Explainability + Scenario Analysis → Analyst section
    try:
        analyst = await _build_analyst_from_predictive_pipeline(doc_id, df)
        result["analyst"] = analyst
    except Exception as e:
        logger.warning("Predictive analyst pipeline failed: %s", e)
        result["analyst"] = {"error": str(e)[:100]}

    return result


async def _build_analyst_from_predictive_pipeline(doc_id: int, df: pd.DataFrame) -> dict:
    """Run AutoML + Explainability + Scenario Analysis for the Analyst view."""
    from app.services.automl_service import run_automl
    from app.services.dataset_intelligence_service import analyze_dataset
    from app.services.data_quality_service import run_data_quality_audit
    from app.services.explainability_service import run_explainability
    from app.services.scenario_simulation_service import run_scenario_analysis

    ds = analyze_dataset(df)
    target = ds.get("target_variable", "")
    if not target or target not in df.columns:
        return {"note": "Target variable not detected — cannot run predictive analysis for this dataset."}

    automl_result = await run_automl(doc_id, "", target)
    if "error" in automl_result:
        return {"note": f"AutoML failed: {automl_result['error']}"}

    X = df.drop(columns=[target]).select_dtypes(include=["number"])
    X = filter_feature_columns(X)
    if X.shape[1] < 1:
        return {"note": "No numeric features available after filtering identifiers — analyst details not available."}
    y = df[target]

    problem_type = automl_result.get("problem_type", "regression")
    if problem_type == "classification" and y.dtype in ("float64", "object"):
        y = y.astype(int)

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    best_name = automl_result.get("best_model", "")
    model = _rebuild_model(best_name, problem_type)
    if model is None:
        return {"note": f"Could not rebuild model '{best_name}' — analyst details not available."}
    model.fit(X_train, y_train)

    dq = run_data_quality_audit(df)
    dq_score = dq.get("overall_score", 80)

    explainability = await run_explainability(
        model, X_train, X_test, y_train, y_test,
        X.columns.tolist(), dq_score,
        problem_type=problem_type,
        n_models_tested=automl_result.get("models_tested", 1),
    )

    scenario_result = await run_scenario_analysis(doc_id)

    y_pred = model.predict(X_test) if hasattr(model, "predict") else None
    analyst = _build_analyst_section(
        model, automl_result, explainability, X_train, X_test, y_train, y_test, y_pred,
        problem_type, df, target,
    )
    analyst["scenario_analysis"] = scenario_result
    return analyst


def _build_analyst_section(
    model, automl: dict, explainability: dict,
    X_train, X_test, y_train, y_test, y_pred,
    problem_type: str, df: pd.DataFrame, target: str,
) -> dict[str, Any]:
    """Build technical analyst section with full model metrics."""
    metrics = {}
    if problem_type == "classification":
        try:
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score,
                f1_score, roc_auc_score, confusion_matrix,
            )
            if y_pred is not None:
                metrics["accuracy"] = round(float(accuracy_score(y_test, y_pred)), 4)
                metrics["precision"] = round(float(precision_score(y_test, y_pred, average="weighted")), 4)
                metrics["recall"] = round(float(recall_score(y_test, y_pred, average="weighted")), 4)
                metrics["f1"] = round(float(f1_score(y_test, y_pred, average="weighted")), 4)
            try:
                y_prob = model.predict_proba(X_test)
                metrics["roc_auc"] = round(float(roc_auc_score(y_test, y_prob, multi_class="ovr")), 4)
            except Exception:
                metrics["roc_auc"] = None
            try:
                cm = confusion_matrix(y_test, y_pred).tolist() if y_pred is not None else []
                metrics["confusion_matrix"] = cm
            except Exception:
                metrics["confusion_matrix"] = []
        except Exception as e:
            logger.warning("Classification metrics failed: %s", e)
    else:
        try:
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
            if y_pred is not None:
                metrics["r2"] = round(float(r2_score(y_test, y_pred)), 4)
                metrics["rmse"] = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4)
                metrics["mae"] = round(float(mean_absolute_error(y_test, y_pred)), 4)
            try:
                mape_val = np.mean(np.abs((y_test - y_pred) / (np.abs(y_test) + 1e-10))) * 100
                metrics["mape"] = round(float(mape_val), 2)
            except Exception:
                metrics["mape"] = None
        except Exception as e:
            logger.warning("Regression metrics failed: %s", e)

    residuals = {}
    if y_pred is not None and len(y_pred) == len(y_test):
        try:
            res = y_test - y_pred
            residuals = {
                "mean": round(float(np.mean(res)), 4),
                "std": round(float(np.std(res)), 4),
                "min": round(float(np.min(res)), 4),
                "max": round(float(np.max(res)), 4),
                "normality_p_value": _normality_test(res),
            }
        except Exception as e:
            residuals = {"error": str(e)[:60]}

    class_report = {}
    if problem_type == "classification" and y_pred is not None:
        try:
            from sklearn.metrics import classification_report
            cr = classification_report(y_test, y_pred, output_dict=True)
            class_report = {str(k): v for k, v in cr.items() if isinstance(v, dict)}
        except Exception:
            pass

    all_results = automl.get("results", [])
    best_metric = automl.get("best_f1") or automl.get("best_r2")

    return {
        "model_info": {
            "selected_model": automl.get("best_model", "Unknown"),
            "models_tested": automl.get("models_tested", 0),
            "problem_type": problem_type,
            "target": automl.get("target", ""),
            "features": automl.get("features", 0),
            "samples": automl.get("samples", 0),
            "best_metric": round(best_metric, 4) if best_metric else None,
        },
        "metrics": metrics,
        "classification_report": class_report,
        "residual_analysis": residuals,
        "feature_importance": explainability.get("feature_importance", []),
        "permutation_importance": explainability.get("permutation_importance", []),
        "shap_values": explainability.get("shap_values", []),
        "cross_validation": explainability.get("cross_validation", {}),
        "prediction_intervals": explainability.get("prediction_intervals", {}),
        "confidence": explainability.get("confidence", {}),
        "automl_details": {
            "models_tested": automl.get("models_tested", 0),
            "all_models": [
                {
                    "name": r.get("model_name", "Unknown"),
                    "metrics": {k: round(v, 4) for k, v in r.items() if k not in ("model_name", "error") and isinstance(v, (int, float))},
                    "error": r.get("error"),
                }
                for r in all_results
            ],
        },
    }


def _rebuild_model(name: str, problem_type: str):
    try:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
        if problem_type == "classification":
            if "Logistic" in name: return LogisticRegression(max_iter=1000, random_state=42)
            if "Random" in name: return RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
            if "XGBoost" in name:
                from xgboost import XGBClassifier
                return XGBClassifier(n_estimators=50, random_state=42, verbosity=0)
            if "LightGBM" in name:
                import lightgbm as lgb
                return lgb.LGBMClassifier(n_estimators=50, random_state=42, verbose=-1)
            if "CatBoost" in name:
                from catboost import CatBoostClassifier
                return CatBoostClassifier(n_estimators=50, random_state=42, verbose=0)
        else:
            if "Linear" in name: return LinearRegression()
            if "Ridge" in name: return Ridge(alpha=1.0, random_state=42)
            if "Random" in name: return RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
            if "XGBoost" in name:
                from xgboost import XGBRegressor
                return XGBRegressor(n_estimators=50, random_state=42, verbosity=0)
            if "LightGBM" in name:
                import lightgbm as lgb
                return lgb.LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
            if "CatBoost" in name:
                from catboost import CatBoostRegressor
                return CatBoostRegressor(n_estimators=50, random_state=42, verbose=0)
    except Exception:
        pass
    return None


def _normality_test(residuals: np.ndarray) -> float | None:
    try:
        from scipy.stats import shapiro
        if len(residuals) >= 3:
            _, p = shapiro(residuals[:5000])
            return round(float(p), 4)
    except ImportError:
        pass
    return None
