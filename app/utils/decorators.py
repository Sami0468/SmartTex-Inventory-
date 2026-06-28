"""
RBAC decorators — restrict routes to specific roles.
"""
from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """Allow access only to users whose role is in `roles` (Admin always allowed)."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(*roles):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapped
