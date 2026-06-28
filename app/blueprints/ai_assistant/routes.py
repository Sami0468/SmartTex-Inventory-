from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models.fabric import Fabric, InventoryMovement
from app.models.sales import SalesOrder
from app.models.supplier import Supplier
from app.ai.chat_assistant import answer_query
from app.ai import forecasting

ai_bp = Blueprint("ai_assistant", __name__)


@ai_bp.route("/chat")
@login_required
def chat():
    return render_template("ai/chat.html")


@ai_bp.route("/chat/ask", methods=["POST"])
@login_required
def ask():
    question = request.json.get("question", "") if request.is_json else request.form.get("question", "")
    if not question.strip():
        return jsonify({"answer": "Please type a question.", "data": None})
    result = answer_query(question)
    return jsonify(result)


@ai_bp.route("/insights")
@login_required
def insights():
    """AI dashboard: demand forecast, reorder suggestions, anomalies, supplier ranking."""
    # --- Sales forecast (monthly revenue, last 12 months bucketed) ---
    now = datetime.utcnow()
    months = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        months.append(month_start.strftime("%Y-%m"))

    monthly_totals = {m: 0 for m in months}
    for order in SalesOrder.query.all():
        if order.order_date:
            key = order.order_date.strftime("%Y-%m")
            if key in monthly_totals:
                monthly_totals[key] += order.total_amount

    sales_history = [(m, monthly_totals[m]) for m in months]
    sales_forecast = forecasting.forecast_series(sales_history, periods_ahead=3)

    # --- Reorder recommendations for low/at-risk stock ---
    reorder_suggestions = []
    for fabric in Fabric.query.filter_by(is_active=True).all():
        movements = fabric.movements.filter_by(movement_type="OUT").all()
        total_out = sum(m.quantity_meters for m in movements)
        months_with_data = max(len(set(m.created_at.strftime("%Y-%m") for m in movements)), 1)
        avg_monthly_usage = (total_out / months_with_data) if movements else None

        rec = forecasting.recommend_reorder_quantity(fabric, avg_monthly_usage)
        if fabric.is_low_stock or rec["recommended_meters"] > 0:
            reorder_suggestions.append({"fabric": fabric, **rec})

    # --- Anomaly detection on recent stock movements ---
    recent_movements = InventoryMovement.query.order_by(InventoryMovement.created_at.desc()).limit(60).all()
    movement_values = [m.quantity_meters if m.movement_type == "IN" else -m.quantity_meters
                       for m in reversed(recent_movements)]
    movement_labels = [f"{m.fabric.fabric_code if m.fabric else '?'} ({m.movement_type})"
                       for m in reversed(recent_movements)]
    anomaly_result = forecasting.detect_anomalies(movement_values, movement_labels)

    # --- Supplier recommendation ---
    suppliers_data = []
    for s in Supplier.query.filter_by(is_active=True).all():
        suppliers_data.append({
            "supplier": s.company_name,
            "on_time_rate": s.on_time_delivery_rate,
            "avg_unit_cost": None,
            "rating": s.rating,
            "total_orders": s.purchase_orders.count(),
        })
    supplier_ranking = forecasting.recommend_supplier(suppliers_data)

    return render_template("ai/insights.html",
                           sales_history=sales_history, sales_forecast=sales_forecast,
                           reorder_suggestions=reorder_suggestions[:10],
                           anomaly_result=anomaly_result, supplier_ranking=supplier_ranking[:8])
