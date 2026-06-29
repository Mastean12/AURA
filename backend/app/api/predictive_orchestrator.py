import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/predictive-orchestrator", tags=["predictive-orchestrator"])


class OrchestratorRequest(BaseModel):
    doc_id: int
    problem_type: str = ""
    target: str = ""


@router.post("/analyze")
async def predictive_orchestrator(payload: OrchestratorRequest):
    """Run full predictive pipeline: AutoML → Explainability → Scenarios → Executive + Analyst."""
    from app.services.predictive_orchestrator_service import run_predictive_orchestrator

    result = await run_predictive_orchestrator(payload.doc_id, payload.problem_type, payload.target)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    def _convert(obj):
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    return _convert(result)
