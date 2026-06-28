from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.production import ProductionOrder
from app.models.fabric import Fabric, InventoryMovement
from app.models.audit import log_action
from app.blueprints.production.forms import ProductionOrderForm, ProductionUpdateForm
from app.utils.codes import next_code
from app.utils.decorators import roles_required
from app.models.user import Role

production_bp = Blueprint("production", __name__)


@production_bp.route("/")
@login_required
def list_orders():
    status_filter = request.args.get("status", "")
    query = ProductionOrder.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(ProductionOrder.created_at.desc()).all()
    return render_template("production/list.html", orders=orders, status_filter=status_filter,
                           statuses=ProductionOrder.STATUS_CHOICES)


@production_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def new_order():
    form = ProductionOrderForm()
    form.fabric_id.choices = [
        (f.id, f"{f.name} ({f.fabric_code}) — {f.available_meters:.1f}m available")
        for f in Fabric.query.filter_by(is_active=True).all()
    ]

    if form.validate_on_submit():
        fabric = Fabric.query.get(form.fabric_id.data)
        if form.quantity_required_meters.data > fabric.available_meters:
            flash(f"Not enough stock of {fabric.name}. Available: {fabric.available_meters:.1f}m.", "danger")
            return render_template("production/form.html", form=form, mode="add")

        order = ProductionOrder(
            production_code=next_code(ProductionOrder, "production_code", "PRD"),
            product_name=form.product_name.data.strip(),
            fabric_id=fabric.id,
            quantity_required_meters=form.quantity_required_meters.data,
            assigned_team=form.assigned_team.data,
            start_date=form.start_date.data,
            deadline=form.deadline.data,
            notes=form.notes.data,
            created_by_id=current_user.id,
        )
        # Reserve fabric for this production order
        fabric.reserved_meters += form.quantity_required_meters.data
        db.session.add(order)
        log_action(current_user.id, "CREATE", "ProductionOrder", description=f"Created {order.production_code}")
        db.session.commit()
        flash(f"Production order {order.production_code} created.", "success")
        return redirect(url_for("production.view_order", order_id=order.id))

    return render_template("production/form.html", form=form, mode="add")


@production_bp.route("/<int:order_id>")
@login_required
def view_order(order_id):
    order = ProductionOrder.query.get_or_404(order_id)
    update_form = ProductionUpdateForm(obj=order)
    return render_template("production/view.html", order=order, update_form=update_form)


@production_bp.route("/<int:order_id>/update", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def update_order(order_id):
    order = ProductionOrder.query.get_or_404(order_id)
    form = ProductionUpdateForm()

    if form.validate_on_submit():
        old_status = order.status
        new_used = form.quantity_used_meters.data or 0
        new_waste = form.waste_meters.data or 0

        # Determine incremental consumption from fabric reserved stock
        delta_used = max(new_used - (order.quantity_used_meters or 0), 0)
        delta_waste = max(new_waste - (order.waste_meters or 0), 0)
        total_delta = delta_used + delta_waste

        fabric = order.fabric
        if total_delta > 0:
            if total_delta > fabric.reserved_meters + 0.001:
                flash("Used + waste exceeds the reserved fabric quantity for this order.", "danger")
                return redirect(url_for("production.view_order", order_id=order.id))
            fabric.reserved_meters -= total_delta
            fabric.quantity_meters -= total_delta
            db.session.add(InventoryMovement(
                fabric_id=fabric.id, movement_type="PRODUCTION_USE", quantity_meters=total_delta,
                reference=order.production_code, note=f"Consumed for production order",
                performed_by_id=current_user.id
            ))

        order.quantity_used_meters = new_used
        order.waste_meters = new_waste
        order.status = form.status.data
        if form.status.data == "Completed" and old_status != "Completed":
            order.completed_date = datetime.utcnow().date()
            # Release any unused reserved fabric back to general stock
            if fabric.reserved_meters > 0:
                released = fabric.reserved_meters
                fabric.reserved_meters = 0
                db.session.add(InventoryMovement(
                    fabric_id=fabric.id, movement_type="ADJUSTMENT", quantity_meters=fabric.quantity_meters,
                    note=f"Released {released:.1f}m reserved stock on production completion",
                    performed_by_id=current_user.id
                ))

        log_action(current_user.id, "UPDATE", "ProductionOrder", entity_id=order.id,
                   description=f"Updated {order.production_code} to status {form.status.data}")
        db.session.commit()
        flash("Production order updated.", "success")
    else:
        flash("Please check the form for errors.", "danger")

    return redirect(url_for("production.view_order", order_id=order.id))
