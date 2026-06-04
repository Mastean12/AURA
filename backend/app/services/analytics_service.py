import io
import logging

import pandas as pd

from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.document import Document
from app.models.schemas import AnalyticsResponse, ColumnStat

logger = logging.getLogger(__name__)

TOP_CATEGORY_LIMIT = 10


def _is_tabular(content: str) -> bool:
    first_line = content.split("\n")[0].strip()
    return "," in first_line and not first_line.startswith("---")


def _parse_tabular(content: str) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(io.StringIO(content))
        if df.shape[1] >= 2:
            return df
    except Exception:
        pass
    return None


def _analyze_column(col: pd.Series) -> ColumnStat:
    total = len(col)
    missing = int(col.isna().sum())
    name = str(col.name)

    if pd.api.types.is_numeric_dtype(col):
        clean = col.dropna()
        if len(clean) > 0:
            numeric = {
                "mean": round(float(clean.mean()), 4),
                "min": float(clean.min()),
                "max": float(clean.max()),
                "std": round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
                "median": round(float(clean.median()), 4),
            }
        else:
            numeric = {"mean": 0, "min": 0, "max": 0, "std": 0, "median": 0}
        return ColumnStat(
            name=name, dtype="numeric", missing=missing, total=total, numeric=numeric
        )

    clean = col.dropna().astype(str)
    top_counts = clean.value_counts().head(TOP_CATEGORY_LIMIT)
    categorical = {
        "unique": int(clean.nunique()),
        "top_values": [
            {"value": str(val), "count": int(cnt)}
            for val, cnt in top_counts.items()
        ],
    }
    return ColumnStat(
        name=name,
        dtype="categorical",
        missing=missing,
        total=total,
        categorical=categorical,
    )


async def get_analytics(doc_id: int) -> AnalyticsResponse:
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB unavailable: %s", e)
        doc = None

    if not doc:
        return AnalyticsResponse(
            doc_id=doc_id,
            row_count=0,
            column_count=0,
            columns=[],
        )

    content = doc.content or ""

    if not _is_tabular(content):
        lines = [l for l in content.split("\n") if l.strip()]
        return AnalyticsResponse(
            doc_id=doc_id,
            row_count=len(lines),
            column_count=1,
            columns=[
                ColumnStat(
                    name="text",
                    dtype="text",
                    missing=0,
                    total=len(lines),
                    categorical={
                        "unique": min(len(lines), 10),
                        "top_values": [],
                    },
                )
            ],
        )

    df = _parse_tabular(content)
    if df is None:
        return AnalyticsResponse(
            doc_id=doc_id,
            row_count=0,
            column_count=0,
            columns=[],
        )

    columns = [_analyze_column(df[col]) for col in df.columns]

    return AnalyticsResponse(
        doc_id=doc_id,
        row_count=len(df),
        column_count=len(df.columns),
        columns=columns,
    )
