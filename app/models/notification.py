"""
Notification model — in-app alerts (low stock, deadlines, payments due, etc).
"""
from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    CATEGORY_CHOICES = ("low_stock", "production_deadline", "supplier_payment",
                         "sales_update", "new_order", "system")

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(30), nullable=False, default="system")
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500))
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Notification {self.title}>"
