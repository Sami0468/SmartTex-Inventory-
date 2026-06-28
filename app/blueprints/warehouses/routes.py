from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.warehouse import Warehouse
from app.models.audit import log_action
from app.blueprints.warehouses.forms import WarehouseForm
from app.utils.codes import next_code
from app.utils.decorators import roles_required
from app.models.user import Role

warehouses_bp = Blueprint("warehouses", __name__)


@warehouses_bp.route("/")
@login_required
def list_warehouses():
    warehouses = Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name.asc()).all()
    return render_template("warehouses/list.html", warehouses=warehouses)


@warehouses_bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def add_warehouse():
    form = WarehouseForm()
    if form.validate_on_submit():
        warehouse = Warehouse(
            warehouse_code=next_code(Warehouse, "warehouse_code", "WH"),
            name=form.name.data.strip(),
            location=form.location.data,
            capacity_meters=form.capacity_meters.data or 0,
        )
        db.session.add(warehouse)
        log_action(current_user.id, "CREATE", "Warehouse", description=f"Added warehouse {warehouse.name}")
        db.session.commit()
        flash(f"Warehouse {warehouse.name} added.", "success")
        return redirect(url_for("warehouses.list_warehouses"))
    return render_template("warehouses/form.html", form=form, mode="add")


@warehouses_bp.route("/<int:warehouse_id>")
@login_required
def view_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    fabrics = warehouse.fabrics.filter_by(is_active=True).all()
    return render_template("warehouses/view.html", warehouse=warehouse, fabrics=fabrics)


@warehouses_bp.route("/<int:warehouse_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def edit_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    form = WarehouseForm(obj=warehouse)
    if form.validate_on_submit():
        warehouse.name = form.name.data.strip()
        warehouse.location = form.location.data
        warehouse.capacity_meters = form.capacity_meters.data or 0
        log_action(current_user.id, "UPDATE", "Warehouse", entity_id=warehouse.id,
                   description=f"Updated warehouse {warehouse.name}")
        db.session.commit()
        flash("Warehouse updated.", "success")
        return redirect(url_for("warehouses.view_warehouse", warehouse_id=warehouse.id))
    return render_template("warehouses/form.html", form=form, mode="edit", warehouse=warehouse)


@warehouses_bp.route("/<int:warehouse_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    warehouse.is_active = False
    warehouse.deleted_at = datetime.utcnow()
    warehouse.deleted_by_id = current_user.id
    log_action(current_user.id, "DELETE", "Warehouse", entity_id=warehouse.id,
               description=f"Deactivated warehouse {warehouse.name}")
    db.session.commit()
    flash(f"Warehouse {warehouse.name} removed. It's preserved in History and can be restored.", "info")
    return redirect(url_for("warehouses.list_warehouses"))


@warehouses_bp.route("/<int:warehouse_id>/restore", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def restore_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    warehouse.is_active = True
    warehouse.deleted_at = None
    warehouse.deleted_by_id = None
    log_action(current_user.id, "RESTORE", "Warehouse", entity_id=warehouse.id,
               description=f"Restored warehouse {warehouse.name}")
    db.session.commit()
    flash(f"Warehouse {warehouse.name} restored.", "success")
    return redirect(request.referrer or url_for("warehouses.list_warehouses"))
