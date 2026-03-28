from flask import Blueprint, jsonify, request

from app.buyer.common import as_non_empty_string, get_collections, normalize_product, to_object_id


wishlist_bp = Blueprint("buyer_wishlist", __name__)


@wishlist_bp.get("/<user_id>")
def get_wishlist(user_id):
    cols = get_collections()
    wishlist = cols["wishlist"].find_one({"user_id": str(user_id)})
    if not wishlist:
        return jsonify({"items": []})

    items = []
    for raw_product_id in wishlist.get("product_ids", []):
        oid = to_object_id(raw_product_id)
        if not oid:
            continue
        product = cols["products"].find_one({"_id": oid})
        if not product:
            continue
        items.append(normalize_product(product))

    return jsonify({"items": items})


@wishlist_bp.post("/toggle")
def toggle_wishlist():
    data = request.get_json(silent=True) or {}
    user_id = as_non_empty_string(data.get("user_id"))
    product_id = as_non_empty_string(data.get("product_id"))
    if not user_id or not product_id:
        return jsonify({"error": "User ID and Product ID are required"}), 400

    col = get_collections()["wishlist"]
    wishlist = col.find_one({"user_id": user_id})
    if not wishlist:
        col.insert_one({"user_id": user_id, "product_ids": [product_id]})
        return jsonify({"message": "Added to wishlist", "status": "added"})

    product_ids = list(wishlist.get("product_ids", []))
    if product_id in product_ids:
        product_ids.remove(product_id)
        col.update_one({"user_id": user_id}, {"$set": {"product_ids": product_ids}})
        return jsonify({"message": "Removed from wishlist", "status": "removed"})

    product_ids.append(product_id)
    col.update_one({"user_id": user_id}, {"$set": {"product_ids": product_ids}})
    return jsonify({"message": "Added to wishlist", "status": "added"})
