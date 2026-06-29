from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.chart_recommendation_engine import run_chart_recommendation

router = APIRouter(prefix="/charts", tags=["charts"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/recommend")
async def recommend_charts(payload: DocRequest):
    """Intelligent chart recommendation using column intelligence + business context."""
    import numpy as np
    result = await run_chart_recommendation(payload.doc_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    def _convert(obj):
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.bool_): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return obj
    return _convert(result)
