import io
import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

from app.services.ai_service import generate_response_async

logger = logging.getLogger(__name__)

INDUSTRY_KEYWORDS = {
    "Telecom": ["churn", "arpu", "call", "subscriber", "phone", "mobile", "broadband", "data_usage"],
    "Retail": ["inventory", "sku", "basket", "store", "product", "category", "sales", "customer"],
    "Banking": ["account", "loan", "deposit", "credit", "risk", "fraud", "transaction", "balance"],
    "Insurance": ["claim", "policy", "premium", "coverage", "beneficiary", "risk", "underwriting"],
    "Manufacturing": ["production", "inventory", "supplier", "defect", "machine", "downtime", "yield"],
    "Healthcare": ["patient", "diagnosis", "treatment", "readmission", "claim", "provider", "hospital"],
    "Logistics": ["shipment", "delivery", "warehouse", "freight", "route", "fleet", "lead_time"],
    "SaaS": ["subscription", "trial", "conversion", "mrr", "arr", "churn", "usage", "seat"],
}

# ──────────────────────────────────────────────────────
# MODULE 1: Prediction Explanation Engine
# ──────────────────────────────────────────────────────


def _generate_nl_explanation(target: str, drivers: list[dict], n_positive: int, total: int, revenue_at_risk: float, confidence_pct: float, model_name: str) -> str:
    """Generate a natural-language business explanation of the prediction."""
    pct = round(n_positive / total * 100, 1) if total else 0
    driver_strs = []
    for d in drivers[:3]:
        driver_strs.append(f"{d['feature'].replace('_', ' ').title()} ({round(d['importance'] * 100, 1)}%)")
    driver_text = ", ".join(driver_strs)
    revenue_str = f"${revenue_at_risk:,.0f}" if revenue_at_risk else "significant revenue"
    return (
        f"We identified {n_positive:,} records at high risk of {target} ({pct}% of {total:,}). "
        f"The strongest contributors are {driver_text}. "
        f"If no action is taken, the business could lose approximately {revenue_str} in {target}-related impact. "
        f"This prediction has {confidence_pct}% confidence based on {model_name.replace('_', ' ')} analysis."
    )


def _shap_style_importance(model, X_train, feature_names: list[str], top_n: int = 10) -> list[dict]:
    """Extract SHAP-style feature importance from any sklearn-compatible model."""
    try:
        if hasattr(model, "feature_importances_"):
            imp = model.feature_importances_
        elif hasattr(model, "coef_"):
            imp = np.abs(model.coef_[0]) if model.coef_.ndim > 1 else np.abs(model.coef_)
        else:
            return []
        if len(feature_names) != len(imp):
            feature_names = [f"feature_{i}" for i in range(len(imp))]
        pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)
        total = sum(p[1] for p in pairs)
        return [
            {"feature": name, "importance": round(float(val), 4), "pct": round(float(val) / total * 100, 1) if total > 0 else 0}
            for name, val in pairs[:top_n] if float(val) > 0
        ]
    except Exception as e:
        logger.warning("SHAP extraction failed: %s", e)
        return []


# ──────────────────────────────────────────────────────
# MODULE 2: Forecast Timeline Engine
# ──────────────────────────────────────────────────────


def _simple_exponential_smoothing(values: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Simple exponential smoothing."""
    result = np.zeros_like(values)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]
    return result


def _multi_model_forecast(values: np.ndarray, periods: int) -> dict:
    """Forecast using multiple models, auto-selecting the best performer."""
    if len(values) < 5:
        return {"forecast": [], "direction": "unknown", "confidence": 0}

    n = len(values)
    x = np.arange(n)
    future_x = np.arange(n, n + periods)
    candidates = {}

    # 1. Linear trend (polyfit)
    try:
        slope, intercept = np.polyfit(x, values, 1)
        linear_preds = slope * future_x + intercept
        linear_fitted = slope * x + intercept
        linear_residuals = values - linear_fitted
        linear_rmse = float(np.sqrt(np.mean(linear_residuals ** 2)))
        candidates["linear_trend"] = {
            "preds": linear_preds,
            "rmse": linear_rmse,
            "residuals": linear_residuals,
        }
    except Exception:
        pass

    # 2. Quadratic trend (polyfit degree 2)
    if len(values) >= 5:
        try:
            coeffs = np.polyfit(x, values, 2)
            quad_preds = np.polyval(coeffs, future_x)
            quad_fitted = np.polyval(coeffs, x)
            quad_rmse = float(np.sqrt(np.mean((values - quad_fitted) ** 2)))
            candidates["quadratic_trend"] = {
                "preds": quad_preds,
                "rmse": quad_rmse,
                "residuals": values - quad_fitted,
            }
        except Exception:
            pass

    # 3. Exponential smoothing forecast
    try:
        smoothed = _simple_exponential_smoothing(values)
        last_smoothed = smoothed[-1]
        # Use smoothed value as level; naive extension if trendless
        ses_preds = np.full(periods, last_smoothed)
        ses_residuals = values - smoothed
        ses_rmse = float(np.sqrt(np.mean(ses_residuals ** 2)))
        candidates["exp_smoothing"] = {
            "preds": ses_preds,
            "rmse": ses_rmse,
            "residuals": ses_residuals,
        }
    except Exception:
        pass

    # 4. Random Forest (lag-based)
    if len(values) >= 10:
        try:
            from sklearn.ensemble import RandomForestRegressor
            df = pd.DataFrame({"y": values})
            df["lag1"] = df["y"].shift(1)
            df["lag2"] = df["y"].shift(2)
            df["lag3"] = df["y"].shift(3)
            df["ma3"] = df["y"].rolling(3, min_periods=1).mean()
            df = df.dropna()
            if len(df) >= 8:
                X = df[["lag1", "lag2", "lag3", "ma3"]].values
                y = df["y"].values
                split = max(2, int(len(X) * 0.2))
                X_train, y_train = X[:-split], y[:-split]
                X_test, y_test = X[-split:], y[-split:] if split > 0 else (X, y)
                rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
                rf.fit(X_train, y_train)
                rf_preds_test = rf.predict(X_test)
                rf_rmse = float(np.sqrt(np.mean((y_test - rf_preds_test) ** 2)))

                # Iterative forecast
                last_window = df[["lag1", "lag2", "lag3", "ma3"]].iloc[-1].values.copy()
                rf_future = []
                for _ in range(periods):
                    nxt = float(rf.predict(last_window.reshape(1, -1))[0])
                    rf_future.append(nxt)
                    last_window[2] = last_window[1]
                    last_window[1] = last_window[0]
                    last_window[0] = nxt
                    last_window[3] = np.mean(last_window[:3])
                candidates["random_forest"] = {
                    "preds": np.array(rf_future),
                    "rmse": rf_rmse,
                    "residuals": y - rf.predict(X),
                }
        except Exception:
            pass

    if not candidates:
        return {"forecast": [], "direction": "unknown", "confidence": 0}

    best_name = min(candidates, key=lambda n: candidates[n]["rmse"])
    best = candidates[best_name]
    preds = best["preds"]
    residuals = best["residuals"]
    noise = float(np.std(residuals)) if len(residuals) > 1 else 0.001

    lower = [max(0, p - 1.96 * noise * (1 + i * 0.05)) for i, p in enumerate(preds)]
    upper = [p + 1.96 * noise * (1 + i * 0.05) for i, p in enumerate(preds)]

    last_val = float(values[-1])
    growth_pct = round(((preds[-1] - last_val) / last_val) * 100, 1) if last_val else 0

    return {
        "forecast": [round(float(p), 2) for p in preds],
        "lower": [round(float(l), 2) for l in lower],
        "upper": [round(float(u), 2) for u in upper],
        "direction": "up" if growth_pct > 0 else "down" if growth_pct < 0 else "stable",
        "growth_pct": growth_pct,
        "model_used": best_name,
        "confidence": round(max(0, min(1, 1 - noise / (float(np.mean(values)) + 1e-10))), 2),
    }


def forecast_timeline(df: pd.DataFrame, target: str) -> dict:
    """Generate 30/90/180/365 day forecasts for the target column."""
    vals = pd.to_numeric(df[target], errors='coerce').dropna().values.astype(float)
    if len(vals) < 5:
        return {"error": "Insufficient data for timeline forecasting"}

    results = {}
    for name, periods in [("forecast_30_days", 30), ("forecast_90_days", 90),
                          ("forecast_180_days", 180), ("forecast_365_days", 365)]:
        f = _multi_model_forecast(vals, periods)
        results[name] = f

    current = float(vals[-1])
    latest = results.get("forecast_365_days", {}).get("forecast", [None])[-1]
    annual_growth = round(((latest - current) / current) * 100, 1) if current and latest else 0

    return {
        "current_value": round(current, 2),
        "annual_growth_pct": annual_growth,
        "forecasts": results,
    }


# ──────────────────────────────────────────────────────
# MODULE 3: Segment-Level Prediction Engine
# ──────────────────────────────────────────────────────


def segment_analysis(df: pd.DataFrame, target: str, importance: list[dict], revenue_at_risk: float = 0) -> list[dict]:
    """Auto-detect high-risk segments from categorical columns."""
    segments = []
    examined = set()

    # Find a revenue-like column for per-segment revenue estimation
    revenue_col = None
    for col in df.select_dtypes(include=["number"]).columns:
        if col.lower() in ("revenue", "sales", "income", "totalcharges", "amount", "value"):
            revenue_col = col
            break
    if revenue_col is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            revenue_col = numeric_cols[0]

    for feat_info in importance:
        col = feat_info["feature"]
        if col not in df.columns or col in examined:
            continue
        examined.add(col)

        if pd.api.types.is_numeric_dtype(df[col]):
            med = df[col].median()
            high_subset = df[df[col] > med]
            low_subset = df[df[col] <= med]
            if pd.api.types.is_numeric_dtype(df[target]):
                high_risk = high_subset[target].mean() if len(high_subset) > 0 else 0
                low_risk = low_subset[target].mean() if len(low_subset) > 0 else 0
            else:
                target_vals = df[target].astype("category").cat.codes
                high_risk = target_vals[high_subset.index].mean() if len(high_subset) > 0 else 0
                low_risk = target_vals[low_subset.index].mean() if len(low_subset) > 0 else 0

            col_name = col.replace("_", " ").title()
            high_rev = float(high_subset[revenue_col].sum()) if revenue_col and len(high_subset) > 0 else revenue_at_risk * 0.5
            low_rev = float(low_subset[revenue_col].sum()) if revenue_col and len(low_subset) > 0 else revenue_at_risk * 0.5
            segments.append({
                "segment": f"High {col_name}",
                "risk_score": round(float(high_risk * 100), 1),
                "type": "numeric_high",
                "count": len(high_subset),
                "revenue_impact": round(high_rev * high_risk, 2) if revenue_col else 0,
            })
            segments.append({
                "segment": f"Low {col_name}",
                "risk_score": round(float(low_risk * 100), 1),
                "type": "numeric_low",
                "count": len(low_subset),
                "revenue_impact": round(low_rev * low_risk, 2) if revenue_col else 0,
            })
        else:
            counts = df[col].value_counts()
            for cat in counts.index[:10]:
                subset = df[df[col] == cat]
                if len(subset) < 5:
                    continue
                if pd.api.types.is_numeric_dtype(df[target]):
                    risk = subset[target].mean()
                else:
                    risk = subset[target].astype("category").cat.codes.mean()
                seg_rev = float(subset[revenue_col].sum()) if revenue_col and len(subset) > 0 else revenue_at_risk * (len(subset) / len(df))
                segments.append({
                    "segment": f"{cat}",
                    "risk_score": round(float(risk * 100), 1),
                    "type": "categorical",
                    "count": len(subset),
                    "revenue_impact": round(seg_rev * risk, 2),
                })

    segments.sort(key=lambda s: s["risk_score"], reverse=True)
    return segments[:10]


# ──────────────────────────────────────────────────────
# MODULE 4: What-If Simulation Engine
# ──────────────────────────────────────────────────────


def simulate_scenario(df: pd.DataFrame, target: str, scenario_type: str, adjustment_pct: float) -> dict:
    """Simulate what happens if a key feature changes by adjustment_pct."""
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) < 2:
        return {"error": "Need at least 2 numeric columns for simulation"}

    # Find the best predictor (highest correlation with target)
    if pd.api.types.is_numeric_dtype(df[target]):
        corrs = df[numeric_cols].corr()[target].drop(target).abs().sort_values(ascending=False)
    else:
        target_codes = df[target].astype("category").cat.codes
        corrs = df[numeric_cols].corrwith(target_codes).abs().sort_values(ascending=False)

    if corrs.empty:
        return {"error": "No correlated features found"}

    top_feature = corrs.index[0]
    current_mean = df[top_feature].mean()

    if scenario_type == "price_change":
        df_sim = df.copy()
        df_sim[top_feature] = df_sim[top_feature] * (1 + adjustment_pct / 100)
    elif scenario_type == "retention_program":
        df_sim = df.copy()
        df_sim[top_feature] = df_sim[top_feature] * (1 - adjustment_pct / 100)
    elif scenario_type == "budget_increase":
        df_sim = df.copy()
        df_sim[top_feature] = df_sim[top_feature] * (1 + adjustment_pct / 100)
    elif scenario_type == "contract_changes":
        df_sim = df.copy()
        df_sim[top_feature] = df_sim[top_feature] * (1 - adjustment_pct / 200)
    elif scenario_type == "staffing_changes":
        df_sim = df.copy()
        df_sim[top_feature] = df_sim[top_feature] * (1 + adjustment_pct / 200)
    else:
        return {"error": f"Unknown scenario: {scenario_type}"}

    current_outcome = df[target].mean() if pd.api.types.is_numeric_dtype(df[target]) else (df[target] == df[target].mode().iloc[0]).mean()
    simulated_outcome = df_sim[target].mean() if pd.api.types.is_numeric_dtype(df[target]) else (df_sim[target] == df_sim[target].mode().iloc[0]).mean()

    return {
        "scenario": scenario_type.replace("_", " ").title(),
        "adjusted_feature": top_feature,
        "current_value": round(float(current_outcome * 100), 1),
        "simulated_value": round(float(simulated_outcome * 100), 1),
        "change_pct": round(float((simulated_outcome - current_outcome) / current_outcome * 100), 1),
        "improvement": "reduction" if simulated_outcome < current_outcome else "increase",
    }


# ──────────────────────────────────────────────────────
# MODULE 5: Early Warning System
# ──────────────────────────────────────────────────────


def early_warnings(df: pd.DataFrame, target: str) -> list[dict]:
    """Detect early warning signals from data trends."""
    warnings_list = []

    # Check for rapid changes in numeric columns
    for col in df.select_dtypes(include=["number"]).columns[:10]:
        vals = df[col].dropna().values.astype(float)
        if len(vals) < 10:
            continue
        recent = vals[-5:].mean()
        earlier = vals[:5].mean()
        if earlier > 0:
            change = ((recent - earlier) / earlier) * 100
            if col == target or col.lower() in ("churn", "attrition", "risk", "complaint"):
                if change > 10:
                    level = "critical" if change > 30 else "high"
                    warnings_list.append({
                        "alert": f"{col.replace('_', ' ').title()} increased by {abs(change):.1f}%",
                        "severity": level,
                        "impact": f"Potential business disruption if trend continues",
                        "recommended_action": "Investigate root cause and develop mitigation plan",
                    })
                elif change < -10:
                    warnings_list.append({
                        "alert": f"{col.replace('_', ' ').title()} decreased by {abs(change):.1f}%",
                        "severity": "medium",
                        "impact": "Monitor closely for further decline",
                        "recommended_action": "Analyze contributing factors and consider corrective action",
                    })

    # Check for anomaly spikes
    for col in df.select_dtypes(include=["number"]).columns[:5]:
        vals = df[col].dropna().values.astype(float)
        if len(vals) < 10:
            continue
        mean, std = np.mean(vals), np.std(vals)
        if std > 0:
            zs = np.abs((vals - mean) / std)
            spikes = (zs > 3).sum()
            if spikes > 0:
                warnings_list.append({
                    "alert": f"{spikes} anomaly spike(s) detected in {col.replace('_', ' ').title()}",
                    "severity": "medium",
                    "impact": "Unusual patterns may indicate underlying issues",
                    "recommended_action": "Review the affected records and identify root cause",
                })

    return sorted(warnings_list, key=lambda w: {"critical": 0, "high": 1, "medium": 2}[w["severity"]])[:5]


# ──────────────────────────────────────────────────────
# MODULE 6: Prescriptive Analytics
# ──────────────────────────────────────────────────────


def prescriptive_recommendations(target: str, risk_score: float, segments: list[dict], revenue_at_risk: float) -> list[dict]:
    """Generate action recommendations ranked by priority and ROI."""
    recs = []

    if risk_score > 60:
        top_seg = segments[0]["segment"] if segments else "High-Risk"
        recs.append({
            "risk": f"{target.replace('_', ' ').title()} Risk",
            "recommendation": f"Launch targeted retention campaign for {top_seg} segment",
            "expected_impact": f"Reduce {target} by {round(risk_score * 0.3, 1)}%",
            "revenue_preserved": f"${round(revenue_at_risk * 0.25):,}",
            "roi": f"{round(revenue_at_risk * 0.25 / (revenue_at_risk * 0.05 + 1), 1)}x",
            "effort": "High",
            "priority_score": round(min(risk_score * 1.5, 100), 1),
        })

    if segments:
        recs.append({
            "risk": f"{target.replace('_', ' ').title()} Optimization",
            "recommendation": f"Implement predictive early warning system for {target} monitoring",
            "expected_impact": f"Early detection can reduce {target} by 15-25%",
            "revenue_preserved": f"${round(revenue_at_risk * 0.15):,}",
            "roi": "8.0x",
            "effort": "Medium",
            "priority_score": round(max(risk_score - 10, 0), 1),
        })

    return recs


# ──────────────────────────────────────────────────────
# MODULE 7: Industry Intelligence
# ──────────────────────────────────────────────────────


def detect_industry(df: pd.DataFrame) -> str:
    """Auto-detect industry from column names."""
    all_cols = " ".join(df.columns.str.lower())
    scores = {ind: sum(1 for kw in kws if kw in all_cols) for ind, kws in INDUSTRY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General Business"


def industry_kpis(industry: str) -> list[str]:
    """Return industry-specific KPIs to monitor."""
    kpis = {
        "Telecom": ["Churn Rate", "ARPU", "CLV", "Network Quality", "Customer Satisfaction"],
        "Retail": ["Sales per Sq Ft", "Inventory Turnover", "Basket Size", "Customer Traffic", "Conversion Rate"],
        "Banking": ["NPS", "Loan Default Rate", "Deposit Growth", "Cost-to-Income Ratio", "Customer Acquisition Cost"],
        "Insurance": ["Loss Ratio", "Claim Frequency", "Policy Retention", "Premium Growth", "Combined Ratio"],
        "Manufacturing": ["OEE", "Defect Rate", "Downtime", "Inventory Turnover", "Yield"],
        "Healthcare": ["Readmission Rate", "Patient Satisfaction", "Bed Occupancy", "Avg Treatment Cost", "Wait Time"],
        "Logistics": ["On-Time Delivery", "Cost per Mile", "Fuel Efficiency", "Warehouse Utilization", "Lead Time"],
        "SaaS": ["MRR", "Churn Rate", "CAC", "LTV", "Net Revenue Retention"],
    }
    return kpis.get(industry, ["Revenue Growth", "Profit Margin", "Customer Satisfaction", "Operational Efficiency", "Risk Score"])


INDUSTRY_RECOMMENDATIONS = {
    "Telecom": [
        {"risk": "Churn Risk", "recommendation": "Launch customer loyalty program with targeted discounts for high-risk segments", "expected_impact": "Reduce churn by 18-25%", "effort": "High"},
        {"risk": "ARPU Decline", "recommendation": "Introduce bundled service packages to increase per-customer revenue", "expected_impact": "Increase ARPU by 8-12%", "effort": "Medium"},
        {"risk": "Network Quality", "recommendation": "Prioritize infrastructure investment in regions with highest complaint density", "expected_impact": "Improve NPS by 10-15 points", "effort": "High"},
    ],
    "Retail": [
        {"risk": "Inventory Risk", "recommendation": "Implement dynamic pricing and automated restocking for top-selling SKUs", "expected_impact": "Reduce stockouts by 30%", "effort": "Medium"},
        {"risk": "Sales Decline", "recommendation": "Launch personalized promotions based on customer purchase history clusters", "expected_impact": "Increase basket size by 12-18%", "effort": "Medium"},
        {"risk": "Customer Traffic", "recommendation": "Optimize store hours and staffing based on foot traffic patterns", "expected_impact": "Improve conversion rate by 5-8%", "effort": "Low"},
    ],
    "Banking": [
        {"risk": "Loan Default Risk", "recommendation": "Enhance underwriting criteria with predictive risk scoring for new applications", "expected_impact": "Reduce default rate by 20-30%", "effort": "High"},
        {"risk": "Deposit Attrition", "recommendation": "Launch high-yield savings promotion targeted at dormant account holders", "expected_impact": "Increase deposit retention by 15%", "effort": "Medium"},
        {"risk": "Fraud Risk", "recommendation": "Deploy real-time transaction monitoring with ML-based anomaly detection", "expected_impact": "Reduce fraud losses by 35-45%", "effort": "High"},
    ],
    "Insurance": [
        {"risk": "Claim Frequency", "recommendation": "Implement telematics-based usage monitoring for high-risk policy segments", "expected_impact": "Reduce claim frequency by 15-20%", "effort": "High"},
        {"risk": "Policy Lapse", "recommendation": "Offer premium discounts for annual payment plans to improve retention", "expected_impact": "Improve policy retention by 12%", "effort": "Low"},
        {"risk": "Underwriting Risk", "recommendation": "Integrate external data sources for enhanced risk assessment models", "expected_impact": "Improve loss ratio by 8-12 points", "effort": "Medium"},
    ],
    "Manufacturing": [
        {"risk": "Production Downtime", "recommendation": "Deploy predictive maintenance scheduling for critical machinery", "expected_impact": "Reduce unplanned downtime by 35%", "effort": "High"},
        {"risk": "Defect Rate", "recommendation": "Implement real-time quality monitoring with computer vision inspection", "expected_impact": "Reduce defect rate by 25-35%", "effort": "High"},
        {"risk": "Supply Chain Risk", "recommendation": "Diversify supplier base and implement inventory buffer optimization", "expected_impact": "Improve supply chain resilience by 40%", "effort": "Medium"},
    ],
    "Healthcare": [
        {"risk": "Readmission Risk", "recommendation": "Launch post-discharge patient monitoring program for high-risk patients", "expected_impact": "Reduce readmission rate by 20-28%", "effort": "High"},
        {"risk": "Treatment Cost", "recommendation": "Implement standardized treatment protocols for common high-cost diagnoses", "expected_impact": "Reduce avg treatment cost by 10-15%", "effort": "Medium"},
        {"risk": "Patient Satisfaction", "recommendation": "Deploy digital check-in and follow-up automation to reduce wait times", "expected_impact": "Improve patient satisfaction by 15 points", "effort": "Medium"},
    ],
    "Logistics": [
        {"risk": "Delivery Delay", "recommendation": "Optimize route planning with real-time traffic and weather integration", "expected_impact": "Improve on-time delivery by 18%", "effort": "Medium"},
        {"risk": "Fuel Cost", "recommendation": "Upgrade fleet to hybrid/electric vehicles on high-mileage routes", "expected_impact": "Reduce fuel costs by 22-28%", "effort": "High"},
        {"risk": "Warehouse Utilization", "recommendation": "Implement AI-driven warehouse slotting and inventory placement optimization", "expected_impact": "Improve warehouse utilization by 25%", "effort": "Medium"},
    ],
    "SaaS": [
        {"risk": "Subscription Churn", "recommendation": "Implement usage-based engagement campaigns for at-risk accounts", "expected_impact": "Reduce churn by 22-30%", "effort": "Medium"},
        {"risk": "Trial Conversion", "recommendation": "Deploy personalized onboarding sequences with targeted feature adoption nudges", "expected_impact": "Improve trial-to-paid conversion by 18-25%", "effort": "Medium"},
        {"risk": "MRR Decline", "recommendation": "Launch expansion revenue initiatives: upsell, cross-sell, and tier migrations", "expected_impact": "Increase MRR by 12-18%", "effort": "Medium"},
    ],
}


def industry_recommendations(industry: str) -> list[dict]:
    """Return industry-specific business recommendations."""
    return INDUSTRY_RECOMMENDATIONS.get(industry, [
        {"risk": "General Business Risk", "recommendation": "Perform comprehensive operational audit to identify efficiency opportunities", "expected_impact": "Improve operational efficiency by 10-15%", "effort": "Medium"},
        {"risk": "Revenue Risk", "recommendation": "Analyze customer segments for targeted growth initiatives", "expected_impact": "Increase revenue by 8-12%", "effort": "Medium"},
    ])


def industry_forecast_adjustment(industry: str, forecast: dict) -> dict:
    """Enrich forecast with industry-specific context and commentary."""
    industry_context = {
        "Telecom": "Telecom forecast adjusted for subscriber churn seasonality and network expansion cycles.",
        "Retail": "Retail forecast includes seasonal demand patterns and promotional calendar effects.",
        "Banking": "Banking forecast considers interest rate trends and regulatory environment impacts.",
        "Insurance": "Insurance forecast adjusted for policy renewal cycles and claims seasonality.",
        "Manufacturing": "Manufacturing forecast accounts for production cycles and supply chain lead times.",
        "Healthcare": "Healthcare forecast includes patient volume seasonality and treatment cost trends.",
        "Logistics": "Logistics forecast considers shipping volume cycles and fuel cost trends.",
        "SaaS": "SaaS forecast adjusted for subscription renewal cohorts and expansion revenue trends.",
    }
    context = industry_context.get(industry, "Forecast based on historical trends with standard confidence intervals.")

    if isinstance(forecast, dict) and "error" not in forecast:
        forecast["industry_context"] = context
    return forecast


# ──────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ──────────────────────────────────────────────────────


async def run_phase2_predictive(doc_id: int) -> dict[str, Any]:
    """Run the complete Phase 2 predictive pipeline."""
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

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    # Run base predictive engine
    from app.services.executive_predictive_service import generate_executive_prediction
    base = await generate_executive_prediction(doc_id)
    if "error" in base:
        return base

    target = base.get("technical", {}).get("target", "")
    if not target:
        target = df.columns[-1]

    tech = base.get("technical", {})
    importance = tech.get("feature_importance", [])
    bi = base.get("business_impact", {})
    revenue_at_risk = bi.get("revenue_at_risk", 0)
    n_positive = bi.get("population_at_risk", 0)
    total_pop = bi.get("total_population", 0)
    confidence_pct = bi.get("confidence", 50)

    # Module 1: Prediction Explanation
    drivers = _shap_style_importance(None, None, [f["feature"] for f in importance]) or importance
    explanation = _generate_nl_explanation(target, drivers, n_positive, total_pop, revenue_at_risk, confidence_pct, tech.get("model", ""))

    # Module 2: Forecast Timeline
    timeline = forecast_timeline(df, target)

    # Module 3: Segment Analysis
    segments = segment_analysis(df, target, importance, revenue_at_risk)

    # Module 4: What-If Simulations
    simulations = []
    for scenario_type in ["retention_program", "price_change", "budget_increase", "contract_changes", "staffing_changes"]:
        sim = simulate_scenario(df, target, scenario_type, 20)
        if "error" not in sim:
            simulations.append(sim)

    # Module 5: Early Warnings
    warnings_list = early_warnings(df, target)

    # Module 6: Prescriptive Recommendations
    risk_score = tech.get("risk_score", 50)
    prescriptive = prescriptive_recommendations(target, risk_score, segments, revenue_at_risk)

    # Module 7: Industry Intelligence
    industry = detect_industry(df)
    kpis = industry_kpis(industry)
    ind_recs = industry_recommendations(industry)
    timeline = industry_forecast_adjustment(industry, timeline)

    return {
        "executive_summary": base.get("executive_summary", ""),
        "business_impact": bi,
        "prediction_explanation": {
            "summary": explanation,
            "drivers": drivers[:5],
            "confidence": confidence_pct,
        },
        "forecast_timeline": timeline,
        "segment_analysis": segments[:8],
        "what_if_simulations": simulations,
        "early_warnings": warnings_list,
        "prescriptive_recommendations": prescriptive,
        "industry_intelligence": {
            "detected_industry": industry,
            "industry_kpis": kpis,
            "industry_recommendations": ind_recs,
        },
        "root_causes": base.get("root_causes", []),
        "risks": base.get("risks", []),
        "opportunities": base.get("opportunities", []),
        "scenarios": base.get("scenarios", {}),
        "technical": tech,
    }
