from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.fabric import Fabric, InventoryMovement
from app.models.warehouse import Warehouse, WarehouseTransfer
from app.models.supplier import Supplier
from app.models.audit import log_action
from app.blueprints.fabrics.forms import FabricForm, StockAdjustmentForm, TransferForm
from app.utils.codes import next_code
from app.utils.codes_gen import generate_qr_code, generate_barcode
from app.utils.decorators import roles_required
from app.models.user import Role

fabrics_bp = Blueprint("fabrics", __name__)


def _populate_choices(form):
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    if hasattr(form, "supplier_id"):
        form.supplier_id.choices = [(0, "— None —")] + [
            (s.id, s.company_name) for s in Supplier.query.filter_by(is_active=True).all()
        ]


@fabrics_bp.route("/")
@login_required
def list_fabrics():
    q = request.args.get("q", "").strip()
    fabric_type = request.args.get("type", "")
    stock_filter = request.args.get("stock", "")
    page = request.args.get("page", 1, type=int)

    query = Fabric.query.filter_by(is_active=True)
    if q:
        query = query.filter(or_(Fabric.name.ilike(f"%{q}%"),
                                  Fabric.fabric_code.ilike(f"%{q}%"),
                                  Fabric.color.ilike(f"%{q}%")))
    if fabric_type:
        query = query.filter_by(fabric_type=fabric_type)

    fabrics_all = query.order_by(Fabric.date_added.desc()).all()
    if stock_filter == "low":
        fabrics_all = [f for f in fabrics_all if f.is_low_stock]

    per_page = 12
    total = len(fabrics_all)
    start = (page - 1) * per_page
    fabrics_page = fabrics_all[start:start + per_page]
    total_pages = max((total + per_page - 1) // per_page, 1)

    from app.blueprints.fabrics.forms import FABRIC_TYPES
    return render_template("fabrics/list.html", fabrics=fabrics_page, q=q,
                           fabric_type=fabric_type, stock_filter=stock_filter,
                           fabric_types=FABRIC_TYPES, page=page, total_pages=total_pages,
                           total=total)


@fabrics_bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def add_fabric():
    form = FabricForm()
    _populate_choices(form)

    if form.validate_on_submit():
        fabric = Fabric(
            fabric_code=next_code(Fabric, "fabric_code", "FB"),
            name=form.name.data.strip(),
            fabric_type=form.fabric_type.data,
            gsm=form.gsm.data,
            width_inches=form.width_inches.data,
            color=form.color.data,
            pattern=form.pattern.data,
            roll_number=form.roll_number.data,
            quantity_meters=form.quantity_meters.data,
            unit_cost=form.unit_cost.data,
            selling_price=form.selling_price.data,
            low_stock_threshold=form.low_stock_threshold.data or 100,
            warehouse_id=form.warehouse_id.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data else None,
        )
        db.session.add(fabric)
        db.session.flush()  # get fabric.id before commit

        # Initial stock-in movement
        db.session.add(InventoryMovement(
            fabric_id=fabric.id, movement_type="IN", quantity_meters=fabric.quantity_meters,
            reference="Initial Stock", note="Fabric created", performed_by_id=current_user.id
        ))

        # Generate QR + barcode
        try:
            fabric.qr_code_path = generate_qr_code(fabric.fabric_code,
                f"SmartTex Fabric: {fabric.fabric_code} | {fabric.name} | {fabric.fabric_type}")
            fabric.barcode_path = generate_barcode(fabric.fabric_code)
        except Exception:
            pass  # non-critical if barcode lib has issues with certain chars

        log_action(current_user.id, "CREATE", "Fabric", entity_id=fabric.id,
                   description=f"Added fabric {fabric.fabric_code} - {fabric.name}")
        db.session.commit()
        flash(f"Fabric {fabric.fabric_code} added successfully.", "success")
        return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))

    return render_template("fabrics/form.html", form=form, mode="add")


@fabrics_bp.route("/<int:fabric_id>")
@login_required
def view_fabric(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    movements = fabric.movements.order_by(InventoryMovement.created_at.desc()).limit(30).all()
    transfer_form = TransferForm()
    transfer_form.to_warehouse_id.choices = [
        (w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()
        if w.id != fabric.warehouse_id
    ]
    adjustment_form = StockAdjustmentForm()
    return render_template("fabrics/view.html", fabric=fabric, movements=movements,
                           transfer_form=transfer_form, adjustment_form=adjustment_form)


@fabrics_bp.route("/<int:fabric_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def edit_fabric(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    form = FabricForm(obj=fabric)
    _populate_choices(form)
    if request.method == "GET":
        form.supplier_id.data = fabric.supplier_id or 0

    if form.validate_on_submit():
        fabric.name = form.name.data.strip()
        fabric.fabric_type = form.fabric_type.data
        fabric.gsm = form.gsm.data
        fabric.width_inches = form.width_inches.data
        fabric.color = form.color.data
        fabric.pattern = form.pattern.data
        fabric.roll_number = form.roll_number.data
        fabric.unit_cost = form.unit_cost.data
        fabric.selling_price = form.selling_price.data
        fabric.low_stock_threshold = form.low_stock_threshold.data or 100
        fabric.warehouse_id = form.warehouse_id.data
        fabric.supplier_id = form.supplier_id.data if form.supplier_id.data else None
        fabric.updated_at = datetime.utcnow()
        # Note: quantity_meters intentionally NOT editable here — use Stock Adjustment
        # so every quantity change leaves a movement-ledger trail.

        log_action(current_user.id, "UPDATE", "Fabric", entity_id=fabric.id,
                   description=f"Updated fabric {fabric.fabric_code}")
        db.session.commit()
        flash("Fabric updated successfully.", "success")
        return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))

    return render_template("fabrics/form.html", form=form, mode="edit", fabric=fabric)


@fabrics_bp.route("/<int:fabric_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_fabric(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    fabric.is_active = False
    fabric.deleted_at = datetime.utcnow()
    fabric.deleted_by_id = current_user.id
    log_action(current_user.id, "DELETE", "Fabric", entity_id=fabric.id,
               description=f"Deactivated fabric {fabric.fabric_code}")
    db.session.commit()
    flash(f"Fabric {fabric.fabric_code} removed from active inventory. "
          f"It's preserved in History and can be restored.", "info")
    return redirect(url_for("fabrics.list_fabrics"))


@fabrics_bp.route("/<int:fabric_id>/restore", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def restore_fabric(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    fabric.is_active = True
    fabric.deleted_at = None
    fabric.deleted_by_id = None
    log_action(current_user.id, "RESTORE", "Fabric", entity_id=fabric.id,
               description=f"Restored fabric {fabric.fabric_code}")
    db.session.commit()
    flash(f"Fabric {fabric.fabric_code} restored to active inventory.", "success")
    return redirect(request.referrer or url_for("fabrics.list_fabrics"))


@fabrics_bp.route("/<int:fabric_id>/adjust", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def adjust_stock(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    form = StockAdjustmentForm()
    if form.validate_on_submit():
        mtype = form.movement_type.data
        qty = form.quantity_meters.data

        if mtype == "IN":
            fabric.quantity_meters += qty
        elif mtype == "OUT":
            if qty > fabric.available_meters:
                flash("Cannot remove more than available stock.", "danger")
                return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))
            fabric.quantity_meters -= qty
        elif mtype == "DAMAGE":
            if qty > fabric.available_meters:
                flash("Cannot mark more than available stock as damaged.", "danger")
                return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))
            fabric.damaged_meters += qty
        elif mtype == "ADJUSTMENT":
            fabric.quantity_meters = qty  # direct correction to a known true value

        db.session.add(InventoryMovement(
            fabric_id=fabric.id, movement_type=mtype, quantity_meters=qty,
            note=form.note.data, performed_by_id=current_user.id
        ))
        log_action(current_user.id, "UPDATE", "Fabric", entity_id=fabric.id,
                   description=f"Stock movement [{mtype}] {qty}m on {fabric.fabric_code}")
        db.session.commit()
        flash("Stock movement recorded.", "success")
    else:
        flash("Please provide a valid quantity.", "danger")

    return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))


@fabrics_bp.route("/<int:fabric_id>/transfer", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def transfer_stock(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    form = TransferForm()
    form.to_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]

    if form.validate_on_submit():
        qty = form.quantity_meters.data
        if qty > fabric.available_meters:
            flash("Cannot transfer more than available stock.", "danger")
            return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))

        to_warehouse = Warehouse.query.get_or_404(form.to_warehouse_id.data)
        from_warehouse_id = fabric.warehouse_id

        db.session.add(WarehouseTransfer(
            fabric_id=fabric.id, from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse.id, quantity_meters=qty,
            transferred_by_id=current_user.id, note=form.note.data
        ))

        # Simplification: move the whole fabric record's remaining stock,
        # or split via reducing source and creating/incrementing a record at destination.
        existing_at_dest = Fabric.query.filter_by(
            name=fabric.name, fabric_type=fabric.fabric_type, color=fabric.color,
            warehouse_id=to_warehouse.id, is_active=True
        ).first()

        fabric.quantity_meters -= qty
        if existing_at_dest:
            existing_at_dest.quantity_meters += qty
        else:
            new_fabric = Fabric(
                fabric_code=next_code(Fabric, "fabric_code", "FB"),
                name=fabric.name, fabric_type=fabric.fabric_type, gsm=fabric.gsm,
                width_inches=fabric.width_inches, color=fabric.color, pattern=fabric.pattern,
                quantity_meters=qty, unit_cost=fabric.unit_cost, selling_price=fabric.selling_price,
                low_stock_threshold=fabric.low_stock_threshold, warehouse_id=to_warehouse.id,
                supplier_id=fabric.supplier_id,
            )
            db.session.add(new_fabric)

        db.session.add(InventoryMovement(
            fabric_id=fabric.id, movement_type="TRANSFER", quantity_meters=qty,
            reference=f"To {to_warehouse.name}", note=form.note.data, performed_by_id=current_user.id
        ))

        log_action(current_user.id, "UPDATE", "Fabric", entity_id=fabric.id,
                   description=f"Transferred {qty}m of {fabric.fabric_code} to {to_warehouse.name}")
        db.session.commit()
        flash(f"Transferred {qty}m to {to_warehouse.name}.", "success")
    else:
        flash("Please select a destination and valid quantity.", "danger")

    return redirect(url_for("fabrics.view_fabric", fabric_id=fabric.id))
