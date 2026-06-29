import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_board_narrative(
    executive_summary: str,
    health: dict,
    risks: list[dict],
    opportunities: list[dict],
    root_causes: list[dict],
    priorities: dict,
    roadmap: dict,
    roi: dict,
    business_impact: dict,
    industry: str = "General Business",
) -> dict[str, Any]:
    """Generate board-ready narrative sections from analysis data."""
    health_overall = health.get("overall", 0)
    health_level = "strong" if health_overall >= 70 else "moderate" if health_overall >= 40 else "concern"

    top_risk = risks[0] if risks else {"name": "General business risk"}
    top_opp = opportunities[0] if opportunities else {"name": "Operational improvements"}
    top_priority = priorities.get("top_priority", {})
    top_priority_name = top_priority.get("title", "Address key findings")
    top_priority_roi = top_priority.get("expected_roi", "TBD")

    risk_count = len(risks)
    opp_count = len(opportunities)
    phase_counts = roadmap.get("phases", {})
    imm_count = len(phase_counts.get("immediate", {}).get("actions", []))
    short_count = len(phase_counts.get("short_term", {}).get("actions", []))
    med_count = len(phase_counts.get("medium_term", {}).get("actions", []))
    long_count = len(phase_counts.get("long_term", {}).get("actions", []))

    # Financial impact
    revenue_at_risk = business_impact.get("revenue_impact", "")
    cost_impact = business_impact.get("cost_impact", "")
    fin_exposure_value = 0
    if isinstance(revenue_at_risk, str) and "$" in revenue_at_risk:
        try:
            fin_exposure_value = float(revenue_at_risk.replace("$", "").replace(",", ""))
        except ValueError:
            fin_exposure_value = 0

    portfolio_roi = roi.get("portfolio_roi", 0)
    net_benefit = roi.get("net_benefit", 0)

    executive_narrative = (
        f"Business health is currently {health_level} with an overall score of {health_overall}/100. "
        f"{executive_summary[:300]} "
        f"Our analysis identified {risk_count} strategic risks and {opp_count} growth opportunities. "
        f"The highest-priority risk is {top_risk['name']}. "
        f"The recommended action plan comprises {imm_count} immediate initiatives, "
        f"{short_count} short-term improvements, {med_count} medium-term enhancements, "
        f"and {long_count} long-term strategic transformations."
    )

    board_summary = (
        f"The organization faces {risk_count} material risks with an estimated financial exposure. "
        f"Our analysis recommends a phased action plan starting with {imm_count} immediate initiatives "
        f"centered on {top_priority_name}. "
        f"The projected portfolio ROI is {portfolio_roi}x with a net benefit of ${net_benefit:,.0f}. "
        f"Key opportunities in {top_opp.get('name', 'growth areas')} offer additional upside."
    )

    strategic_context = (
        f"In the context of the {industry} industry, the identified risks and opportunities "
        f"reflect broader market dynamics. {top_risk.get('name', 'Key risks')} require "
        f"board-level attention, while {top_opp.get('name', 'growth opportunities')} "
        f"represent actionable paths to value creation."
    )

    call_to_action = (
        f"The board is recommended to approve the {imm_count}-initiative immediate action plan "
        f"with an estimated investment yielding {portfolio_roi}x ROI. "
        f"Priority should be given to {top_priority_name} "
        f"(expected ROI: {top_priority_roi}). "
        f"A 90-day review cycle is recommended to track progress against the roadmap."
    )

    return {
        "executive_narrative": executive_narrative,
        "board_summary": board_summary,
        "strategic_context": strategic_context,
        "call_to_action": call_to_action,
        "risk_count": risk_count,
        "opportunity_count": opp_count,
        "immediate_actions": imm_count,
        "portfolio_roi": portfolio_roi,
        "net_benefit": net_benefit,
        "health_level": health_level,
    }
