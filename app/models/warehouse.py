"""
Warehouse models — locations and inter-warehouse stock transfers.
"""
from datetime import datetime
from app.extensions import db


class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    warehouse_code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255))
    capacity_meters = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fabrics = db.relationship("Fabric", backref="warehouse", lazy="dynamic")
    deleted_by = db.relationship("User", foreign_keys=[deleted_by_id])

    @property
    def current_stock_meters(self):
        return round(sum(f.quantity_meters for f in self.fabrics), 2)

    @property
    def utilization_pct(self):
        if not self.capacity_meters:
            return 0
        return round(min(self.current_stock_meters / self.capacity_meters * 100, 100), 1)

    def __repr__(self):
        return f"<Warehouse {self.name}>"


class WarehouseTransfer(db.Model):
    __tablename__ = "warehouse_transfers"

    id = db.Column(db.Integer, primary_key=True)
    fabric_id = db.Column(db.Integer, db.ForeignKey("fabrics.id"), nullable=False)
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    quantity_meters = db.Column(db.Float, nullable=False)
    transferred_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fabric = db.relationship("Fabric")
    from_warehouse = db.relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = db.relationship("Warehouse", foreign_keys=[to_warehouse_id])
    transferred_by = db.relationship("User")
