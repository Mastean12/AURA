from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.analytics_orchestrator import run_full_pipeline

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/pipeline")
async def analytics_pipeline(payload: DocRequest):
    """Run the full analytics pipeline with status tracking."""
    import numpy as np
    try:
        result = await run_full_pipeline(payload.doc_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        def _convert(obj):
            if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [_convert(v) for v in obj]
            elif isinstance(obj, np.integer): return int(obj)
            elif isinstance(obj, np.floating): return float(obj)
            elif isinstance(obj, np.bool_): return bool(obj)
            elif isinstance(obj, np.ndarray): return obj.tolist()
            return obj
        return _convert(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
