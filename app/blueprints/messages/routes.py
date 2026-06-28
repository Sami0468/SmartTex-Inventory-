from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.message import Message
from app.blueprints.messages.forms import MessageForm

messages_bp = Blueprint("messages", __name__)


def _serialize(msg):
    return {
        "id": msg.id,
        "body": msg.body,
        "created_at": msg.created_at.strftime("%d %b, %H:%M"),
        "created_at_iso": msg.created_at.isoformat(),
        "user_id": msg.user_id,
        "user_name": msg.user.full_name if msg.user else "Unknown",
        "user_role": msg.user.role if msg.user else "",
        "user_initials": msg.user.initials if msg.user else "?",
        "is_own": msg.user_id == current_user.id,
    }


@messages_bp.route("/")
@login_required
def channel():
    form = MessageForm()
    recent = Message.query.order_by(Message.created_at.desc()).limit(50).all()
    recent = list(reversed(recent))  # oldest first for natural chat reading order
    return render_template("messages/channel.html", messages=recent, form=form)


@messages_bp.route("/post", methods=["POST"])
@login_required
def post_message():
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(user_id=current_user.id, body=form.body.data.strip())
        db.session.add(msg)
        db.session.commit()
        return jsonify({"ok": True, "message": _serialize(msg)})
    return jsonify({"ok": False, "errors": form.body.errors}), 400


@messages_bp.route("/poll")
@login_required
def poll():
    """Returns messages newer than the given message id, for lightweight auto-refresh."""
    after_id = request.args.get("after_id", 0, type=int)
    new_messages = Message.query.filter(Message.id > after_id).order_by(Message.created_at.asc()).limit(100).all()
    return jsonify({"messages": [_serialize(m) for m in new_messages]})
