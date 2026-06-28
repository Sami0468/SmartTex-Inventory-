from datetime import datetime
from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from app.models.fabric import Fabric
from app.models.supplier import Supplier, PurchaseOrder
from app.models.warehouse import Warehouse
from app.models.sales import SalesOrder
from app.models.production import ProductionOrder
from app.models.worker import Worker, Payroll
from app.utils.pdf_generator import generate_table_report_pdf
from app.utils.excel_export import build_excel_report, build_csv_report

reports_bp = Blueprint("reports", __name__)

REPORT_TYPES = {
    "inventory": "Inventory Report",
    "suppliers": "Supplier Report",
    "warehouses": "Warehouse Report",
    "sales": "Sales Report",
    "production": "Production Report",
    "employees": "Employee Report",
    "financial": "Financial Report",
}


@reports_bp.route("/")
@login_required
def index():
    return render_template("reports/index.html", report_types=REPORT_TYPES)


def _get_report_data(report_type):
    """Returns (headers, rows) for the given report type."""
    if report_type == "inventory":
        headers = ["Fabric Code", "Name", "Type", "Available (m)", "Unit Cost", "Selling Price", "Stock Value", "Warehouse"]
        rows = [[f.fabric_code, f.name, f.fabric_type, f"{f.available_meters:.1f}",
                f"{f.unit_cost:.2f}", f"{f.selling_price:.2f}", f"{f.stock_value:.2f}",
                f.warehouse.name if f.warehouse else "—"]
               for f in Fabric.query.filter_by(is_active=True).all()]
        return headers, rows

    if report_type == "suppliers":
        headers = ["Supplier Code", "Company", "Country", "Rating", "Total Purchases", "On-Time Rate"]
        rows = [[s.supplier_code, s.company_name, s.country or "—", f"{s.rating:.1f}",
                f"{s.total_purchase_value:.2f}",
                f"{s.on_time_delivery_rate}%" if s.on_time_delivery_rate is not None else "N/A"]
               for s in Supplier.query.filter_by(is_active=True).all()]
        return headers, rows

    if report_type == "warehouses":
        headers = ["Warehouse Code", "Name", "Location", "Current Stock (m)", "Capacity (m)", "Utilization %"]
        rows = [[w.warehouse_code, w.name, w.location or "—", f"{w.current_stock_meters:.1f}",
                f"{w.capacity_meters:.1f}", f"{w.utilization_pct}%"]
               for w in Warehouse.query.filter_by(is_active=True).all()]
        return headers, rows

    if report_type == "sales":
        headers = ["Invoice #", "Customer", "Date", "Total Amount", "Payment Status"]
        rows = [[o.invoice_number, o.customer.name, o.order_date.strftime("%Y-%m-%d") if o.order_date else "—",
                f"{o.total_amount:.2f}", o.payment_status]
               for o in SalesOrder.query.order_by(SalesOrder.order_date.desc()).all()]
        return headers, rows

    if report_type == "production":
        headers = ["Code", "Product", "Fabric", "Required (m)", "Used (m)", "Waste (m)", "Status", "Deadline"]
        rows = [[p.production_code, p.product_name, p.fabric.name, f"{p.quantity_required_meters:.1f}",
                f"{p.quantity_used_meters or 0:.1f}", f"{p.waste_meters or 0:.1f}", p.status,
                p.deadline.strftime("%Y-%m-%d") if p.deadline else "—"]
               for p in ProductionOrder.query.order_by(ProductionOrder.created_at.desc()).all()]
        return headers, rows

    if report_type == "employees":
        headers = ["Code", "Name", "Department", "Designation", "Base Salary", "Date Joined"]
        rows = [[w.worker_code, w.name, w.department, w.designation or "—", f"{w.base_salary:.2f}",
                w.date_joined.strftime("%Y-%m-%d") if w.date_joined else "—"]
               for w in Worker.query.filter_by(is_active=True).all()]
        return headers, rows

    if report_type == "financial":
        headers = ["Category", "Description", "Amount (Rs.)"]
        total_sales = sum(o.total_amount for o in SalesOrder.query.all())
        total_paid_sales = sum(o.amount_paid for o in SalesOrder.query.all())
        total_purchases = sum(po.total_amount for po in PurchaseOrder.query.all())
        total_paid_purchases = sum(po.amount_paid for po in PurchaseOrder.query.all())
        total_payroll = sum(p.net_pay for p in Payroll.query.all())
        stock_value = sum(f.stock_value for f in Fabric.query.filter_by(is_active=True).all())
        rows = [
            ["Revenue", "Total Sales (Invoiced)", f"{total_sales:.2f}"],
            ["Revenue", "Total Collected from Sales", f"{total_paid_sales:.2f}"],
            ["Revenue", "Outstanding Receivables", f"{total_sales - total_paid_sales:.2f}"],
            ["Expense", "Total Purchase Orders", f"{total_purchases:.2f}"],
            ["Expense", "Total Paid to Suppliers", f"{total_paid_purchases:.2f}"],
            ["Expense", "Outstanding Payables", f"{total_purchases - total_paid_purchases:.2f}"],
            ["Expense", "Total Payroll Disbursed", f"{total_payroll:.2f}"],
            ["Assets", "Current Inventory Value", f"{stock_value:.2f}"],
        ]
        return headers, rows

    return [], []


@reports_bp.route("/<report_type>")
@login_required
def view_report(report_type):
    if report_type not in REPORT_TYPES:
        return render_template("errors/404.html"), 404
    headers, rows = _get_report_data(report_type)
    return render_template("reports/view.html", report_type=report_type,
                           title=REPORT_TYPES[report_type], headers=headers, rows=rows)


@reports_bp.route("/<report_type>/export/<fmt>")
@login_required
def export_report(report_type, fmt):
    if report_type not in REPORT_TYPES:
        return render_template("errors/404.html"), 404
    headers, rows = _get_report_data(report_type)
    title = REPORT_TYPES[report_type]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    if fmt == "pdf":
        buf = generate_table_report_pdf(title, f"Generated {datetime.utcnow().strftime('%d %b %Y')}", headers, rows)
        return send_file(buf, mimetype="application/pdf", as_attachment=True,
                         download_name=f"{report_type}_report_{timestamp}.pdf")
    if fmt == "excel":
        buf = build_excel_report(title, headers, rows, sheet_name=title)
        return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name=f"{report_type}_report_{timestamp}.xlsx")
    if fmt == "csv":
        buf = build_csv_report(headers, rows)
        return send_file(buf, mimetype="text/csv", as_attachment=True,
                         download_name=f"{report_type}_report_{timestamp}.csv")

    return render_template("errors/404.html"), 404
