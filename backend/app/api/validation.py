from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.statistical_validation_service import validate_all_charts

router = APIRouter(prefix="/validate", tags=["validate"])


class ValidateRequest(BaseModel):
    doc_id: int


@router.post("/charts")
async def validate_charts(payload: ValidateRequest):
    """Validate all pending charts for a document."""
    import numpy as np
    import pandas as pd, io
    from app.database.database import get_session_factory
    from app.models.document import Document
    from app.services.chart_recommendation_engine import run_chart_recommendation
    from sqlalchemy import select

    result = await run_chart_recommendation(payload.doc_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == payload.doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None

    df = None
    if doc and doc.content:
        df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None

    if df is None or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="Dataset not available")

    validation = await validate_all_charts(df, result.get("charts", []))

    def _convert(obj):
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.bool_): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    return {
        "doc_id": payload.doc_id,
        "validation": _convert(validation),
        "recommendation": _convert(result),
    }
