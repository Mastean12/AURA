import json
import logging
import time
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CLASSIFIERS = {}
REGRESSORS = {}
CLUSTERERS = {}
ANOMALY_DETECTORS = {}

try:
    from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.svm import OneClassSVM
    CLASSIFIERS["Logistic Regression"] = lambda: LogisticRegression(max_iter=1000, random_state=42)
    CLASSIFIERS["Random Forest"] = lambda: RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    REGRESSORS["Linear Regression"] = lambda: LinearRegression()
    REGRESSORS["Ridge"] = lambda: Ridge(alpha=1.0, random_state=42)
    REGRESSORS["Random Forest"] = lambda: RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    CLUSTERERS["K-Means"] = lambda n: KMeans(n_clusters=n, random_state=42, n_init="auto")
    CLUSTERERS["DBSCAN"] = lambda: DBSCAN()
    CLUSTERERS["Hierarchical"] = lambda n: AgglomerativeClustering(n_clusters=n)
    ANOMALY_DETECTORS["Isolation Forest"] = lambda: IsolationForest(random_state=42, contamination="auto")
    ANOMALY_DETECTORS["LOF"] = lambda: LocalOutlierFactor(contamination="auto")
    ANOMALY_DETECTORS["One-Class SVM"] = lambda: OneClassSVM(nu=0.1)
except ImportError:
    logger.warning("sklearn not fully available")

try:
    from xgboost import XGBClassifier, XGBRegressor
    CLASSIFIERS["XGBoost"] = lambda: XGBClassifier(n_estimators=50, random_state=42, verbosity=0)
    REGRESSORS["XGBoost"] = lambda: XGBRegressor(n_estimators=50, random_state=42, verbosity=0)
except ImportError:
    pass

try:
    import lightgbm as lgb
    CLASSIFIERS["LightGBM"] = lambda: lgb.LGBMClassifier(n_estimators=50, random_state=42, verbose=-1)
    REGRESSORS["LightGBM"] = lambda: lgb.LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
except ImportError:
    pass

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CLASSIFIERS["CatBoost"] = lambda: CatBoostClassifier(n_estimators=50, random_state=42, verbose=0)
    REGRESSORS["CatBoost"] = lambda: CatBoostRegressor(n_estimators=50, random_state=42, verbose=0)
except ImportError:
    pass


def _classification_metrics(y_true, y_pred, y_prob=None) -> dict:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    try:
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
        auc = roc_auc_score(y_true, y_prob, multi_class="ovr") if y_prob is not None else None
        return {"accuracy": round(float(acc), 4), "precision": round(float(prec), 4),
                "recall": round(float(rec), 4), "f1": round(float(f1), 4), "roc_auc": round(float(auc), 4) if auc else None}
    except Exception:
        return {"accuracy": 0, "precision": 0, "recall": 0, "f1": 0}


def _regression_metrics(y_true, y_pred) -> dict:
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "mape": round(float(mean_absolute_percentage_error(y_true, y_pred) * 100), 2),
    }


def _clustering_metrics(X, labels) -> dict:
    from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    if n_clusters < 2:
        return {"silhouette": 0, "calinski_harabasz": 0, "davies_bouldin": 0, "n_clusters": n_clusters, "note": "Need 2+ clusters"}
    try:
        sil = silhouette_score(X, labels)
        ch = calinski_harabasz_score(X, labels)
        db = davies_bouldin_score(X, labels)
        return {"silhouette": round(float(sil), 4), "calinski_harabasz": round(float(ch), 2),
                "davies_bouldin": round(float(db), 4), "n_clusters": n_clusters}
    except Exception:
        return {"silhouette": 0, "calinski_harabasz": 0, "davies_bouldin": 0, "n_clusters": n_clusters}


def _anomaly_metrics(y_pred, contamination: float = 0.1) -> dict:
    n_anomalies = int((y_pred == -1).sum()) if y_pred is not None else 0
    ratio = n_anomalies / len(y_pred) if len(y_pred) > 0 else 0
    return {"anomalies_detected": n_anomalies, "anomaly_ratio": round(float(ratio), 4), "expected_contamination": contamination}


def _train_test_split(X, y, test_size=0.2):
    from sklearn.model_selection import train_test_split
    return train_test_split(X, y, test_size=test_size, random_state=42)


def _get_feature_target(df: pd.DataFrame, target: str):
    """Split dataframe into features and target."""
    y = df[target]
    X = df.drop(columns=[target]).select_dtypes(include=["number"])
    X = X.loc[:, X.nunique() > 1]
    return X, y


async def run_automl(doc_id: int, problem_type: str = "", target: str = "") -> dict[str, Any]:
    """Run full AutoML model selection and comparison."""
    from app.database.database import get_session_factory
    from app.models.document import Document
    from sqlalchemy import select

    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        return {"error": "Document not found"}

    import io
    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    if not target and problem_type != "clustering":
        from app.services.dataset_intelligence_service import analyze_dataset
        ds = analyze_dataset(df)
        target = ds.get("target_variable", "")
        if not target:
            return {"error": "Could not detect target variable"}

    if problem_type == "clustering":
        X = df.select_dtypes(include=["number"]).dropna()
        if X.shape[1] < 2:
            return {"error": "Need 2+ numeric columns for clustering"}
        return _run_clustering(X, df)

    if problem_type == "anomaly_detection":
        X = df.select_dtypes(include=["number"]).dropna()
        if X.shape[1] < 1:
            return {"error": "Need numeric columns for anomaly detection"}
        return _run_anomaly_detection(X)

    if problem_type == "classification":
        return await _run_classification(df, target)

    if problem_type == "regression" or problem_type == "time_series":
        return await _run_regression(df, target)

    # Auto-detect
    X, y = _get_feature_target(df, target)
    if X.shape[0] < 10 or X.shape[1] < 1:
        return {"error": "Insufficient data after feature selection"}

    if y.nunique() <= 20 and y.dtype in ("int64", "int32", "int", "object"):
        return await _run_classification(df, target)
    else:
        return await _run_regression(df, target)


async def _run_classification(df: pd.DataFrame, target: str) -> dict:
    X, y = _get_feature_target(df, target)
    if X.shape[0] < 10 or X.shape[1] < 1:
        return {"error": "Insufficient data"}
    if y.nunique() < 2:
        return {"error": "Target must have at least 2 classes"}

    y = y.astype(int) if y.dtype in ("float64", "float32") else y
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = _train_test_split(X, y_enc)
    results = []

    for name, model_fn in CLASSIFIERS.items():
        try:
            start = time.time()
            model = model_fn()
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            probs = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None
            elapsed = round(time.time() - start, 2)
            metrics = _classification_metrics(y_test, preds, probs[:, 1] if probs is not None and probs.shape[1] == 2 else None)
            metrics["training_time_s"] = elapsed
            metrics["model_name"] = name
            results.append(metrics)
        except Exception as e:
            results.append({"model_name": name, "error": str(e)[:80]})

    results.sort(key=lambda r: -r.get("f1", 0))
    return {
        "problem_type": "classification",
        "target": target,
        "features": X.shape[1],
        "samples": X.shape[0],
        "results": results,
        "best_model": results[0]["model_name"] if results else None,
        "best_f1": results[0].get("f1") if results else None,
        "models_tested": len(results),
        "label_classes": le.classes_.tolist() if hasattr(le, "classes_") else [],
    }


async def _run_regression(df: pd.DataFrame, target: str) -> dict:
    X, y = _get_feature_target(df, target)
    if X.shape[0] < 10 or X.shape[1] < 1:
        return {"error": "Insufficient data"}

    X_train, X_test, y_train, y_test = _train_test_split(X, y)
    results = []

    for name, model_fn in REGRESSORS.items():
        try:
            start = time.time()
            model = model_fn()
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            elapsed = round(time.time() - start, 2)
            metrics = _regression_metrics(y_test, preds)
            metrics["training_time_s"] = elapsed
            metrics["model_name"] = name
            results.append(metrics)
        except Exception as e:
            results.append({"model_name": name, "error": str(e)[:80]})

    results.sort(key=lambda r: -r.get("r2", 0))
    return {
        "problem_type": "regression",
        "target": target,
        "features": X.shape[1],
        "samples": X.shape[0],
        "results": results,
        "best_model": results[0]["model_name"] if results else None,
        "best_r2": results[0].get("r2") if results else None,
        "models_tested": len(results),
    }


def _run_clustering(X: pd.DataFrame, df_full: pd.DataFrame) -> dict:
    n_clusters = min(10, max(2, int(np.sqrt(X.shape[0] / 2))))
    results = []

    for name, model_fn in [("K-Means", lambda: KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")),
                           ("DBSCAN", lambda: DBSCAN()),
                           ("Hierarchical", lambda: AgglomerativeClustering(n_clusters=n_clusters))]:
        try:
            start = time.time()
            model = model_fn()
            labels = model.fit_predict(X)
            elapsed = round(time.time() - start, 2)
            metrics = _clustering_metrics(X, labels)
            metrics["training_time_s"] = elapsed
            metrics["model_name"] = name
            results.append(metrics)
        except Exception as e:
            results.append({"model_name": name, "error": str(e)[:80]})

    results.sort(key=lambda r: -r.get("silhouette", 0))
    return {
        "problem_type": "clustering",
        "features": X.shape[1],
        "samples": X.shape[0],
        "results": results,
        "best_model": results[0]["model_name"] if results else None,
        "models_tested": len(results),
        "n_clusters": n_clusters,
    }


def _run_anomaly_detection(X: pd.DataFrame) -> dict:
    results = []
    for name, model_fn in ANOMALY_DETECTORS.items():
        try:
            start = time.time()
            model = model_fn()
            preds = model.fit_predict(X)
            elapsed = round(time.time() - start, 2)
            metrics = _anomaly_metrics(preds)
            metrics["training_time_s"] = elapsed
            metrics["model_name"] = name
            results.append(metrics)
        except Exception as e:
            results.append({"model_name": name, "error": str(e)[:80]})

    results.sort(key=lambda r: -r.get("anomalies_detected", 0))
    return {
        "problem_type": "anomaly_detection",
        "features": X.shape[1],
        "samples": X.shape[0],
        "results": results,
        "best_model": results[0]["model_name"] if results else None,
        "models_tested": len(results),
    }
