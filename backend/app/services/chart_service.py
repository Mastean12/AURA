import json
import logging
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.document import Document

logger = logging.getLogger(__name__)

CHART_COLORS = [
    "#636efa", "#ef553b", "#00cc96", "#ab63fa", "#ffa15a",
    "#19d3f3", "#ff6692", "#b6e880", "#ff97ff", "#fecb52",
]

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a1a1aa", size=11, family="-apple-system, BlinkMacSystemFont, sans-serif"),
    xaxis=dict(gridcolor="#27272a", zerolinecolor="#27272a", showgrid=True),
    yaxis=dict(gridcolor="#27272a", zerolinecolor="#27272a", showgrid=True),
    margin=dict(l=50, r=20, t=30, b=50),
    hovermode="closest",
)


def _to_html(fig: go.Figure, height: int = 300) -> str:
    fig.update_layout(height=height, **DARK_LAYOUT)
    return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)


def _best_chart_type(df: pd.DataFrame, col: str, n_unique: int) -> str:
    """Determine the single most appropriate chart type for a column."""
    if pd.api.types.is_numeric_dtype(df[col]):
        return "histogram"
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return "line"
    if n_unique <= 10:
        return "pie"
    return "bar"


def _make_chart(df: pd.DataFrame, col: str, chart_type: str, height: int = 300) -> dict:
    """Generate a Plotly chart for a column with the specified chart type."""
    data = df[col].dropna()
    fig = go.Figure()
    title = f"{col} ({chart_type})"

    if chart_type == "pie":
        counts = data.value_counts().head(10)
        fig.add_trace(go.Pie(labels=counts.index.tolist(), values=counts.values.tolist(),
                             marker=dict(colors=CHART_COLORS), textinfo="label+percent",
                             hovertemplate="%{label}<br>%{value} (%{percent})"))
        fig.update_layout(showlegend=False, title=title)
    elif chart_type == "bar":
        counts = data.value_counts().head(15)
        fig.add_trace(go.Bar(x=counts.index.tolist(), y=counts.values.tolist(),
                             marker_color=CHART_COLORS[0], hovertemplate="%{x}<br>%{y}"))
        fig.update_layout(xaxis_title=col, yaxis_title="Count", title=title)
    elif chart_type == "histogram":
        fig.add_trace(go.Histogram(x=data.tolist(), marker_color=CHART_COLORS[0],
                                   hovertemplate="Range: %{x}<br>Count: %{y}"))
        fig.update_layout(xaxis_title=col, yaxis_title="Frequency", title=title,
                          bargap=0.05)
    elif chart_type == "line":
        fig.add_trace(go.Scatter(x=data.index.tolist(), y=data.tolist(), mode="lines+markers",
                                 marker_color=CHART_COLORS[0], hovertemplate="Index: %{x}<br>Value: %{y}"))
        fig.update_layout(xaxis_title="Index", yaxis_title=col, title=title)

    return {
        "column": col,
        "chart_type": chart_type,
        "nunique": int(data.nunique()),
        "data": json.loads(fig.to_json()),
        "html": _to_html(fig, height),
    }


async def _parse_document(doc_id: int) -> pd.DataFrame | None:
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content or doc.content.count(",") <= 5:
        return None
    try:
        return pd.read_csv(pd.io.common.StringIO(doc.content))
    except Exception:
        return None


def _correlation_heatmap(df: pd.DataFrame) -> dict | None:
    numeric = df.select_dtypes(include=["number"]).dropna(axis=1, how="all")
    if numeric.shape[1] < 2:
        return None
    corr = numeric.corr().round(3)
    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns.tolist(), y=corr.columns.tolist(),
        colorscale="RdBu_r", zmin=-1, zmax=1, text=corr.values,
        texttemplate="%{text}", hovertemplate="%{x} vs %{y}<br>r = %{z}",
    ))
    fig.update_layout(title="Correlation Heatmap", height=400, **DARK_LAYOUT)
    return {
        "data": json.loads(fig.to_json()),
        "html": _to_html(fig, 400),
    }


async def generate_smart_charts(doc_id: int) -> dict[str, Any]:
    """
    Generate charts for the top 5 most impactful features.
    Each feature gets the single most appropriate chart type.
    """
    df = await _parse_document(doc_id)
    if df is None:
        return {"charts": [], "correlation": None}

    from app.services.dataset_intelligence_service import analyze_dataset
    ds = analyze_dataset(df)
    is_target = ds.get("target_variable")
    numeric_cols = ds.get("numeric_columns", [])
    kpi_cols = ds.get("kpi_columns", [])
    cat_cols = ds.get("categorical_columns", [])
    date_cols = ds.get("date_columns", [])
    geo_cols = ds.get("geographic_columns", [])
    skip = {"identifier", "text"}

    # Score all columns for business impact
    scored: list[tuple[float, str]] = []
    for col_info in ds.get("columns", []):
        name = col_info["name"]
        cls = col_info.get("classification", "")
        if cls in skip:
            continue
        if name == is_target:
            continue  # Don't chart the target itself

        score = 0.0
        nunique = col_info.get("nunique", 0)
        if cls == "kpi":
            score = 9.0
        elif name in numeric_cols:
            score = 7.0
        elif cls == "date":
            score = 6.0
        elif cls == "geographic":
            score = 5.0
        elif cls == "categorical":
            score = 4.0 if nunique <= 10 else 2.0

        # Boost columns strongly correlated with target
        if is_target and pd.api.types.is_numeric_dtype(df[name]) and pd.api.types.is_numeric_dtype(df[is_target]):
            try:
                corr_val = df[name].corr(df[is_target])
                if not pd.isna(corr_val):
                    score += abs(corr_val) * 5
            except Exception:
                pass

        scored.append((score, name, nunique))

    scored.sort(reverse=True)
    top_5 = scored[:5]

    charts = []
    for score, col, nunique in top_5:
        chart_type = _best_chart_type(df, col, nunique)
        charts.append(_make_chart(df, col, chart_type, 280))

    correlation = _correlation_heatmap(df)

    return {
        "charts": charts,
        "correlation": correlation,
        "target_variable": is_target,
        "total_columns_evaluated": len(scored),
    }


async def generate_charts(doc_id: int, column: str) -> dict[str, Any] | None:
    """Legacy: generate all chart types for a single column."""
    df = await _parse_document(doc_id)
    if df is None or column not in df.columns:
        return None

    nunique = int(df[column].nunique())
    result = {
        "bar": _make_chart(df, column, "bar", 280),
        "pie": _make_chart(df, column, "pie", 280) if nunique <= 10 else None,
        "line": _make_chart(df, column, "line", 280),
    }
    if pd.api.types.is_numeric_dtype(df[column]):
        result["histogram"] = _make_chart(df, column, "histogram", 280)
    return result


async def generate_all_charts(doc_id: int) -> dict[str, Any] | None:
    """Legacy: chart for best single column."""
    result = await generate_smart_charts(doc_id)
    if result.get("charts"):
        return {
            "column": result["charts"][0]["column"],
            "bar": result["charts"][0],
            "correlation": result["correlation"],
        }
    return None
