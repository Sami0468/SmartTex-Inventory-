"""
Production Order model — manufacturing job tracking with fabric consumption.
"""
from datetime import datetime
from app.extensions import db


class ProductionOrder(db.Model):
    __tablename__ = "production_orders"

    STATUS_CHOICES = ("Pending", "Approved", "In Progress", "Completed", "Delayed")

    id = db.Column(db.Integer, primary_key=True)
    production_code = db.Column(db.String(30), unique=True, nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    fabric_id = db.Column(db.Integer, db.ForeignKey("fabrics.id"), nullable=False)
    quantity_required_meters = db.Column(db.Float, nullable=False)
    quantity_used_meters = db.Column(db.Float, default=0)
    waste_meters = db.Column(db.Float, default=0)
    assigned_team = db.Column(db.String(120))
    start_date = db.Column(db.Date, default=datetime.utcnow)
    deadline = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="Pending")
    notes = db.Column(db.String(255))
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fabric = db.relationship("Fabric")
    created_by = db.relationship("User")

    @property
    def is_overdue(self):
        from datetime import date
        return (self.deadline and self.deadline < date.today()
                and self.status not in ("Completed",))

    @property
    def efficiency_pct(self):
        """Output efficiency: used material vs (used + waste)."""
        total = (self.quantity_used_meters or 0) + (self.waste_meters or 0)
        if not total:
            return None
        return round((self.quantity_used_meters / total) * 100, 1)

    @property
    def progress_pct(self):
        if self.status == "Completed":
            return 100
        if self.status == "Pending":
            return 0
        if not self.quantity_required_meters:
            return 0
        return round(min((self.quantity_used_meters or 0) / self.quantity_required_meters * 100, 99), 1)

    def __repr__(self):
        return f"<ProductionOrder {self.production_code} {self.status}>"
