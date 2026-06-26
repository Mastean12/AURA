import asyncio
import io
import json
import logging
import time
from typing import Any

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.dataset_intelligence_service import analyze_dataset
from app.services.data_quality_service import run_data_quality_audit
from app.services.business_analytics_engine_v2 import get_business_analytics
from app.services.statistical_quality_service import run_full_quality_analysis
from app.services.executive_intelligence_engine_v3 import run_executive_intelligence
from app.services.chart_service import generate_smart_charts
from app.services.cache_service import compute_doc_hash, get_cached, set_cached
from sqlalchemy import select

logger = logging.getLogger(__name__)

STAGES = [
    {"id": "understanding", "label": "Understanding Dataset", "icon": "📊"},
    {"id": "business_context", "label": "Detecting Business Context", "icon": "🏢"},
    {"id": "data_quality", "label": "Assessing Data Quality", "icon": "✅"},
    {"id": "statistical", "label": "Running Statistical Analysis", "icon": "📈"},
    {"id": "kpis", "label": "Identifying KPIs & Metrics", "icon": "🎯"},
    {"id": "executive", "label": "Generating Executive Insights", "icon": "🧠"},
    {"id": "visualizations", "label": "Building Visualizations", "icon": "📉"},
    {"id": "dashboard", "label": "Preparing Executive Dashboard", "icon": "📋"},
]


class PipelineResult:
    def __init__(self):
        self.stages: list[dict] = []
        self.results: dict[str, Any] = {}
        self.errors: list[str] = []
        self.start_time = time.time()
        self.doc_id = 0
        self.doc_title = ""

    def add_stage(self, stage_id: str) -> None:
        self.stages.append({"id": stage_id, "status": "running", "started_at": time.time()})

    def complete_stage(self, stage_id: str, data: Any = None) -> None:
        for s in self.stages:
            if s["id"] == stage_id:
                s["status"] = "completed"
                s["completed_at"] = time.time()
                s["duration_ms"] = int((s["completed_at"] - s.get("started_at", s["completed_at"])) * 1000)
                break
        if data is not None:
            self.results[stage_id] = data

    def fail_stage(self, stage_id: str, error: str) -> None:
        for s in self.stages:
            if s["id"] == stage_id:
                s["status"] = "failed"
                s["error"] = str(error)[:200]
                break
        self.errors.append(f"{stage_id}: {error}")

    def to_dict(self) -> dict:
        total = time.time() - self.start_time
        return {
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "total_duration_ms": int(total * 1000),
            "stages": self.stages,
            "errors": self.errors[:5],
            "success": len([s for s in self.stages if s["status"] == "failed"]) == 0,
            "results": self.results,
        }


async def run_full_pipeline(doc_id: int) -> dict:
    """Orchestrate all analytics engines in sequence with status tracking."""
    pipeline = PipelineResult()
    pipeline.doc_id = doc_id

    # Load document
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        return {"error": "Document not found", "doc_id": doc_id}

    pipeline.doc_title = doc.title or f"Document #{doc_id}"
    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular with 2+ columns", "doc_id": doc_id}

    doc_hash = compute_doc_hash(doc.content)

    # ── Stage 1: Dataset Understanding ──
    pipeline.add_stage("understanding")
    cache_key_u = f"ds_intel_{doc_id}"
    cached = await get_cached(doc_id, doc_hash, "dataset_intelligence")
    if cached:
        ds_intel = cached
        pipeline.complete_stage("understanding", ds_intel)
    else:
        try:
            ds_intel = analyze_dataset(df)
            await set_cached(doc_id, doc_hash, "dataset_intelligence", ds_intel)
            pipeline.complete_stage("understanding", ds_intel)
        except Exception as e:
            pipeline.fail_stage("understanding", str(e))
            return pipeline.to_dict()

    # ── Stage 2: Business Context Detection ──
    pipeline.add_stage("business_context")
    pipeline.complete_stage("business_context", {
        "industry": ds_intel.get("industry"),
        "dataset_type": ds_intel.get("dataset_type"),
        "target_variable": ds_intel.get("target_variable"),
    })

    # ── Stage 3: Data Quality ──
    pipeline.add_stage("data_quality")
    cached_dq = await get_cached(doc_id, doc_hash, "data_quality")
    if cached_dq:
        dq = cached_dq
        pipeline.complete_stage("data_quality", dq)
    else:
        try:
            dq = run_data_quality_audit(df)
            await set_cached(doc_id, doc_hash, "data_quality", dq)
            pipeline.complete_stage("data_quality", dq)
        except Exception as e:
            pipeline.fail_stage("data_quality", str(e))
            dq = {"overall_score": 0, "grade": "Unknown", "issues": []}

    # ── Stage 4: Statistical Analysis ──
    pipeline.add_stage("statistical")
    cached_stat = await get_cached(doc_id, doc_hash, "statistical")
    if cached_stat:
        stat_result = cached_stat
        pipeline.complete_stage("statistical", stat_result)
    else:
        try:
            stat_result = await run_full_quality_analysis(doc_id, df)
            await set_cached(doc_id, doc_hash, "statistical", stat_result)
            pipeline.complete_stage("statistical", stat_result)
        except Exception as e:
            pipeline.fail_stage("statistical", str(e))
            stat_result = {}

    # ── Stage 5: KPI Detection & Business Analytics ──
    pipeline.add_stage("kpis")
    cached_kpi = await get_cached(doc_id, doc_hash, "kpis")
    if cached_kpi:
        biz_analytics = cached_kpi
        pipeline.complete_stage("kpis", biz_analytics)
    else:
        try:
            biz_analytics = await get_business_analytics(doc_id)
            await set_cached(doc_id, doc_hash, "kpis", biz_analytics)
            pipeline.complete_stage("kpis", biz_analytics)
        except Exception as e:
            pipeline.fail_stage("kpis", str(e))
            biz_analytics = {"kpi_summary": {}, "charts": []}

    # ── Stage 6: Executive Intelligence ──
    pipeline.add_stage("executive")
    cached_exec = await get_cached(doc_id, doc_hash, "executive")
    if cached_exec:
        exec_intel = cached_exec
        pipeline.complete_stage("executive", exec_intel)
    else:
        try:
            exec_intel = await run_executive_intelligence(doc_id)
            await set_cached(doc_id, doc_hash, "executive", exec_intel)
            pipeline.complete_stage("executive", exec_intel)
        except Exception as e:
            pipeline.fail_stage("executive", str(e))
            exec_intel = {"executive_summary": "", "key_findings": [], "risks": [], "recommendations": []}

    # ── Stage 7: Visualizations ──
    pipeline.add_stage("visualizations")
    cached_viz = await get_cached(doc_id, doc_hash, "visualizations")
    if cached_viz:
        viz = cached_viz
        pipeline.complete_stage("visualizations", viz)
    else:
        try:
            viz = await generate_smart_charts(doc_id)
            await set_cached(doc_id, doc_hash, "visualizations", viz)
            pipeline.complete_stage("visualizations", viz)
        except Exception as e:
            pipeline.fail_stage("visualizations", str(e))
            viz = {"charts": []}

    # ── Stage 8: Dashboard (consolidation) ──
    pipeline.add_stage("dashboard")
    try:
        dashboard = {
            "dataset_intelligence": ds_intel,
            "data_quality": dq,
            "statistical": stat_result.get("statistical_confidence", {}),
            "kpis": biz_analytics.get("kpi_summary", {}),
            "charts": biz_analytics.get("charts", []),
            "trend_analysis": biz_analytics.get("trend_analysis", {}),
            "comparative_analysis": biz_analytics.get("comparative_analysis", []),
            "correlations": biz_analytics.get("correlations", []),
            "executive_summary": exec_intel.get("executive_summary", ""),
            "key_findings": exec_intel.get("key_findings", []),
            "root_causes": exec_intel.get("root_causes", []),
            "risks": exec_intel.get("risks", []),
            "opportunities": exec_intel.get("opportunities", []),
            "recommendations": exec_intel.get("recommendations", []),
            "business_health": exec_intel.get("business_health", {}),
            "growth_rates": exec_intel.get("growth_rates", []),
            "regional_breakdown": exec_intel.get("regional_breakdown", []),
            "margin_analysis": exec_intel.get("margin_analysis"),
            "confidence": exec_intel.get("confidence", 0),
            "data_quality_score": dq.get("overall_score", 0),
        }
        pipeline.complete_stage("dashboard", dashboard)
    except Exception as e:
        pipeline.fail_stage("dashboard", str(e))

    return pipeline.to_dict()
