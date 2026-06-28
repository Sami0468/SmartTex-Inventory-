"""
Worker, Attendance, Payroll models — HR for factory floor staff.
"""
from datetime import datetime
from app.extensions import db


class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.Integer, primary_key=True)
    worker_code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    cnic = db.Column(db.String(20))  # National ID (Pakistan format aware, but free text)
    phone = db.Column(db.String(30))
    department = db.Column(db.String(80))  # Cutting, Stitching, Dyeing, Packing, QA, etc.
    designation = db.Column(db.String(80))
    base_salary = db.Column(db.Float, nullable=False, default=0)
    date_joined = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship("Attendance", backref="worker", lazy="dynamic",
                                          cascade="all, delete-orphan")
    payroll_records = db.relationship("Payroll", backref="worker", lazy="dynamic",
                                       cascade="all, delete-orphan")
    deleted_by = db.relationship("User", foreign_keys=[deleted_by_id])

    def __repr__(self):
        return f"<Worker {self.name}>"


class Attendance(db.Model):
    __tablename__ = "attendance"

    STATUS_CHOICES = ("Present", "Absent", "Half-Day", "Leave")

    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Present")
    hours_worked = db.Column(db.Float, default=8)
    overtime_hours = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("worker_id", "date", name="uq_worker_date"),)


class Payroll(db.Model):
    __tablename__ = "payroll"

    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # 'YYYY-MM'
    base_salary = db.Column(db.Float, nullable=False)
    overtime_pay = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    bonus = db.Column(db.Float, default=0)
    net_pay = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("worker_id", "month", name="uq_worker_month"),)
