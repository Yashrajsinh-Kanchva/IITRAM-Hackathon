from flask import request

from app.services.exceptions import ServiceError
from app.utils.validators import ALLOWED_USER_ROLES


def _sanitize_header(value):
    if value is None:
        return ""
    return str(value).replace("\x00", "").strip()


def extract_user_identity():
    user_id = _sanitize_header(request.headers.get("X-User-Id"))
    role = _sanitize_header(request.headers.get("X-User-Role")).lower()

    if not user_id:
        raise ServiceError("Missing X-User-Id header", status_code=401)
    if role not in ALLOWED_USER_ROLES:
        raise ServiceError("Invalid or missing X-User-Role header", status_code=401)

    return {"user_id": user_id, "role": role}
