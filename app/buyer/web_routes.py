from pathlib import Path

from flask import Blueprint, abort, current_app, send_from_directory


buyer_web_bp = Blueprint("buyer_web", __name__, url_prefix="/buyer")


def _buyer_frontend_dir():
    app_root = Path(current_app.root_path)
    return app_root.parent / "frontend" / "buyer"


def _serve(filename):
    frontend_dir = _buyer_frontend_dir()
    target = (frontend_dir / filename).resolve()
    if not str(target).startswith(str(frontend_dir.resolve())):
        abort(404)
    if not target.exists() or not target.is_file():
        abort(404)
    return send_from_directory(frontend_dir, filename)


@buyer_web_bp.get("/")
def buyer_index():
    return _serve("index.html")


@buyer_web_bp.get("/login")
def buyer_login():
    return _serve("login.html")


@buyer_web_bp.get("/<path:filename>")
def buyer_files(filename):
    return _serve(filename)
