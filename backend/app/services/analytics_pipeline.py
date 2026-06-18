import logging
from typing import Any

import pandas as pd

from app.services.dataset_intelligence_service import analyze_dataset
from app.services.data_quality_service import run_data_quality_audit
from app.services.business_analytics_service import run_business_analytics
from app.services.executive_intelligence_v2 import generate_enhanced_executive_intelligence
from app.services.forecast_intelligence_service import check_forecast_eligibility, select_forecast_model, validate_forecast, explain_forecast

logger = logging.getLogger(__name__)


async def run_full_analytics_pipeline(doc_id: int, df: pd.DataFrame) -> dict[str, Any]:
    """Run the complete 5-layer analytics pipeline and return consolidated results."""
    logger.info("Running full analytics pipeline for doc_id=%d (%d rows, %d cols)", doc_id, len(df), len(df.columns))

    # Layer 1: Dataset Intelligence
    logger.info("Layer 1: Dataset Intelligence")
    dataset_intel = analyze_dataset(df)

    # Layer 2: Data Quality
    logger.info("Layer 2: Data Quality")
    data_quality = run_data_quality_audit(df)

    # Layer 3: Business Analytics
    logger.info("Layer 3: Business Analytics")
    business_analytics = run_business_analytics(df)

    # Layer 4: Executive Intelligence
    logger.info("Layer 4: Executive Intelligence")
    try:
        exec_intel = await generate_enhanced_executive_intelligence(doc_id, df)
    except Exception as e:
        logger.warning("Executive intelligence failed: %s", e)
        exec_intel = {}

    # Layer 5: Forecast Intelligence
    logger.info("Layer 5: Forecast Intelligence")
    eligibility = check_forecast_eligibility(df)
    forecast_info = {"eligibility": eligibility, "model": None, "validation": None, "explanation": ""}
    if eligibility["eligible"] and eligibility["target"] and eligibility["time_column"]:
        try:
            model_info = select_forecast_model(df, eligibility["target"], eligibility["time_column"])
            forecast_info["model"] = model_info
        except Exception as e:
            logger.warning("Forecast model selection failed: %s", e)

    return {
        "doc_id": doc_id,
        "dataset_intelligence": dataset_intel,
        "data_quality": data_quality,
        "business_analytics": business_analytics,
        "executive_intelligence": exec_intel.get("executive_intelligence", {}),
        "forecast_intelligence": forecast_info,
    }
