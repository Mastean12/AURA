import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# MODULE 1: Problem Detection
# ──────────────────────────────────────────────

CLASSIFICATION_TARGETS = {
    "churn", "attrition", "fraud", "default", "conversion", "converted",
    "exited", "left", "stopped", "cancelled", "response", "purchased",
    "retained", "survived", "died", "fail", "success", "approved",
    "rejected", "flagged", "complaint", "returned", "subscribed",
}
REGRESSION_TARGETS = {
    "revenue", "profit", "cost", "sales", "demand", "production",
    "price", "amount", "spend", "quantity", "volume", "hours",
    "count", "stock", "inventory", "rate", "score", "value",
    "balance", "income", "expense", "margin", "growth",
}
TIME_SERIES_INDICATORS = {"date", "time", "timestamp", "year", "month", "quarter", "period"}


def detect_problem_type(target: str, df: pd.DataFrame) -> dict:
    """Classify the prediction problem type."""
    col = df[target].dropna()
    nunique = col.nunique()
    dtype = str(df[target].dtype)

    is_numeric = pd.api.types.is_numeric_dtype(col)
    target_lower = target.lower()

    # Classification candidate: categorical or binary with few unique values
    if not is_numeric or nunique <= 20:
        task = "classification"
        subtype = "binary" if nunique == 2 else "multiclass"
        sample_vals = col.unique()[:5].tolist()
    elif any(kw in target_lower for kw in TIME_SERIES_INDICATORS):
        task = "time_series"
        subtype = "forecast"
        sample_vals = []
    elif is_numeric:
        # Check if there's a time column for time series
        has_time = any(
            any(kw in c.lower() for kw in TIME_SERIES_INDICATORS)
            for c in df.columns if c != target
        )
        if has_time:
            task = "time_series"
            subtype = "forecast"
        else:
            task = "regression"
            subtype = "continuous"
        sample_vals = []

    return {
        "target": target,
        "task": task,
        "subtype": subtype,
        "unique_values": int(nunique),
        "classification_type": "binary" if nunique == 2 else "multiclass" if nunique <= 20 else "regression",
    }


# ──────────────────────────────────────────────
# MODULE 2: Automatic Target Detection
# ──────────────────────────────────────────────

SKIP_COLUMNS = {"identifier", "text", "date"}


def detect_target(df: pd.DataFrame, columns_info: list[dict] | None = None) -> dict:
    """Auto-detect the best target column for prediction."""
    from app.services.dataset_intelligence_service import analyze_dataset

    ds = columns_info
    if ds is None:
        ds = analyze_dataset(df)
    columns = ds.get("columns", [])

    # Priority 1: Already flagged as target
    for c in columns:
        if c.get("is_target"):
            return {"target": c["name"], "type": c.get("target_type", "unknown"), "method": "pattern_matched"}

    # Priority 2: Identify classification targets (binary with <=10 unique)
    for c in columns:
        if c.get("classification") in SKIP_COLUMNS:
            continue
        name = c["name"]
        if c.get("nunique", 0) == 2 and c.get("dtype") in ("int64", "int32", "int", "object"):
            return {"target": name, "type": "classification", "method": "binary_detected"}

    # Priority 3: Check for regression KPIs
    for c in columns:
        if c.get("classification") == "kpi":
            return {"target": c["name"], "type": c.get("kpi_type", "kpi"), "method": "kpi_based"}

    # Priority 4: Last numeric column
    numeric_cols = [c for c in columns if c.get("dtype") == "numeric" and c.get("classification") not in SKIP_COLUMNS]
    if numeric_cols:
        return {"target": numeric_cols[-1]["name"], "type": "numeric", "method": "fallback"}

    return {"target": None, "type": None, "method": "none"}


# ──────────────────────────────────────────────
# MODULE 3: Feature Engineering
# ──────────────────────────────────────────────


def engineer_features(df: pd.DataFrame, target: str, problem_type: dict) -> pd.DataFrame:
    """Auto-engineer features: encoding, scaling, lags, date features."""
    df = df.copy()
    if target in df.columns:
        df = df.drop(columns=[target])

    result = df.copy()

    # Date feature extraction
    for col in df.select_dtypes(include=["datetime64", "datetime"]).columns:
        try:
            dt = pd.to_datetime(df[col], errors="coerce")
            result[f"{col}_year"] = dt.dt.year
            result[f"{col}_month"] = dt.dt.month
            result[f"{col}_quarter"] = dt.dt.quarter
            result[f"{col}_weekday"] = dt.dt.weekday
            result[f"{col}_day"] = dt.dt.day
            result.drop(columns=[col], inplace=True)
        except Exception:
            pass

    # Handle feature columns for time series
    if problem_type.get("task") == "time_series":
        for col in result.select_dtypes(include=["number"]).columns[:5]:
            try:
                vals = result[col].dropna()
                if len(vals) >= 5:
                    result[f"{col}_lag1"] = result[col].shift(1)
                    result[f"{col}_lag2"] = result[col].shift(2)
                    result[f"{col}_lag3"] = result[col].shift(3)
                    result[f"{col}_ma3"] = result[col].rolling(3, min_periods=1).mean()
                    result[f"{col}_ma7"] = result[col].rolling(7, min_periods=1).mean() if len(vals) >= 7 else float("nan")
            except Exception:
                pass

    # Encode low-cardinality categoricals
    for col in result.select_dtypes(include=["object", "category"]).columns:
        try:
            nunique = result[col].nunique()
            if nunique <= 2:
                # Binary encoding
                result[col] = result[col].astype(str).map(
                    lambda v: 1 if v == result[col].value_counts().index[0] else 0
                )
            elif nunique <= 10:
                # One-hot
                dummies = pd.get_dummies(result[col], prefix=col, drop_first=True)
                result = pd.concat([result.drop(columns=[col]), dummies], axis=1)
            else:
                # Drop high-cardinality categoricals
                result.drop(columns=[col], inplace=True)
        except Exception:
            pass

    # Fill missing values
    for col in result.select_dtypes(include=["number"]).columns:
        result[col] = result[col].fillna(result[col].median() if result[col].nunique() > 0 else 0)
    for col in result.select_dtypes(include=["object"]).columns:
        result[col] = result[col].fillna(result[col].mode().iloc[0] if not result[col].mode().empty else "MISSING")

    return result


# ──────────────────────────────────────────────
# MODULE 4: Model Selection + Validation
# ──────────────────────────────────────────────


def _train_test_split(df: pd.DataFrame, target: str, test_size: float = 0.2):
    """Simple train/test split."""
    from sklearn.model_selection import train_test_split
    y = df[target]
    X = df.drop(columns=[target])
    # Drop non-numeric columns
    X = X.select_dtypes(include=["number"])
    # Drop constant columns
    X = X.loc[:, X.nunique() > 1]
    if X.empty or y.nunique() == 0:
        return None, None, None, None
    return train_test_split(X, y, test_size=test_size, random_state=42)


def evaluate_regression(y_true, y_pred) -> dict:
    """Regression metrics."""
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "mape": round(float(mean_absolute_percentage_error(y_true, y_pred) * 100), 2),
    }


def evaluate_classification(y_true, y_pred, y_prob=None) -> dict:
    """Classification metrics."""
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    try:
        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_true, y_prob if y_prob is not None else y_pred, multi_class="ovr")), 4) if y_prob is not None else None,
        }
    except Exception:
        return {"accuracy": 0, "precision": 0, "recall": 0, "f1": 0}


def select_best_model(df: pd.DataFrame, target: str, problem_type: dict) -> dict:
    """Auto-select best model by evaluating multiple candidates."""
    result = _train_test_split(df, target)
    if result[0] is None:
        return {"error": "Insufficient data for modeling"}
    X_train, X_test, y_train, y_test = result
    task = problem_type.get("task", "regression")
    candidates = {}
    errors = []

    if task == "classification":
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
        try:
            from xgboost import XGBClassifier
            has_xgb = True
        except ImportError:
            has_xgb = False

        models = {
            "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
            "random_forest": RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1),
        }
        if has_xgb:
            models["xgboost"] = XGBClassifier(n_estimators=50, random_state=42, use_label_encoder=False, verbosity=0)

        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                probs = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None
                metrics = evaluate_classification(y_test, preds, probs[:, 1] if probs is not None and probs.shape[1] == 2 else None)
                candidates[name] = {"model": model, "metrics": metrics, "score": metrics.get("f1", 0)}
            except Exception as e:
                errors.append(f"{name}: {e}")
    else:
        from sklearn.linear_model import LinearRegression, Ridge
        from sklearn.ensemble import RandomForestRegressor
        try:
            from xgboost import XGBRegressor
            has_xgb = True
        except ImportError:
            has_xgb = False

        models = {
            "linear_regression": LinearRegression(),
            "ridge": Ridge(alpha=1.0, random_state=42),
            "random_forest": RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        }
        if has_xgb:
            models["xgboost"] = XGBRegressor(n_estimators=50, random_state=42, verbosity=0)

        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                metrics = evaluate_regression(y_test, preds)
                candidates[name] = {"model": model, "metrics": metrics, "score": metrics.get("r2", 0)}
            except Exception as e:
                errors.append(f"{name}: {e}")

    if not candidates:
        return {"error": "No models could be trained", "errors": errors}

    best_name = max(candidates, key=lambda n: candidates[n]["score"])
    best = candidates[best_name]
    return {
        "best_model": best_name,
        "metrics": best["metrics"],
        "score": best["score"],
        "all_models": {n: {"metrics": c["metrics"], "score": c["score"]} for n, c in candidates.items()},
        "errors": errors[:3],
        "n_features": X_train.shape[1],
        "n_train": len(X_train),
        "n_test": len(X_test),
    }


# ──────────────────────────────────────────────
# MODULE 6: Prediction Confidence
# ──────────────────────────────────────────────


def compute_confidence(model_result: dict, dq_score: float, n_samples: int) -> dict:
    """Compute overall prediction confidence from multiple factors."""
    data_quality_weight = min(dq_score / 100, 1) * 0.2
    model_perf = max(0, min(model_result.get("score", 0) if not isinstance(model_result.get("score", ""), str) else 0, 1)) * 0.4
    sample_size_weight = min(n_samples / 1000, 1) * 0.2

    # Feature strength: how many features made it into the model
    n_features = model_result.get("n_features", 0)
    feature_strength = min(n_features / 10, 1) * 0.2

    confidence = round((data_quality_weight + model_perf + sample_size_weight + feature_strength) * 100, 1)
    confidence = max(0, min(100, confidence))

    factors = []
    if data_quality_weight > 0.15: factors.append("High data quality")
    elif data_quality_weight > 0.1: factors.append("Moderate data quality")
    else: factors.append("Low data quality")

    if model_perf > 0.3: factors.append(f"Strong model performance ({model_result.get('score', 'N/A')})")
    elif model_perf > 0.15: factors.append("Adequate model performance")
    else: factors.append("Weak model performance")

    if n_samples > 500: factors.append("Large sample size")
    elif n_samples > 100: factors.append("Moderate sample size")
    else: factors.append("Small sample size")

    return {
        "confidence": confidence,
        "factors": factors,
        "breakdown": {
            "data_quality": round(data_quality_weight * 100, 1),
            "model_performance": round(model_perf * 100, 1),
            "sample_size": round(sample_size_weight * 100, 1),
            "feature_strength": round(feature_strength * 100, 1),
        },
    }


# ──────────────────────────────────────────────
# MODULE 7: Feature Importance (XAI)
# ──────────────────────────────────────────────


def compute_feature_importance(model, X_train, feature_names: list[str], top_n: int = 10) -> list[dict]:
    """Extract feature importance from the trained model."""
    try:
        if hasattr(model, "feature_importances_"):
            imp = model.feature_importances_
        elif hasattr(model, "coef_"):
            imp = np.abs(model.coef_[0]) if model.coef_.ndim > 1 else np.abs(model.coef_)
        else:
            return []

        if len(feature_names) != len(imp):
            feature_names = [f"feature_{i}" for i in range(len(imp))]

        pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)
        return [
            {"feature": name, "importance": round(float(val), 4)}
            for name, val in pairs[:top_n] if float(val) > 0
        ]
    except Exception as e:
        logger.warning("Feature importance failed: %s", e)
        return []


# ──────────────────────────────────────────────
# MODULE 8: Risk Prediction
# ──────────────────────────────────────────────


def compute_risk_score(prob: float, problem_type: str) -> dict:
    """Convert model probability into a business risk score (0-100)."""
    if prob is None:
        return {"score": 50, "level": "moderate", "description": "Default risk assessment"}
    risk = round(prob * 100, 1)
    if risk >= 70:
        level, desc = "critical", "Immediate attention required"
    elif risk >= 50:
        level, desc = "high", "Significant risk identified"
    elif risk >= 30:
        level, desc = "moderate", "Monitor closely"
    else:
        level, desc = "low", "Within acceptable range"
    return {"score": risk, "level": level, "description": desc}


# ──────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ──────────────────────────────────────────────


async def run_predictive_analysis(doc_id: int, df: pd.DataFrame, dq_score: float = 85.0) -> dict:
    """Run full predictive intelligence pipeline: detect problem → engineer features → model → validate → explain."""
    from app.services.dataset_intelligence_service import analyze_dataset
    ds = analyze_dataset(df)

    # Step 1-2: Detect target and problem
    target_info = detect_target(df, ds)
    target = target_info.get("target")
    if not target:
        return {"error": "No suitable target variable detected", "target_info": target_info}

    problem = detect_problem_type(target, df)
    logger.info("Problem: target=%s task=%s subtype=%s", target, problem["task"], problem["subtype"])

    # Step 3: Feature engineering
    df_fe = engineer_features(df, target, problem)
    df_model = pd.concat([df_fe, df[target]], axis=1)
    # Drop non-numeric columns
    df_model = df_model.select_dtypes(include=["number"]).dropna(how="all", axis=1)
    df_model = df_model.dropna(subset=[target])

    if len(df_model) < 10:
        return {"error": f"Insufficient data ({len(df_model)} rows) after feature engineering"}

    # Step 4-5: Model selection and validation
    model_result = select_best_model(df_model, target, problem)
    if "error" in model_result:
        return {"error": model_result["error"], "target": target, "problem": problem}

    # Step 6: Confidence
    confidence = compute_confidence(model_result, dq_score, len(df_model))

    # Step 7: Feature importance
    best_model_name = model_result.get("best_model")
    best_model = None
    feature_names = [c for c in df_fe.columns if c in df_model.columns and c != target]
    X_full = df_model[feature_names].select_dtypes(include=["number"])
    X_full = X_full.loc[:, X_full.nunique() > 1]

    if best_model_name and X_full.shape[1] > 0:
        from sklearn.model_selection import train_test_split
        y_full = df_model[target]
        try:
            X_tr, _, y_tr, _ = train_test_split(X_full, y_full, test_size=0.2, random_state=42)
            # Retrain best model
            if best_model_name == "logistic_regression":
                from sklearn.linear_model import LogisticRegression
                best_model = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr, y_tr)
            elif best_model_name == "random_forest":
                if problem["task"] == "classification":
                    from sklearn.ensemble import RandomForestClassifier
                    best_model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1).fit(X_tr, y_tr)
                else:
                    from sklearn.ensemble import RandomForestRegressor
                    best_model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1).fit(X_tr, y_tr)
            elif "xgboost" in best_model_name:
                mod = __import__("xgboost", fromlist=["XGBClassifier", "XGBRegressor"])
                ModelClass = mod.XGBClassifier if problem["task"] == "classification" else mod.XGBRegressor
                best_model = ModelClass(n_estimators=50, random_state=42, verbosity=0).fit(X_tr, y_tr)
        except Exception as e:
            logger.warning("Model retrain failed: %s", e)

    importance = compute_feature_importance(best_model, X_full, feature_names) if best_model is not None else []

    # Step 8: Risk prediction
    risk = compute_risk_score(model_result.get("score", 0.5), problem["task"])

    return {
        "target": target,
        "problem": problem,
        "model": {
            "name": best_model_name,
            "metrics": model_result.get("metrics", {}),
            "all_models_evaluated": list(model_result.get("all_models", {}).keys()),
            "n_features": X_full.shape[1] if not X_full.empty else 0,
            "n_samples": len(df_model),
        },
        "confidence": confidence,
        "feature_importance": importance[:10],
        "risk": risk,
        "dataset_type": ds.get("dataset_type", "General"),
        "data_quality_score": dq_score,
    }
