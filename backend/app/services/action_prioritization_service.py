import logging
from typing import Any

from app.services.roi_analysis_service import compute_priority_score

logger = logging.getLogger(__name__)


def _estimate_impact_pct(risk_score: float, recommendation: dict) -> float:
    """Estimate impact as percentage (0-100) from risk and recommendation data."""
    base = min(risk_score, 95)
    effort = recommendation.get("effort", "Medium").lower()
    effort_bonus = {"low": 10, "medium": 5, "high": 0, "critical": -5}
    return max(10, min(100, base + effort_bonus.get(effort, 0)))


def _estimate_effort_pct(recommendation: dict) -> float:
    """Estimate effort as percentage (0-100) where higher = more effort."""
    effort = recommendation.get("effort", "Medium").lower()
    effort_map = {"low": 20, "medium": 50, "high": 80, "critical": 95}
    return effort_map.get(effort, 50)


def prioritize_actions(
    recommendations: list[dict],
    risk_score: float,
    risk_level: str,
    business_health: dict | None = None,
) -> dict[str, Any]:
    """Prioritize recommendations by urgency, impact, effort, and ROI."""
    if not recommendations:
        return {"priorities": [], "summary": "No recommendations to prioritize."}

    scored = []
    for r in recommendations:
        impact_pct = _estimate_impact_pct(risk_score, r)
        effort_pct = _estimate_effort_pct(r)
        confidence = min(risk_score + 10, 95)

        urgency_map = {"critical": 100, "high": 80, "medium": 50, "low": 20}
        urgency = urgency_map.get(risk_level.lower(), 50)
        if r.get("priority", "").lower() in urgency_map:
            urgency = urgency_map[r["priority"].lower()]

        score = compute_priority_score(impact_pct, effort_pct, confidence, urgency)

        timeline = "Immediate" if score >= 80 else "Short-term (90 days)" if score >= 60 else "Medium-term (180 days)" if score >= 40 else "Long-term (365 days)"

        scored.append({
            "title": r.get("recommendation", r.get("title", r.get("action", "Action"))),
            "description": r.get("description", r.get("expected_impact", "")),
            "priority_score": score,
            "impact_pct": impact_pct,
            "effort_pct": effort_pct,
            "confidence": confidence,
            "urgency": urgency,
            "timeline": timeline,
            "effort": r.get("effort", "Medium"),
            "expected_roi": r.get("roi", r.get("expected_roi", "TBD")),
        })

    scored.sort(key=lambda x: -x["priority_score"])

    immediate = [s for s in scored if s["timeline"] == "Immediate"]
    short_term = [s for s in scored if s["timeline"] == "Short-term (90 days)"]
    medium_term = [s for s in scored if s["timeline"] == "Medium-term (180 days)"]
    long_term = [s for s in scored if s["timeline"] == "Long-term (365 days)"]

    return {
        "priorities": scored,
        "timeline_breakdown": {
            "immediate": [s["title"] for s in immediate],
            "short_term": [s["title"] for s in short_term],
            "medium_term": [s["title"] for s in medium_term],
            "long_term": [s["title"] for s in long_term],
        },
        "counts": {
            "immediate": len(immediate),
            "short_term": len(short_term),
            "medium_term": len(medium_term),
            "long_term": len(long_term),
            "total": len(scored),
        },
        "top_priority": scored[0] if scored else None,
        "summary": (
            f"Priority analysis ranked {len(scored)} actions: "
            f"{len(immediate)} immediate, {len(short_term)} short-term, "
            f"{len(medium_term)} medium-term, {len(long_term)} long-term. "
            f"Top priority: {scored[0]['title']} (score: {scored[0]['priority_score']})"
        ),
    }
