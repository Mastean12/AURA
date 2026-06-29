import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.document import Document
from app.models.column_meta import ColumnMetadata
from app.services.column_intelligence_service import column_intelligence_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/columns", tags=["columns"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/analyze")
async def analyze_columns(payload: DocRequest):
    """Run Column Intelligence analysis and store results."""
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == payload.doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        raise HTTPException(status_code=404, detail="Document not found")

    import io
    import pandas as pd
    import numpy as np

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip", engine="python") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="Dataset must be tabular")

    result = column_intelligence_analysis(df)

    # Persist per-column metadata
    try:
        async with get_session_factory()() as db:
            # Delete old metadata for this doc
            old = await db.execute(select(ColumnMetadata).where(ColumnMetadata.doc_id == payload.doc_id))
            for o in old.scalars().all():
                await db.delete(o)
            
            pk_names = result.get("primary_keys", [])
            fk_names = [fk["column"] for fk in result.get("foreign_keys", [])]
            dupe_names = [d["column"] for d in result.get("duplicate_identifiers", [])]
            
            for col in result.get("columns", []):
                cm = ColumnMetadata(
                    doc_id=payload.doc_id,
                    column_name=col["name"],
                    category=col.get("category"),
                    dtype=col.get("dtype"),
                    nunique=col.get("nunique"),
                    cardinality=col.get("cardinality"),
                    missing=col.get("missing", 0),
                    missing_pct=col.get("missing_pct", 0),
                    min_val=col.get("min"),
                    max_val=col.get("max"),
                    mean_val=col.get("mean"),
                    std_val=col.get("std"),
                    is_primary_key=col["name"] in pk_names,
                    is_foreign_key=col["name"] in fk_names,
                    has_duplicates=col["name"] in dupe_names,
                    is_skewed=col.get("is_skewed", False),
                )
                db.add(cm)
            await db.commit()
    except Exception as e:
        logger.warning("Column metadata persistence failed: %s", e)

    # Convert numpy types
    def _convert(obj):
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.bool_): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    result["doc_id"] = payload.doc_id
    return _convert(result)


@router.get("/{doc_id}")
async def get_column_metadata(doc_id: int):
    """Retrieve stored column metadata for a document."""
    try:
        async with get_session_factory()() as db:
            rows = await db.execute(
                select(ColumnMetadata).where(ColumnMetadata.doc_id == doc_id)
                .order_by(ColumnMetadata.column_name)
            )
            cols = []
            for r in rows.scalars().all():
                cols.append({
                    "column_name": r.column_name,
                    "category": r.category,
                    "dtype": r.dtype,
                    "nunique": r.nunique,
                    "cardinality": r.cardinality,
                    "missing": r.missing,
                    "missing_pct": r.missing_pct,
                    "min": r.min_val,
                    "max": r.max_val,
                    "mean": r.mean_val,
                    "is_primary_key": r.is_primary_key,
                    "is_foreign_key": r.is_foreign_key,
                    "has_duplicates": r.has_duplicates,
                    "is_skewed": r.is_skewed,
                })
            return {"doc_id": doc_id, "columns": cols, "count": len(cols)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
