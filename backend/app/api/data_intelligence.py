import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.document import Document
from app.models.dataset_meta import DatasetMetadata
from app.services.dataset_intelligence_service import analyze_dataset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-intelligence", tags=["data-intelligence"])


class MetadataUpdate(BaseModel):
    industry: str | None = None
    dataset_type: str | None = None
    target_variable: str | None = None
    time_column: str | None = None
    kpis: list[str] | None = None
    identifier_columns: list[str] | None = None


@router.get("/{doc_id}")
async def get_dataset_intelligence(doc_id: int):
    """Analyze dataset and return intelligence metadata."""
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        raise HTTPException(status_code=404, detail="Document not found")

    import io
    import pandas as pd
    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="Dataset must be tabular with 2+ columns")

    analysis = analyze_dataset(df)

    time_col = analysis["date_columns"][0] if analysis.get("date_columns") else None

    # Store in PostgreSQL
    try:
        async with get_session_factory()() as db:
            existing = await db.execute(select(DatasetMetadata).where(DatasetMetadata.doc_id == doc_id))
            meta = existing.scalar_one_or_none()
            if meta and not meta.overridden:
                meta.industry = analysis["industry"]
                meta.dataset_type = analysis["dataset_type"]
                meta.target_variable = analysis["target_variable"]
                meta.time_column = time_col
                meta.kpis = json.dumps([k["name"] for k in analysis.get("kpi_details", [])])
                meta.identifier_columns = json.dumps(analysis.get("identifier_columns", []))
            elif not meta:
                meta = DatasetMetadata(
                    doc_id=doc_id, industry=analysis["industry"],
                    dataset_type=analysis["dataset_type"],
                    target_variable=analysis["target_variable"],
                    time_column=time_col,
                    kpis=json.dumps([k["name"] for k in analysis.get("kpi_details", [])]),
                    identifier_columns=json.dumps(analysis.get("identifier_columns", [])),
                )
                db.add(meta)
            await db.commit()
    except Exception as e:
        logger.warning("Metadata storage failed: %s", e)

    return {
        "doc_id": doc_id,
        "industry": analysis["industry"],
        "dataset_type": analysis["dataset_type"],
        "target_variable": analysis["target_variable"],
        "time_column": time_col,
        "kpi_columns": analysis.get("kpi_columns", []),
        "kpi_details": analysis.get("kpi_details", []),
        "currency_columns": analysis.get("currency_columns", []),
        "identifier_columns": analysis.get("identifier_columns", []),
        "date_columns": analysis.get("date_columns", []),
        "numeric_columns": analysis.get("numeric_columns", []),
        "categorical_columns": analysis.get("categorical_columns", []),
        "geographic_columns": analysis.get("geographic_columns", []),
        "text_columns": analysis.get("text_columns", []),
        "relationships": analysis.get("relationships", []),
        "column_count": analysis["column_count"],
        "row_count": analysis["row_count"],
    }


@router.put("/{doc_id}")
async def update_metadata(doc_id: int, payload: MetadataUpdate):
    """Override automatically detected metadata."""
    try:
        async with get_session_factory()() as db:
            existing = await db.execute(select(DatasetMetadata).where(DatasetMetadata.doc_id == doc_id))
            meta = existing.scalar_one_or_none()
            if not meta:
                meta = DatasetMetadata(doc_id=doc_id)
                db.add(meta)
            meta.overridden = True
            if payload.industry is not None:
                meta.industry = payload.industry
            if payload.dataset_type is not None:
                meta.dataset_type = payload.dataset_type
            if payload.target_variable is not None:
                meta.target_variable = payload.target_variable
            if payload.time_column is not None:
                meta.time_column = payload.time_column
            if payload.kpis is not None:
                meta.kpis = json.dumps(payload.kpis)
            if payload.identifier_columns is not None:
                meta.identifier_columns = json.dumps(payload.identifier_columns)
            await db.commit()
        return {"detail": "Metadata updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
