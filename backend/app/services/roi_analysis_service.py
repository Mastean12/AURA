import logging
from typing import Any

logger = logging.getLogger(__name__)


def compute_roi(
    risk_score: float,
    revenue_at_risk: float,
    population_at_risk: int,
    total_population: int,
    recommendations: list[dict] | None = None,
) -> dict[str, Any]:
    """Compute ROI estimates based on risk metrics and recommended actions."""
    if recommendations:
        rec_rois = []
        for r in recommendations:
            risk_pct = risk_score / 100
            impact_pct = min(risk_pct * 0.3, 0.25)
            cost_estimate = revenue_at_risk * risk_pct * 0.15
            benefit = revenue_at_risk * impact_pct
            roi_x = round(benefit / (cost_estimate + 1), 1)
            rec_rois.append({
                "action": r.get("recommendation", r.get("title", "Action"))[:80],
                "investment": round(cost_estimate, 2),
                "expected_return": round(benefit, 2),
                "roi": roi_x,
                "payback_months": max(1, round(12 / max(roi_x, 0.1))),
            })
        avg_roi = round(sum(r["roi"] for r in rec_rois) / len(rec_rois), 1) if rec_rois else 0
    else:
        rec_rois = []
        for name, impact, cost_frac in [
            ("Retention program", 0.30, 0.15),
            ("Early warning system", 0.20, 0.10),
            ("Process optimization", 0.15, 0.08),
        ]:
            cost = revenue_at_risk * (risk_score / 100) * cost_frac
            benefit = revenue_at_risk * impact * (risk_score / 100)
            roi_x = round(benefit / (cost + 1), 1)
            rec_rois.append({
                "action": name,
                "investment": round(cost, 2),
                "expected_return": round(benefit, 2),
                "roi": roi_x,
                "payback_months": max(1, round(12 / max(roi_x, 0.1))),
            })
        avg_roi = round(sum(r["roi"] for r in rec_rois) / len(rec_rois), 1) if rec_rois else 0

    total_investment = round(sum(r["investment"] for r in rec_rois), 2)
    total_return = round(sum(r["expected_return"] for r in rec_rois), 2)
    portfolio_roi = round(total_return / (total_investment + 1), 1)

    return {
        "portfolio_roi": portfolio_roi,
        "average_roi": avg_roi,
        "total_investment": total_investment,
        "total_expected_return": total_return,
        "net_benefit": round(total_return - total_investment, 2),
        "recommendations": rec_rois,
        "narrative": (
            f"Investing ${total_investment:,.0f} across {len(rec_rois)} initiatives "
            f"is projected to deliver ${total_return:,.0f} in return, "
            f"a {portfolio_roi}x portfolio ROI with an average {avg_roi}x per initiative. "
            f"Payback ranges from {rec_rois[0]['payback_months']} to {rec_rois[-1]['payback_months']} months."
        ),
    }


def compute_priority_score(
    impact_pct: float, effort_pct: float, confidence: float, urgency: float
) -> float:
    """Compute a priority score 0-100 from impact, effort (inverse), confidence, urgency."""
    score = (impact_pct * 0.35 + (100 - effort_pct) * 0.25 + confidence * 0.20 + urgency * 0.20)
    return max(0, min(100, round(score, 1)))
