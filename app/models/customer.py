"""
Customer model.
"""
from datetime import datetime
from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    company_name = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales_orders = db.relationship("SalesOrder", backref="customer", lazy="dynamic")
    deleted_by = db.relationship("User", foreign_keys=[deleted_by_id])

    @property
    def total_purchases(self):
        return round(sum(o.total_amount for o in self.sales_orders), 2)

    @property
    def order_count(self):
        return self.sales_orders.count()

    def __repr__(self):
        return f"<Customer {self.name}>"
