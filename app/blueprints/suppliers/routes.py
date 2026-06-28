from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.supplier import Supplier, PurchaseOrder, PurchaseOrderItem
from app.models.fabric import Fabric
from app.models.audit import log_action
from app.blueprints.suppliers.forms import SupplierForm, PurchaseOrderForm, PaymentForm
from app.utils.codes import next_code
from app.utils.decorators import roles_required
from app.models.user import Role

suppliers_bp = Blueprint("suppliers", __name__)


@suppliers_bp.route("/")
@login_required
def list_suppliers():
    q = request.args.get("q", "").strip()
    query = Supplier.query.filter_by(is_active=True)
    if q:
        query = query.filter(or_(Supplier.company_name.ilike(f"%{q}%"),
                                  Supplier.contact_person.ilike(f"%{q}%"),
                                  Supplier.country.ilike(f"%{q}%")))
    suppliers = query.order_by(Supplier.company_name.asc()).all()
    return render_template("suppliers/list.html", suppliers=suppliers, q=q)


@suppliers_bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            supplier_code=next_code(Supplier, "supplier_code", "SUP"),
            company_name=form.company_name.data.strip(),
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            country=form.country.data,
            rating=form.rating.data or 0,
        )
        db.session.add(supplier)
        log_action(current_user.id, "CREATE", "Supplier", description=f"Added supplier {supplier.company_name}")
        db.session.commit()
        flash(f"Supplier {supplier.company_name} added.", "success")
        return redirect(url_for("suppliers.view_supplier", supplier_id=supplier.id))
    return render_template("suppliers/form.html", form=form, mode="add")


@suppliers_bp.route("/<int:supplier_id>")
@login_required
def view_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    purchase_orders = supplier.purchase_orders.order_by(PurchaseOrder.order_date.desc()).all()
    fabrics = supplier.fabrics.filter_by(is_active=True).all()
    return render_template("suppliers/view.html", supplier=supplier,
                           purchase_orders=purchase_orders, fabrics=fabrics)


@suppliers_bp.route("/<int:supplier_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    if form.validate_on_submit():
        supplier.company_name = form.company_name.data.strip()
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data
        supplier.country = form.country.data
        supplier.rating = form.rating.data or 0
        log_action(current_user.id, "UPDATE", "Supplier", entity_id=supplier.id,
                   description=f"Updated supplier {supplier.company_name}")
        db.session.commit()
        flash("Supplier updated.", "success")
        return redirect(url_for("suppliers.view_supplier", supplier_id=supplier.id))
    return render_template("suppliers/form.html", form=form, mode="edit", supplier=supplier)


@suppliers_bp.route("/<int:supplier_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    supplier.deleted_at = datetime.utcnow()
    supplier.deleted_by_id = current_user.id
    log_action(current_user.id, "DELETE", "Supplier", entity_id=supplier.id,
               description=f"Deactivated supplier {supplier.company_name}")
    db.session.commit()
    flash(f"Supplier {supplier.company_name} removed. It's preserved in History and can be restored.", "info")
    return redirect(url_for("suppliers.list_suppliers"))


@suppliers_bp.route("/<int:supplier_id>/restore", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def restore_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = True
    supplier.deleted_at = None
    supplier.deleted_by_id = None
    log_action(current_user.id, "RESTORE", "Supplier", entity_id=supplier.id,
               description=f"Restored supplier {supplier.company_name}")
    db.session.commit()
    flash(f"Supplier {supplier.company_name} restored.", "success")
    return redirect(request.referrer or url_for("suppliers.list_suppliers"))


@suppliers_bp.route("/<int:supplier_id>/purchase-orders/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def new_purchase_order(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    form = PurchaseOrderForm(supplier_id=supplier.id)
    form.supplier_id.choices = [(s.id, s.company_name) for s in Supplier.query.filter_by(is_active=True).all()]
    fabrics = Fabric.query.filter_by(is_active=True).all()

    if request.method == "POST":
        po = PurchaseOrder(
            po_number=next_code(PurchaseOrder, "po_number", "PO"),
            supplier_id=supplier.id,
            expected_date=request.form.get("expected_date") or None,
            notes=request.form.get("notes"),
        )
        db.session.add(po)
        db.session.flush()

        fabric_ids = request.form.getlist("fabric_id")
        descriptions = request.form.getlist("description")
        quantities = request.form.getlist("quantity_meters")
        costs = request.form.getlist("unit_cost")

        items_added = 0
        for i in range(len(quantities)):
            if not quantities[i]:
                continue
            db.session.add(PurchaseOrderItem(
                purchase_order_id=po.id,
                fabric_id=int(fabric_ids[i]) if fabric_ids[i] else None,
                description=descriptions[i],
                quantity_meters=float(quantities[i]),
                unit_cost=float(costs[i]) if costs[i] else 0,
            ))
            items_added += 1

        if items_added == 0:
            db.session.rollback()
            flash("Add at least one item to the purchase order.", "danger")
            return redirect(url_for("suppliers.new_purchase_order", supplier_id=supplier.id))

        log_action(current_user.id, "CREATE", "PurchaseOrder", entity_id=po.id,
                   description=f"Created PO {po.po_number} for {supplier.company_name}")
        db.session.commit()
        flash(f"Purchase order {po.po_number} created.", "success")
        return redirect(url_for("suppliers.view_supplier", supplier_id=supplier.id))

    return render_template("suppliers/po_form.html", form=form, supplier=supplier, fabrics=fabrics)


@suppliers_bp.route("/purchase-orders/<int:po_id>")
@login_required
def view_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    payment_form = PaymentForm()
    return render_template("suppliers/po_view.html", po=po, payment_form=payment_form)


@suppliers_bp.route("/purchase-orders/<int:po_id>/status", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def update_po_status(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    new_status = request.form.get("status")
    if new_status in PurchaseOrder.STATUS_CHOICES:
        po.status = new_status
        if new_status == "Received":
            po.delivered_date = datetime.utcnow().date()
            # Add stock to inventory for each item with a linked fabric
            from app.models.fabric import InventoryMovement
            for item in po.items:
                if item.fabric_id:
                    fabric = Fabric.query.get(item.fabric_id)
                    if fabric:
                        fabric.quantity_meters += item.quantity_meters
                        db.session.add(InventoryMovement(
                            fabric_id=fabric.id, movement_type="IN",
                            quantity_meters=item.quantity_meters,
                            reference=po.po_number, note="Purchase order received",
                            performed_by_id=current_user.id
                        ))
        log_action(current_user.id, "UPDATE", "PurchaseOrder", entity_id=po.id,
                   description=f"PO {po.po_number} status changed to {new_status}")
        db.session.commit()
        flash(f"Purchase order marked as {new_status}.", "success")
    return redirect(url_for("suppliers.view_purchase_order", po_id=po.id))


@suppliers_bp.route("/purchase-orders/<int:po_id>/payment", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.INVENTORY_MANAGER)
def record_payment(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    form = PaymentForm()
    if form.validate_on_submit():
        po.amount_paid += form.amount.data
        if po.amount_paid >= po.total_amount:
            po.payment_status = "Paid"
        elif po.amount_paid > 0:
            po.payment_status = "Partial"
        log_action(current_user.id, "UPDATE", "PurchaseOrder", entity_id=po.id,
                   description=f"Payment of Rs.{form.amount.data} recorded for {po.po_number}")
        db.session.commit()
        flash("Payment recorded.", "success")
    return redirect(url_for("suppliers.view_purchase_order", po_id=po.id))
