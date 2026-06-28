"""
History — a single admin view of every deleted (soft-deleted) record across
the system: fabrics, suppliers, warehouses, workers, customers. Each entry
shows what it was, when and by whom it was removed, and offers a Restore
action. Nothing shown here was ever hard-deleted from the database — it's
just hidden from the active lists/dropdowns everywhere else.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.fabric import Fabric
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse
from app.models.worker import Worker
from app.models.customer import Customer
from app.utils.decorators import admin_required

history_bp = Blueprint("history", __name__)

TYPE_CONFIG = {
    "fabrics": {"model": Fabric, "label": "Fabrics", "icon": "fabric",
                "name_attr": "name", "code_attr": "fabric_code"},
    "suppliers": {"model": Supplier, "label": "Suppliers", "icon": "supplier",
                  "name_attr": "company_name", "code_attr": "supplier_code"},
    "warehouses": {"model": Warehouse, "label": "Warehouses", "icon": "warehouse",
                   "name_attr": "name", "code_attr": "warehouse_code"},
    "workers": {"model": Worker, "label": "Workers", "icon": "workers",
                "name_attr": "name", "code_attr": "worker_code"},
    "customers": {"model": Customer, "label": "Customers", "icon": "customers",
                  "name_attr": "name", "code_attr": "customer_code"},
}


@history_bp.route("/")
@login_required
@admin_required
def index():
    type_filter = request.args.get("type", "")

    entries = []
    for key, cfg in TYPE_CONFIG.items():
        if type_filter and type_filter != key:
            continue
        model = cfg["model"]
        deleted = model.query.filter_by(is_active=False).order_by(model.deleted_at.desc()).all()
        for item in deleted:
            entries.append({
                "type_key": key,
                "type_label": cfg["label"],
                "icon": cfg["icon"],
                "id": item.id,
                "name": getattr(item, cfg["name_attr"]),
                "code": getattr(item, cfg["code_attr"]),
                "deleted_at": item.deleted_at,
                "deleted_by": item.deleted_by.full_name if item.deleted_by else "Unknown",
                "item": item,
            })

    entries.sort(key=lambda e: e["deleted_at"] or "", reverse=True)

    counts = {key: cfg["model"].query.filter_by(is_active=False).count() for key, cfg in TYPE_CONFIG.items()}

    return render_template("history/index.html", entries=entries, type_filter=type_filter,
                           type_config=TYPE_CONFIG, counts=counts, total=len(entries))
