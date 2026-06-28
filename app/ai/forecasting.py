"""
Forecasting engine — fabric demand & sales revenue forecasting.

Design notes:
- Real factories start with little historical data. Rather than faking confidence,
  this module is explicit about data sufficiency:
    * < AI_MIN_DATA_POINTS points  -> falls back to a simple moving-average / naive
      projection and flags `method: "naive"` with low confidence.
    * >= AI_MIN_DATA_POINTS points -> fits scikit-learn LinearRegression on a time
      index and flags `method: "linear_regression"`.
- All outputs include a `confidence` label so the UI can be honest with the user
  rather than presenting a guess as certainty.
"""
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression


def _confidence_label(n_points, min_points):
    if n_points >= min_points * 3:
        return "High"
    if n_points >= min_points:
        return "Medium"
    return "Low"


def forecast_series(history, periods_ahead=4, min_points=5):
    """
    history: list of (period_label, value) tuples ordered oldest -> newest, e.g.
             [("2026-01", 1200), ("2026-02", 1340), ...]
    Returns dict with forecast points, method used, and confidence.
    """
    values = [v for _, v in history]
    n = len(values)

    if n == 0:
        return {
            "method": "insufficient_data",
            "confidence": "None",
            "forecast": [],
            "message": "No historical data available yet. Forecast will improve as data accumulates.",
        }

    if n < min_points:
        # Naive: project the average of available points flat forward,
        # nudged by the trend between first and last point if we have >= 2.
        avg = float(np.mean(values))
        trend = 0.0
        if n >= 2:
            trend = (values[-1] - values[0]) / max(n - 1, 1)
        forecast_vals = [round(max(avg + trend * (i + 1), 0), 2) for i in range(periods_ahead)]
        return {
            "method": "naive",
            "confidence": _confidence_label(n, min_points),
            "forecast": forecast_vals,
            "message": f"Only {n} data point(s) available — using a simple trend projection. "
                       f"Accuracy improves once at least {min_points} periods of history exist.",
        }

    # Linear regression on time index
    X = np.arange(n).reshape(-1, 1)
    y = np.array(values, dtype=float)
    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(n, n + periods_ahead).reshape(-1, 1)
    preds = model.predict(future_X)
    preds = [round(max(float(p), 0), 2) for p in preds]

    r2 = model.score(X, y) if n > 2 else None

    return {
        "method": "linear_regression",
        "confidence": _confidence_label(n, min_points),
        "r_squared": round(r2, 3) if r2 is not None else None,
        "forecast": preds,
        "message": "Forecast generated using linear regression on historical trend.",
    }


def recommend_reorder_quantity(fabric, avg_monthly_usage, lead_time_days=14, safety_stock_pct=20):
    """
    Smart reorder recommendation.
    avg_monthly_usage: float meters/month derived from movement history (None if no data).
    """
    if avg_monthly_usage is None or avg_monthly_usage <= 0:
        # Fall back to threshold-based suggestion
        suggested = max(fabric.low_stock_threshold * 1.5 - fabric.available_meters, 0)
        return {
            "recommended_meters": round(suggested, 1),
            "basis": "threshold_fallback",
            "message": "No usage history yet — recommendation based on configured low-stock threshold.",
        }

    daily_usage = avg_monthly_usage / 30.0
    lead_time_consumption = daily_usage * lead_time_days
    safety_stock = avg_monthly_usage * (safety_stock_pct / 100.0)
    reorder_point = lead_time_consumption + safety_stock

    deficit = max(reorder_point - fabric.available_meters, 0)
    # Round up to nearest 10 meters for practical ordering
    recommended = float(np.ceil(deficit / 10.0) * 10) if deficit > 0 else 0.0

    return {
        "recommended_meters": recommended,
        "reorder_point_meters": round(reorder_point, 1),
        "avg_monthly_usage": round(avg_monthly_usage, 1),
        "basis": "usage_history",
        "message": "Based on average monthly consumption, lead time, and safety stock buffer.",
    }


def detect_anomalies(values, labels=None, z_threshold=2.0):
    """
    Detect unusual stock movements using a z-score against the historical distribution.
    values: list of numeric movement magnitudes (e.g. daily net stock change).
    Returns list of indices flagged as anomalous + details.
    """
    if len(values) < 4:
        return {
            "anomalies": [],
            "message": "Not enough movement history to reliably detect anomalies (need at least 4 records).",
        }

    arr = np.array(values, dtype=float)
    mean = arr.mean()
    std = arr.std()

    if std == 0:
        return {"anomalies": [], "message": "No variance in recent movements — nothing unusual detected."}

    z_scores = (arr - mean) / std
    flagged = []
    for i, z in enumerate(z_scores):
        if abs(z) >= z_threshold:
            flagged.append({
                "index": i,
                "label": labels[i] if labels else None,
                "value": float(arr[i]),
                "z_score": round(float(z), 2),
                "severity": "High" if abs(z) >= 3 else "Medium",
            })

    return {
        "anomalies": flagged,
        "mean": round(float(mean), 2),
        "std_dev": round(float(std), 2),
        "message": f"{len(flagged)} unusual movement(s) detected out of {len(values)} records."
                    if flagged else "No unusual stock movements detected.",
    }


def recommend_supplier(suppliers_data):
    """
    suppliers_data: list of dicts with keys:
        supplier, on_time_rate (0-100 or None), avg_unit_cost, rating (0-5), total_orders
    Returns ranked list using a weighted score. Transparent about weighting so it's
    not a black box recommendation.
    """
    scored = []
    valid_costs = [s["avg_unit_cost"] for s in suppliers_data if s.get("avg_unit_cost")]
    min_cost = min(valid_costs) if valid_costs else None

    for s in suppliers_data:
        if s.get("total_orders", 0) == 0:
            scored.append({**s, "score": None, "note": "No order history yet"})
            continue

        on_time = s.get("on_time_rate")
        on_time_score = (on_time / 100.0) if on_time is not None else 0.5  # neutral if unknown

        cost_score = 0.5
        if min_cost and s.get("avg_unit_cost"):
            cost_score = min(min_cost / s["avg_unit_cost"], 1.0)

        rating_score = (s.get("rating", 0) or 0) / 5.0

        # Weighted: delivery reliability 40%, cost competitiveness 35%, rating 25%
        score = round((on_time_score * 0.40 + cost_score * 0.35 + rating_score * 0.25) * 100, 1)
        scored.append({**s, "score": score, "note": None})

    scored.sort(key=lambda s: (s["score"] is None, -(s["score"] or 0)))
    return scored
