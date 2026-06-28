from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.worker import Worker, Attendance, Payroll
from app.models.audit import log_action
from app.blueprints.workers.forms import WorkerForm, AttendanceForm, PayrollForm
from app.utils.codes import next_code
from app.utils.decorators import roles_required
from app.models.user import Role

workers_bp = Blueprint("workers", __name__)


@workers_bp.route("/")
@login_required
def list_workers():
    dept_filter = request.args.get("department", "")
    query = Worker.query.filter_by(is_active=True)
    if dept_filter:
        query = query.filter_by(department=dept_filter)
    workers = query.order_by(Worker.name.asc()).all()
    from app.blueprints.workers.forms import DEPARTMENTS
    return render_template("workers/list.html", workers=workers, dept_filter=dept_filter, departments=DEPARTMENTS)


@workers_bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def add_worker():
    form = WorkerForm()
    if form.validate_on_submit():
        worker = Worker(
            worker_code=next_code(Worker, "worker_code", "EMP"),
            name=form.name.data.strip(),
            cnic=form.cnic.data,
            phone=form.phone.data,
            department=form.department.data,
            designation=form.designation.data,
            base_salary=form.base_salary.data,
            date_joined=form.date_joined.data or datetime.utcnow().date(),
        )
        db.session.add(worker)
        log_action(current_user.id, "CREATE", "Worker", description=f"Added worker {worker.name}")
        db.session.commit()
        flash(f"Worker {worker.name} added.", "success")
        return redirect(url_for("workers.view_worker", worker_id=worker.id))
    return render_template("workers/form.html", form=form, mode="add")


@workers_bp.route("/<int:worker_id>")
@login_required
def view_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    attendance = worker.attendance_records.order_by(Attendance.date.desc()).limit(30).all()
    payroll = worker.payroll_records.order_by(Payroll.month.desc()).all()
    attendance_form = AttendanceForm(date=datetime.utcnow().date())
    payroll_form = PayrollForm()
    present_count = sum(1 for a in attendance if a.status == "Present")
    return render_template("workers/view.html", worker=worker, attendance=attendance,
                           payroll=payroll, attendance_form=attendance_form,
                           payroll_form=payroll_form, present_count=present_count)


@workers_bp.route("/<int:worker_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def edit_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = WorkerForm(obj=worker)
    if form.validate_on_submit():
        worker.name = form.name.data.strip()
        worker.cnic = form.cnic.data
        worker.phone = form.phone.data
        worker.department = form.department.data
        worker.designation = form.designation.data
        worker.base_salary = form.base_salary.data
        log_action(current_user.id, "UPDATE", "Worker", entity_id=worker.id,
                   description=f"Updated worker {worker.name}")
        db.session.commit()
        flash("Worker updated.", "success")
        return redirect(url_for("workers.view_worker", worker_id=worker.id))
    return render_template("workers/form.html", form=form, mode="edit", worker=worker)


@workers_bp.route("/<int:worker_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    worker.is_active = False
    worker.deleted_at = datetime.utcnow()
    worker.deleted_by_id = current_user.id
    log_action(current_user.id, "DELETE", "Worker", entity_id=worker.id,
               description=f"Deactivated worker {worker.name}")
    db.session.commit()
    flash(f"Worker {worker.name} removed. They're preserved in History and can be restored.", "info")
    return redirect(url_for("workers.list_workers"))


@workers_bp.route("/<int:worker_id>/restore", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def restore_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    worker.is_active = True
    worker.deleted_at = None
    worker.deleted_by_id = None
    log_action(current_user.id, "RESTORE", "Worker", entity_id=worker.id,
               description=f"Restored worker {worker.name}")
    db.session.commit()
    flash(f"Worker {worker.name} restored.", "success")
    return redirect(request.referrer or url_for("workers.list_workers"))


@workers_bp.route("/<int:worker_id>/attendance", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def mark_attendance(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = AttendanceForm()
    if form.validate_on_submit():
        existing = Attendance.query.filter_by(worker_id=worker.id, date=form.date.data).first()
        if existing:
            existing.status = form.status.data
            existing.hours_worked = form.hours_worked.data or 0
            existing.overtime_hours = form.overtime_hours.data or 0
        else:
            db.session.add(Attendance(
                worker_id=worker.id, date=form.date.data, status=form.status.data,
                hours_worked=form.hours_worked.data or 0, overtime_hours=form.overtime_hours.data or 0,
            ))
        db.session.commit()
        flash("Attendance recorded.", "success")
    else:
        flash("Please check the attendance form.", "danger")
    return redirect(url_for("workers.view_worker", worker_id=worker.id))


@workers_bp.route("/<int:worker_id>/payroll", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def generate_payroll(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    form = PayrollForm()
    if form.validate_on_submit():
        overtime_pay = form.overtime_pay.data or 0
        deductions = form.deductions.data or 0
        bonus = form.bonus.data or 0
        net_pay = worker.base_salary + overtime_pay + bonus - deductions

        existing = Payroll.query.filter_by(worker_id=worker.id, month=form.month.data).first()
        if existing:
            existing.overtime_pay = overtime_pay
            existing.deductions = deductions
            existing.bonus = bonus
            existing.net_pay = net_pay
        else:
            db.session.add(Payroll(
                worker_id=worker.id, month=form.month.data, base_salary=worker.base_salary,
                overtime_pay=overtime_pay, deductions=deductions, bonus=bonus, net_pay=net_pay,
            ))
        log_action(current_user.id, "CREATE", "Payroll",
                   description=f"Generated payroll for {worker.name} ({form.month.data})")
        db.session.commit()
        flash(f"Payroll generated for {form.month.data}.", "success")
    else:
        flash("Please provide a valid month (YYYY-MM).", "danger")
    return redirect(url_for("workers.view_worker", worker_id=worker.id))


@workers_bp.route("/payroll/<int:payroll_id>/mark-paid", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.PRODUCTION_MANAGER)
def mark_payroll_paid(payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)
    payroll.is_paid = True
    payroll.paid_date = datetime.utcnow().date()
    db.session.commit()
    flash("Payroll marked as paid.", "success")
    return redirect(url_for("workers.view_worker", worker_id=payroll.worker_id))
