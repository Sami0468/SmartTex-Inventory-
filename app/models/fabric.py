"""
Fabric Inventory models — core stock item + movement ledger for history/audit/AI.
"""
from datetime import datetime
from app.extensions import db


class Fabric(db.Model):
    __tablename__ = "fabrics"

    id = db.Column(db.Integer, primary_key=True)
    fabric_code = db.Column(db.String(30), unique=True, nullable=False, index=True)  # e.g. FB-0001
    name = db.Column(db.String(120), nullable=False)
    fabric_type = db.Column(db.String(60), nullable=False)  # Cotton, Polyester, Silk, Denim, etc.
    gsm = db.Column(db.Integer)  # Grams per Square Meter
    width_inches = db.Column(db.Float)
    color = db.Column(db.String(40))
    pattern = db.Column(db.String(60))
    roll_number = db.Column(db.String(40))

    quantity_meters = db.Column(db.Float, nullable=False, default=0)
    reserved_meters = db.Column(db.Float, nullable=False, default=0)  # allocated to production
    damaged_meters = db.Column(db.Float, nullable=False, default=0)

    unit_cost = db.Column(db.Float, nullable=False, default=0)       # cost per meter
    selling_price = db.Column(db.Float, nullable=False, default=0)   # price per meter

    low_stock_threshold = db.Column(db.Float, default=100)

    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))

    qr_code_path = db.Column(db.String(255))
    barcode_path = db.Column(db.String(255))

    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    movements = db.relationship("InventoryMovement", backref="fabric", lazy="dynamic",
                                 cascade="all, delete-orphan")
    deleted_by = db.relationship("User", foreign_keys=[deleted_by_id])

    @property
    def available_meters(self):
        return max(self.quantity_meters - self.reserved_meters - self.damaged_meters, 0)

    @property
    def is_low_stock(self):
        return self.available_meters <= (self.low_stock_threshold or 0)

    @property
    def stock_value(self):
        return round(self.quantity_meters * self.unit_cost, 2)

    @property
    def margin_per_meter(self):
        return round(self.selling_price - self.unit_cost, 2)

    def __repr__(self):
        return f"<Fabric {self.fabric_code} {self.name}>"


class InventoryMovement(db.Model):
    """Immutable ledger of every stock change — feeds history, audit, and AI forecasting."""
    __tablename__ = "inventory_movements"

    MOVEMENT_TYPES = ("IN", "OUT", "ADJUSTMENT", "DAMAGE", "TRANSFER", "PRODUCTION_USE")

    id = db.Column(db.Integer, primary_key=True)
    fabric_id = db.Column(db.Integer, db.ForeignKey("fabrics.id"), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    quantity_meters = db.Column(db.Float, nullable=False)  # positive value; sign implied by type
    reference = db.Column(db.String(120))  # e.g. PO number, Sales Invoice, Production ID
    note = db.Column(db.String(255))
    performed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    performed_by = db.relationship("User")

    def __repr__(self):
        return f"<Movement {self.movement_type} {self.quantity_meters}m fabric={self.fabric_id}>"
