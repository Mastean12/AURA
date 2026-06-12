import json
import logging

from app.services.ai_service import generate_response
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)

RISK_CATEGORIES = [
    "Financial Risks",
    "Operational Risks",
    "Compliance Risks",
    "Market Risks",
    "Strategic Risks",
    "Data Quality Risks",
]


async def analyze_risks(doc_ids: list[int] | None = None) -> dict:
    if not doc_ids:
        return {"risks": [], "confidence": 0}

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
        return {"risks": [], "confidence": 0}

    prompt = f"""You are an AI risk analyst. Analyze the following documents and identify business risks.

For each risk, classify it into one of: {', '.join(RISK_CATEGORIES)}.

Return ONLY valid JSON:
{{
  "risks": [
    {{
      "name": "Risk name",
      "description": "Brief description",
      "category": "One of the categories above",
      "severity": "High | Medium | Low",
      "probability": "High | Medium | Low",
      "potential_impact": "Description of potential business impact",
      "mitigation": "Recommended mitigation action"
    }}
  ],
  "confidence": 80
}}

Identify 3-7 risks spanning different categories.

Documents:
{combined}
"""

    try:
        raw = generate_response(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Risk analysis failed: %s", e)
        result = {"risks": [], "confidence": 0}

    result.setdefault("risks", [])
    result.setdefault("confidence", 0)
    result["sources"] = source_refs
    return result
