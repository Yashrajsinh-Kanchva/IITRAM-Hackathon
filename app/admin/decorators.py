from functools import wraps

from flask import g, jsonify, redirect, request, url_for

from app.admin.dependencies import get_services
from app.utils.auth import current_admin_id, logout_admin


def _unauthorized_response():
    if request.path.startswith("/admin/api"):
        return jsonify({"error": "Authentication required", "status": 401}), 401

    target = request.full_path if request.query_string else request.path
    return redirect(url_for("admin.login", next=target))


def admin_required(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        admin_id = current_admin_id()
        if not admin_id:
            return _unauthorized_response()

        admin = get_services()["auth"].get_public_admin(admin_id)
        if not admin or admin.get("status") != "active":
            logout_admin()
            return _unauthorized_response()

        g.current_admin = admin
        return view_fn(*args, **kwargs)

    return wrapped
