"""
User & Role models — authentication and role-based access control.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class Role:
    """Role name constants used across the app (stored as string on User)."""
    ADMIN = "Admin"
    INVENTORY_MANAGER = "Inventory Manager"
    PRODUCTION_MANAGER = "Production Manager"
    SALES_MANAGER = "Sales Manager"

    ALL = [ADMIN, INVENTORY_MANAGER, PRODUCTION_MANAGER, SALES_MANAGER]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default=Role.INVENTORY_MANAGER)
    phone = db.Column(db.String(30))
    avatar_url = db.Column(db.String(255))
    is_active_user = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    notifications = db.relationship("Notification", backref="user", lazy="dynamic",
                                     cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    def has_role(self, *roles):
        return self.role in roles or self.is_admin

    @property
    def initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.full_name[:2].upper() if self.full_name else "U"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
