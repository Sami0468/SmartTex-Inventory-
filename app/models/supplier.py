"""
Supplier models — supplier directory, purchase orders/payments, performance tracking.
"""
from datetime import datetime
from app.extensions import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    company_name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    country = db.Column(db.String(80))
    rating = db.Column(db.Float, default=0)  # 0-5, can be manual or computed
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fabrics = db.relationship("Fabric", backref="supplier", lazy="dynamic")
    purchase_orders = db.relationship("PurchaseOrder", backref="supplier", lazy="dynamic",
                                       cascade="all, delete-orphan")
    deleted_by = db.relationship("User", foreign_keys=[deleted_by_id])

    @property
    def total_purchase_value(self):
        return round(sum(po.total_amount for po in self.purchase_orders), 2)

    @property
    def on_time_delivery_rate(self):
        completed = [po for po in self.purchase_orders if po.status == "Received"]
        if not completed:
            return None
        on_time = [po for po in completed if po.delivered_date and po.expected_date
                   and po.delivered_date <= po.expected_date]
        return round(len(on_time) / len(completed) * 100, 1)

    def __repr__(self):
        return f"<Supplier {self.company_name}>"


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    STATUS_CHOICES = ("Pending", "Ordered", "Received", "Cancelled")
    PAYMENT_STATUS = ("Unpaid", "Partial", "Paid")

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(30), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    order_date = db.Column(db.Date, default=datetime.utcnow)
    expected_date = db.Column(db.Date)
    delivered_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="Pending")
    payment_status = db.Column(db.String(20), default="Unpaid")
    amount_paid = db.Column(db.Float, default=0)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("PurchaseOrderItem", backref="purchase_order", lazy="dynamic",
                             cascade="all, delete-orphan")

    @property
    def total_amount(self):
        return round(sum(i.subtotal for i in self.items), 2)

    @property
    def balance_due(self):
        return round(self.total_amount - self.amount_paid, 2)

    def __repr__(self):
        return f"<PO {self.po_number}>"


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    fabric_id = db.Column(db.Integer, db.ForeignKey("fabrics.id"))
    description = db.Column(db.String(150))
    quantity_meters = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)

    fabric = db.relationship("Fabric")

    @property
    def subtotal(self):
        return round(self.quantity_meters * self.unit_cost, 2)
