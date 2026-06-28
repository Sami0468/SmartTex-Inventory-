"""
Sales models — invoices/orders and line items.
"""
from datetime import datetime
from app.extensions import db


class SalesOrder(db.Model):
    __tablename__ = "sales_orders"

    PAYMENT_STATUS = ("Unpaid", "Partial", "Paid")

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    order_date = db.Column(db.Date, default=datetime.utcnow)
    tax_percent = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    payment_status = db.Column(db.String(20), default="Unpaid")
    amount_paid = db.Column(db.Float, default=0)
    notes = db.Column(db.String(255))
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("SalesOrderItem", backref="sales_order", lazy="dynamic",
                             cascade="all, delete-orphan")
    created_by = db.relationship("User")

    @property
    def subtotal(self):
        return round(sum(i.subtotal for i in self.items), 2)

    @property
    def tax_amount(self):
        return round(self.subtotal * (self.tax_percent or 0) / 100, 2)

    @property
    def total_amount(self):
        return round(self.subtotal + self.tax_amount - (self.discount_amount or 0), 2)

    @property
    def balance_due(self):
        return round(self.total_amount - self.amount_paid, 2)

    def __repr__(self):
        return f"<SalesOrder {self.invoice_number}>"


class SalesOrderItem(db.Model):
    __tablename__ = "sales_order_items"

    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey("sales_orders.id"), nullable=False)
    fabric_id = db.Column(db.Integer, db.ForeignKey("fabrics.id"), nullable=False)
    quantity_meters = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    fabric = db.relationship("Fabric")

    @property
    def subtotal(self):
        return round(self.quantity_meters * self.unit_price, 2)
