"""
AuditLog model — tracks user actions across all modules for accountability.
"""
from datetime import datetime
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50), nullable=False)   # CREATE, UPDATE, DELETE, LOGIN, etc.
    module = db.Column(db.String(50), nullable=False)    # Fabric, Supplier, Sales, etc.
    entity_id = db.Column(db.Integer)
    description = db.Column(db.String(500))
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog {self.module}.{self.action} by user={self.user_id}>"


def log_action(user_id, action, module, entity_id=None, description=None, ip_address=None):
    """Helper to quickly record an audit entry. Call db.session.commit() separately
    or let it ride with the caller's existing transaction."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        module=module,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
    )
    db.session.add(entry)
    return entry
