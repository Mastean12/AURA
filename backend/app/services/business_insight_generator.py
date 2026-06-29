import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _format_currency(val: float) -> str:
    if abs(val) >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if abs(val) >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:.0f}"


def _detect_trend(values: np.ndarray) -> dict:
    """Detect trend direction and magnitude from a series."""
    if len(values) < 4:
        return {"direction": "stable", "change_pct": 0.0}
    recent = values[-3:].mean()
    earlier = values[:3].mean()
    change = ((recent - earlier) / earlier) * 100 if earlier != 0 else 0
    direction = "increasing" if change > 2 else "decreasing" if change < -2 else "stable"
    return {"direction": direction, "change_pct": round(float(change), 1)}


def _compute_regional_breakdown(df: pd.DataFrame, kpi_col: str, geo_cols: list[str]) -> list[dict]:
    """Calculate regional contributions to a KPI."""
    regions = []
    for geo in geo_cols[:2]:
        if geo not in df.columns or kpi_col not in df.columns:
            continue
        try:
            grouped = df.groupby(geo)[kpi_col].sum().sort_values(ascending=False)
            total = grouped.sum()
            for region, val in grouped.head(3).items():
                pct = round(val / total * 100, 1) if total else 0
                if pct > 5:
                    regions.append({"region": str(region), "value": round(float(val), 2), "contribution_pct": pct})
        except Exception:
            pass
    return regions


def _compute_department_gaps(df: pd.DataFrame, kpi_col: str, dept_cols: list[str]) -> list[dict]:
    """Find performance gaps between best and worst departments."""
    gaps = []
    for dept in dept_cols[:2]:
        if dept not in df.columns or kpi_col not in df.columns:
            continue
        try:
            grouped = df.groupby(dept)[kpi_col].mean().sort_values(ascending=False)
            if len(grouped) >= 2:
                best, worst = str(grouped.index[0]), str(grouped.index[-1])
                best_val, worst_val = round(float(grouped.iloc[0]), 2), round(float(grouped.iloc[-1]), 2)
                gap = round((best_val - worst_val) / abs(worst_val) * 100, 1) if worst_val else 0
                gaps.append({"kpi": kpi_col, "best": best, "best_value": best_val,
                            "worst": worst, "worst_value": worst_val, "gap_pct": gap})
        except Exception:
            pass
    return gaps


def _detect_margin_squeeze(revenue_cols: list[str], profit_cols: list[str], df: pd.DataFrame) -> dict | None:
    """Detect profit margin squeeze despite revenue growth."""
    for rev in revenue_cols:
        for prof in profit_cols:
            if rev not in df.columns or prof not in df.columns:
                continue
            try:
                rev_vals = df[rev].dropna().values.astype(float)
                prof_vals = df[prof].dropna().values.astype(float)
                if len(rev_vals) < 4 or len(prof_vals) < 4:
                    continue
                rev_growth = (rev_vals[-3:].mean() / rev_vals[:3].mean() - 1) * 100
                prof_growth = (prof_vals[-3:].mean() / prof_vals[:3].mean() - 1) * 100
                if rev_growth > 5 and prof_growth < rev_growth / 2:
                    return {
                        "revenue_growth": round(rev_growth, 1),
                        "profit_growth": round(prof_growth, 1),
                        "gap": round(rev_growth - prof_growth, 1),
                    }
            except Exception:
                pass
    return None


def _top_performers(df: pd.DataFrame, kpi_col: str, cat_col: str) -> dict | None:
    """Find best and worst performing segments."""
    if kpi_col not in df.columns or cat_col not in df.columns:
        return None
    try:
        grouped = df.groupby(cat_col)[kpi_col].mean().sort_values(ascending=False)
        if len(grouped) < 2:
            return None
        return {
            "segment": cat_col,
            "best": str(grouped.index[0]),
            "best_value": round(float(grouped.iloc[0]), 2),
            "worst": str(grouped.index[-1]),
            "worst_value": round(float(grouped.iloc[-1]), 2),
            "gap": round(float(grouped.iloc[0] - grouped.iloc[-1]), 2),
        }
    except Exception:
        return None


def generate_business_insights(df: pd.DataFrame, ds: dict | None = None) -> list[dict]:
    """
    Generate deterministic business insights from actual statistical outputs.
    No AI calls. No generic summaries. All insights are data-driven.
    """
    insights = []
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist() if ds is None else \
        ds.get("categorical_columns", []) if isinstance(ds, dict) else []

    if not numeric_cols:
        return [{"type": "observation", "summary": "No numeric columns found for analysis."}]

    kpi_cols = numeric_cols[:8]
    dept_cols = [c for c in cat_cols if any(kw in c.lower() for kw in ["department", "division", "team", "region", "group"])]
    geo_cols = [c for c in cat_cols if any(kw in c.lower() for kw in ["country", "region", "city", "state", "area"])]
    revenue_like = [c for c in numeric_cols if any(kw in c.lower() for kw in ["revenue", "sales", "income", "turnover"])]
    cost_like = [c for c in numeric_cols if any(kw in c.lower() for kw in ["cost", "expense", "spend"])]
    profit_like = [c for c in numeric_cols if any(kw in c.lower() for kw in ["profit", "margin", "earnings"])]

    # ── Insight 1: Growth trends ──
    for col in kpi_cols[:3]:
        vals = df[col].dropna().values.astype(float)
        if len(vals) < 4:
            continue
        trend = _detect_trend(vals)
        if trend["direction"] != "stable":
            insights.append({
                "type": "trend",
                "metric": col,
                "direction": trend["direction"],
                "change_pct": trend["change_pct"],
                "summary": f"{col} is {trend['direction']} by {abs(trend['change_pct']):.1f}%",
            })

    # ── Insight 2: Top/bottom performers ──
    for kpi in kpi_cols[:2]:
        for cat in cat_cols[:2]:
            result = _top_performers(df, kpi, cat)
            if result and result["gap"] > 0.01:
                insights.append({
                    "type": "performance_gap",
                    "kpi": kpi,
                    "segment": result["segment"],
                    "best": result["best"],
                    "worst": result["worst"],
                    "gap": result["gap"],
                    "summary": f"'{result['best']}' leads in {kpi} ({result['best_value']}), while '{result['worst']}' trails ({result['worst_value']}) — a gap of {result['gap']:.1f}",
                })

    # ── Insight 3: Regional contributions ──
    for kpi in kpi_cols[:2]:
        regions = _compute_regional_breakdown(df, kpi, geo_cols or cat_cols[:2])
        for r in regions[:2]:
            insights.append({
                "type": "regional_contribution",
                "kpi": kpi,
                "region": r["region"],
                "pct": r["contribution_pct"],
                "summary": f"{r['region']} contributed {r['contribution_pct']}% of {kpi}",
            })

    # ── Insight 4: Department gaps ──
    for kpi in kpi_cols[:2]:
        gaps = _compute_department_gaps(df, kpi, dept_cols or cat_cols[:2])
        for g in gaps[:2]:
            insights.append({
                "type": "department_gap",
                "kpi": g["kpi"],
                "best": g["best"],
                "worst": g["worst"],
                "gap_pct": g["gap_pct"],
                "summary": f"Department gap: {g['best']} leads {g['kpi']}. {g['worst']} lags by {g['gap_pct']}%",
            })

    # ── Insight 5: Margin squeeze ──
    squeeze = _detect_margin_squeeze(revenue_like or kpi_cols, profit_like or kpi_cols[1:2], df)
    if squeeze:
        insights.append({
            "type": "margin_squeeze",
            "summary": f"Revenue grew {squeeze['revenue_growth']}% but profit only grew {squeeze['profit_growth']}% — margin gap of {squeeze['gap']}%",
            "recommendation": "Review cost structure and optimize expenses to protect margins",
        })

    # ── Insight 6: Volatility/risk signals ──
    for col in numeric_cols[:3]:
        vals = df[col].dropna().values.astype(float)
        if len(vals) < 10:
            continue
        cv = np.std(vals) / (np.mean(vals) + 1e-10)
        if cv > 1.0:
            insights.append({
                "type": "volatility_risk",
                "metric": col,
                "cv": round(float(cv), 2),
                "summary": f"{col} shows high volatility (CV={cv:.2f}) — may indicate instability",
                "recommendation": "Investigate causes of volatility and implement monitoring",
            })

    # ── Insight 7: Seasonality/pattern detection ──
    for col in numeric_cols[:2]:
        vals = df[col].dropna().values.astype(float)
        if len(vals) < 14:
            continue
        try:
            autocorr = np.corrcoef(vals[:-7], vals[7:])[0, 1]
            if not np.isnan(autocorr) and abs(autocorr) > 0.5:
                insights.append({
                    "type": "seasonal_pattern",
                    "metric": col,
                    "autocorrelation": round(float(autocorr), 2),
                    "summary": f"{col} shows weekly seasonality (autocorr={autocorr:.2f}) — predictable cycle",
                })
        except Exception:
            pass

    # ── Insight 8: KPI correlations ──
    if len(numeric_cols) >= 3:
        corr = df[numeric_cols[:6]].corr().round(3)
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                val = abs(corr.iloc[i, j])
                if val >= 0.7:
                    col_a, col_b = corr.columns[i], corr.columns[j]
                    direction = "increases" if corr.iloc[i, j] > 0 else "decreases"
                    insights.append({
                        "type": "key_correlation",
                        "col_a": col_a,
                        "col_b": col_b,
                        "r": float(corr.iloc[i, j]),
                        "summary": f"Strong correlation: {col_a} and {col_b} move together (r={corr.iloc[i, j]:.2f})",
                    })

    # Deduplicate by summary
    seen = set()
    unique = []
    for ins in insights:
        key = ins.get("summary", "")[:80]
        if key not in seen:
            seen.add(key)
            unique.append(ins)
    return unique[:15]


def generate_executive_recommendations(insights: list[dict]) -> list[dict]:
    """Generate deterministic recommendations from insights."""
    recs = []
    priorities = {"margin_squeeze": 1, "volatility_risk": 2, "trend": 3, "performance_gap": 4, "department_gap": 5,
                  "regional_contribution": 6, "seasonal_pattern": 7, "key_correlation": 8}

    for ins in sorted(insights, key=lambda i: priorities.get(i.get("type", ""), 99)):
        if ins.get("recommendation"):
            recs.append({
                "insight": ins.get("summary", ""),
                "action": ins["recommendation"],
                "priority": "High" if ins.get("type") in ("margin_squeeze", "volatility_risk") else "Medium",
            })

    if not recs:
        recs.append({"insight": "All metrics within normal range", "action": "Continue monitoring", "priority": "Low"})

    return recs


def generate_executive_summary(kpi_cols: list[str], trend_analysis: dict, insights: list[dict]) -> str:
    """Generate a deterministic executive summary from actual data."""
    parts = []
    for col in kpi_cols[:2]:
        if col in trend_analysis:
            t = trend_analysis[col]
            if t.get("change_pct", 0) > 0:
                parts.append(f"{col} grew by {abs(t['change_pct']):.1f}%")
            elif t.get("change_pct", 0) < 0:
                parts.append(f"{col} declined by {abs(t['change_pct']):.1f}%")

    for ins in insights[:3]:
        if ins["type"] == "regional_contribution":
            parts.append(f"{ins['region']} generated {ins['pct']}% of {ins['kpi']}")
        elif ins["type"] == "margin_squeeze":
            parts.append(f"Margins compressed: revenue {ins.get('summary','')}")
        elif ins["type"] == "performance_gap":
            parts.append(f"{ins['best']} leads in {ins['kpi']}, {ins['worst']} lags")

    if not parts:
        return "Analysis complete. All metrics within expected ranges."

    recs = generate_executive_recommendations(insights)
    if recs:
        parts.append(f"Recommendation: {recs[0]['action']}")

    return ". ".join(parts)
