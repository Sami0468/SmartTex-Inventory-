"""
SmartTex Inventory — Application Entry Point

Run with:
    python run.py

Or with Flask CLI:
    flask --app run.py run

First-time setup:
    flask --app run.py init-db
    flask --app run.py seed-db
"""
import os
from app import create_app
from app.extensions import db

app = create_app()


@app.shell_context_processor
def make_shell_context():
    from app.models import (User, Fabric, Supplier, Warehouse, Customer,
                            SalesOrder, ProductionOrder, Worker, Notification, AuditLog)
    return dict(db=db, User=User, Fabric=Fabric, Supplier=Supplier, Warehouse=Warehouse,
               Customer=Customer, SalesOrder=SalesOrder, ProductionOrder=ProductionOrder,
               Worker=Worker, Notification=Notification, AuditLog=AuditLog)


if __name__ == "__main__":
    # Ensure instance + upload folders exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)
    os.makedirs(app.config["QRCODE_FOLDER"], exist_ok=True)
    os.makedirs(app.config["BARCODE_FOLDER"], exist_ok=True)

    with app.app_context():
        db.create_all()

    app.run(debug=True, host="0.0.0.0", port=5000)
    from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
