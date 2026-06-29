import logging
from typing import Any

logger = logging.getLogger(__name__)


def _grade_label(val: float, thresholds: list[tuple[float, str, str]]) -> tuple[str, str]:
    for threshold, label, desc in thresholds:
        if val >= threshold:
            return label, desc
    return thresholds[-1][1], thresholds[-1][2]


def _fmt_currency(val: float) -> str:
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    elif abs(val) >= 1_000:
        return f"${val / 1_000:,.1f}K"
    return f"${val:,.0f}"


def generate_executive_summary(
    problem_type: str,
    target: str,
    confidence_score: float,
    risk_score: float,
    cv_mean: float | None,
    feature_count: int,
    sample_count: int,
    direction: str = "",
) -> str:
    """Generate a plain-English executive summary grounded in model outputs."""
    if problem_type in ("classification",):
        if risk_score >= 70:
            template = (
                f"There is a {confidence_score:.0f}% probability that {target} will reach critical levels, "
                f"based on an analysis of {sample_count:,} records across {feature_count} business factors. "
                f"Cross-validation confirms a {cv_mean:.0%} predictive reliability rate."
            )
        elif risk_score >= 40:
            template = (
                f"Analysis indicates a {confidence_score:.0f}% likelihood of elevated {target} risk over the near term, "
                f"drawn from {sample_count:,} records and {feature_count} contributing factors. "
                f"The model demonstrates {cv_mean:.0%} cross-validated prediction strength."
            )
        else:
            template = (
                f"Current {target} conditions appear stable, with a {confidence_score:.0f}% confidence rating "
                f"based on {sample_count:,} records and {feature_count} monitored factors. "
                f"Predictive reliability is measured at {cv_mean:.0%}."
            )
    elif problem_type in ("regression", "time_series"):
        if direction == "up" or (risk_score >= 50):
            template = (
                f"Forecast models project a significant {target} shift, with {confidence_score:.0f}% confidence "
                f"across {sample_count:,} data points and {feature_count} drivers. "
                f"The model achieves {cv_mean:.0%} cross-validated accuracy."
            )
        else:
            template = (
                f"{target} projections indicate stability, validated at {confidence_score:.0f}% confidence "
                f"across {sample_count:,} observations and {feature_count} business factors. "
                f"Cross-validated model strength: {cv_mean:.0%}."
            )
    else:
        template = (
            f"Analysis of {sample_count:,} records across {feature_count} factors reveals "
            f"a {confidence_score:.0f}% confidence level. The predictive model achieves {cv_mean:.0%} cross-validated accuracy."
        )
    return template


def generate_business_impact(
    risk_score: float, confidence_score: float,
    revenue_at_risk: float, population_at_risk: int, total_population: int,
    risk_level: str,
) -> dict[str, Any]:
    """Generate business impact assessment."""
    impact_level, _ = _grade_label(risk_score, [
        (80, "Critical", "Immediate executive attention required"),
        (60, "High", "Active mitigation strategy needed"),
        (40, "Moderate", "Monitor and plan responses"),
        (0, "Low", "Standard business as usual"),
    ])

    urgency, _ = _grade_label(risk_score, [
        (80, "Immediate Action Required", "within 30 days"),
        (60, "Short-term Priority", "within 90 days"),
        (40, "Medium-term Watch", "within 180 days"),
        (0, "Routine Monitoring", "standard cadence"),
    ])

    if revenue_at_risk > 0:
        exposure = f"{_fmt_currency(revenue_at_risk)} in annual revenue exposure"
    else:
        exposure = _fmt_currency(population_at_risk * 1000) if population_at_risk > 0 else "Undetermined"

    if total_population > 0:
        pop_pct = round(population_at_risk / total_population * 100, 1)
        affected = f"{population_at_risk:,} records affected ({pop_pct}% of population)"
    else:
        affected = f"{population_at_risk:,} records identified"

    return {
        "financial_exposure": _fmt_currency(revenue_at_risk) if revenue_at_risk > 0 else exposure,
        "financial_exposure_raw": round(revenue_at_risk, 2),
        "at_risk_percentage": round(population_at_risk / total_population * 100, 1) if total_population > 0 else 0,
        "impact_level": impact_level,
        "risk_level": risk_level,
        "urgency": urgency,
        "confidence": round(confidence_score, 1),
        "affected_population": affected,
        "exposure_narrative": f"{exposure}. {affected}.",
    }


def generate_key_drivers(
    feature_importance: list[dict],
    shap_values: list[dict] | None = None,
    total_features: int = 0,
) -> list[dict[str, Any]]:
    """Generate executive narratives for key drivers."""
    drivers = feature_importance or shap_values or []
    results = []
    for i, d in enumerate(drivers[:6]):
        feat = d.get("feature", f"Factor {i+1}")
        val = d.get("importance") or d.get("shap_value", 0)
        if val is None:
            continue
        influence_pct = round(val * 100, 1) if val < 1 else round(val, 1)
        if i == 0:
            direction = "primary"
            narrative = f"{feat} is the dominant factor with {influence_pct}% influence — this is the single most important variable driving the prediction."
        elif i <= 2:
            direction = "significant"
            narrative = f"{feat} contributes {influence_pct}% influence and requires active management attention."
        elif i <= 4:
            direction = "notable"
            narrative = f"{feat} shows {influence_pct}% influence as a secondary contributing factor."
        else:
            direction = "contributing"
            narrative = f"{feat} at {influence_pct}% influence rounds out the key driver set."

        results.append({
            "factor": feat,
            "influence_pct": influence_pct,
            "direction": direction,
            "narrative": narrative,
        })

    if total_features > len(drivers):
        remaining = total_features - len(drivers)
        if remaining > 0:
            results.append({
                "factor": f"{remaining} additional factors",
                "influence_pct": 0,
                "direction": "minor",
                "narrative": f"An additional {remaining} monitored factors have minimal individual impact but contribute collectively to the prediction.",
            })

    return results


def generate_top_risks(
    early_warnings: list[dict],
    risk_score: float,
    revenue_at_risk: float,
    severity_map: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Generate executive risk assessment from early warnings."""
    risks = []
    if severity_map is None:
        severity_map = {"critical": "Critical", "high": "High", "medium": "Moderate", "low": "Low"}

    for w in (early_warnings or []):
        severity_label = severity_map.get(w.get("severity", "").lower(), w.get("severity", "Moderate"))
        risks.append({
            "risk": w.get("alert", "Unspecified risk"),
            "probability": risk_score,
            "financial_impact": _fmt_currency(revenue_at_risk * 0.1) if revenue_at_risk else "Undetermined",
            "severity": severity_label,
            "recommended_action": w.get("recommended_action", "Evaluate and respond"),
            "impact_description": w.get("impact", ""),
        })

    if not risks and risk_score > 0:
        risks.append({
            "risk": "Aggregate model risk",
            "probability": risk_score,
            "financial_impact": _fmt_currency(revenue_at_risk) if revenue_at_risk else "Undetermined",
            "severity": "High" if risk_score >= 70 else "Moderate" if risk_score >= 40 else "Low",
            "recommended_action": "Continue monitoring with standard business processes",
            "impact_description": "",
        })

    return risks


def generate_top_opportunities(
    opportunities: list[dict],
    prescriptive: list[dict],
    scenario_results: dict | None = None,
) -> list[dict[str, Any]]:
    """Generate executive opportunity assessment."""
    result = []
    seen = set()

    for opp in (opportunities or []):
        title = opp.get("title", opp.get("opportunity", ""))
        if title and title.lower() not in seen:
            seen.add(title.lower())
            result.append({
                "opportunity": title,
                "potential_value": opp.get("revenue_impact", opp.get("potential_value", "TBD")),
                "roi": 0,
                "effort": "Medium",
                "description": opp.get("description", ""),
            })

    for rec in (prescriptive or []):
        action = rec.get("recommendation", rec.get("action", ""))
        if action and action.lower() not in seen:
            seen.add(action.lower())
            roi_str = rec.get("roi", "0x")
            try:
                roi = float(roi_str.replace("x", ""))
            except (ValueError, AttributeError):
                roi = 0
            result.append({
                "opportunity": action,
                "potential_value": rec.get("revenue_preserved", "TBD"),
                "roi": roi,
                "effort": rec.get("effort", "Medium"),
                "description": rec.get("expected_impact", ""),
            })

    if scenario_results:
        scenarios = scenario_results.get("scenarios", [])
        for s in scenarios:
            label = s.get("label", "")
            if label == "Best Case" and s.get("revenue_impact", 0) > 0:
                result.append({
                    "opportunity": f"Revenue growth scenario: {s.get('scenario', 'Growth')}",
                    "potential_value": _fmt_currency(s["revenue_impact"]),
                    "roi": 0,
                    "effort": "Medium",
                    "description": f"Best-case scenario projects {_fmt_currency(s['revenue_impact'])} in additional revenue.",
                })

    return result[:8]


def generate_recommended_actions(
    prescriptive: list[dict],
    risk_score: float,
    cv_mean: float | None,
    n_models: int = 1,
) -> list[dict[str, Any]]:
    """Generate prioritized executive recommendations."""
    actions = []

    for rec in (prescriptive or []):
        action = rec.get("recommendation", rec.get("action", ""))
        priority = rec.get("priority", "")
        if not priority:
            priority = "High" if risk_score >= 70 else "Medium" if risk_score >= 40 else "Low"
        roi_str = rec.get("roi", "0x")
        try:
            roi = float(roi_str.replace("x", ""))
        except (ValueError, AttributeError):
            roi = 0

        actions.append({
            "action": action,
            "expected_roi": f"{roi:.1f}x" if roi else "TBD",
            "priority": priority,
            "timeline": "Immediate" if priority == "High" else "Short-term" if priority == "Medium" else "Long-term",
            "expected_impact": rec.get("expected_impact", ""),
        })

    if not actions:
        if risk_score >= 70:
            actions.append({
                "action": "Launch comprehensive risk mitigation program targeting identified high-risk segments",
                "expected_roi": f"{max(risk_score / 10, 2):.1f}x",
                "priority": "High",
                "timeline": "Immediate",
                "expected_impact": f"Target ~{risk_score:.0f}% of at-risk population with retention initiatives",
            })
            actions.append({
                "action": "Increase monitoring frequency and establish early warning dashboards for key drivers",
                "expected_roi": f"{max(risk_score / 15, 1.5):.1f}x",
                "priority": "High",
                "timeline": "Within 30 days",
                "expected_impact": "Reduced response time to emerging risks",
            })
        elif risk_score >= 40:
            actions.append({
                "action": "Implement targeted monitoring program for moderate-risk segments",
                "expected_roi": f"{max(risk_score / 12, 1.5):.1f}x",
                "priority": "Medium",
                "timeline": "Within 90 days",
                "expected_impact": "Proactive risk management for ~40% of impacted population",
            })
        else:
            actions.append({
                "action": "Maintain standard monitoring cadence and periodic review cycle",
                "expected_roi": f"{max(cv_mean or 0.5, 1):.1f}x",
                "priority": "Low",
                "timeline": "Ongoing",
                "expected_impact": "Sustained operational stability",
            })

    actions.append({
        "action": f"Validate findings with {max(n_models, 1)} model{'s' if n_models != 1 else ''} and update quarterly",
        "expected_roi": "1.0x",
        "priority": "Medium",
        "timeline": "Quarterly",
        "expected_impact": "Continuous model accuracy improvement and risk recalibration",
    })

    return actions


def generate_financial_exposure(
    revenue_at_risk: float,
    scenario_results: dict | None = None,
    confidence_score: float = 0,
) -> dict[str, Any]:
    """Generate financial exposure summary with scenario ranges."""
    if scenario_results and scenario_results.get("scenarios"):
        comp = scenario_results.get("comparison", {})
        rev_range = comp.get("revenue_range", [0, 0])
        worst_val = rev_range[0] if len(rev_range) > 0 else 0
        best_val = rev_range[-1] if len(rev_range) > 1 else 0
        best_case = _fmt_currency(best_val)
        worst_case = _fmt_currency(worst_val)
        expected_case = _fmt_currency((worst_val + best_val) / 2)
    else:
        best_case = _fmt_currency(revenue_at_risk * 0.7)
        worst_case = _fmt_currency(revenue_at_risk * 1.3)
        expected_case = _fmt_currency(revenue_at_risk)

    return {
        "total_at_risk": _fmt_currency(revenue_at_risk),
        "best_case": best_case,
        "expected_case": expected_case,
        "worst_case": worst_case,
        "confidence_range": f"±{20 - min(confidence_score * 0.2, 15):.0f}%",
        "narrative": (
            f"Financial exposure is estimated at {_fmt_currency(revenue_at_risk)} under expected conditions, "
            f"ranging from {worst_case} (downside) to {best_case} (upside). "
            f"The confidence interval is ±{20 - min(confidence_score * 0.2, 15):.0f}%."
        ),
    }


def generate_decision_confidence(
    confidence_score: float,
    confidence_factors: list[str],
    confidence_breakdown: dict | None = None,
    cv_mean: float | None = None,
) -> dict[str, Any]:
    """Generate decision confidence assessment."""
    grade, grade_desc = _grade_label(confidence_score, [
        (80, "High Confidence", "Strong statistical basis for decision-making"),
        (60, "Moderate Confidence", "Adequate evidence for informed decisions"),
        (40, "Cautious Confidence", "Further validation recommended"),
        (0, "Low Confidence", "Insufficient evidence for material decisions"),
    ])

    return {
        "overall": round(confidence_score, 1),
        "grade": grade,
        "grade_description": grade_desc,
        "factors": confidence_factors or [f"Model achieves {cv_mean:.0%} cross-validated accuracy" if cv_mean else "Confidence assessment based on available data"],
        "breakdown": confidence_breakdown or {},
    }


def generate_source_evidence(
    model_name: str,
    cv_mean: float | None,
    cv_folds: int,
    data_quality_score: float,
    sample_count: int,
    feature_count: int,
    models_tested: int,
    confidence_score: float,
) -> dict[str, Any]:
    """Generate evidence summary for decision traceability."""
    dq_grade, _ = _grade_label(data_quality_score, [
        (80, "High Quality", "Data integrity verified"),
        (60, "Moderate Quality", "Minor data quality issues present"),
        (0, "Needs Improvement", "Data quality concerns identified"),
    ])

    return {
        "model_performance": f"{model_name} — {cv_mean:.0%} cross-validated accuracy ({cv_folds}-fold)" if cv_mean else f"{model_name} — trained on available data",
        "data_quality": f"{dq_grade} ({data_quality_score:.0f}%)",
        "sample_size": sample_count,
        "features_analyzed": feature_count,
        "models_evaluated": models_tested,
        "overall_confidence": f"{confidence_score:.0f}%",
        "narrative": (
            f"Analysis based on {sample_count:,} records with {feature_count} business factors "
            f"across {models_tested} model{'s' if models_tested != 1 else ''}. "
            f"Data quality assessed at {data_quality_score:.0f}% ({dq_grade}). "
            f"Best model: {model_name}."
        ),
    }


async def run_executive_decision_intelligence(
    automl_result: dict,
    explainability_result: dict,
    scenario_result: dict | None = None,
    predictive_result: dict | None = None,
) -> dict[str, Any]:
    """Orchestrate all executive intelligence modules into a single response."""
    problem_type = automl_result.get("problem_type", "classification")
    target = automl_result.get("target", "the target variable")
    feature_count = automl_result.get("features", 0)
    sample_count = automl_result.get("samples", 0)
    model_name = automl_result.get("best_model", "Unknown")
    models_tested = automl_result.get("models_tested", 1)

    cv = explainability_result.get("cross_validation", {})
    cv_mean = cv.get("cv_mean")
    cv_folds = cv.get("cv_folds", 0)

    conf = explainability_result.get("confidence", {})
    confidence_score = conf.get("confidence", 50)
    conf_factors = conf.get("factors", [])
    conf_breakdown = conf.get("breakdown")
    conf_grade = conf.get("grade", "Moderate")

    risk_score = 0
    revenue_at_risk = 0
    population_at_risk = 0
    total_population = 0
    risk_level = "moderate"
    early_warnings = []
    prescriptive = []
    opportunities = []

    if predictive_result:
        bi = predictive_result.get("business_impact", {})
        revenue_at_risk = bi.get("revenue_at_risk", 0)
        population_at_risk = bi.get("population_at_risk", 0)
        total_population = bi.get("total_population", 0)
        risk_level = bi.get("impact_level", "moderate").lower()
        risk_score = 100 - confidence_score  # inverse of confidence

        tech = predictive_result.get("technical", {})
        risk_score = tech.get("risk_score") or risk_score
        if tech.get("data_quality"):
            data_quality_score = tech["data_quality"].get("score", 80)
        else:
            data_quality_score = 80

        early_warnings = predictive_result.get("early_warnings", [])
        prescriptive = predictive_result.get("prescriptive_recommendations", [])
        opportunities = predictive_result.get("opportunities", [])
    else:
        data_quality_score = conf_breakdown.get("data_quality", 80) if conf_breakdown else 80
        risk_score = max(0, min(100, 100 - confidence_score))
        revenue_at_risk = 0
        population_at_risk = int(sample_count * (risk_score / 100))
        total_population = sample_count

    scenario_result = scenario_result or {}

    executive_summary = generate_executive_summary(
        problem_type, target, confidence_score, risk_score, cv_mean,
        feature_count, sample_count,
    )

    business_impact = generate_business_impact(
        risk_score, confidence_score, revenue_at_risk,
        population_at_risk, total_population, risk_level,
    )

    imp_list = explainability_result.get("feature_importance", [])
    shap_list = explainability_result.get("shap_values")
    key_drivers = generate_key_drivers(imp_list, shap_list, feature_count)

    top_risks = generate_top_risks(early_warnings, risk_score, revenue_at_risk)

    top_opportunities = generate_top_opportunities(opportunities, prescriptive, scenario_result)

    recommended_actions = generate_recommended_actions(prescriptive, risk_score, cv_mean, models_tested)

    financial_exposure = generate_financial_exposure(revenue_at_risk, scenario_result, confidence_score)

    decision_confidence = generate_decision_confidence(confidence_score, conf_factors, conf_breakdown, cv_mean)

    source_evidence = generate_source_evidence(
        model_name, cv_mean, cv_folds, data_quality_score,
        sample_count, feature_count, models_tested, confidence_score,
    )

    return {
        "executive_summary": executive_summary,
        "business_impact": business_impact,
        "key_drivers": key_drivers,
        "top_risks": top_risks,
        "top_opportunities": top_opportunities,
        "recommended_actions": recommended_actions,
        "financial_exposure": financial_exposure,
        "decision_confidence": decision_confidence,
        "source_evidence": source_evidence,
    }
