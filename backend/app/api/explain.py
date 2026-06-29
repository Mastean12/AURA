from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/explain", tags=["explain"])


class ExplainRequest(BaseModel):
    doc_id: int
    problem_type: str = ""
    target: str = ""


@router.post("/model")
async def explain_model(payload: ExplainRequest):
    """Run explainability on the best AutoML model: feature importance, SHAP, confidence."""
    import numpy as np, pandas as pd, io
    from app.database.database import get_session_factory
    from app.models.document import Document
    from app.services.automl_service import run_automl
    from app.services.explainability_service import run_explainability
    from app.services.data_quality_service import run_data_quality_audit
    from app.services.intelligent_prediction_engine import detect_problem
    from app.services.dataset_intelligence_service import analyze_dataset
    from sqlalchemy import select

    # Run AutoML to get the best model
    automl_result = await run_automl(payload.doc_id, payload.problem_type, payload.target)
    if "error" in automl_result:
        raise HTTPException(status_code=400, detail=automl_result["error"])

    # Load data
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

    dq = run_data_quality_audit(df)
    ds = analyze_dataset(df)
    target = payload.target or ds.get("target_variable", "")
    if not target or target not in df.columns:
        raise HTTPException(status_code=400, detail="Could not determine target variable")

    # Retrain best model for explainability
    X = df.drop(columns=[target]).select_dtypes(include=["number"])
    X = X.loc[:, X.nunique() > 1]
    y = df[target]

    if payload.problem_type == "classification" and y.dtype in ("float64", "object"):
        y = y.astype(int)

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    best_name = automl_result.get("best_model", "")
    model = _rebuild_model(best_name, payload.problem_type or automl_result.get("problem_type", "regression"))
    if model is None:
        raise HTTPException(status_code=400, detail=f"Could not rebuild model: {best_name}")

    try:
        model.fit(X_train, y_train)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {e}")

    explain = await run_explainability(
        model, X_train, X_test, y_train, y_test,
        X.columns.tolist(), dq.get("overall_score", 80),
        problem_type=payload.problem_type or automl_result.get("problem_type", "regression"),
        n_models_tested=automl_result.get("models_tested", 1),
    )

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
        "target": target,
        "best_model": best_name,
        "problem_type": automl_result.get("problem_type", ""),
        "explainability": explain,
        "automl_summary": {
            "models_tested": automl_result.get("models_tested", 1),
            "best_metric": automl_result.get("best_f1") or automl_result.get("best_r2"),
        },
    })


def _rebuild_model(name: str, problem_type: str):
    """Rebuild a model by name for explainability."""
    try:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge

        if problem_type == "classification":
            if "Logistic" in name: return LogisticRegression(max_iter=1000, random_state=42)
            if "Random" in name: return RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
            if "XGBoost" in name:
                from xgboost import XGBClassifier
                return XGBClassifier(n_estimators=50, random_state=42, verbosity=0)
            if "LightGBM" in name:
                import lightgbm as lgb
                return lgb.LGBMClassifier(n_estimators=50, random_state=42, verbose=-1)
            if "CatBoost" in name:
                from catboost import CatBoostClassifier
                return CatBoostClassifier(n_estimators=50, random_state=42, verbose=0)
        else:
            if "Linear" in name: return LinearRegression()
            if "Ridge" in name: return Ridge(alpha=1.0, random_state=42)
            if "Random" in name: return RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
            if "XGBoost" in name:
                from xgboost import XGBRegressor
                return XGBRegressor(n_estimators=50, random_state=42, verbosity=0)
            if "LightGBM" in name:
                import lightgbm as lgb
                return lgb.LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
            if "CatBoost" in name:
                from catboost import CatBoostRegressor
                return CatBoostRegressor(n_estimators=50, random_state=42, verbose=0)
    except Exception:
        pass
    return None
