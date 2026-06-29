from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.automl_service import run_automl

router = APIRouter(prefix="/automl", tags=["automl"])


class AutoMLRequest(BaseModel):
    doc_id: int
    problem_type: str = ""
    target: str = ""


@router.post("/train")
async def automl_train(payload: AutoMLRequest):
    """Train and compare multiple models, select the best."""
    import numpy as np
    result = await run_automl(payload.doc_id, payload.problem_type, payload.target)
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
