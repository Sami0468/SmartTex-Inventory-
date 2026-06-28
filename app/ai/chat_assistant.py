"""
AI Chat Assistant — answers natural-language questions about live inventory/sales data.

This is intentionally rule-based / intent-matching rather than a hosted LLM call,
since it needs to return precise, verifiable numbers from the database (stock levels,
supplier performance, sales totals) where hallucination would be unacceptable in a
factory operations tool. Pattern matching covers the question types specified in the
project brief; falls back to a helpful suggestion list if no intent matches.
"""
import re
from datetime import datetime, timedelta
from app.models.fabric import Fabric, InventoryMovement
from app.models.supplier import Supplier
from app.models.sales import SalesOrder
from app.extensions import db


def answer_query(question: str) -> dict:
    q = question.lower().strip()

    if any(p in q for p in ["low stock", "low in stock", "running low", "reorder"]):
        return _low_stock_answer()

    if any(p in q for p in ["how much stock", "stock available", "total stock", "current stock"]):
        return _total_stock_answer(q)

    if any(p in q for p in ["best supplier", "top supplier", "which supplier", "supplier perform"]):
        return _best_supplier_answer()

    if any(p in q for p in ["monthly sales", "sales summary", "sales this month", "revenue this month"]):
        return _monthly_sales_answer()

    if any(p in q for p in ["total sales", "total revenue"]):
        return _total_sales_answer()

    if any(p in q for p in ["damaged", "damage"]):
        return _damaged_stock_answer()

    return {
        "answer": "I can help with questions like stock levels, low-stock fabrics, supplier "
                  "performance, and sales summaries. Try asking something like "
                  "\"Which fabric is low in stock?\" or \"What's this month's sales summary?\"",
        "data": None,
        "suggestions": [
            "How much stock is available?",
            "Which fabric is low in stock?",
            "Which supplier performs best?",
            "Monthly sales summary",
        ],
    }


def _low_stock_answer():
    fabrics = Fabric.query.filter_by(is_active=True).all()
    low = [f for f in fabrics if f.is_low_stock]
    if not low:
        return {"answer": "No fabrics are currently below their low-stock threshold. Inventory looks healthy.",
                "data": None}

    lines = [f"{f.name} ({f.fabric_code}): {f.available_meters:.1f}m available, threshold {f.low_stock_threshold:.0f}m"
             for f in low[:10]]
    answer = f"{len(low)} fabric(s) are low in stock:\n" + "\n".join(f"• {l}" for l in lines)
    return {"answer": answer, "data": [
        {"fabric_code": f.fabric_code, "name": f.name, "available": f.available_meters,
         "threshold": f.low_stock_threshold} for f in low
    ]}


def _total_stock_answer(q):
    # If a specific fabric name is mentioned, try to match it
    fabrics = Fabric.query.filter_by(is_active=True).all()
    for f in fabrics:
        if f.name.lower() in q:
            return {"answer": f"{f.name} ({f.fabric_code}): {f.available_meters:.1f}m available "
                               f"out of {f.quantity_meters:.1f}m total.",
                    "data": {"fabric_code": f.fabric_code, "available": f.available_meters}}

    total = sum(f.available_meters for f in fabrics)
    total_value = sum(f.stock_value for f in fabrics)
    return {"answer": f"Total available stock across all fabrics: {total:,.1f} meters "
                      f"(estimated value: Rs. {total_value:,.0f}).",
            "data": {"total_meters": total, "total_value": total_value}}


def _best_supplier_answer():
    from app.ai.forecasting import recommend_supplier
    suppliers = Supplier.query.filter_by(is_active=True).all()
    data = []
    for s in suppliers:
        data.append({
            "supplier": s.company_name,
            "on_time_rate": s.on_time_delivery_rate,
            "avg_unit_cost": None,
            "rating": s.rating,
            "total_orders": s.purchase_orders.count(),
        })
    if not data:
        return {"answer": "No suppliers found in the system yet.", "data": None}

    ranked = recommend_supplier(data)
    top = next((s for s in ranked if s["score"] is not None), None)
    if not top:
        return {"answer": "No suppliers have order history yet to evaluate performance. "
                          "Rankings will appear once purchase orders are recorded.", "data": ranked}

    return {"answer": f"Based on delivery reliability, cost, and rating, {top['supplier']} is the "
                      f"top-performing supplier (score: {top['score']}/100).",
            "data": ranked[:5]}


def _monthly_sales_answer():
    now = datetime.utcnow()
    start_of_month = now.replace(day=1).date()
    orders = SalesOrder.query.filter(SalesOrder.order_date >= start_of_month).all()
    total = sum(o.total_amount for o in orders)
    count = len(orders)
    return {"answer": f"This month: {count} sales order(s) totaling Rs. {total:,.0f}.",
            "data": {"order_count": count, "total_amount": total}}


def _total_sales_answer():
    orders = SalesOrder.query.all()
    total = sum(o.total_amount for o in orders)
    return {"answer": f"Total sales recorded: {len(orders)} order(s) totaling Rs. {total:,.0f}.",
            "data": {"order_count": len(orders), "total_amount": total}}


def _damaged_stock_answer():
    fabrics = Fabric.query.filter(Fabric.damaged_meters > 0).all()
    if not fabrics:
        return {"answer": "No damaged stock currently recorded.", "data": None}
    total_damaged = sum(f.damaged_meters for f in fabrics)
    lines = [f"{f.name}: {f.damaged_meters:.1f}m damaged" for f in fabrics[:10]]
    answer = f"Total damaged stock: {total_damaged:.1f}m across {len(fabrics)} fabric(s):\n" + \
             "\n".join(f"• {l}" for l in lines)
    return {"answer": answer, "data": [{"name": f.name, "damaged": f.damaged_meters} for f in fabrics]}
