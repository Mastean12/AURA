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


async def _parse_document(doc_id: int) -> pd.DataFrame | None:
    from app.database.database import get_session_factory
    from app.models.document import Document
    from sqlalchemy import select
    import io

    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
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


def _area_chart(df: pd.DataFrame, col: str) -> dict[str, Any]:
    clean = df[col].dropna().reset_index(drop=True)
    fig = go.Figure(
        data=[go.Scatter(x=list(range(len(clean))), y=list(clean), mode="lines", fill="tozeroy",
                         name=col, line=dict(color="#636efa", width=2))],
        layout=go.Layout(title=f"Area trend of &quot;{col}&quot;", xaxis_title="Row Index",
                         yaxis_title=col, template="plotly_white", height=400),
    )
    return json.loads(fig.to_json())


def _histogram_chart(df: pd.DataFrame, col: str) -> dict[str, Any]:
    clean = df[col].dropna()
    fig = go.Figure(
        data=[go.Histogram(x=list(clean), nbinsx=20, marker_color="#636efa")],
        layout=go.Layout(title=f"Distribution of &quot;{col}&quot;", xaxis_title=col,
                         yaxis_title="Frequency", template="plotly_white", height=400,
                         bargap=0.05),
    )
    return json.loads(fig.to_json())


def _distribution_chart(df: pd.DataFrame, col: str) -> dict[str, Any]:
    clean = df[col].dropna()
    fig = go.Figure()
    fig.add_trace(go.Box(y=list(clean), name=col, boxmean="sd", marker_color="#636efa"))
    fig.update_layout(title=f"Distribution of &quot;{col}&quot;", yaxis_title=col,
                      template="plotly_white", height=400)
    return json.loads(fig.to_json())


def _correlation_heatmap(df: pd.DataFrame) -> dict[str, Any] | None:
    num_df = df.select_dtypes(include=["number"]).dropna(axis=1, how="all")
    if num_df.shape[1] < 2:
        return None
    corr = num_df.corr(numeric_only=True)
    fig = go.Figure(
        data=go.Heatmap(z=corr.values, x=list(corr.columns), y=list(corr.columns),
                        colorscale="RdBu", zmid=0, text=[[f"{v:.2f}" for v in row] for row in corr.values],
                        texttemplate="%{text}", textfont={"size": 10}),
        layout=go.Layout(title="Correlation Heatmap", template="plotly_white", height=450),
    )
    return json.loads(fig.to_json())


async def generate_charts(doc_id: int, column: str) -> dict[str, Any] | None:
    df = await _parse_document(doc_id)
    if df is None or column not in df.columns:
        return None

    result = {
        "bar": _bar_chart(df, column),
        "pie": _pie_chart(df, column),
        "line": _line_chart(df, column),
        "area": _area_chart(df, column),
    }

    if pd.api.types.is_numeric_dtype(df[column]):
        result["histogram"] = _histogram_chart(df, column)
        result["distribution"] = _distribution_chart(df, column)
    else:
        result["histogram"] = None
        result["distribution"] = None

    return result


async def generate_all_charts(doc_id: int) -> dict[str, Any] | None:
    df = await _parse_document(doc_id)
    if df is None:
        return None

    # Intelligent column selection - skip IDs, dates, high-cardinality text
    from app.services.dataset_intelligence_service import analyze_dataset
    ds = analyze_dataset(df)
    skip_types = {"identifier", "text"}
    priority_types = {"kpi", "numeric", "categorical"}

    best_col = None
    for col_info in ds.get("columns", []):
        if col_info.get("classification") in priority_types and col_info.get("classification") not in skip_types:
            best_col = col_info["name"]
            break
    if not best_col:
        for col_info in ds.get("columns", []):
            if col_info.get("classification") not in skip_types:
                best_col = col_info["name"]
                break
    if not best_col:
        best_col = df.columns[0]

    result = await generate_charts(doc_id, best_col) or {}
    result["correlation"] = _correlation_heatmap(df)
    result["column"] = best_col
    result["dataset_type"] = ds.get("dataset_type")
    return result
