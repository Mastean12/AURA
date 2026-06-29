import json
import logging
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from app.services.column_intelligence_service import column_intelligence_analysis
from app.services.business_context_service import detect_industry, detect_dataset_type, detect_analytical_problem

logger = logging.getLogger(__name__)

CHART_COLORS = ["#636efa", "#ef553b", "#00cc96", "#ab63fa", "#ffa15a", "#19d3f3"]
SKIP_NAMES = {"id", "_id", "uuid", "email", "phone", "fax", "password", "token", "secret", "hash", "url", "link", "img", "image", "icon", "avatar"}
SKIP_CATEGORIES = {"Identifier", "Text"}

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


def _is_skip(name: str, category: str) -> bool:
    name_lower = name.lower().strip()
    if category in SKIP_CATEGORIES:
        return True
    return any(kw in name_lower for kw in SKIP_NAMES)


def _quality_score(col: str, category: str, dtype: str, nunique: int, nrows: int) -> float:
    """Score a column's chart-worthiness from 0-100."""
    score = 0.0
    if category in ("Currency", "Percentage", "Continuous Numeric", "Discrete Numeric"):
        score += 40
    elif category == "Categorical" and 2 < nunique <= 15:
        score += 35
    elif category == "Time":
        score += 30
    elif category == "Geographic":
        score += 20
    else:
        return 0
    
    if dtype in ("int64", "float64"):
        score += 20
    if nunique >= 5:
        score += 15
    if nunique >= 20:
        score += 10
    if nrows >= 50:
        score += 10
    return min(score, 100)


def _recommend_chart_type(col: str, category: str, dtype: str, nunique: int, nrows: int,
                          has_time: bool) -> list[dict]:
    """Recommend the best chart types for a column based on business meaning."""
    name_lower = col.lower()
    recs = []

    if category == "Time" or has_time:
        recs.append({"chart_type": "line", "reason": "Trend over time", "priority": 100})
        recs.append({"chart_type": "area", "reason": "Cumulative trend", "priority": 70})
        return recs

    if category == "Currency":
        if nunique > 10:
            recs.append({"chart_type": "histogram", "reason": "Value distribution", "priority": 90})
            recs.append({"chart_type": "box", "reason": "Spread and outliers", "priority": 70})
        if nunique <= 15:
            recs.append({"chart_type": "bar", "reason": "Compare values", "priority": 80})
        return sorted(recs, key=lambda r: -r["priority"])[:3]

    if category == "Percentage":
        recs.append({"chart_type": "histogram", "reason": "Rate distribution", "priority": 90})
        recs.append({"chart_type": "box", "reason": "Rate spread", "priority": 70})
        return recs

    if category == "Continuous Numeric":
        recs.append({"chart_type": "histogram", "reason": "Distribution analysis", "priority": 95})
        recs.append({"chart_type": "box", "reason": "Outlier detection", "priority": 75})
        return recs

    if category == "Discrete Numeric":
        if nunique <= 10:
            recs.append({"chart_type": "bar", "reason": "Count comparison", "priority": 85})
        else:
            recs.append({"chart_type": "histogram", "reason": "Frequency distribution", "priority": 80})
        return recs

    if category == "Categorical":
        if nunique <= 2:
            recs.append({"chart_type": "bar", "reason": "Binary breakdown", "priority": 60})
        elif nunique <= 8:
            recs.append({"chart_type": "bar", "reason": "Category comparison", "priority": 85})
            recs.append({"chart_type": "pie", "reason": "Proportion analysis", "priority": 70})
        elif nunique <= 15:
            recs.append({"chart_type": "bar", "reason": "Top categories", "priority": 75})
        return recs

    if category == "Geographic":
        recs.append({"chart_type": "bar", "reason": "Regional comparison", "priority": 70})
        return recs

    return recs


def _render_chart(df: pd.DataFrame, col: str, chart_type: str, category: str, height: int = 280) -> dict | None:
    """Render a Plotly chart for the given column and chart type."""
    data = df[col].dropna()
    if len(data) < 3:
        return None

    fig = go.Figure()
    title = f"{col}"

    try:
        if chart_type == "line":
            date_col = None
            for c in df.columns:
                if c != col and pd.api.types.is_datetime64_any_dtype(df[c]):
                    date_col = c; break
            if date_col:
                x = df[date_col].iloc[data.index]
                fig.add_trace(go.Scatter(x=x, y=data, mode="lines", line=dict(color=CHART_COLORS[0], width=2),
                                         hovertemplate="%{x|%b %d, %Y}<br>%{y:.2f}", fill="tozeroy" if len(data) < 50 else None))
                fig.update_layout(xaxis_title=date_col, yaxis_title=col, hovermode="x unified")
            else:
                fig.add_trace(go.Scatter(x=data.index, y=data, mode="lines", line=dict(color=CHART_COLORS[0], width=1.5)))
                fig.update_layout(xaxis_title="Record", yaxis_title=col)
            fig.update_layout(xaxis=dict(rangeslider=dict(visible=True, thickness=0.05)) if len(data) > 200 else {})

        elif chart_type == "area":
            date_col = None
            for c in df.columns:
                if c != col and pd.api.types.is_datetime64_any_dtype(df[c]):
                    date_col = c; break
            if date_col:
                x = df[date_col].iloc[data.index]
            else:
                x = data.index
            fig.add_trace(go.Scatter(x=x, y=data, mode="lines", fill="tozeroy", line=dict(color=CHART_COLORS[0], width=1.5),
                                     fillcolor="rgba(99,102,241,0.12)", hovertemplate="%{y:.2f}"))
            fig.update_layout(showlegend=False)

        elif chart_type == "bar":
            counts = data.value_counts().head(15).sort_values(ascending=False)
            fig.add_trace(go.Bar(x=counts.index.tolist(), y=counts.values.tolist(), marker_color=CHART_COLORS[0],
                                 hovertemplate="%{x}<br>%{y}"))
            fig.update_layout(xaxis_title=col, yaxis_title="Count")

        elif chart_type == "pie":
            counts = data.value_counts().head(10)
            fig.add_trace(go.Pie(labels=counts.index.tolist(), values=counts.values.tolist(),
                                 marker=dict(colors=CHART_COLORS), textinfo="label+percent",
                                 hovertemplate="%{label}<br>%{value} (%{percent})"))
            fig.update_layout(showlegend=False)

        elif chart_type == "histogram":
            fig.add_trace(go.Histogram(x=data, marker_color=CHART_COLORS[0], nbinsx=min(30, len(data) // 5 or 10),
                                       hovertemplate="Range: %{x}<br>Count: %{y}"))
            fig.update_layout(xaxis_title=col, yaxis_title="Frequency", bargap=0.05)

        elif chart_type == "box":
            fig.add_trace(go.Box(y=data, name=col, marker_color=CHART_COLORS[0], boxmean="sd",
                                 hovertemplate="Min: %{minimum}<br>Q1: %{lowerfence}<br>Median: %{median}<br>Q3: %{upperfence}<br>Max: %{maximum}"))
            fig.update_layout(yaxis_title=col)

        elif chart_type == "scatter":
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            other = [c for c in numeric_cols if c != col][:1]
            if other:
                fig.add_trace(go.Scattergl(x=df[other[0]], y=data, mode="markers", marker=dict(color=CHART_COLORS[0], size=4, opacity=0.5),
                                           hovertemplate=f"{other[0]}: %{{x}}<br>{col}: %{{y}}"))
                fig.update_layout(xaxis_title=other[0], yaxis_title=col)
            else:
                return None

        else:
            return None

        fig.update_layout(title=title)
        return {
            "column": col,
            "chart_type": chart_type,
            "nunique": int(data.nunique()),
            "data": json.loads(fig.to_json()),
            "html": _to_html(fig, height),
        }
    except Exception as e:
        logger.warning("Chart render failed for %s (%s): %s", col, chart_type, e)
        return None


async def run_chart_recommendation(doc_id: int) -> dict[str, Any]:
    """Run the full Intelligent Chart Recommendation Engine."""
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

    nrows = len(df)

    # Step 1: Column Intelligence
    col_intel = column_intelligence_analysis(df)
    columns = col_intel.get("columns", [])

    # Step 2: Business Context
    industry = detect_industry(df)
    dataset_type = detect_dataset_type(df)
    problem = detect_analytical_problem(df)

    # Step 3: Detect time columns
    time_cols = [c["name"] for c in columns if c.get("category") == "Time"]

    # Step 4: Generate chart recommendations
    recommendations = []
    rendered_charts = []

    for col_info in columns:
        name = col_info["name"]
        category = col_info.get("category", "Unknown")
        dtype = col_info.get("dtype", "str")
        nunique = col_info.get("nunique", 0)

        if _is_skip(name, category):
            continue

        q_score = _quality_score(name, category, dtype, nunique, nrows)
        if q_score < 20:
            continue

        has_time = name in time_cols or any(tc for tc in time_cols)
        chart_options = _recommend_chart_type(name, category, dtype, nunique, nrows, bool(time_cols))

        for opt in chart_options:
            # Never create line charts without time data
            if opt["chart_type"] == "line" and not time_cols and not has_time:
                continue
            if opt["chart_type"] == "area" and not time_cols:
                continue

            chart = _render_chart(df, name, opt["chart_type"], category)
            if chart:
                chart["quality_score"] = round(q_score * (opt["priority"] / 100), 1)
                chart["business_reason"] = opt["reason"]
                rendered_charts.append(chart)
                if not any(r["column"] == name and r["chart_type"] == opt["chart_type"] for r in recommendations):
                    recommendations.append({
                        "column": name,
                        "chart_type": opt["chart_type"],
                        "quality_score": round(q_score * (opt["priority"] / 100), 1),
                        "business_reason": opt["reason"],
                        "category": category,
                    })

    # Sort by quality score
    recommendations.sort(key=lambda r: -r["quality_score"])
    rendered_charts.sort(key=lambda c: -c.get("quality_score", 0))

    # Correlation heatmap
    heatmap = None
    numeric_cols = [c["name"] for c in columns if c.get("category") in ("Continuous Numeric", "Discrete Numeric", "Currency", "Percentage")]
    if len(numeric_cols) >= 2:
        actual_num = [c for c in numeric_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if len(actual_num) >= 2:
            corr = df[actual_num].corr().round(3)
            fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns.tolist(), y=corr.columns.tolist(),
                                            colorscale="RdBu_r", zmin=-1, zmax=1, text=corr.values,
                                            texttemplate="%{text}", hovertemplate="%{x} vs %{y}<br>r = %{z}"))
            fig.update_layout(title="Correlation Heatmap", height=400, **DARK_LAYOUT)
            heatmap = {"data": json.loads(fig.to_json()), "html": _to_html(fig, 400)}

    return {
        "doc_id": doc_id,
        "industry": industry,
        "dataset_type": dataset_type,
        "analytical_problem": problem,
        "recommendations": recommendations[:15],
        "charts": rendered_charts[:10],
        "correlation": heatmap,
        "total_columns_evaluated": len(columns),
    }
