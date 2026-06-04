import json
import logging
from typing import Any

import pandas as pd
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

CHART_COLORS = [
    "#636efa", "#ef553b", "#00cc96", "#ab63fa", "#ffa15a",
    "#19d3f3", "#ff6692", "#b6e880", "#ff97ff", "#fecb52",
]


def _parse_document(doc_id: int) -> pd.DataFrame | None:
    from app.database.database import get_session_factory
    from app.models.document import Document
    from sqlalchemy import select
    import io

    try:
        import asyncio

        factory = get_session_factory()
        async def _fetch():
            async with factory() as db:
                result = await db.execute(
                    select(Document).where(Document.id == doc_id)
                )
                return result.scalar_one_or_none()

        doc = asyncio.run(_fetch())
    except Exception as e:
        logger.warning("DB unavailable: %s", e)
        return None

    if not doc or not doc.content:
        return None

    try:
        df = pd.read_csv(io.StringIO(doc.content))
        if df.shape[1] >= 2:
            return df
    except Exception:
        pass
    return None


def _bar_chart(df: pd.DataFrame, col: str) -> dict[str, Any]:
    counts = df[col].dropna().value_counts().head(20)
    fig = go.Figure(
        data=[
            go.Bar(
                x=list(counts.index.astype(str)),
                y=list(counts.values),
                marker_color=CHART_COLORS[: len(counts)],
            )
        ],
        layout=go.Layout(
            title=f"Top values in &quot;{col}&quot;",
            xaxis_title=col,
            yaxis_title="Count",
            template="plotly_white",
            height=400,
        ),
    )
    return json.loads(fig.to_json())


def _pie_chart(df: pd.DataFrame, col: str) -> dict[str, Any]:
    counts = df[col].dropna().value_counts().head(10)
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(counts.index.astype(str)),
                values=list(counts.values),
                marker=dict(colors=CHART_COLORS),
                textinfo="label+percent",
            )
        ],
        layout=go.Layout(
            title=f"Distribution of &quot;{col}&quot;",
            template="plotly_white",
            height=400,
        ),
    )
    return json.loads(fig.to_json())


def _line_chart(df: pd.DataFrame, col: str) -> dict[str, Any]:
    clean = df[col].dropna().reset_index(drop=True)

    if pd.api.types.is_numeric_dtype(clean):
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=list(range(len(clean))),
                    y=list(clean),
                    mode="lines+markers",
                    name=col,
                    line=dict(color="#636efa", width=2),
                    marker=dict(size=4),
                )
            ],
            layout=go.Layout(
                title=f"Trend of &quot;{col}&quot; (row order)",
                xaxis_title="Row Index",
                yaxis_title=col,
                template="plotly_white",
                height=400,
            ),
        )
    else:
        counts = clean.value_counts().head(10)
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=list(counts.index.astype(str)),
                    y=list(counts.values),
                    mode="lines+markers",
                    name=col,
                    line=dict(color="#ef553b", width=2),
                    marker=dict(size=6),
                )
            ],
            layout=go.Layout(
                title=f"Category frequency &quot;{col}&quot;",
                xaxis_title=col,
                yaxis_title="Count",
                template="plotly_white",
                height=400,
            ),
        )

    return json.loads(fig.to_json())


def generate_charts(doc_id: int, column: str) -> dict[str, Any] | None:
    df = _parse_document(doc_id)
    if df is None or column not in df.columns:
        return None

    return {
        "bar": _bar_chart(df, column),
        "pie": _pie_chart(df, column),
        "line": _line_chart(df, column),
    }
