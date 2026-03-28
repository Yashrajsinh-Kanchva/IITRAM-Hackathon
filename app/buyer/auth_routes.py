from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.buyer.common import as_non_empty_string, get_collections, now

try:  # pragma: no cover - optional compatibility path
    import bcrypt
except Exception:  # pragma: no cover
    bcrypt = None


auth_bp = Blueprint("buyer_auth", __name__)


def _safe_check_password_hash(password_hash, plain_password):
    try:
        return check_password_hash(str(password_hash or ""), plain_password)
    except Exception:
        return False


def _legacy_password_match(legacy_user, plain_password):
    if not legacy_user:
        return False

    password_hash = legacy_user.get("password_hash")
    if isinstance(password_hash, str) and password_hash:
        return _safe_check_password_hash(password_hash, plain_password)

    raw = legacy_user.get("password")
    if bcrypt is not None and raw:
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if isinstance(raw, (bytes, bytearray)):
            return bcrypt.checkpw(plain_password.encode("utf-8"), raw)
    return False


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    name = as_non_empty_string(data.get("name"))
    email = as_non_empty_string(data.get("email")).lower()
    password = str(data.get("password") or "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    cols = get_collections()
    users = cols["users"]
    legacy_users = cols["legacy_users"]

    if users.find_one({"email": email, "role": "buyer"}) or legacy_users.find_one(
        {"email": email}
    ):
        return jsonify({"error": "User already exists"}), 400

    timestamp = now()
    password_hash = generate_password_hash(password)
    user_id = users.insert_one(
        {
            "name": name,
            "email": email,
            "role": "buyer",
            "status": "active",
            "password_hash": password_hash,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    ).inserted_id

    # Keep legacy buyer branch compatibility data.
    legacy_users.update_one(
        {"email": email},
        {
            "$set": {
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "updated_at": timestamp,
            },
            "$setOnInsert": {"created_at": timestamp},
        },
        upsert=True,
    )

    return jsonify({"message": "Signup successful", "user_id": str(user_id)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = as_non_empty_string(data.get("email")).lower()
    password = str(data.get("password") or "")

    cols = get_collections()
    users = cols["users"]
    legacy_users = cols["legacy_users"]

    user = users.find_one({"email": email, "role": "buyer"})
    if user and user.get("status") != "active":
        return jsonify({"error": "Account is not active"}), 403

    if user and _safe_check_password_hash(user.get("password_hash"), password):
        return jsonify(
            {
                "message": "Login successful",
                "user": {
                    "id": str(user["_id"]),
                    "name": user.get("name"),
                    "email": user.get("email"),
                },
            }
        )

    legacy_user = legacy_users.find_one({"email": email})
    if _legacy_password_match(legacy_user, password):
        if not user:
            timestamp = now()
            inserted = users.insert_one(
                {
                    "name": legacy_user.get("name") or "Buyer",
                    "email": email,
                    "role": "buyer",
                    "status": "active",
                    "password_hash": legacy_user.get("password_hash")
                    or generate_password_hash(password),
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
            )
            user = users.find_one({"_id": inserted.inserted_id})
        return jsonify(
            {
                "message": "Login successful",
                "user": {
                    "id": str(user["_id"]),
                    "name": user.get("name"),
                    "email": user.get("email"),
                },
            }
        )

    return jsonify({"error": "Invalid email or password"}), 401
