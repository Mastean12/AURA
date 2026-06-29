from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.intelligent_prediction_engine import run_prediction_detection

router = APIRouter(prefix="/predict", tags=["predict"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/detect")
async def detect_problem(payload: DocRequest):
    """Auto-detect prediction problem type, target, and recommended models."""
    import numpy as np
    result = await run_prediction_detection(payload.doc_id)
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
