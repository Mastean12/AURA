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


def _compute_feature_importance(df: pd.DataFrame, target: str, skip_set: set | None = None) -> list[dict]:
    """
    Compute statistical feature importance of every column against the target.
    Returns list of {name, importance, method} sorted by importance descending.
    """
    import numpy as np
    from app.services.dataset_intelligence_service import analyze_dataset

    if skip_set is None:
        skip_set = {"identifier", "text"}

    # Classify columns to know which to skip
    ds = analyze_dataset(df)
    col_map = {c["name"]: c.get("classification", "") for c in ds.get("columns", [])}

    results = []
    target_is_num = pd.api.types.is_numeric_dtype(df[target])

    for col in df.columns:
        if col == target:
            continue
        if col_map.get(col, "") in skip_set:
            continue

        col_data = df[col].dropna()
        if len(col_data) < 5:
            continue

        col_is_num = pd.api.types.is_numeric_dtype(df[col])
        importance = 0.0
        method = "none"

        # Find common indices where both exist
        common = df[[col, target]].dropna()
        if len(common) < 5:
            continue

        if col_is_num and target_is_num:
            # Pearson correlation for numeric vs numeric
            try:
                r = common[col].corr(common[target])
                if not np.isnan(r):
                    importance = abs(r)
                    method = f"pearson r={r:.3f}"
            except Exception:
                pass

        elif col_is_num and not target_is_num:
            # ANOVA-style: how well does the numeric feature separate the target groups
            try:
                groups = [g.dropna().values for _, g in common.groupby(target)[col]]
                if len(groups) >= 2:
                    from scipy.stats import f_oneway
                    f_stat, p_val = f_oneway(*groups)
                    if not np.isnan(f_stat) and f_stat > 0:
                        importance = min(1.0, 1.0 - (p_val / 10.0) if not np.isnan(p_val) else 0.5)
                        method = f"anova F={f_stat:.1f}, p={p_val:.4f}"
            except Exception:
                pass

        elif not col_is_num and target_is_num:
            # Correlation ratio: how much of target variance is explained by category
            try:
                grand_mean = common[target].mean()
                ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for _, g in common.groupby(col)[target])
                ss_total = sum((common[target] - grand_mean) ** 2)
                eta_sq = ss_between / ss_total if ss_total > 0 else 0
                importance = min(1.0, float(eta_sq))
                method = f"eta_sq={eta_sq:.3f}"
            except Exception:
                pass

        else:
            # Categorical vs categorical: Cramer's V approximation
            try:
                ct = pd.crosstab(common[col], common[target])
                if ct.size > 0:
                    chi2 = (ct.values - ct.values.mean()) ** 2 / (ct.values.mean() + 1e-10)
                    chi2_sum = chi2.sum()
                    n = ct.values.sum()
                    k = min(ct.shape) - 1
                    v = np.sqrt(chi2_sum / (n * max(k, 1))) if n > 0 and k > 0 else 0
                    importance = min(1.0, float(v))
                    method = f"cramer_v={v:.3f}"
            except Exception:
                pass

        if importance > 0:
            results.append({"name": col, "importance": round(importance, 4), "method": method})

    results.sort(key=lambda r: r["importance"], reverse=True)
    return results


async def generate_smart_charts(doc_id: int) -> dict[str, Any]:
    """
    Generate charts for the top 6 most important features.
    Uses statistical feature importance (correlation, ANOVA, eta-squared, Cramer's V).
    """
    df = await _parse_document(doc_id)
    if df is None:
        return {"charts": [], "correlation": None}

    from app.services.dataset_intelligence_service import analyze_dataset
    ds = analyze_dataset(df)
    is_target = ds.get("target_variable")
    skip = {"identifier", "text"}

    if not is_target:
        # Fall back to column scoring when no target is detected
        scored: list[tuple[float, str]] = []
        for col_info in ds.get("columns", []):
            name = col_info["name"]
            cls = col_info.get("classification", "")
            if cls in skip:
                continue
            nunique = col_info.get("nunique", 0)
            score = 9.0 if cls == "kpi" else 7.0 if cls == "numeric" else 6.0 if cls == "date" else 5.0 if cls == "geographic" else 4.0 if nunique <= 10 else 2.0
            scored.append((score, name, nunique))
        scored.sort(reverse=True)
        rankings = [{"name": s[1], "importance": s[0], "method": "column_type"} for s in scored[:6]]
    else:
        rankings = _compute_feature_importance(df, is_target, skip_set=skip)
        # If few features found, pad with highest-column-type-scored remaining
        if len(rankings) < 6:
            existing_names = {r["name"] for r in rankings}
            for col_info in ds.get("columns", []):
                if len(rankings) >= 6:
                    break
                name = col_info["name"]
                if name == is_target or name in existing_names or col_info.get("classification") in skip:
                    continue
                rankings.append({"name": name, "importance": 0.0, "method": "not_available"})

    top_6 = rankings[:6]

    charts = []
    for r in top_6:
        col = r["name"]
        nunique = int(df[col].nunique())
        chart_type = _best_chart_type(df, col, nunique)
        chart = _make_chart(df, col, chart_type, 280)
        chart["importance"] = r["importance"]
        chart["importance_method"] = r["method"]
        # Update chart title with importance information
        importance_pct = round(r["importance"] * 100, 1)
        fig_data = chart.get("data", {})
        if fig_data:
            layout = fig_data.get("layout", {})
            layout["title"] = f"{col} — Importance: {importance_pct}%"
            fig_data["layout"] = layout
            chart["data"] = fig_data
            # Re-render HTML with updated title
            import plotly.graph_objects as go
            fig = go.Figure(fig_data)
            chart["html"] = _to_html(fig, 280)
        charts.append(chart)

    correlation = _correlation_heatmap(df)

    return {
        "charts": charts,
        "correlation": correlation,
        "target_variable": is_target,
        "total_columns_evaluated": len(rankings),
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
