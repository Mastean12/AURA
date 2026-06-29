import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEPARTMENT_KEYWORDS = ["department", "division", "unit", "team", "branch", "region", "location", "store"]
PROCESS_KEYWORDS = ["process", "workflow", "step", "stage", "phase", "task", "cycle", "lead_time", "duration"]
WORKFORCE_KEYWORDS = ["employee", "staff", "headcount", "fte", "salary", "wage", "overtime", "turnover", "absent",
                      "training", "hours", "productivity", "utilization"]
SUPPLY_CHAIN_KEYWORDS = ["supplier", "vendor", "inventory", "stock", "warehouse", "logistics", "shipment",
                         "delivery", "procurement", "lead_time", "po", "order", "freight"]
CUSTOMER_KEYWORDS = ["customer", "client", "account", "clv", "ltv", "satisfaction", "nps", "retention",
                     "acquisition", "repeat", "loyalty", "segment", "tier"]
COST_KEYWORDS = ["cost", "expense", "spend", "overhead", "budget", "cogs", "opex", "capex", "waste"]
MATURITY_INDICATORS = ["automation", "digital", "ai", "ml", "cloud", "api", "integration", "analytics",
                       "dashboard", "reporting", "kpi", "sla", "compliance", "governance"]


def _safe_mean(s: pd.Series) -> float:
    return float(s.dropna().mean()) if len(s.dropna()) > 0 else 0.0


def _safe_min_max(val: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, round(val, 1)))


def _detect_columns(df: pd.DataFrame, keywords: list[str]) -> list[str]:
    cols = []
    for kw in keywords:
        for c in df.columns:
            if kw in c.lower() and c not in cols:
                cols.append(c)
    return cols


def _score_by_range(val: float, thresholds: list[tuple[float, float, float]]) -> float:
    """Map value to 0-100 score using threshold ranges: (lower_bound, upper_bound, score)."""
    for lo, hi, score in thresholds:
        if lo <= val <= hi:
            return score
    return 50.0


def _compute_department_benchmarks(df: pd.DataFrame) -> dict[str, Any]:
    """Benchmark departments against each other using available numeric KPIs."""
    dept_cols = _detect_columns(df, DEPARTMENT_KEYWORDS)
    if not dept_cols:
        return {"benchmarks": [], "summary": "No department columns detected."}

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    benchmarks = []
    for dept_col in dept_cols:
        groups = df.groupby(dept_col)
        for name, grp in groups:
            if len(grp) < 3:
                continue
            scores = {}
            for n_col in numeric_cols[:5]:
                mean_val = _safe_mean(grp[n_col])
                overall_mean = _safe_mean(df[n_col])
                pct_diff = ((mean_val - overall_mean) / overall_mean * 100) if overall_mean else 0
                scores[n_col] = {"value": round(mean_val, 2), "vs_org_pct": round(pct_diff, 1)}
            perf_score = _safe_min_max(sum(abs(v.get("vs_org_pct", 0)) for v in scores.values()) / max(len(scores), 1) + 50)
            benchmarks.append({
                "department": str(name),
                "score": perf_score,
                "metrics": scores,
                "member_count": len(grp),
            })

    benchmarks.sort(key=lambda x: -x["score"])
    top_dept = benchmarks[0]["department"] if benchmarks else "N/A"
    worst_dept = benchmarks[-1]["department"] if len(benchmarks) > 1 else top_dept
    gap = round(benchmarks[0]["score"] - benchmarks[-1]["score"], 1) if len(benchmarks) > 1 else 0

    return {
        "benchmarks": benchmarks,
        "top_department": top_dept,
        "worst_department": worst_dept,
        "gap": gap,
        "departments_analyzed": len(benchmarks),
        "summary": f"Analyzed {len(benchmarks)} departments. Top: {top_dept} ({benchmarks[0]['score']}%). "
                   f"Worst: {worst_dept}. Performance gap: {gap} points."
    }


def _compute_process_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze business processes and detect bottlenecks."""
    process_cols = _detect_columns(df, PROCESS_KEYWORDS)
    if not process_cols:
        return {"processes": [], "bottlenecks": [], "summary": "No process-related columns detected."}

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    processes = []
    bottlenecks = []
    for col in process_cols:
        if col not in numeric_cols:
            continue
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 5:
            continue
        mean_val = float(vals.mean())
        std_val = float(vals.std())
        p95 = float(vals.quantile(0.95))
        max_val = float(vals.max())
        is_bottleneck = (max_val > mean_val + 3 * std_val) if std_val > 0 else False
        efficiency = _safe_min_max(100 - (std_val / (mean_val + 1e-10) * 20))
        processes.append({
            "metric": col,
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "p95": round(p95, 2),
            "max": round(max_val, 2),
            "efficiency": efficiency,
        })
        if is_bottleneck:
            bottlenecks.append({
                "metric": col,
                "mean": round(mean_val, 2),
                "p95": round(p95, 2),
                "impact": f"Values reach {round(max_val, 2)} vs mean {round(mean_val, 2)} — potential bottleneck",
            })

    return {
        "processes": sorted(processes, key=lambda x: x["efficiency"]),
        "bottlenecks": bottlenecks,
        "bottleneck_count": len(bottlenecks),
        "summary": f"Analyzed {len(processes)} process metrics. Found {len(bottlenecks)} potential bottlenecks."
    }


def _compute_cost_optimization(df: pd.DataFrame) -> dict[str, Any]:
    """Identify cost optimization opportunities."""
    cost_cols = _detect_columns(df, COST_KEYWORDS)
    if not cost_cols:
        return {"opportunities": [], "summary": "No cost-related columns detected."}

    numeric_cols = [c for c in cost_cols if c in df.select_dtypes(include=["number"]).columns]
    opportunities = []
    total_potential = 0
    for col in numeric_cols[:8]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 5:
            continue
        mean_val = float(vals.mean())
        total_val = float(vals.sum())
        std_val = float(vals.std())
        p90 = float(vals.quantile(0.90))
        # Outliers above p90 represent potential savings
        outliers = vals[vals > p90]
        outlier_avg = float(outliers.mean()) if len(outliers) > 0 else 0
        savings_potential = round((outlier_avg - p90) * len(outliers) * 0.3, 2)
        total_potential += savings_potential
        if savings_potential > 0:
            opportunities.append({
                "cost_driver": col,
                "total": round(total_val, 2),
                "mean": round(mean_val, 2),
                "p90": round(p90, 2),
                "savings_potential": savings_potential,
                "approach": f"Reduce {col} outliers above {round(p90, 2)} to target level",
            })

    return {
        "opportunities": sorted(opportunities, key=lambda x: -x["savings_potential"]),
        "total_savings_potential": round(total_potential, 2),
        "summary": f"Identified {len(opportunities)} cost reduction opportunities "
                   f"totaling ${total_potential:,.0f} in potential savings."
    }


def _compute_workforce_intelligence(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze workforce metrics."""
    wf_cols = _detect_columns(df, WORKFORCE_KEYWORDS)
    if not wf_cols:
        return {"metrics": [], "summary": "No workforce columns detected."}

    numeric_cols = [c for c in wf_cols if c in df.select_dtypes(include=["number"]).columns]
    metrics = []
    alerts = []
    for col in numeric_cols[:8]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 3:
            continue
        mean_val = float(vals.mean())
        std_val = float(vals.std())
        trend = "up" if len(vals) > 3 and vals.iloc[-3:].mean() > vals.iloc[:3].mean() else "down" if len(vals) > 3 else "stable"
        metric_name = col.replace("_", " ").title()
        metrics.append({
            "metric": metric_name,
            "value": round(mean_val, 2),
            "trend": trend,
        })
        if "turnover" in col.lower() and mean_val > 15:
            alerts.append(f"{metric_name} at {round(mean_val, 1)}% — exceeds 15% threshold")
        if "absent" in col.lower() and mean_val > 5:
            alerts.append(f"{metric_name} at {round(mean_val, 1)}% — exceeds 5% threshold")

    engagement_score = _safe_min_max(75 - sum(1 for a in alerts) * 5)

    return {
        "metrics": metrics,
        "alerts": alerts,
        "alert_count": len(alerts),
        "engagement_score": engagement_score,
        "summary": f"Analyzed {len(metrics)} workforce metrics. {len(alerts)} alerts. "
                   f"Engagement score: {engagement_score}/100."
    }


def _compute_supply_chain_intelligence(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze supply chain performance."""
    sc_cols = _detect_columns(df, SUPPLY_CHAIN_KEYWORDS)
    if not sc_cols:
        return {"metrics": [], "summary": "No supply chain columns detected."}

    numeric_cols = [c for c in sc_cols if c in df.select_dtypes(include=["number"]).columns]
    metrics = []
    for col in numeric_cols[:8]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 3:
            continue
        mean_val = float(vals.mean())
        std_val = float(vals.std())
        efficiency = _safe_min_max(100 - (std_val / (mean_val + 1e-10) * 15))
        metrics.append({
            "metric": col.replace("_", " ").title(),
            "value": round(mean_val, 2),
            "variation": round(std_val, 2),
            "efficiency": efficiency,
        })

    return {
        "metrics": sorted(metrics, key=lambda x: x["efficiency"]),
        "overall_efficiency": round(sum(m["efficiency"] for m in metrics) / max(len(metrics), 1), 1),
        "summary": f"Analyzed {len(metrics)} supply chain metrics. "
                   f"Overall efficiency: {round(sum(m['efficiency'] for m in metrics) / max(len(metrics), 1), 1)}/100."
    }


def _compute_customer_intelligence(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze customer metrics and lifetime value indicators."""
    cust_cols = _detect_columns(df, CUSTOMER_KEYWORDS)
    if not cust_cols:
        return {"metrics": [], "summary": "No customer columns detected."}

    numeric_cols = [c for c in cust_cols if c in df.select_dtypes(include=["number"]).columns]
    metrics = []
    for col in numeric_cols[:8]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 3:
            continue
        mean_val = float(vals.mean())
        high_val = float(vals.quantile(0.9))
        low_val = float(vals.quantile(0.1))
        metrics.append({
            "metric": col.replace("_", " ").title(),
            "average": round(mean_val, 2),
            "top_10pct": round(high_val, 2),
            "bottom_10pct": round(low_val, 2),
            "gap_pct": round((high_val - low_val) / (low_val + 1e-10) * 100, 1),
        })

    segments = []
    for col in df.select_dtypes(include=["object", "category"]).columns[:3]:
        if "segment" in col.lower() or "tier" in col.lower() or "type" in col.lower():
            counts = df[col].value_counts()
            for cat, cnt in counts.items():
                segments.append({"segment": str(cat), "count": int(cnt), "pct": round(cnt / len(df) * 100, 1)})

    return {
        "metrics": metrics,
        "segments": segments,
        "summary": f"Analyzed {len(metrics)} customer metrics across {len(segments)} segments."
    }


def _compute_digital_maturity(df: pd.DataFrame) -> dict[str, Any]:
    """Assess digital transformation maturity."""
    maturity_cols = _detect_columns(df, MATURITY_INDICATORS)
    if not maturity_cols:
        return {"score": 35, "level": "Emerging", "factors": [],
                "summary": "No digital maturity indicators detected. Score estimated at 35 (Emerging)."}

    numeric_cols = [c for c in maturity_cols if c in df.select_dtypes(include=["number"]).columns]
    factors = []
    scores = []
    for col in numeric_cols[:8]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 3:
            continue
        mean_val = float(vals.mean())
        max_val = float(vals.max())
        min_val = float(vals.min())
        norm_score = _safe_min_max((mean_val - min_val) / (max_val - min_val + 1e-10) * 100)
        scores.append(norm_score)
        factors.append({
            "factor": col.replace("_", " ").title(),
            "score": norm_score,
            "value": round(mean_val, 2),
        })

    overall = round(np.mean(scores)) if scores else 35
    level = "Leader" if overall >= 80 else "Advanced" if overall >= 60 else "Developing" if overall >= 40 else "Emerging"

    return {
        "score": overall,
        "level": level,
        "factors": factors,
        "summary": f"Digital maturity score: {overall}/100 — {level}. "
                   f"Assessed {len(factors)} maturity indicators."
    }


def _compute_operational_efficiency(df: pd.DataFrame) -> dict[str, Any]:
    """Compute overall operational efficiency score."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    scores = []
    factors = []

    for col in numeric_cols[:10]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) < 5:
            continue
        mean_val = float(vals.mean())
        std_val = float(vals.std())
        cv = std_val / (mean_val + 1e-10)
        efficiency = _safe_min_max(100 - cv * 20)
        scores.append(efficiency)
        factors.append({
            "metric": col.replace("_", " ").title(),
            "efficiency": efficiency,
            "variation": round(cv, 3),
        })

    overall = round(np.mean(scores)) if scores else 50
    factors.sort(key=lambda x: x["efficiency"])

    return {
        "overall": overall,
        "factors": factors,
        "top_efficiency": factors[-1] if factors else None,
        "worst_efficiency": factors[0] if factors else None,
        "summary": f"Operational efficiency: {overall}/100. "
                   f"Best: {factors[-1]['metric'] if factors else 'N/A'} ({factors[-1]['efficiency'] if factors else 'N/A'}). "
                   f"Needs improvement: {factors[0]['metric'] if factors else 'N/A'} ({factors[0]['efficiency'] if factors else 'N/A'})."
    }


def _compute_enterprise_health_score(results: dict) -> float:
    """Aggregate all domain scores into an enterprise health score."""
    scores = []
    if results.get("department_benchmarks", {}).get("benchmarks"):
        scores.append(b["score"] for b in results["department_benchmarks"]["benchmarks"])
    if results.get("operational_efficiency", {}).get("overall"):
        scores.append(results["operational_efficiency"]["overall"])
    if results.get("digital_maturity", {}).get("score"):
        scores.append(results["digital_maturity"]["score"])
    if results.get("workforce_intelligence", {}).get("engagement_score"):
        scores.append(results["workforce_intelligence"]["engagement_score"])
    if results.get("supply_chain_intelligence", {}).get("overall_efficiency"):
        scores.append(results["supply_chain_intelligence"]["overall_efficiency"])
    flat = [s for sub in scores for s in sub] if any(isinstance(s, float) and not isinstance(s, (int,)) for s in scores) else [s if isinstance(s, (int, float)) else 0 for s in scores]
    if not flat:
        return 50.0
    return round(sum(flat) / len(flat), 1)


async def run_enterprise_intelligence(doc_id: int) -> dict[str, Any]:
    """Run full Enterprise Intelligence Engine across all domains."""
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

    import io
    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    results = {
        "department_benchmarks": _compute_department_benchmarks(df),
        "process_analysis": _compute_process_analysis(df),
        "cost_optimization": _compute_cost_optimization(df),
        "workforce_intelligence": _compute_workforce_intelligence(df),
        "supply_chain_intelligence": _compute_supply_chain_intelligence(df),
        "customer_intelligence": _compute_customer_intelligence(df),
        "digital_maturity": _compute_digital_maturity(df),
        "operational_efficiency": _compute_operational_efficiency(df),
    }

    health = _compute_enterprise_health_score(results)
    results["enterprise_health_score"] = health
    results["enterprise_health_level"] = "Excellent" if health >= 80 else "Good" if health >= 60 else "Moderate" if health >= 40 else "Critical"

    all_opps = results.get("cost_optimization", {}).get("opportunities", [])
    all_bottlenecks = results.get("process_analysis", {}).get("bottlenecks", [])
    all_alerts = results.get("workforce_intelligence", {}).get("alerts", [])

    risk_items = []
    for b in all_bottlenecks[:5]:
        risk_items.append({
            "risk": f"Process bottleneck: {b['metric']}",
            "severity": "High",
            "impact": b["impact"][:150],
        })
    for a in all_alerts[:3]:
        risk_items.append({
            "risk": a,
            "severity": "Medium",
            "impact": "",
        })

    opportunity_items = []
    for o in all_opps[:5]:
        opportunity_items.append({
            "opportunity": f"Cost reduction: {o['cost_driver']}",
            "potential_savings": o["savings_potential"],
            "approach": o["approach"][:150],
        })

    dept = results.get("department_benchmarks", {})
    process = results.get("process_analysis", {})
    recommendations = []
    if dept.get("gap", 0) > 10:
        recommendations.append({
            "action": f"Address performance gap in {dept.get('worst_department', 'underperforming')} department",
            "expected_roi": f"Bridge {dept['gap']}pt gap",
            "priority": "High",
        })
    if results.get("digital_maturity", {}).get("score", 100) < 60:
        recommendations.append({
            "action": f"Accelerate digital transformation ({results['digital_maturity']['level']} stage)",
            "expected_roi": "2-5x through automation gains",
            "priority": "Medium",
        })
    if all_opps:
        top_opp = all_opps[0]
        recommendations.append({
            "action": top_opp["approach"],
            "expected_roi": f"${top_opp['savings_potential']:,.0f} savings",
            "priority": "High",
        })
    if process.get("bottleneck_count", 0) > 0:
        recommendations.append({
            "action": f"Resolve {process['bottleneck_count']} identified process bottlenecks",
            "expected_roi": f"Improve efficiency by {process['bottleneck_count'] * 5}%",
            "priority": "High",
        })

    return {
        "doc_id": doc_id,
        "enterprise_health": {
            "score": health,
            "level": results["enterprise_health_level"],
        },
        "department_benchmarks": results["department_benchmarks"],
        "process_analysis": results["process_analysis"],
        "cost_optimization": results["cost_optimization"],
        "workforce_intelligence": results["workforce_intelligence"],
        "supply_chain_intelligence": results["supply_chain_intelligence"],
        "customer_intelligence": results["customer_intelligence"],
        "digital_maturity": results["digital_maturity"],
        "operational_efficiency": results["operational_efficiency"],
        "risks": risk_items,
        "opportunities": opportunity_items,
        "recommendations": recommendations,
    }
