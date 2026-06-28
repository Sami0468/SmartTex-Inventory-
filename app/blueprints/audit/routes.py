from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.audit import AuditLog
from app.utils.decorators import admin_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/")
@login_required
@admin_required
def list_logs():
    module_filter = request.args.get("module", "")
    page = request.args.get("page", 1, type=int)
    query = AuditLog.query
    if module_filter:
        query = query.filter_by(module=module_filter)
    pagination = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    modules = [r[0] for r in AuditLog.query.with_entities(AuditLog.module).distinct().all()]
    return render_template("audit/list.html", logs=pagination.items, pagination=pagination,
                           modules=modules, module_filter=module_filter)
