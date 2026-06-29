from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.business_insight_generator import (
    generate_business_insights, generate_executive_recommendations, generate_executive_summary
)

router = APIRouter(prefix="/insights", tags=["insights"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/generate")
async def generate_insights(payload: DocRequest):
    """Generate deterministic business insights from actual data — no AI calls."""
    import numpy as np, pandas as pd, io
    from app.database.database import get_session_factory
    from app.models.document import Document
    from app.services.business_analytics_service import compute_descriptive_stats
    from app.services.dataset_intelligence_service import analyze_dataset
    from sqlalchemy import select

    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == payload.doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        raise HTTPException(status_code=404, detail="Document not found")

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="Dataset must be tabular")

    ds = analyze_dataset(df)
    stats = compute_descriptive_stats(df)
    insights = generate_business_insights(df, ds)
    recommendations = generate_executive_recommendations(insights)
    kpi_cols = ds.get("kpi_columns", []) or ds.get("numeric_columns", [])[:5]
    trend = {}
    for col in kpi_cols[:5]:
        if col in df.columns:
            vals = df[col].dropna().values.astype(float)
            if len(vals) >= 4:
                from app.services.business_insight_generator import _detect_trend
                trend[col] = _detect_trend(vals)
    summary = generate_executive_summary(kpi_cols, trend, insights)

    def _convert(obj):
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.bool_): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    return _convert({
        "doc_id": payload.doc_id,
        "executive_summary": summary,
        "insights": insights,
        "recommendations": recommendations,
        "trend_analysis": trend,
        "insight_types": list(set(i["type"] for i in insights)),
    })
