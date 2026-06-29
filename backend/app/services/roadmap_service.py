import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def build_roadmap(
    priorities: list[dict],
    risk_level: str,
    revenue_at_risk: float,
    industry: str = "General Business",
) -> dict[str, Any]:
    """Build an implementation roadmap with phased timeline."""
    today = datetime.now()

    phases = {
        "immediate": {
            "label": "Immediate (First 30 Days)",
            "start": today.strftime("%Y-%m-%d"),
            "end": today.replace(month=today.month + 1 if today.month < 12 else 1).strftime("%Y-%m-%d"),
            "focus": "Critical risk mitigation and quick wins",
            "actions": [],
        },
        "short_term": {
            "label": "Short-Term (31–90 Days)",
            "start": today.replace(month=today.month + 1 if today.month < 12 else 1).strftime("%Y-%m-%d"),
            "end": today.replace(month=today.month + 3 if today.month <= 9 else today.month - 9).strftime("%Y-%m-%d"),
            "focus": "Structural improvements and process changes",
            "actions": [],
        },
        "medium_term": {
            "label": "Medium-Term (91–180 Days)",
            "start": today.replace(month=today.month + 3 if today.month <= 9 else today.month - 9).strftime("%Y-%m-%d"),
            "end": today.replace(month=today.month + 6 if today.month <= 6 else today.month - 6).strftime("%Y-%m-%d"),
            "focus": "Systematic enhancements and capability building",
            "actions": [],
        },
        "long_term": {
            "label": "Long-Term (181–365 Days)",
            "start": today.replace(month=today.month + 6 if today.month <= 6 else today.month - 6).strftime("%Y-%m-%d"),
            "end": today.replace(year=today.year + 1).strftime("%Y-%m-%d"),
            "focus": "Strategic transformation and sustained optimization",
            "actions": [],
        },
    }

    timeline_map = {
        "Immediate": "immediate",
        "Short-term (90 days)": "short_term",
        "Medium-term (180 days)": "medium_term",
        "Long-term (365 days)": "long_term",
    }

    for p in priorities:
        phase_key = timeline_map.get(p.get("timeline", ""), "long_term")
        if phase_key in phases:
            phases[phase_key]["actions"].append({
                "action": p["title"],
                "priority_score": p["priority_score"],
                "effort": p.get("effort", "Medium"),
                "expected_roi": p.get("expected_roi", "TBD"),
            })

    total_protected = round(revenue_at_risk * 0.35, 2)
    risk_multiplier = {"critical": 0.5, "high": 0.35, "medium": 0.2, "low": 0.1}
    estimated_recovery = round(revenue_at_risk * risk_multiplier.get(risk_level.lower(), 0.2), 2)

    return {
        "phases": phases,
        "risk_level": risk_level,
        "revenue_at_risk": revenue_at_risk,
        "estimated_recovery": estimated_recovery,
        "total_actions": len(priorities),
        "narrative": (
            f"The implementation roadmap spans four phases over 12 months. "
            f"Phase 1 (immediate) focuses on {len(phases['immediate']['actions'])} critical actions "
            f"to address {risk_level.lower()} risk exposure of ${revenue_at_risk:,.0f}. "
            f"Subsequent phases build on these foundations with structural and strategic initiatives. "
            f"Estimated revenue recovery: ${estimated_recovery:,.0f}."
        ),
    }
