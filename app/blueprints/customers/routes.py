from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.customer import Customer
from app.models.sales import SalesOrder
from app.models.audit import log_action
from app.blueprints.customers.forms import CustomerForm
from app.utils.codes import next_code
from app.utils.decorators import roles_required
from app.models.user import Role

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/")
@login_required
def list_customers():
    q = request.args.get("q", "").strip()
    query = Customer.query.filter_by(is_active=True)
    if q:
        query = query.filter(or_(Customer.name.ilike(f"%{q}%"),
                                  Customer.company_name.ilike(f"%{q}%"),
                                  Customer.phone.ilike(f"%{q}%")))
    customers = query.order_by(Customer.name.asc()).all()
    return render_template("customers/list.html", customers=customers, q=q)


@customers_bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.SALES_MANAGER)
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            customer_code=next_code(Customer, "customer_code", "CUST"),
            name=form.name.data.strip(),
            company_name=form.company_name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
        )
        db.session.add(customer)
        log_action(current_user.id, "CREATE", "Customer", description=f"Added customer {customer.name}")
        db.session.commit()
        flash(f"Customer {customer.name} added.", "success")
        return redirect(url_for("customers.view_customer", customer_id=customer.id))
    return render_template("customers/form.html", form=form, mode="add")


@customers_bp.route("/<int:customer_id>")
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = customer.sales_orders.order_by(SalesOrder.order_date.desc()).all()
    return render_template("customers/view.html", customer=customer, orders=orders)


@customers_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.SALES_MANAGER)
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = form.name.data.strip()
        customer.company_name = form.company_name.data
        customer.phone = form.phone.data
        customer.email = form.email.data
        customer.address = form.address.data
        log_action(current_user.id, "UPDATE", "Customer", entity_id=customer.id,
                   description=f"Updated customer {customer.name}")
        db.session.commit()
        flash("Customer updated.", "success")
        return redirect(url_for("customers.view_customer", customer_id=customer.id))
    return render_template("customers/form.html", form=form, mode="edit", customer=customer)


@customers_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.is_active = False
    customer.deleted_at = datetime.utcnow()
    customer.deleted_by_id = current_user.id
    log_action(current_user.id, "DELETE", "Customer", entity_id=customer.id,
               description=f"Deactivated customer {customer.name}")
    db.session.commit()
    flash(f"Customer {customer.name} removed. They're preserved in History and can be restored.", "info")
    return redirect(url_for("customers.list_customers"))


@customers_bp.route("/<int:customer_id>/restore", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def restore_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.is_active = True
    customer.deleted_at = None
    customer.deleted_by_id = None
    log_action(current_user.id, "RESTORE", "Customer", entity_id=customer.id,
               description=f"Restored customer {customer.name}")
    db.session.commit()
    flash(f"Customer {customer.name} restored.", "success")
    return redirect(request.referrer or url_for("customers.list_customers"))
