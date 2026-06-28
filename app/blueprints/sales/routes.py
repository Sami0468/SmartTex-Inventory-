from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.sales import SalesOrder, SalesOrderItem
from app.models.customer import Customer
from app.models.fabric import Fabric, InventoryMovement
from app.models.audit import log_action
from app.blueprints.sales.forms import SalesOrderForm, PaymentForm
from app.utils.codes import next_invoice_number
from app.utils.pdf_generator import generate_invoice_pdf
from app.utils.decorators import roles_required
from app.models.user import Role

sales_bp = Blueprint("sales", __name__)


@sales_bp.route("/")
@login_required
def list_orders():
    page = request.args.get("page", 1, type=int)
    pagination = SalesOrder.query.order_by(SalesOrder.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)
    return render_template("sales/list.html", orders=pagination.items, pagination=pagination)


@sales_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.SALES_MANAGER)
def new_order():
    form = SalesOrderForm()
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(is_active=True).all()]
    preselect_customer = request.args.get("customer_id", type=int)
    if request.method == "GET" and preselect_customer:
        form.customer_id.data = preselect_customer

    fabrics = Fabric.query.filter_by(is_active=True).all()

    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        if not customer_id:
            flash("Please select a customer.", "danger")
            return redirect(url_for("sales.new_order"))

        order = SalesOrder(
            invoice_number=next_invoice_number(SalesOrder),
            customer_id=customer_id,
            tax_percent=float(request.form.get("tax_percent") or 0),
            discount_amount=float(request.form.get("discount_amount") or 0),
            notes=request.form.get("notes"),
            created_by_id=current_user.id,
        )
        db.session.add(order)
        db.session.flush()

        fabric_ids = request.form.getlist("fabric_id")
        quantities = request.form.getlist("quantity_meters")
        prices = request.form.getlist("unit_price")

        items_added = 0
        stock_error = None
        for i in range(len(fabric_ids)):
            if not fabric_ids[i] or not quantities[i]:
                continue
            fabric = Fabric.query.get(int(fabric_ids[i]))
            qty = float(quantities[i])
            if not fabric or qty <= 0:
                continue
            if qty > fabric.available_meters:
                stock_error = f"Not enough stock for {fabric.name} (available: {fabric.available_meters:.1f}m)."
                break

            db.session.add(SalesOrderItem(
                sales_order_id=order.id, fabric_id=fabric.id,
                quantity_meters=qty, unit_price=float(prices[i]) if prices[i] else fabric.selling_price,
            ))
            fabric.quantity_meters -= qty
            db.session.add(InventoryMovement(
                fabric_id=fabric.id, movement_type="OUT", quantity_meters=qty,
                reference=order.invoice_number, note="Sold via sales order",
                performed_by_id=current_user.id
            ))
            items_added += 1

        if stock_error:
            db.session.rollback()
            flash(stock_error, "danger")
            return redirect(url_for("sales.new_order"))

        if items_added == 0:
            db.session.rollback()
            flash("Add at least one fabric item to the order.", "danger")
            return redirect(url_for("sales.new_order"))

        log_action(current_user.id, "CREATE", "SalesOrder", entity_id=order.id,
                   description=f"Created invoice {order.invoice_number}")
        db.session.commit()
        flash(f"Invoice {order.invoice_number} created successfully.", "success")
        return redirect(url_for("sales.view_order", order_id=order.id))

    return render_template("sales/form.html", form=form, fabrics=fabrics)


@sales_bp.route("/<int:order_id>")
@login_required
def view_order(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    payment_form = PaymentForm()
    return render_template("sales/view.html", order=order, payment_form=payment_form)


@sales_bp.route("/<int:order_id>/pdf")
@login_required
def download_invoice_pdf(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    buf = generate_invoice_pdf(order)
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"Invoice_{order.invoice_number}.pdf")


@sales_bp.route("/<int:order_id>/payment", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.SALES_MANAGER)
def record_payment(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    form = PaymentForm()
    if form.validate_on_submit():
        order.amount_paid += form.amount.data
        if order.amount_paid >= order.total_amount:
            order.payment_status = "Paid"
        elif order.amount_paid > 0:
            order.payment_status = "Partial"
        log_action(current_user.id, "UPDATE", "SalesOrder", entity_id=order.id,
                   description=f"Payment of Rs.{form.amount.data} recorded for {order.invoice_number}")
        db.session.commit()
        flash("Payment recorded.", "success")
    return redirect(url_for("sales.view_order", order_id=order.id))
