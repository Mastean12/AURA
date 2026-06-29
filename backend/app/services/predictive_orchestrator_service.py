import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


async def run_predictive_orchestrator(
    doc_id: int,
    problem_type: str = "",
    target: str = "",
) -> dict[str, Any]:
    """Orchestrate AutoML → Explainability → Scenarios → Executive Decision Intelligence."""
    import io
    from app.database.database import get_session_factory
    from app.models.document import Document
    from app.services.automl_service import run_automl
    from app.services.explainability_service import run_explainability, _cross_val_score, compute_prediction_intervals
    from app.services.scenario_simulation_service import run_scenario_analysis
    from app.services.executive_decision_intelligence_service import run_executive_decision_intelligence
    from app.services.data_quality_service import run_data_quality_audit
    from app.services.dataset_intelligence_service import analyze_dataset
    from app.services.chart_recommendation_engine import recommend_charts_for_dataset
    from sqlalchemy import select

    # 1. Load document
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception as e:
        return {"error": f"Database error: {e}"}

    if not doc or not doc.content:
        return {"error": "Document not found"}

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    # 2. Run AutoML
    automl_result = await run_automl(doc_id, problem_type, target)
    if "error" in automl_result:
        return automl_result

    ds = analyze_dataset(df)
    detected_target = target or ds.get("target_variable", "")
    if not detected_target or detected_target not in df.columns:
        return {"error": "Could not determine target variable"}

    X = df.drop(columns=[detected_target]).select_dtypes(include=["number"])
    X = X.loc[:, X.nunique() > 1]
    if X.shape[1] < 1:
        return {"error": "No valid numeric features found"}
    y = df[detected_target]

    resolved_problem = problem_type or automl_result.get("problem_type", "regression")
    if resolved_problem == "classification" and y.dtype in ("float64", "object"):
        y = y.astype(int)

    # 3. Rebuild & train best model
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    best_name = automl_result.get("best_model", "")
    model = _rebuild_model(best_name, resolved_problem)
    if model is None:
        return {"error": f"Could not rebuild model: {best_name}"}

    try:
        model.fit(X_train, y_train)
    except Exception as e:
        return {"error": f"Model training failed: {e}"}

    # 4. Data quality
    dq = run_data_quality_audit(df)
    dq_score = dq.get("overall_score", 80)

    # 5. Explainability
    explainability = await run_explainability(
        model, X_train, X_test, y_train, y_test,
        X.columns.tolist(), dq_score,
        problem_type=resolved_problem,
        n_models_tested=automl_result.get("models_tested", 1),
    )

    # 6. Scenario analysis
    scenario_result = await run_scenario_analysis(doc_id)

    # 7. Executive decision intelligence
    executive = await run_executive_decision_intelligence(
        automl_result, explainability, scenario_result,
    )

    # 8. Analyst-specific computations
    y_pred = model.predict(X_test) if hasattr(model, "predict") else None
    analyst = _build_analyst_section(
        model, automl_result, explainability, X_train, X_test, y_train, y_test, y_pred,
        resolved_problem, df, detected_target,
    )

    # 9. Chart recommendations
    try:
        chart_recs = recommend_charts_for_dataset(doc_id)
    except Exception:
        chart_recs = []

    return {
        "doc_id": doc_id,
        "target": detected_target,
        "problem_type": resolved_problem,
        "executive": executive,
        "analyst": analyst,
        "chart_recommendations": chart_recs,
    }


def _build_analyst_section(
    model, automl: dict, explainability: dict,
    X_train, X_test, y_train, y_test, y_pred,
    problem_type: str, df: pd.DataFrame, target: str,
) -> dict[str, Any]:
    """Build technical analyst section with full model metrics."""
    metrics = {}
    if problem_type == "classification":
        try:
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score,
                f1_score, roc_auc_score, confusion_matrix,
                classification_report,
            )
            metrics["accuracy"] = round(float(accuracy_score(y_test, y_pred)), 4) if y_pred is not None else None
            metrics["precision"] = round(float(precision_score(y_test, y_pred, average="weighted")), 4) if y_pred is not None else None
            metrics["recall"] = round(float(recall_score(y_test, y_pred, average="weighted")), 4) if y_pred is not None else None
            metrics["f1"] = round(float(f1_score(y_test, y_pred, average="weighted")), 4) if y_pred is not None else None
            try:
                y_prob = model.predict_proba(X_test)
                metrics["roc_auc"] = round(float(roc_auc_score(y_test, y_prob, multi_class="ovr")), 4)
            except Exception:
                metrics["roc_auc"] = None
            try:
                cm = confusion_matrix(y_test, y_pred).tolist() if y_pred is not None else []
                metrics["confusion_matrix"] = cm
            except Exception:
                metrics["confusion_matrix"] = []
        except Exception as e:
            logger.warning("Classification metrics failed: %s", e)
    else:
        try:
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
            metrics["r2"] = round(float(r2_score(y_test, y_pred)), 4) if y_pred is not None else None
            metrics["rmse"] = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4) if y_pred is not None else None
            metrics["mae"] = round(float(mean_absolute_error(y_test, y_pred)), 4) if y_pred is not None else None
            try:
                mape_val = np.mean(np.abs((y_test - y_pred) / (np.abs(y_test) + 1e-10))) * 100
                metrics["mape"] = round(float(mape_val), 2)
            except Exception:
                metrics["mape"] = None
        except Exception as e:
            logger.warning("Regression metrics failed: %s", e)

    # Residual analysis
    residuals = {}
    if y_pred is not None and len(y_pred) == len(y_test):
        try:
            res = y_test - y_pred
            residuals = {
                "mean": round(float(np.mean(res)), 4),
                "std": round(float(np.std(res)), 4),
                "min": round(float(np.min(res)), 4),
                "max": round(float(np.max(res)), 4),
                "normality_p_value": _normality_test(res),
            }
        except Exception as e:
            residuals = {"error": str(e)[:60]}

    # Classification report
    class_report = {}
    if problem_type == "classification" and y_pred is not None:
        try:
            from sklearn.metrics import classification_report
            cr = classification_report(y_test, y_pred, output_dict=True)
            class_report = {str(k): v for k, v in cr.items() if isinstance(v, dict)}
        except Exception:
            pass

    models_tested = automl.get("models_tested", 0)
    all_results = automl.get("results", [])
    best_metric = automl.get("best_f1") or automl.get("best_r2")

    return {
        "model_info": {
            "selected_model": automl.get("best_model", "Unknown"),
            "models_tested": models_tested,
            "problem_type": problem_type,
            "target": automl.get("target", ""),
            "features": automl.get("features", 0),
            "samples": automl.get("samples", 0),
            "best_metric": round(best_metric, 4) if best_metric else None,
        },
        "metrics": metrics,
        "classification_report": class_report,
        "residual_analysis": residuals,
        "feature_importance": explainability.get("feature_importance", []),
        "permutation_importance": explainability.get("permutation_importance", []),
        "shap_values": explainability.get("shap_values", []),
        "cross_validation": explainability.get("cross_validation", {}),
        "prediction_intervals": explainability.get("prediction_intervals", {}),
        "confidence": explainability.get("confidence", {}),
        "automl_details": {
            "models_tested": models_tested,
            "all_models": [
                {
                    "name": r.get("model_name", "Unknown"),
                    "metrics": {k: round(v, 4) for k, v in r.items() if k not in ("model_name", "error") and isinstance(v, (int, float))},
                    "error": r.get("error"),
                }
                for r in all_results
            ],
        },
    }


def _rebuild_model(name: str, problem_type: str):
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


def _normality_test(residuals: np.ndarray) -> float | None:
    """Shapiro-Wilk normality test on residuals."""
    try:
        from scipy.stats import shapiro
        if len(residuals) >= 3:
            _, p = shapiro(residuals[:5000])
            return round(float(p), 4)
    except ImportError:
        pass
    return None
