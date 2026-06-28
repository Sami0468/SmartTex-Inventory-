from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required
from app.models.fabric import Fabric, InventoryMovement
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.sales import SalesOrder
from app.models.production import ProductionOrder
from app.models.audit import AuditLog
from app.extensions import db
from app.utils.notification_generator import generate_notifications

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    generate_notifications()

    fabrics = Fabric.query.filter_by(is_active=True).all()
    low_stock = [f for f in fabrics if f.is_low_stock]
    total_stock_value = sum(f.stock_value for f in fabrics)

    total_suppliers = Supplier.query.filter_by(is_active=True).count()
    total_customers = Customer.query.filter_by(is_active=True).count()

    all_sales = SalesOrder.query.all()
    total_sales = sum(o.total_amount for o in all_sales)

    production_orders = ProductionOrder.query.all()
    active_production = [p for p in production_orders if p.status not in ("Completed",)]

    # --- Monthly sales chart (last 6 months) ---
    now = datetime.utcnow()
    months = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        months.append(month_start.strftime("%Y-%m"))
    monthly_sales = {m: 0 for m in months}
    for o in all_sales:
        if o.order_date:
            key = o.order_date.strftime("%Y-%m")
            if key in monthly_sales:
                monthly_sales[key] += o.total_amount

    # --- Inventory trend (stock value over recent movements, simplified as current snapshot by type) ---
    fabric_type_totals = {}
    for f in fabrics:
        fabric_type_totals[f.fabric_type] = fabric_type_totals.get(f.fabric_type, 0) + f.available_meters

    # --- Production analytics: status breakdown ---
    status_counts = {}
    for p in production_orders:
        status_counts[p.status] = status_counts.get(p.status, 0) + 1

    # --- Revenue growth: same monthly data ---
    revenue_growth = list(monthly_sales.values())
    revenue_growth_pct = None
    if len(revenue_growth) >= 2 and revenue_growth[-2] > 0:
        revenue_growth_pct = round((revenue_growth[-1] - revenue_growth[-2]) / revenue_growth[-2] * 100, 1)

    # --- Fabric usage statistics (OUT movements grouped by fabric, last 90 days) ---
    cutoff = now - timedelta(days=90)
    usage_movements = InventoryMovement.query.filter(
        InventoryMovement.movement_type.in_(["OUT", "PRODUCTION_USE"]),
        InventoryMovement.created_at >= cutoff
    ).all()
    usage_by_fabric = {}
    for m in usage_movements:
        if m.fabric:
            usage_by_fabric[m.fabric.name] = usage_by_fabric.get(m.fabric.name, 0) + m.quantity_meters
    top_usage = sorted(usage_by_fabric.items(), key=lambda x: -x[1])[:6]

    # --- Recent activity ---
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()

    return render_template(
        "dashboard/index.html",
        total_fabric_types=len(set(f.fabric_type for f in fabrics)),
        total_stock=sum(f.available_meters for f in fabrics),
        total_stock_value=total_stock_value,
        total_suppliers=total_suppliers,
        total_customers=total_customers,
        total_sales=total_sales,
        total_production_orders=len(production_orders),
        active_production_count=len(active_production),
        low_stock=low_stock,
        recent_logs=recent_logs,
        monthly_sales_labels=list(monthly_sales.keys()),
        monthly_sales_values=list(monthly_sales.values()),
        fabric_type_labels=list(fabric_type_totals.keys()),
        fabric_type_values=list(fabric_type_totals.values()),
        status_labels=list(status_counts.keys()),
        status_values=list(status_counts.values()),
        revenue_growth_pct=revenue_growth_pct,
        usage_labels=[u[0] for u in top_usage],
        usage_values=[u[1] for u in top_usage],
    )
