import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ── 13 industries with keyword patterns ──
INDUSTRY_DETECTORS = {
    "Sales": ["revenue", "sales", "deal", "pipeline", "customer", "product", "region", "discount", "order", "invoice"],
    "Finance": ["revenue", "expense", "profit", "cash", "asset", "liability", "budget", "forecast", "tax", "accounting", "audit"],
    "Banking": ["account", "loan", "deposit", "transaction", "balance", "interest", "credit", "fraud", "mortgage"],
    "Retail": ["sku", "basket", "store", "product", "category", "inventory", "customer", "sales", "promotion"],
    "Manufacturing": ["production", "machine", "downtime", "yield", "defect", "supplier", "assembly", "batch"],
    "Healthcare": ["patient", "diagnosis", "treatment", "readmission", "hospital", "claim", "provider", "medication"],
    "Marketing": ["campaign", "click", "impression", "conversion", "lead", "acquisition", "channel", "roi", "cpa", "cpc"],
    "HR": ["employee", "hiring", "salary", "attrition", "turnover", "promotion", "performance", "headcount", "recruitment"],
    "Education": ["student", "course", "grade", "enrollment", "teacher", "class", "attendance", "exam", "curriculum"],
    "Government": ["citizen", "tax", "budget", "service", "compliance", "regulation", "population", "census"],
    "Customer Support": ["ticket", "support", "complaint", "resolution", "csat", "sla", "priority", "escalation"],
    "Logistics": ["shipment", "delivery", "warehouse", "freight", "route", "fleet", "courier", "dispatch"],
    "Supply Chain": ["supplier", "procurement", "warehouse", "freight", "lead_time", "stock", "vendor", "logistics"],
}

# ── Dataset type patterns ──
DATASET_TYPES = [
    {"type": "Customer Churn", "keywords": ["churn", "attrition", "exited", "cancelled", "left", "retained", "stopped"]},
    {"type": "Sales Performance", "keywords": ["revenue", "sales", "profit", "margin", "growth", "target", "quota"]},
    {"type": "Employee Analytics", "keywords": ["employee", "hiring", "attrition", "turnover", "salary", "promotion", "headcount"]},
    {"type": "Financial Performance", "keywords": ["revenue", "expense", "profit", "income", "balance", "cash_flow"]},
    {"type": "Customer Analytics", "keywords": ["customer", "segment", "lifetime", "satisfaction", "feedback", "support"]},
    {"type": "Marketing Performance", "keywords": ["campaign", "conversion", "click", "impression", "cpa", "roi"]},
    {"type": "Operational Performance", "keywords": ["efficiency", "productivity", "downtime", "cycle_time", "utilization"]},
    {"type": "Supply Chain Analytics", "keywords": ["supplier", "inventory", "warehouse", "delivery", "lead_time"]},
    {"type": "Healthcare Analytics", "keywords": ["patient", "diagnosis", "readmission", "hospital", "claim"]},
    {"type": "Banking Analytics", "keywords": ["account", "loan", "transaction", "fraud", "credit"]},
    {"type": "Education Analytics", "keywords": ["student", "course", "grade", "enrollment", "teacher"]},
    {"type": "Product Analytics", "keywords": ["product", "sku", "category", "price", "inventory"]},
    {"type": "General Business Analytics", "keywords": []},
]

# ── Business objective detection ──
BUSINESS_OBJECTIVES = [
    {"objective": "Customer Retention", "keywords": ["churn", "attrition", "retention", "loyalty", "satisfaction"]},
    {"objective": "Revenue Growth", "keywords": ["revenue", "sales", "growth", "upsell", "cross_sell"]},
    {"objective": "Cost Reduction", "keywords": ["cost", "expense", "overhead", "efficiency", "waste"]},
    {"objective": "Risk Management", "keywords": ["risk", "fraud", "default", "compliance", "audit"]},
    {"objective": "Operational Excellence", "keywords": ["efficiency", "productivity", "quality", "downtime"]},
    {"objective": "Employee Engagement", "keywords": ["employee", "satisfaction", "turnover", "retention", "engagement"]},
    {"objective": "Customer Acquisition", "keywords": ["acquisition", "conversion", "lead", "campaign", "channel"]},
    {"objective": "Financial Planning", "keywords": ["budget", "forecast", "planning", "projection", "scenario"]},
    {"objective": "Market Expansion", "keywords": ["market", "region", "expansion", "growth", "opportunity"]},
    {"objective": "General Performance Monitoring", "keywords": []},
]

# ── Analytical problem detection ──
ANALYTICAL_PROBLEMS = [
    {"problem": "Classification", "indicators": ["churn", "fraud", "default", "conversion", "response", "attrition"]},
    {"problem": "Regression / Forecasting", "indicators": ["revenue", "sales", "demand", "price", "growth", "forecast"]},
    {"problem": "Customer Segmentation", "indicators": ["segment", "cluster", "customer", "profile", "persona"]},
    {"problem": "Time Series Analysis", "indicators": ["date", "time", "timestamp", "year", "month", "quarter", "trend"]},
    {"problem": "Risk Analysis", "indicators": ["risk", "fraud", "default", "compliance", "exposure"]},
    {"problem": "Anomaly Detection", "indicators": ["anomaly", "outlier", "fraud", "irregular", "unusual"]},
    {"problem": "Descriptive Analytics", "indicators": []},
]


def _score_columns(df: pd.DataFrame, keywords: list[str]) -> int:
    """Score how many keywords appear in column names."""
    all_cols = " ".join(df.columns.str.lower().tolist())
    return sum(1 for kw in keywords if kw in all_cols)


def detect_industry(df: pd.DataFrame) -> str:
    """Detect the most likely industry from column names."""
    scores = {ind: _score_columns(df, kws) for ind, kws in INDUSTRY_DETECTORS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General Business"


def detect_dataset_type(df: pd.DataFrame) -> str:
    """Detect the type of business dataset."""
    best_score = 0
    best_type = "General Business Analytics"
    for dt in DATASET_TYPES:
        if not dt["keywords"]:
            continue
        score = _score_columns(df, dt["keywords"])
        if score > best_score:
            best_score = score
            best_type = dt["type"]
    return best_type


def detect_business_objective(df: pd.DataFrame) -> str:
    """Detect the primary business objective from column names."""
    best_score = 0
    best_objective = "General Performance Monitoring"
    for obj in BUSINESS_OBJECTIVES:
        if not obj["keywords"]:
            continue
        score = _score_columns(df, obj["keywords"])
        if score > best_score:
            best_score = score
            best_objective = obj["objective"]
    return best_objective


def detect_analytical_problem(df: pd.DataFrame, target: str = "") -> str:
    """Detect the primary analytical problem (classification, regression, etc.)."""
    if target:
        target_lower = target.lower()
        for prob in ANALYTICAL_PROBLEMS:
            if any(kw in target_lower for kw in prob["indicators"]):
                return prob["problem"]

    all_cols = " ".join(df.columns.str.lower().tolist())
    for prob in ANALYTICAL_PROBLEMS:
        if not prob["indicators"]:
            continue
        if any(kw in all_cols for kw in prob["indicators"]):
            return prob["problem"]

    # Fallback: check if target has few unique values
    if target and target in df.columns:
        nunique = df[target].nunique()
        if nunique <= 2:
            return "Classification"
        if pd.api.types.is_numeric_dtype(df[target]) and nunique > 10:
            return "Regression / Forecasting"

    return "Descriptive Analytics"


async def run_business_context_detection(doc_id: int) -> dict[str, Any]:
    """Run full business context detection pipeline."""
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

    industry = detect_industry(df)
    dataset_type = detect_dataset_type(df)
    objective = detect_business_objective(df)

    # Detect target variable (simplified)
    from app.services.dataset_intelligence_service import analyze_dataset
    ds = analyze_dataset(df)
    target = ds.get("target_variable", "")

    problem = detect_analytical_problem(df, target)

    return {
        "doc_id": doc_id,
        "industry": industry,
        "dataset_type": dataset_type,
        "business_objective": objective,
        "analytical_problem": problem,
        "target_variable": target,
    }
