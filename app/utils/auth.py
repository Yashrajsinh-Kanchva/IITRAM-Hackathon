from flask import session


def login_admin(admin):
    session.permanent = True
    session["admin_id"] = str(admin["_id"])
    session["admin_email"] = admin["email"]


def logout_admin():
    session.pop("admin_id", None)
    session.pop("admin_email", None)


def current_admin_id():
    return session.get("admin_id")
