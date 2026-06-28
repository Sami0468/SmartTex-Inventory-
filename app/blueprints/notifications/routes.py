from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/")
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()).limit(100).all()
    return render_template("notifications/list.html", notifications=notifications)


@notifications_bp.route("/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for("notifications.list_notifications"))


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications.list_notifications"))
