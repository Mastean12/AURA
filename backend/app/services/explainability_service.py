import logging
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.inspection import permutation_importance
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


def _validate_pct(value: float, name: str = "") -> float:
    """Clamp percentage to 0-100 and reject NaN/Inf."""
    if np.isnan(value) or np.isinf(value):
        logger.warning("Invalid %s value: %s, replacing with 0", name, value)
        return 0.0
    return max(0.0, min(100.0, round(float(value), 1)))


def _validate_prob(proba: float, name: str = "") -> float:
    """Clamp probability to 0-1 and reject NaN/Inf."""
    if np.isnan(proba) or np.isinf(proba):
        logger.warning("Invalid %s probability: %s, replacing with 0", name, proba)
        return 0.0
    return max(0.0, min(1.0, float(proba)))


def _normalize_importance(values: list[float]) -> list[float]:
    """Normalize a list of importance values so they sum to 1.0."""
    arr = np.array([abs(v) for v in values])
    total = arr.sum()
    if total <= 0:
        return [0.0] * len(values)
    return (arr / total).tolist()


def _cross_val_score(model, X, y, cv: int = 5) -> dict:
    """Cross-validated performance metrics."""
    from sklearn.model_selection import cross_val_score, KFold
    from sklearn.metrics import make_scorer, r2_score, accuracy_score, f1_score

    if X.shape[0] < 50 or X.shape[1] < 1:
        return {"cv_r2_mean": None, "cv_r2_std": None, "cv_folds": 0}

    try:
        kf = KFold(n_splits=min(cv, X.shape[0] // 5), shuffle=True, random_state=42)
        if y.nunique() <= 20 and y.dtype in ("int64", "int32", "int", "object"):
            scorer = make_scorer(f1_score, average="weighted")
            scores = cross_val_score(model, X, y, cv=kf, scoring=scorer, n_jobs=-1)
        else:
            scorer = make_scorer(r2_score)
            scores = cross_val_score(model, X, y, cv=kf, scoring=scorer, n_jobs=-1)

        return {
            "cv_mean": round(float(scores.mean()), 4),
            "cv_std": round(float(scores.std()), 4),
            "cv_folds": len(scores),
            "cv_min": round(float(scores.min()), 4),
            "cv_max": round(float(scores.max()), 4),
        }
    except Exception as e:
        return {"cv_mean": None, "cv_std": None, "cv_folds": 0, "error": str(e)[:60]}


def _permutation_importance(model, X_test, y_test, metric: str = "r2") -> list[dict]:
    """Compute permutation feature importance."""
    if not HAS_SKLEARN:
        return []
    try:
        from sklearn.metrics import r2_score, f1_score, make_scorer

        scorer = make_scorer(r2_score) if metric == "r2" else make_scorer(f1_score, average="weighted")
        result = permutation_importance(model, X_test, y_test, scoring=scorer, n_repeats=5, random_state=42, n_jobs=-1)

        importances = []
        for i in range(len(X_test.columns)):
            importances.append({
                "feature": X_test.columns[i],
                "importance": round(float(result.importances_mean[i]), 4),
                "std": round(float(result.importances_std[i]), 4),
            })
        importances.sort(key=lambda x: -abs(x["importance"]))
        return importances
    except Exception as e:
        logger.warning("Permutation importance failed: %s", e)
        return []


def _shap_values(model, X_test) -> list[dict]:
    """Compute SHAP values for model explainability."""
    if not HAS_SHAP:
        return []

    try:
        if hasattr(model, "feature_importances_") or hasattr(model, "coef_"):
            explainer = shap.Explainer(model, X_test, check_additivity=False)
            shap_vals = explainer(X_test)
            mean_abs_shap = np.abs(shap_vals.values).mean(axis=0)
            feature_names = X_test.columns if hasattr(X_test, "columns") else [f"f{i}" for i in range(len(mean_abs_shap))]

            results = []
            for i, name in enumerate(feature_names):
                if i < len(mean_abs_shap):
                    results.append({
                        "feature": name,
                        "shap_value": round(float(mean_abs_shap[i]), 4),
                    })
            results.sort(key=lambda x: -abs(x["shap_value"]))
            return results
    except Exception as e:
        logger.warning("SHAP failed: %s", e)
    return []


def _normalize_shap(results: list[dict]) -> list[dict]:
    """Normalize SHAP values so absolute values sum to ~1.0."""
    raw = [abs(r["shap_value"]) for r in results]
    total = sum(raw)
    if total > 0:
        for r, v in zip(results, raw):
            r["shap_value"] = round(v / total, 4)
    return results


def _model_based_importance(model, feature_names: list[str]) -> list[dict]:
    """Extract built-in feature importance from model and normalize to sum of 1.0."""
    try:
        if hasattr(model, "feature_importances_"):
            imp = model.feature_importances_
        elif hasattr(model, "coef_"):
            imp = np.abs(model.coef_[0]) if model.coef_.ndim > 1 else np.abs(model.coef_)
        else:
            return []

        if len(feature_names) != len(imp):
            feature_names = [f"feature_{i}" for i in range(len(imp))]

        raw = [float(v) for v in imp]
        normalized = _normalize_importance(raw)

        results = []
        for i, name in enumerate(feature_names):
            results.append({"feature": name, "importance": round(normalized[i], 4)})
        results.sort(key=lambda x: -x["importance"])
        return results
    except Exception:
        return []


def compute_confidence(
    cv_result: dict, dq_score: float, n_samples: int, n_features: int,
    n_models_tested: int, feature_importance: list[dict],
    prediction_intervals: dict | None = None,
) -> dict:
    """
    Compute prediction confidence from deterministic factors only.
    No AI estimates. Based on: cross-validation, data quality,
    sample size, feature consistency, model stability, prediction intervals.
    """
    score = 50.0

    # Cross-validation (25% weight)
    cv_mean = cv_result.get("cv_mean")
    cv_std = cv_result.get("cv_std")
    if cv_mean is not None:
        score += min(cv_mean * 25, 20)
        cv_stability = 1 - min(cv_std / (abs(cv_mean) + 1e-10), 1)
        score += cv_stability * 5
    else:
        score -= 10

    # Data quality (15% weight)
    dq_weight = min(dq_score / 100, 1) * 15
    score += dq_weight

    # Sample size (20% weight)
    if n_samples >= 1000:
        score += 20
    elif n_samples >= 500:
        score += 15
    elif n_samples >= 100:
        score += 10
    elif n_samples >= 50:
        score += 5
    else:
        score -= 5

    # Feature count (10% weight)
    if n_features >= 10:
        score += 10
    elif n_features >= 5:
        score += 5
    elif n_features >= 3:
        score += 2

    # Feature consistency (10% weight)
    if feature_importance:
        top_pct = feature_importance[0].get("importance", 0)
        if top_pct > 0.3:
            score += 10
        elif top_pct > 0.1:
            score += 5

    # Model stability (10% weight)
    if n_models_tested >= 3:
        score += 10
    elif n_models_tested >= 2:
        score += 5

    # Prediction intervals (10% weight)
    pi_width = prediction_intervals.get("interval_width") if prediction_intervals else None
    if pi_width is not None and pi_width > 0:
        pi_score = max(0, 10 - min(pi_width * 2, 10))
        score += pi_score

    score = max(0, min(100, round(score, 1)))

    factors = []
    if cv_mean is not None and cv_mean > 0.7:
        factors.append(f"Strong cross-validation (mean={cv_mean:.2f})")
    elif cv_mean is not None and cv_mean > 0.5:
        factors.append(f"Adequate cross-validation (mean={cv_mean:.2f})")
    else:
        factors.append("Cross-validation needs improvement")

    if n_samples >= 500:
        factors.append(f"Large sample size ({n_samples:,})")
    elif n_samples >= 100:
        factors.append(f"Moderate sample size ({n_samples:,})")
    else:
        factors.append(f"Small sample size ({n_samples:,})")

    if dq_score >= 80:
        factors.append("High data quality")
    elif dq_score >= 50:
        factors.append("Moderate data quality")
    else:
        factors.append("Low data quality")

    if n_features >= 5:
        factors.append(f"Sufficient features ({n_features})")
    else:
        factors.append(f"Limited features ({n_features})")

    if pi_width is not None:
        if pi_width < 0.5:
            factors.append("Tight prediction intervals")
        elif pi_width < 1.0:
            factors.append("Adequate prediction intervals")
        else:
            factors.append("Wide prediction intervals — forecasts less precise")

    breakdown = {
        "cross_validation": round(min(cv_mean * 25 if cv_mean else 8, 25), 1) if cv_mean else 5,
        "data_quality": round(dq_weight, 1),
        "sample_size": round(min(n_samples / 50, 20), 1),
        "feature_strength": round(min(n_features * 2, 10), 1),
        "model_stability": round(min(n_models_tested * 3, 10), 1),
        "prediction_intervals": round(max(0, min(pi_width * 2, 10)), 1) if pi_width else 0,
    }

    grade = "Excellent" if score >= 80 else "Good" if score >= 60 else "Moderate" if score >= 40 else "Poor"

    return {
        "confidence": score,
        "grade": grade,
        "factors": factors,
        "breakdown": breakdown,
    }


def compute_prediction_intervals(model, X_test, y_pred: np.ndarray, alpha: float = 0.05) -> dict:
    """Estimate prediction intervals using residual variance."""
    try:
        residuals = []
        if hasattr(model, "predict"):
            cv_preds = model.predict(X_test)
            residuals = y_pred - cv_preds if len(y_pred) == len(cv_preds) else np.zeros_like(y_pred)

        residual_std = np.std(residuals) if len(residuals) > 0 else 0
        z_score = 1.96  # 95% confidence

        return {
            "method": "residual_based",
            "confidence_level": 0.95,
            "interval_width": round(float(z_score * residual_std), 4),
            "lower_bound": [round(float(p - z_score * residual_std), 4) for p in y_pred[:5]],
            "upper_bound": [round(float(p + z_score * residual_std), 4) for p in y_pred[:5]],
        }
    except Exception as e:
        return {"method": "residual_based", "error": str(e)[:60]}


async def run_explainability(
    model, X_train, X_test, y_train, y_test,
    feature_names: list[str], dq_score: float, problem_type: str = "regression",
    n_models_tested: int = 1
) -> dict[str, Any]:
    """Run full explainability pipeline: importance, confidence, intervals."""
    results = {}

    # 1. Feature Importance (model-based)
    results["feature_importance"] = _model_based_importance(model, feature_names)[:10]

    # 2. Permutation Importance
    perm_metric = "r2" if problem_type != "classification" else "f1"
    results["permutation_importance"] = _permutation_importance(model, X_test, y_test, perm_metric)[:10]
    if results["permutation_importance"]:
        raw = [abs(p["importance"]) for p in results["permutation_importance"]]
        total = sum(raw)
        if total > 0:
            for p, v in zip(results["permutation_importance"], raw):
                p["importance"] = round(v / total, 4)

    # 3. SHAP Values
    results["shap_values"] = _shap_values(model, X_test)
    results["shap_values"] = _normalize_shap(results["shap_values"])[:10]

    # 4. Cross-validation
    cv_result = _cross_val_score(model, X_train, y_train)
    results["cross_validation"] = cv_result

    # 5. Confidence
    imp_for_conf = results["feature_importance"] or results["permutation_importance"] or []
    pi = results.get("prediction_intervals", {})
    results["confidence"] = compute_confidence(
        cv_result, dq_score, X_train.shape[0], X_train.shape[1], n_models_tested, imp_for_conf, pi
    )

    # 6. Prediction Intervals
    try:
        y_pred = model.predict(X_test)
        results["prediction_intervals"] = compute_prediction_intervals(model, X_test, y_pred)
    except Exception as e:
        results["prediction_intervals"] = {"error": str(e)[:60]}

    return results
