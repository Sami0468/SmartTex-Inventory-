"""
Message model — simple team-wide chat ("Team Channel") so Admin and all
managers can communicate and see each other's messages, like a shared
Slack channel. Deliberately single-channel (no DMs/threads) to keep this
genuinely simple to use day-to-day on a factory floor.
"""
from datetime import datetime
from app.extensions import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")

    def __repr__(self):
        return f"<Message {self.id} by user={self.user_id}>"
