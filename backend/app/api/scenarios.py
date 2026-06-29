from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.scenario_simulation_service import simulate_scenario, run_scenario_analysis, SCENARIO_TEMPLATES

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioRequest(BaseModel):
    doc_id: int
    scenario_id: str = ""
    adjustment_pct: float = 0


@router.post("/simulate")
async def run_simulation(payload: ScenarioRequest):
    """Run a specific scenario simulation."""
    import numpy as np
    if payload.scenario_id:
        result = await simulate_scenario(payload.doc_id, payload.scenario_id, payload.adjustment_pct)
    else:
        result = await run_scenario_analysis(payload.doc_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    def _convert(obj):
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        return obj
    return _convert(result)


@router.get("/templates")
async def list_templates():
    """List available scenario templates."""
    return {
        "templates": [{"id": k, **v} for k, v in SCENARIO_TEMPLATES.items()]
    }
