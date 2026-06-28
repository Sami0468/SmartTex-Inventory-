"""
Notification generator — scans live data for conditions that deserve a
manager's attention (low stock, approaching/overdue production deadlines,
overdue supplier payments) and creates in-app notifications for the right
roles. Designed to be idempotent: re-running it doesn't spam duplicate
notifications for a condition that's already been flagged and not yet
resolved — each check looks for an existing unread notification with a
matching link before creating a new one.

Called automatically on dashboard load (cheap enough — a handful of small
queries) so notifications stay fresh without needing a background scheduler.
"""
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User, Role
from app.models.notification import Notification
from app.models.fabric import Fabric
from app.models.production import ProductionOrder
from app.models.supplier import PurchaseOrder


def _users_with_roles(*roles):
    return User.query.filter(User.role.in_(roles), User.is_active_user == True).all()


def _already_notified(user_id, link):
    """Avoid re-flagging the same unresolved issue to the same user repeatedly."""
    return Notification.query.filter_by(user_id=user_id, link=link, is_read=False).first() is not None


def _notify(user_id, category, title, message, link):
    if _already_notified(user_id, link):
        return False
    db.session.add(Notification(user_id=user_id, category=category, title=title,
                                 message=message, link=link))
    return True


def generate_notifications():
    """Run all checks. Returns count of new notifications created."""
    created = 0
    recipients = _users_with_roles(Role.ADMIN, Role.INVENTORY_MANAGER)
    prod_recipients = _users_with_roles(Role.ADMIN, Role.PRODUCTION_MANAGER)

    # --- Low stock ---
    for fabric in Fabric.query.filter_by(is_active=True).all():
        if fabric.is_low_stock:
            link = f"/fabrics/{fabric.id}"
            for user in recipients:
                if _notify(user.id, "low_stock",
                          f"Low stock: {fabric.name}",
                          f"{fabric.name} ({fabric.fabric_code}) is down to "
                          f"{fabric.available_meters:.1f}m, below its {fabric.low_stock_threshold:.0f}m threshold.",
                          link):
                    created += 1

    # --- Production deadlines (due within 3 days, or overdue, and not completed) ---
    soon = datetime.utcnow().date() + timedelta(days=3)
    at_risk = ProductionOrder.query.filter(
        ProductionOrder.status.notin_(["Completed"]),
        ProductionOrder.deadline.isnot(None),
        ProductionOrder.deadline <= soon,
    ).all()
    for order in at_risk:
        link = f"/production/{order.id}"
        overdue = order.is_overdue
        for user in prod_recipients:
            if _notify(user.id, "production_deadline",
                      f"{'Overdue' if overdue else 'Deadline approaching'}: {order.product_name}",
                      f"{order.production_code} ({order.product_name}) "
                      f"{'is overdue' if overdue else 'is due'} on {order.deadline.strftime('%d %b %Y')}. "
                      f"Status: {order.status}.",
                      link):
                created += 1

    # --- Overdue supplier payments ---
    today = datetime.utcnow().date()
    overdue_pos = PurchaseOrder.query.filter(
        PurchaseOrder.payment_status.in_(["Unpaid", "Partial"]),
        PurchaseOrder.expected_date.isnot(None),
        PurchaseOrder.expected_date < today,
    ).all()
    for po in overdue_pos:
        link = f"/suppliers/purchase-orders/{po.id}"
        for user in recipients:
            if _notify(user.id, "supplier_payment",
                      f"Payment due: {po.supplier.company_name}",
                      f"{po.po_number} to {po.supplier.company_name} has a balance of "
                      f"Rs. {po.balance_due:,.0f} and was expected by {po.expected_date.strftime('%d %b %Y')}.",
                      link):
                created += 1

    if created:
        db.session.commit()
    return created
