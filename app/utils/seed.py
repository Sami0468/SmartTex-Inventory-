"""
Seed script — populates the database with realistic demo data so every module
(including AI forecasting/anomaly detection) has something meaningful to show.
Run with: flask seed-db
"""
import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User, Role
from app.models.warehouse import Warehouse
from app.models.supplier import Supplier, PurchaseOrder, PurchaseOrderItem
from app.models.fabric import Fabric, InventoryMovement
from app.models.customer import Customer
from app.models.sales import SalesOrder, SalesOrderItem
from app.models.production import ProductionOrder
from app.models.worker import Worker, Attendance, Payroll
from app.utils.codes import next_code, next_invoice_number

random.seed(42)


def seed_database():
    if User.query.filter_by(username="admin").first():
        print("Database already seeded. Skipping.")
        return

    # --- Users ---
    admin = User(full_name="Ayesha Khan", username="admin", email="admin@smarttex.com", role=Role.ADMIN)
    admin.set_password("admin123")
    inv_mgr = User(full_name="Bilal Ahmed", username="inventory", email="inventory@smarttex.com", role=Role.INVENTORY_MANAGER)
    inv_mgr.set_password("admin123")
    prod_mgr = User(full_name="Sana Tariq", username="production", email="production@smarttex.com", role=Role.PRODUCTION_MANAGER)
    prod_mgr.set_password("admin123")
    sales_mgr = User(full_name="Hamza Sheikh", username="sales", email="sales@smarttex.com", role=Role.SALES_MANAGER)
    sales_mgr.set_password("admin123")
    db.session.add_all([admin, inv_mgr, prod_mgr, sales_mgr])
    db.session.commit()

    # --- Warehouses ---
    warehouses = [
        Warehouse(warehouse_code="WH-0001", name="Faisalabad Main Warehouse", location="Faisalabad, Punjab", capacity_meters=50000),
        Warehouse(warehouse_code="WH-0002", name="Lahore Distribution Center", location="Lahore, Punjab", capacity_meters=25000),
    ]
    db.session.add_all(warehouses)
    db.session.commit()

    # --- Suppliers ---
    suppliers_data = [
        ("Indus Textile Mills", "Kamran Malik", "+92-300-1234567", "kamran@industextile.pk", "Pakistan", 4.5),
        ("Lahore Cotton Co.", "Fariha Noor", "+92-321-7654321", "fariha@lahorecotton.pk", "Pakistan", 4.0),
        ("Karachi Weaving House", "Asif Raza", "+92-333-9988776", "asif@karachiweaving.pk", "Pakistan", 3.8),
        ("Faisalabad Fabric Hub", "Nida Iqbal", "+92-345-1122334", "nida@ffhub.pk", "Pakistan", 4.2),
    ]
    suppliers = []
    for i, (name, contact, phone, email, country, rating) in enumerate(suppliers_data, start=1):
        s = Supplier(supplier_code=f"SUP-{i:04d}", company_name=name, contact_person=contact,
                    phone=phone, email=email, country=country, rating=rating)
        suppliers.append(s)
    db.session.add_all(suppliers)
    db.session.commit()

    # --- Fabrics ---
    fabric_specs = [
        ("Premium Combed Cotton", "Cotton", 180, 58, "Navy Blue", "Plain"),
        ("Classic Denim Twill", "Denim", 320, 60, "Indigo", "Twill"),
        ("Soft Polyester Blend", "Polyester", 140, 56, "White", "Plain"),
        ("Pure Silk Charmeuse", "Silk", 60, 44, "Ivory", "Plain"),
        ("Heavy Wool Suiting", "Wool", 280, 58, "Charcoal Grey", "Herringbone"),
        ("Printed Lawn Cotton", "Lawn", 100, 52, "Floral Print", "Printed"),
        ("Stretch Jersey Knit", "Jersey", 160, 60, "Black", "Knit"),
        ("Chiffon Georgette", "Chiffon", 50, 44, "Blush Pink", "Plain"),
        ("Brushed Fleece", "Fleece", 240, 58, "Heather Grey", "Plain"),
        ("Linen Blend Suiting", "Linen", 200, 56, "Beige", "Plain"),
    ]
    fabrics = []
    for i, (name, ftype, gsm, width, color, pattern) in enumerate(fabric_specs, start=1):
        qty = random.uniform(150, 1800)
        unit_cost = round(random.uniform(250, 1200), 2)
        fabric = Fabric(
            fabric_code=f"FB-{i:04d}", name=name, fabric_type=ftype, gsm=gsm, width_inches=width,
            color=color, pattern=pattern, roll_number=f"R-2026-{i:03d}",
            quantity_meters=round(qty, 1), unit_cost=unit_cost,
            selling_price=round(unit_cost * random.uniform(1.3, 1.8), 2),
            low_stock_threshold=random.choice([80, 100, 120, 150]),
            warehouse_id=random.choice(warehouses).id,
            supplier_id=random.choice(suppliers).id,
            date_added=datetime.utcnow() - timedelta(days=random.randint(30, 300)),
        )
        fabrics.append(fabric)
    db.session.add_all(fabrics)
    db.session.commit()

    # Make a couple fabrics intentionally low stock for dashboard demo
    fabrics[2].quantity_meters = 45
    fabrics[2].low_stock_threshold = 100
    fabrics[7].quantity_meters = 30
    fabrics[7].low_stock_threshold = 80
    db.session.commit()

    # Initial stock movements
    for f in fabrics:
        db.session.add(InventoryMovement(fabric_id=f.id, movement_type="IN", quantity_meters=f.quantity_meters,
                                         reference="Initial Stock", note="Seed data", created_at=f.date_added))
    db.session.commit()

    # Historical OUT movements (for AI usage/forecast data) across past 4 months
    for f in fabrics:
        for month_offset in range(4, 0, -1):
            date = datetime.utcnow() - timedelta(days=30 * month_offset + random.randint(0, 10))
            qty = round(random.uniform(20, 90), 1)
            db.session.add(InventoryMovement(fabric_id=f.id, movement_type="OUT", quantity_meters=qty,
                                             reference="Historical sale", created_at=date))
    db.session.commit()

    # One intentional anomaly (large unusual movement) for anomaly detection demo
    db.session.add(InventoryMovement(fabric_id=fabrics[0].id, movement_type="OUT", quantity_meters=480,
                                     reference="Bulk export order", note="Unusually large single movement",
                                     created_at=datetime.utcnow() - timedelta(days=3)))
    db.session.commit()

    # --- Customers ---
    customers_data = [
        ("Zenith Garments Ltd.", "Imran Sheikh", "+92-300-5566778", "imran@zenithgarments.pk"),
        ("Royal Apparel House", "Maria Yousaf", "+92-321-3344556", "maria@royalapparel.pk"),
        ("Crescent Fashion Studio", "Usman Tahir", "+92-333-7788990", "usman@crescentfashion.pk"),
        ("Bright Stitch Boutique", "Hira Aslam", "+92-345-2233445", "hira@brightstitch.pk"),
    ]
    customers = []
    for i, (name, company, phone, email) in enumerate(customers_data, start=1):
        c = Customer(customer_code=f"CUST-{i:04d}", name=company, company_name=name, phone=phone, email=email)
        customers.append(c)
    db.session.add_all(customers)
    db.session.commit()

    # --- Sales Orders (spread over last 6 months for chart data) ---
    for month_offset in range(5, -1, -1):
        for _ in range(random.randint(2, 5)):
            order_date = (datetime.utcnow() - timedelta(days=30 * month_offset + random.randint(0, 25))).date()
            customer = random.choice(customers)
            order = SalesOrder(
                invoice_number=f"INV-{order_date.year}-{random.randint(1000,9999)}",
                customer_id=customer.id, order_date=order_date,
                tax_percent=random.choice([0, 5, 10]),
                payment_status=random.choice(["Paid", "Paid", "Partial", "Unpaid"]),
                created_by_id=sales_mgr.id,
            )
            db.session.add(order)
            db.session.flush()
            for _ in range(random.randint(1, 3)):
                fabric = random.choice(fabrics)
                qty = round(random.uniform(10, 60), 1)
                db.session.add(SalesOrderItem(sales_order_id=order.id, fabric_id=fabric.id,
                                              quantity_meters=qty, unit_price=fabric.selling_price))
            if order.payment_status == "Paid":
                order.amount_paid = order.total_amount
            elif order.payment_status == "Partial":
                order.amount_paid = round(order.total_amount * 0.5, 2)
    db.session.commit()

    # --- Production Orders ---
    statuses = ["Pending", "Approved", "In Progress", "Completed", "Delayed"]
    products = ["Men's Formal Shirt", "Ladies Kurta", "Denim Jeans", "School Uniform Set", "Casual T-Shirt"]
    for i, (product, status) in enumerate(zip(products, statuses), start=1):
        fabric = random.choice(fabrics)
        qty_req = round(random.uniform(50, 300), 1)
        if qty_req > fabric.available_meters:
            qty_req = round(fabric.available_meters * 0.3, 1)
        used = qty_req * random.uniform(0.3, 1.0) if status != "Pending" else 0
        waste = used * random.uniform(0.02, 0.08)
        fabric.reserved_meters += max(qty_req - used - waste, 0) if status != "Completed" else 0

        order = ProductionOrder(
            production_code=f"PRD-{i:04d}", product_name=product, fabric_id=fabric.id,
            quantity_required_meters=qty_req, quantity_used_meters=round(used, 1), waste_meters=round(waste, 1),
            assigned_team=random.choice(["Stitching Line A", "Stitching Line B", "Cutting Team", "Finishing Unit"]),
            start_date=datetime.utcnow().date() - timedelta(days=random.randint(5, 40)),
            deadline=datetime.utcnow().date() + timedelta(days=random.randint(-5, 30)),
            status=status, created_by_id=prod_mgr.id,
        )
        if status == "Completed":
            order.completed_date = datetime.utcnow().date() - timedelta(days=random.randint(1, 10))
        db.session.add(order)
    db.session.commit()

    # --- Workers ---
    workers_data = [
        ("Tariq Mehmood", "Cutting", "Senior Cutter", 38000),
        ("Saima Bibi", "Stitching", "Machine Operator", 32000),
        ("Faisal Khan", "Dyeing", "Dye Master", 42000),
        ("Rabia Sultana", "Finishing", "Quality Checker", 30000),
        ("Adnan Latif", "Packing", "Packing Supervisor", 35000),
        ("Mehwish Anwar", "Quality Assurance", "QA Inspector", 36000),
    ]
    workers = []
    for i, (name, dept, designation, salary) in enumerate(workers_data, start=1):
        w = Worker(worker_code=f"EMP-{i:04d}", name=name, department=dept, designation=designation,
                  base_salary=salary, date_joined=datetime.utcnow().date() - timedelta(days=random.randint(100, 900)))
        workers.append(w)
    db.session.add_all(workers)
    db.session.commit()

    # Attendance for last 14 days
    for w in workers:
        for d in range(14):
            date = datetime.utcnow().date() - timedelta(days=d)
            status = random.choices(["Present", "Absent", "Half-Day"], weights=[85, 5, 10])[0]
            db.session.add(Attendance(worker_id=w.id, date=date, status=status,
                                      hours_worked=8 if status == "Present" else (4 if status == "Half-Day" else 0)))
    db.session.commit()

    # Payroll for last month
    last_month = (datetime.utcnow().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    for w in workers:
        net = w.base_salary + random.choice([0, 1500, 3000])
        db.session.add(Payroll(worker_id=w.id, month=last_month, base_salary=w.base_salary,
                               overtime_pay=random.choice([0, 1500, 3000]), net_pay=net, is_paid=True,
                               paid_date=datetime.utcnow().date() - timedelta(days=5)))
    db.session.commit()

    # --- Purchase Orders ---
    for i, supplier in enumerate(suppliers, start=1):
        for j in range(random.randint(1, 3)):
            po = PurchaseOrder(
                po_number=f"PO-{i:04d}{j}", supplier_id=supplier.id,
                order_date=datetime.utcnow().date() - timedelta(days=random.randint(10, 100)),
                expected_date=datetime.utcnow().date() - timedelta(days=random.randint(0, 90)),
                status="Received", payment_status=random.choice(["Paid", "Partial"]),
            )
            po.delivered_date = po.expected_date - timedelta(days=random.choice([-3, -1, 0, 1, 2]))
            db.session.add(po)
            db.session.flush()
            for _ in range(random.randint(1, 2)):
                fabric = random.choice(fabrics)
                db.session.add(PurchaseOrderItem(purchase_order_id=po.id, fabric_id=fabric.id,
                                                 quantity_meters=round(random.uniform(100, 500), 1),
                                                 unit_cost=fabric.unit_cost))
            db.session.flush()
            if po.payment_status == "Paid":
                po.amount_paid = po.total_amount
            else:
                po.amount_paid = round(po.total_amount * 0.5, 2)
    db.session.commit()

    print("✓ Seed data created successfully.")
    print("  Admin login -> username: admin / password: admin123")
