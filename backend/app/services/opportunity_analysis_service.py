import json
import logging

from app.services.ai_service import generate_response
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)

OPP_CATEGORIES = [
    "Revenue Growth",
    "Cost Reduction",
    "Operational Efficiency",
    "Market Expansion",
    "Workforce Optimization",
    "Strategic Partnerships",
]


async def analyze_opportunities(doc_ids: list[int] | None = None) -> dict:
    if not doc_ids:
        return {"opportunities": [], "confidence": 0}

    context_parts = []
    source_refs = []
    for did in doc_ids:
        try:
            async with get_session_factory()() as db:
                result = await db.execute(select(Document).where(Document.id == did))
                doc = result.scalar_one_or_none()
                if doc:
                    preview = doc.content[:3000] if doc.content else ""
                    context_parts.append(f"--- {doc.title} ---\n{preview}")
                    source_refs.append(doc.title)
        except Exception:
            pass

    combined = "\n\n".join(context_parts) if context_parts else ""
    if not combined:
        return {"opportunities": [], "confidence": 0}

    prompt = f"""You are an AI business strategist. Analyze the following documents and identify growth opportunities and operational improvements.

Categories: {', '.join(OPP_CATEGORIES)}.

Return ONLY valid JSON:
{{
  "opportunities": [
    {{
      "name": "Opportunity name",
      "description": "Brief description",
      "category": "One of the categories above",
      "expected_impact": "High | Medium | Low",
      "priority": "High | Medium | Low",
      "confidence": 75,
      "recommended_action": "Specific recommended action"
    }}
  ],
  "confidence": 80
}}

Identify 3-5 opportunities.

Documents:
{combined}
"""

    try:
        raw = generate_response(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Opportunity analysis failed: %s", e)
        result = {"opportunities": [], "confidence": 0}

    result.setdefault("opportunities", [])
    result.setdefault("confidence", 0)
    result["sources"] = source_refs
    return result
