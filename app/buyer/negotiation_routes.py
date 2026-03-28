from flask import Blueprint, jsonify, request

from app.buyer.common import as_non_empty_string, get_collections, now, to_object_id


negotiation_bp = Blueprint("buyer_negotiation", __name__)


@negotiation_bp.post("/submit")
def submit_negotiation():
    data = request.get_json(silent=True) or {}
    user_id = as_non_empty_string(data.get("user_id"))
    user_name = as_non_empty_string(data.get("user_name")) or "Buyer"
    product_id = as_non_empty_string(data.get("product_id"))
    message = as_non_empty_string(data.get("message"))

    try:
        negotiated_price = float(data.get("negotiated_price"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid negotiated price"}), 400
    if negotiated_price <= 0:
        return jsonify({"error": "Invalid negotiated price"}), 400

    cols = get_collections()
    product = cols["products"].find_one({"_id": to_object_id(product_id)})
    if not product:
        return jsonify({"error": "Product not found"}), 404

    cols["negotiations"].insert_one(
        {
            "user_id": user_id,
            "user_name": user_name,
            "product_id": product_id,
            "product_name": product.get("name", product.get("crop_name", "Fresh Harvest")),
            "original_price": product.get("price", product.get("base_price", 0)),
            "negotiated_price": negotiated_price,
            "message": message,
            "status": "pending",
            "created_at": now(),
            "updated_at": now(),
        }
    )
    return jsonify({"message": "Negotiation offer sent successfully!"}), 201


@negotiation_bp.get("/<user_id>")
def get_user_negotiations(user_id):
    rows = list(
        get_collections()["negotiations"]
        .find({"user_id": str(user_id)})
        .sort("created_at", -1)
    )
    for row in rows:
        row["_id"] = str(row["_id"])
    return jsonify(rows)


@negotiation_bp.post("/update/<neg_id>")
def update_negotiation(neg_id):
    oid = to_object_id(neg_id)
    if not oid:
        return jsonify({"error": "Invalid negotiation ID"}), 400

    data = request.get_json(silent=True) or {}
    try:
        new_price = float(data.get("negotiated_price"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid negotiated price"}), 400
    if new_price <= 0:
        return jsonify({"error": "Invalid negotiated price"}), 400

    new_message = as_non_empty_string(data.get("message"))
    updated = get_collections()["negotiations"].update_one(
        {"_id": oid},
        {
            "$set": {
                "negotiated_price": new_price,
                "message": new_message,
                "status": "pending",
                "updated_at": now(),
            }
        },
    )
    if updated.matched_count == 0:
        return jsonify({"error": "Negotiation not found"}), 404
    return jsonify({"message": "Negotiation offer successfully updated!"})


@negotiation_bp.post("/reject/<neg_id>")
def reject_negotiation(neg_id):
    oid = to_object_id(neg_id)
    if not oid:
        return jsonify({"error": "Invalid negotiation ID"}), 400

    updated = get_collections()["negotiations"].update_one(
        {"_id": oid},
        {"$set": {"status": "rejected", "updated_at": now()}},
    )
    if updated.matched_count == 0:
        return jsonify({"error": "Negotiation not found"}), 404
    return jsonify({"message": "Negotiation offer securely rejected."})
